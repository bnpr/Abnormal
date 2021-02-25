import bpy
import bmesh
import math
from mathutils import Vector, kdtree, Matrix
from mathutils.geoemtry import intersect_point_tri_2d
from bpy_extras import view3d_utils

gen_mods = ['ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE',
            'EDGE_SPLIT', 'MASK', 'MIRROR', 'MULTIRES', 'REMESH',
            'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE', 'WIREFRAME'
            ]


def rotate_2d(origin, point, angle):
    x = origin[0] + math.cos(angle) * (point[0] - origin[0]) - \
        math.sin(angle) * (point[1] - origin[1])
    y = origin[1] + math.sin(angle) * (point[0] - origin[0]) + \
        math.cos(angle) * (point[1] - origin[1])

    vec = Vector((x, y))
    return vec


def refresh_bm(bm):
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return


def create_kd(bm):
    size = len(bm.verts)
    kd = kdtree.KDTree(size)

    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)

    kd.balance()

    return kd


def ob_to_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    refresh_bm(bm)

    bm.normal_update()

    return bm


def ob_to_bm_world(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    refresh_bm(bm)

    # bm in world space
    for v in bm.verts:
        v.co = ob.matrix_world @ v.co

    bm.normal_update()

    return bm


def create_simple_bm(self, ob):

    # turn off generative modifiers
    for mod in ob.modifiers:
        self._objects_mod_status.append(
            [mod.show_viewport, mod.show_render, mod.name])

        if mod.type != 'MIRROR':
            mod.show_viewport = False
            mod.show_render = False

    # worldspace object data in bmesh
    bm = ob_to_bm_world(ob)

    fac = 1
    if ob.scale[0] < .0:
        fac = -1
    if ob.scale[1] < .0:
        fac = -1
    if ob.scale[2] < .0:
        fac = -1

    if fac == -1:
        all_faces = [f for f in bm.faces]
        bmesh.ops.reverse_faces(bm, faces=all_faces)

    refresh_bm(bm)

    return bm


def force_scene_update():
    bpy.context.scene.cursor.location = bpy.context.scene.cursor.location
    return


def generate_matrix(v1, v2, v3, cross, normalized):
    a = (v2-v1)
    b = (v3-v1)

    if normalized:
        a = a.normalized()
        b = b.normalized()

    c = a.cross(b).normalized()

    if cross:
        b2 = c.cross(a)

        m = Matrix([-c, b2, a]).transposed()
    else:
        m = Matrix([-c, b, a]).transposed()
    matrix = Matrix.Translation(v1) @ m.to_4x4()
    #matrix.translation = v1

    return matrix


def average_vecs(vecs):
    if len(vecs) > 0:
        vec = Vector((0, 0, 0))
        for v in vecs:
            vec += v

        vec = vec/len(vecs)

        return vec
    return None


def get_edge_loop(bm, ed, direction=0, skip_verts=[], skip_eds=[], cross_eds=[]):
    #
    # Get edge loop from a single edge
    # Goes along verts with 4 connected edge otherwise it stops
    # Direction controls which vertice to test first
    #
    if direction == 0:
        v1 = ed.verts[0]
        v2 = ed.verts[1]
    else:
        v1 = ed.verts[1]
        v2 = ed.verts[0]
    verts = [v1, v2]

    used_eds = [ed.index]
    used_eds += skip_eds
    loop = [ed.index]
    backwards = False
    for v, vert in enumerate(verts):
        cur_vert = vert
        cur_ed = ed

        searching = True
        while searching:
            next_ed = None
            next_vert = None
            found = False

            ed_faces = [lf.index for lf in cur_ed.link_faces]

            if len(cur_vert.link_edges) == 4:
                got_ed = True
                for o_ed in cur_vert.link_edges:
                    if o_ed.index in used_eds:
                        continue

                    for lf in o_ed.link_faces:
                        if lf.index in ed_faces:
                            got_ed = False

                    if got_ed:
                        next_ed = o_ed
                        break
                    else:
                        got_ed = True

                if next_ed != None:
                    con_ed_inds = [o_ed.index for o_ed in cur_vert.link_edges if o_ed.index !=
                                   cur_ed.index and o_ed.index != next_ed.index]

                    next_vert = next_ed.other_vert(cur_vert)
                    if next_vert.index in skip_verts:
                        next_vert = None

                    for ind in con_ed_inds:
                        if ind in cross_eds:
                            next_vert = None
                            next_ed = None

                if next_vert != None and next_ed != None:

                    cur_vert = next_vert
                    cur_ed = next_ed

                    used_eds.append(cur_ed.index)
                    if backwards:
                        loop.insert(0, cur_ed.index)
                    else:
                        loop.append(cur_ed.index)
                    found = True

            searching = found
            if searching == False and v == 0:
                backwards = True
    return loop


def get_face_loop(bm, ed, skip_fs=[], skip_eds=[]):
    #
    # Get face loop from a single edge
    # Goes along linked faces until hitting a non quad face
    #

    # No linked faces so return empty list
    if len(ed.link_faces) == 0:
        return []

    used_eds = [ed.index]
    used_eds += skip_eds
    used_fs = []
    used_fs += skip_fs
    loop = []
    backwards = False

    cur_ed = ed

    searching = True
    while searching:
        next_ed = None
        next_f = None
        found = False

        ed_faces = [lf for lf in cur_ed.link_faces if len(
            lf.verts) == 4 and lf.index not in used_fs]
        if len(ed_faces) > 0:
            next_f = ed_faces[0]
            for e, f_ed in enumerate(next_f.edges):
                if f_ed.index == cur_ed.index:
                    o_ind = (e+2) % len(next_f.edges)
                    next_ed = next_f.edges[o_ind]
                    if next_ed.index not in used_eds:
                        break

        if next_f != None:
            loop.append(next_f.index)
            used_fs.append(next_f.index)
            used_eds.append(next_ed.index)
            cur_ed = next_ed
            found = True

        searching = found
        if searching == False and backwards == False:
            backwards = True
            searching = True
            cur_ed = ed

    return loop


def nearest_co_on_line(co, lv1, lv2):
    vec = (lv1 - lv2).normalized()

    v1_vec = co - lv1
    v2_vec = co - lv2

    dot = v1_vec.dot(vec)

    line_co = lv1 + dot * vec

    line_len = (lv1 - lv2).length
    v1_dist = (line_co-lv1).length
    v2_dist = (line_co-lv2).length

    if v1_dist > line_len or v2_dist > line_len:
        if v1_dist < v2_dist:
            new_co = lv1
        else:
            new_co = lv2
    else:
        new_co = line_co

    dist = (new_co-co).length

    return new_co, dist


def find_path_between_verts(verts, bm):
    #
    # Find shortest path between 2 verts. Start at first vertex and expand outward till it reaches the second vertex
    #
    v1 = bm.verts[verts[0]]
    v2 = bm.verts[verts[1]]

    cur_layer = [v1.index]
    searching, path_completed = True, False
    vert_order, edge_order, layers, found_inds = [], [], [], []
    while searching:
        found = False

        next_layer = []
        for ind in cur_layer:
            v = bm.verts[ind]
            lvs = [ed.other_vert(v).index for ed in v.link_edges if ed.other_vert(
                v).index not in found_inds]

            if v2.index in lvs:
                path_completed = True
            next_layer += lvs

        if path_completed:
            found = False
        else:
            next_layer = set(next_layer)
            if len(next_layer) > 0:
                found = True
                found_inds += next_layer
                cur_layer = next_layer.copy()
                layers.append(next_layer.copy())

        searching = found

    # Found the second vertex so construct path
    if path_completed:
        vert_order.append(v2.index)
        cur_v = bm.verts[v2.index]
        for l, layer in enumerate(layers[::-1]):
            l_eds = [ed for ed in cur_v.link_edges]
            for ed in l_eds:
                ov = ed.other_vert(cur_v)
                if ov.index in layer:
                    vert_order.insert(0, ov.index)
                    edge_order.insert(0, ed.index)
                    cur_v = bm.verts[ov.index]
                    break

        for ed in v1.link_edges:
            if ed.other_vert(v1).index == vert_order[0]:
                edge_order.insert(0, ed.index)
        vert_order.insert(0, v1.index)

    return vert_order, edge_order


def find_path_between_faces(faces, bm):
    #
    # Find shortest path between 2 f. Start at first vertex and expand outward till it reaches the second vertex
    #
    f1 = bm.faces[faces[0]]
    f2 = bm.faces[faces[1]]

    cur_layer = [f1.index]
    searching, path_completed = True, False
    face_order, layers, found_inds = [], [], []
    while searching:
        found = False

        next_layer = []
        for ind in cur_layer:
            f = bm.faces[ind]
            lfs = []
            for ed in f.edges:
                for of in ed.link_faces:
                    if of.index not in found_inds and of.index != f.index:
                        lfs.append(of.index)

            if f2.index in lfs:
                path_completed = True

            next_layer += lfs

        if path_completed:
            found = False
        else:
            next_layer = set(next_layer)
            if len(next_layer) > 0:
                found = True
                found_inds += next_layer
                cur_layer = next_layer.copy()
                layers.append(next_layer.copy())

        searching = found

    # Found the second face so construct path
    if path_completed:
        face_order.append(f2.index)

        cur_f = bm.faces[f2.index]
        for l, layer in enumerate(layers[::-1]):
            cur_len = len(face_order)
            for ed in cur_f.edges:
                for of in ed.link_faces:
                    if of.index != cur_f.index and of.index in layer:
                        face_order.insert(0, of.index)
                        cur_f = bm.faces[of.index]
                        break

                if cur_len != len(face_order):
                    break

        face_order.insert(0, f1.index)

    return face_order


#
#


def hsv_to_rgb(h, s, v, a=1.0):
    if s == 0.0:
        return (v, v, v, a)
    i = int(h*6.)  # XXX assume int() truncates!
    f = (h*6.)-i
    p, q, t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f))
    i %= 6
    if i == 0:
        return (v, t, p, a)
    if i == 1:
        return (q, v, p, a)
    if i == 2:
        return (p, v, t, a)
    if i == 3:
        return (p, q, v, a)
    if i == 4:
        return (t, p, v, a)
    if i == 5:
        return (v, p, q, a)


def hsv_to_rgb_list(hsv):
    if len(hsv) > 3:
        rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2], hsv[3])
    else:
        rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    return rgb


#
#


def ray_cast_view_occlude_test(co, mouse_co, bvh, region, rv3d):
    orig_co = view3d_utils.region_2d_to_origin_3d(
        region, rv3d, mouse_co)
    direction_to = (orig_co - co).normalized()

    occluded = False
    hit_to_view, norm_to_view, ind_to_view, dist_to_view = bvh.ray_cast(
        co+direction_to*.001, direction_to, 1000000)

    if hit_to_view != None:
        occluded = True

    return occluded


def ray_cast_to_mouse(self):
    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(
        self.act_reg, self.act_rv3d, self._mouse_reg_loc)
    ray_origin = view3d_utils.region_2d_to_origin_3d(
        self.act_reg, self.act_rv3d, self._mouse_reg_loc)

    hit, norm, ind, dist = self._object_bvh.ray_cast(
        ray_origin, view_vector, 10000)

    if hit != None and ind != None:
        return hit, ind
    return None


#
#


def get_outer_v(axis, min, cos, unavail=[]):
    val = 0
    ind = None

    for c, co in enumerate(cos):
        if c not in unavail:
            if min:
                if ind == None or co[axis] < val:
                    ind = c
                    val = co[axis]
            else:
                if ind == None or co[axis] > val:
                    ind = c
                    val = co[axis]

    return ind, val


def bounding_box_filter(shape_cos, cos):
    # GET BOUNDING BOX TO FILTER LASSO TESTING POINTS
    min_x_ind, min_x = get_outer_v(0, True, shape_cos)
    max_x_ind, max_x = get_outer_v(0, False, shape_cos)
    min_y_ind, min_y = get_outer_v(1, True, shape_cos)
    max_y_ind, max_y = get_outer_v(1, False, shape_cos)

    in_range_cos = []
    for c, co in enumerate(cos):
        if co != None:
            if min_x < co[0] < max_x and min_y < co[1] < max_y:
                in_range_cos.append(c)

    return in_range_cos


def test_point_in_shape(shape_cos, test_co):
    tot_rot = 0

    l_vec = Vector((shape_cos[0][0], shape_cos[0][1])) - test_co
    prev_vec = l_vec.copy()
    for lv in shape_cos:
        s_co = Vector((lv[0], lv[1]))

        c_vec = s_co - test_co

        ang = math.degrees(prev_vec.xy.angle_signed(c_vec.xy))

        tot_rot += ang
        prev_vec = c_vec.copy()

    ang = math.degrees(prev_vec.xy.angle_signed(l_vec.xy))

    tot_rot += ang
    if abs(tot_rot) > 180:
        return True
    else:
        return False


def vec_to_dashed(co, vec, segments):
    cos = []
    length_vec = vec / ((segments*2)+1)

    for i in range(segments+1):

        cos.append(co+(length_vec*i*2))
        cos.append(co+(length_vec*((i*2)+1)))

    return cos


def get_linked_geo(bm, inds, vis=None):
    if vis == None:
        vis = inds.copy()

    v_list = []
    for ind in inds:
        still_going = True
        if ind not in v_list and ind in vis:
            verts = [ind]
            v_list.append(ind)

            while still_going:
                found = False

                next_verts = []
                for v_ind in verts:
                    vert = bm.verts[v_ind]

                    link_eds = [ed for ed in vert.link_edges]

                    for ed in link_eds:
                        ov = ed.other_vert(vert)
                        if ov.index not in v_list and ov.index in vis:
                            next_verts.append(ov.index)
                            v_list.append(ov.index)
                            found = True

                verts = next_verts.copy()
                still_going = found
    return v_list


#
#
#


def click_points_selection_test(coords, sel_status, mouse_co, region, rv3d, shift, x_ray, bvh, active=None, radius=15):
    mouse_co = Vector(mouse_co)

    if x_ray:
        bvh = None

    change = False
    nearest_dist = -1
    nearest_point = None
    nearest_sel_point = None
    # Test selection of points
    for c, co in enumerate(coords):
        rco = view3d_utils.location_3d_to_region_2d(
            region, rv3d, co)
        if rco:
            status = sel_status[c]
            dist = (rco - mouse_co).length
            if (nearest_point == None or dist < nearest_dist) and dist < radius:
                # make sure co is valid. test occlusion if it is enabled
                valid_po = True
                if bvh:
                    valid_po = not ray_cast_view_occlude_test(
                        co, mouse_co, bvh, region, rv3d)

                if valid_po:
                    if status:
                        nearest_sel_point = c
                    else:
                        nearest_dist = dist
                        nearest_point = c

    # If no points to select then go with nearest already selected point as active
    if nearest_point == None and nearest_sel_point != None:
        nearest_point = nearest_sel_point

    # Make selection changes if a point is in range
    unselect = False
    new_active = None
    new_sel = None
    new_sel_status = False
    if nearest_point != None:
        # Unselect all and clear active point if shift not held
        unselect = not shift
        new_sel = nearest_point
        new_active = nearest_point
        new_sel_status = True

        if active != None and nearest_point == active and shift:
            new_active = None
            new_sel_status = False

        change = True

    return change, unselect, new_active, new_sel, new_sel_status


def click_tris_selection_test(tris, sel_status, mouse_co, region, rv3d, shift, x_ray, bvh, active=None, radius=15):
    mouse_co = Vector(mouse_co)

    if x_ray:
        bvh = None

    change = False
    nearest_dist = -1
    nearest_tri = None
    nearest_sel_tri = None
    # Test selection of tris
    for t, tri_set in enumerate(tris):
        status = sel_status[t]
        if nearest_sel_tri == None and nearest_tri == None:
            p1 = view3d_utils.location_3d_to_region_2d(
                region, rv3d, tri_set[0])
            p2 = view3d_utils.location_3d_to_region_2d(
                region, rv3d, tri_set[1])
            p3 = view3d_utils.location_3d_to_region_2d(
                region, rv3d, tri_set[2])

            if p1 and p2 and p3:
                intersect = intersect_point_tri_2d(
                    mouse_co, p1, p2, p3)
                if intersect != 0:
                    if bvh:
                        all_true = True
                        for co in tri_set:
                            no_hit = not ray_cast_view_occlude_test(
                                co, mouse_co, bvh, region, rv3d)

                            if no_hit == False:
                                all_true = False

                        if all_true:
                            if status == False:
                                if nearest_tri == None:
                                    nearest_tri = t
                            else:
                                if nearest_sel_tri == None:
                                    nearest_sel_tri = t
                    else:
                        if status == False:
                            if nearest_tri == None:
                                nearest_tri = t
                        else:
                            if nearest_sel_tri == None:
                                nearest_sel_tri = t

    # If no new tris to select then go with nearest already selected tri as active or remove
    if nearest_tri == None and nearest_sel_tri != None:
        nearest_tri = nearest_sel_tri

    # Make selection changes if a tri is in range
    unselect = False
    new_active = None
    new_sel = None
    new_sel_status = False
    if nearest_tri != None:
        # Unselect all and clear active tri if shift not held
        unselect = not shift
        new_sel = nearest_tri
        new_active = nearest_tri
        new_sel_status = True

        if active != None and nearest_tri == active and shift:
            new_active = None
            new_sel_status = False

        change = True
    return change, unselect, new_active, new_sel, new_sel_status


def box_points_selection_test(coords, sel_status, mouse_co, corner_co, region, rv3d, add_rem_status, x_ray, bvh, active=None, just_one=False):
    mouse_co = Vector(mouse_co)

    if x_ray:
        bvh = None

    low_x = corner_co[0]
    hi_x = mouse_co[0]
    low_y = corner_co[1]
    hi_y = mouse_co[1]

    if corner_co[0] > mouse_co[0]:
        low_x = mouse_co[0]
        hi_x = corner_co[0]

    if corner_co[1] > mouse_co[1]:
        low_y = mouse_co[1]
        hi_y = corner_co[1]

    change = False
    unselect = add_rem_status == 0
    new_active = active
    new_sel_add = []
    new_sel_remove = []
    for c, co in enumerate(coords):
        rco = view3d_utils.location_3d_to_region_2d(
            region, rv3d, co)
        if rco:
            status = sel_status[c]
            if rco[0] > low_x and rco[0] < hi_x and rco[1] > low_y and rco[1] < hi_y:
                if bvh:
                    no_hit = not ray_cast_view_occlude_test(
                        co, mouse_co, bvh, region, rv3d)
                    # INSIDE BOX AND IN VIEW
                    if no_hit:
                        if add_rem_status == 0:
                            new_sel_add.append(c)
                            change = True
                        elif add_rem_status == 2:
                            if status:
                                new_sel_remove.append(c)
                                change = True
                        else:
                            if status != True:
                                new_sel_add.append(c)
                                change = True

                # INSIDE BOX NO BVH TEST
                else:
                    if add_rem_status == 0:
                        new_sel_add.append(c)
                        change = True
                    elif add_rem_status == 2:
                        if status:
                            new_sel_remove.append(c)
                            change = True
                    else:
                        if status != True:
                            new_sel_add.append(c)
                            change = True
                if change and just_one:
                    break

    if active != None and active in new_sel_remove:
        new_active = None

    return change, unselect, new_active, new_sel_add, new_sel_remove


def circle_points_selection_test(coords, sel_status, mouse_co, radius, region, rv3d, add_rem_status, x_ray, bvh, active=None, just_one=False):
    mouse_co = Vector(mouse_co)

    if x_ray:
        bvh = None

    change = False
    unselect = False
    new_active = active
    new_sel = []
    new_sel_status = add_rem_status != 2
    for c, co in enumerate(coords):
        rco = view3d_utils.location_3d_to_region_2d(
            region, rv3d, co)
        if rco:
            status = sel_status[c]
            dist = (rco - mouse_co).length
            if dist < radius:
                if bvh:
                    no_hit = not ray_cast_view_occlude_test(
                        co, mouse_co, bvh, region, rv3d)
                    if no_hit:
                        if add_rem_status == 2:
                            if status:
                                new_sel.append(c)
                                change = True
                        else:
                            if status != True:
                                new_sel.append(c)
                                change = True

                else:
                    if add_rem_status == 2:
                        if status:
                            new_sel.append(c)
                            change = True
                    else:
                        if status != True:
                            new_sel.append(c)
                            change = True
                if change and just_one:
                    break

    if active != None and active in new_sel and new_sel_status == False:
        new_active = None

    return change, unselect, new_active, new_sel, new_sel_status


def lasso_points_selection_test(lasso_points, coords, sel_status, mouse_co, region, rv3d, add_rem_status, x_ray, bvh, active=None, just_one=False):
    mouse_co = Vector(mouse_co)

    if x_ray:
        bvh = None

    change = False
    unselect = add_rem_status == 0
    new_active = None
    new_sel_add = []
    new_sel_remove = []
    in_range_inds = bounding_box_filter(lasso_points, [
                                        view3d_utils.location_3d_to_region_2d(region, rv3d, co) for co in coords])
    for c, co in enumerate(coords):
        status = sel_status[c]
        if c in in_range_inds:
            rco = view3d_utils.location_3d_to_region_2d(
                region, rv3d, co)
            if rco:
                sel_res = test_point_in_shape(lasso_points, rco)
                if sel_res:
                    if bvh:
                        no_hit = not ray_cast_view_occlude_test(
                            co, mouse_co, bvh, region, rv3d)
                        # INSIDE BOX AND IN VIEW
                        if no_hit:
                            if add_rem_status == 0:
                                new_sel_add.append(c)
                                change = True
                            elif add_rem_status == 2:
                                if status:
                                    new_sel_remove.append(c)
                                    change = True
                            else:
                                if status != True:
                                    new_sel_add.append(c)
                                    change = True
                        # # INSIDE BOX BUT NOT IN VIEW
                        # else:
                        #     if add_rem_status == 0:
                        #         if status:
                        #             new_sel_remove.append(c)
                        #             change = True

                    # INSIDE BOX NO BVH TEST
                    else:
                        if add_rem_status == 0:
                            new_sel_add.append(c)
                            change = True
                        elif add_rem_status == 2:
                            if status:
                                new_sel_remove.append(c)
                                change = True
                        else:
                            if status != True:
                                new_sel_add.append(c)
                                change = True

                # else:
                #     if add_rem_status == 0:
                #         if status:
                #             new_sel_remove.append(c)
                #             change = True
                    if change and just_one:
                        break

    if active != None and active in new_sel_remove:
        new_active = None

    return change, unselect, new_active, new_sel_add, new_sel_remove
