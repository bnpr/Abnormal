import bpy
import bmesh
import math
import numpy as np
from mathutils import Vector, kdtree, Matrix
from mathutils.geometry import intersect_point_tri_2d
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

    bm.transform(ob.matrix_world)

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


def find_path_between_verts(verts, bm, skip_verts=[]):
    #
    # Find shortest path between 2 verts. Start at first vertex and expand outward till it reaches the second vertex
    #
    v1 = bm.verts[verts[0]]
    v2 = bm.verts[verts[1]]

    cur_layer = [v1.index]
    searching, path_completed = True, False
    vert_order, edge_order, layers, found_inds = [], [], [], []
    found_inds += skip_verts
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

    else:
        vert_order = [v2.index]

    return vert_order, edge_order


def find_path_between_faces(faces, bm, skip_fs=[]):
    #
    # Find shortest path between 2 f. Start at first vertex and expand outward till it reaches the second vertex
    #
    f1 = bm.faces[faces[0]]
    f2 = bm.faces[faces[1]]

    cur_layer = [f1.index]
    searching, path_completed = True, False
    face_order, layers, found_inds = [], [], []
    found_inds += skip_fs
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


def get_normalized_reg_cos(coords, mat, depth_dist):
    #
    # Get region coordinates at a normalized depth from a set of coordinates
    #
    cos = np.array(coords)
    cos.shape = [len(coords), 3]

    pmat = mat[:3, :3].T  # rotates backwards without T
    loc = mat[:3, 3]
    r_cos = cos @ pmat + loc

    # Scale sscos to be on a flat plane 1.5 from view matrix
    # -1.5 / r_cos[:,2] Gets a scale factor for each coord based on its depth in comparison with the value used
    # [:,None] rebroadcasts the single scale value into a column to scale along the rows or coords of the ss cos
    r_cos *= (-depth_dist / r_cos[:, 2])[:, None]
    return r_cos


def get_np_region_cos(coords, region, region_data, depth=1.5):
    #
    # Use numpy to get coords in region space
    # Bottom Left of region is 0,0
    #

    mat = np.array(region_data.view_matrix)
    pmat = mat[:3, :3].T
    loc = mat[:3, 3]
    r_cos = get_normalized_reg_cos(coords, mat, depth)

    # Get the bottom left and bottom right coords projected into 3d space
    # This gives us the region width for scaling our region coords
    center_co = pmat @ Vector(np.array([0, 0, -1.5])-loc)
    vec1 = view3d_utils.region_2d_to_location_3d(
        region, region_data, [0, 0], center_co)
    vec2 = view3d_utils.region_2d_to_location_3d(
        region, region_data, [region.width, 0], center_co)

    width = (vec2-vec1).length
    scale = region.width/width

    origin = get_normalized_reg_cos([vec1], mat, 1.5) * scale

    # Scale up the sscords and offset them
    r_cos *= scale
    r_cos[:, 0] -= origin[0][0]
    r_cos[:, 1] -= origin[0][1]
    r_cos[:, 2] = 0.0

    return r_cos


def get_np_vec_dists(array, test_co):
    #
    # Given a vector numpy array get distance to test coord
    # Subtract test_co from array, Square each axis,
    # get the square root of each axis, and sum the axis of each vector for a distance
    #
    dists = np.sqrt(np.sum(np.square(array-test_co), axis=1))
    return dists


def get_np_vec_ordered_dists(array, test_co, threshold=None):
    #
    # Given a vector numpy array get distance to test coord
    # Subtract test_co from array, Square each axis,
    # get the square root of each axis, and sum the axis of each vector for a distance
    #
    dists = get_np_vec_dists(array, test_co)
    dist_inds = np.argsort(dists)
    if threshold != None:
        mask = dists < threshold
        dist_inds = dist_inds[mask[dist_inds]]

    return dist_inds


def get_np_nearest_co_on_edge(edge_cos, test_co):
    #
    # Given a list of edge coords (2 vectors per edge)
    # we get the nearest coordinate project onto the edge
    # the nearest coordinate will clamp to the ends of the edge
    #

    edge_vecs = edge_cos[:, 1] - edge_cos[:, 0]
    edge_vecs_norm = edge_vecs * \
        (1 / np.sqrt(np.sum(np.square(edge_vecs), axis=1)))[:, None]

    test_co = np.array(test_co)

    test_vecs = test_co - edge_cos[:, 0]

    dots = np.sum(edge_vecs_norm * test_vecs, axis=1)
    ed_lens = np.sqrt(np.sum(np.square(edge_vecs), axis=1))

    # Get the status of which projected coords are outside of the edges bounds
    off_ed_a = dots > ed_lens
    off_ed_b = dots < 0.0

    coords = edge_cos[:, 0] + edge_vecs_norm * dots[:, None]
    coords[off_ed_b] = edge_cos[:, 0][off_ed_b]
    coords[off_ed_a] = edge_cos[:, 1][off_ed_a]

    return coords


def get_np_dist_to_edge(edge_cos, test_co):
    #
    # Given a list of edge coords (2 vectors per edge)
    # we get the nearest coordinate project onto the edge
    # the nearest coordinate will clamp to the ends of the edge
    #
    coords = get_np_nearest_co_on_edge(edge_cos, test_co)

    dists = np.sqrt(np.sum(np.square(np.array(test_co) - coords), axis=1))
    return dists


def get_np_nearest_edge_order(edge_cos, test_co):
    #
    # Given a list of edge coords (2 vectors per edge)
    # we get the clipped distance from the test coord onto the edges
    # and then sort the distances from smallest to longest
    #
    return np.argsort(get_np_dist_to_edge(edge_cos, test_co))


#
#


def get_np_normalized_vecs(array):
    #
    # Given a vector numpy array normalize each vector
    #
    scale = 1 / np.sqrt(np.sum(np.square(array), axis=1))
    return array*scale[:, None]


def np_box_selection_test(cos, x_cos, y_cos):
    #
    # Test if coords inside a box
    # tests the 2 axis min and max and filters the shape until only
    # points inside are left True
    #
    in_range_inds = cos[:, 0] > x_cos.min()
    x_max = cos[:, 0] < x_cos.max()
    y_min = cos[:, 1] > y_cos.min()
    y_max = cos[:, 1] < y_cos.max()

    in_range_inds[~x_max] = False
    in_range_inds[~y_min] = False
    in_range_inds[~y_max] = False

    return in_range_inds.nonzero()[0]


def np_test_co_in_shape(cos, shape_arr):
    #
    # Test if coord inside a shape
    # Gets vectors from the points to the shape coords
    # Gets a rolled set of the same vectors to get the angles between the points
    # if total summed rotation angle is greater than 180 it is inside shape
    # if the point is outisde shape the total rotation angle would be 0
    # inside is a sum rotation of 360 but I use 180 just to be safe
    #
    in_shape = False

    roll_arr = np.roll(shape_arr, 1, axis=0)

    vecs_a = get_np_normalized_vecs(shape_arr - cos)
    vecs_b = get_np_normalized_vecs(roll_arr - cos)

    tot_rot = math.degrees(np.sum(np.arccos(np.sum(vecs_a * vecs_b, axis=1))))
    if tot_rot >= 180:
        in_shape = True

    return in_shape


def np_test_cos_in_shape(cos, shape_arr):
    #
    # Test if coords inside a shape
    # Gets vectors from the points to the shape coords
    # Gets a rolled set of the same vectors to get the angles between the points
    # if total summed rotation angle is greater than 180 it is inside shape
    # if the point is outisde shape the total rotation angle would be 0
    # inside is a sum rotation of 360 but I use 180 just to be safe
    #
    vecs_a = shape_arr - cos[:, np.newaxis]
    shape = vecs_a.shape
    vecs_a.shape = [shape[0]*shape[1], 3]
    vecs_a = get_np_normalized_vecs(vecs_a)
    vecs_a.shape = shape

    vecs_b = np.roll(vecs_a, 1, axis=1)

    angs = np.arccos(np.sum(vecs_a * vecs_b, axis=2))
    sign = np.sum(np.cross(vecs_a, vecs_b), axis=2)
    angs[sign <= 0.0] *= -1
    tot_rots = np.degrees(np.sum(angs, axis=1))

    in_shape = np.absolute(tot_rots) >= 180
    return in_shape.nonzero()[0]
