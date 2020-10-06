import bpy
import mathutils
import os
from bpy_extras import view3d_utils
from .functions_general import *
from .functions_drawing import *
from .functions_modal_keymap import *
from .classes import *


def match_point_loops_vecs(self, po, o_tangs, flip_axis=None):

    match_inds = []
    for loop in self._object_bm.verts[po.index].link_loops:
        tang = loop.calc_tangent()

        small = 0
        small_ind = None
        for o, o_tang in enumerate(o_tangs):
            t_tang = o_tang.copy()
            if flip_axis != None:
                t_tang[flip_axis] *= -1

            ang = tang.angle(t_tang)
            if ang < small or small_ind == None:
                small_ind = o
                small = ang

        match_inds.append(small_ind)

    return match_inds


def match_point_loops_index(self, po, o_po, flip_axis=None):

    match_inds = []
    for loop in self._object_bm.verts[po.index].link_loops:
        tang = loop.calc_tangent()

        small = 0
        small_ind = None
        for o, o_loop in enumerate(self._object_bm.verts[o_po.index].link_loops):
            t_tang = o_loop.calc_tangent()
            if flip_axis != None:
                t_tang[flip_axis] *= -1

            ang = tang.angle(t_tang)
            if ang < small or small_ind == None:
                small_ind = o
                small = ang

        match_inds.append(small_ind)
    return match_inds


#
#


def set_new_normals(self,):
    for ed in self._object.data.edges:
        ed.use_edge_sharp = self.og_sharp_edges[ed.index]

    new_l_norms = self.og_loop_norms.copy()
    for po in self._points_container.points:
        for loop in po.loops:
            new_l_norms[loop.loop_index] = loop.normal.normalized()

    self._object.data.normals_split_custom_set(new_l_norms)

    return


def loop_norm_set(self, po, l, og_vec, to_vec):
    weight = None
    if self._filter_weights != None:
        weight = self._filter_weights[po.index]

    if weight == None:
        new_vec = get_locked_normal(
            self, po.loops[l].normal, to_vec).normalized()
    else:
        new_vec = get_locked_normal(
            self, po.loops[l].normal, og_vec.lerp(to_vec, weight)).normalized()

    po.loops[l].normal = new_vec
    return


def get_locked_normal(self, cur_vec, tar_vec):
    new_vec = cur_vec.copy()

    if self._lock_x == False:
        new_vec[0] = tar_vec[0]
    if self._lock_y == False:
        new_vec[1] = tar_vec[1]
    if self._lock_z == False:
        new_vec[2] = tar_vec[2]

    return new_vec


def mirror_normals(self, po_inds, axis):
    for ind in po_inds:
        po = self._points_container.points[ind]
        co = self._object.matrix_world.inverted() @ po.co
        co[axis] *= -1

        co = self._object.matrix_world @ co

        result = self._object_kd.find(co)
        if result != None:
            if result[1] != po.index:
                o_po = self._points_container.points[result[1]]
                if o_po.valid:
                    inds = match_point_loops_index(
                        self, o_po, po, flip_axis=axis)

                    for o_loop in o_po.loops:
                        loop = po.loops[inds[o_loop.index]]

                        mir_norm = loop.normal.copy()
                        mir_norm[axis] *= -1

                        o_loop.normal = get_locked_normal(
                            self, o_loop.normal, mir_norm)
                self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def incremental_rotate_vectors(self, sel_pos, axis, increment):
    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)

    cache_norms = self._points_container.get_current_normals(sel_pos)

    self._mode_cache.clear()
    self._mode_cache.append(self._mouse_reg_loc)
    self._mode_cache.append(avg_loc)
    self._mode_cache.append(cache_norms)
    self._mode_cache.append(0)

    self.translate_mode = 2
    self.translate_axis = axis
    rotate_vectors(self, math.radians(increment * self._rot_increment))
    self.translate_mode = 0
    self.translate_axis = 2
    self._mode_cache.clear()
    self.redraw = True
    return


def rotate_vectors(self, angle):
    sel_pos = self._points_container.get_selected()

    for p, p_ind in enumerate(sel_pos):
        po = self._points_container.points[p_ind]
        if self.translate_mode == 0:
            mouse_co = mathutils.Vector(
                (self._mouse_reg_loc[0], self._mouse_reg_loc[1]))
            rco = view3d_utils.location_3d_to_region_2d(
                self.act_reg, self.act_rv3d, po.co)

            co1 = view3d_utils.region_2d_to_location_3d(
                self.act_reg, self.act_rv3d, rco, po.co)
            rco[0] += 10
            co2 = view3d_utils.region_2d_to_location_3d(
                self.act_reg, self.act_rv3d, rco, po.co)
            rco[0] -= 10
            rco[1] -= 10
            co3 = view3d_utils.region_2d_to_location_3d(
                self.act_reg, self.act_rv3d, rco, po.co)

            co4 = co1 + (co3-co1).cross(co2-co1)

            mat = generate_matrix(co1, co4, co2, True, True)
            mat.translation = po.co

        elif self.translate_mode == 1:
            mat = generate_matrix(mathutils.Vector((0, 0, 0)), mathutils.Vector(
                (0, 0, 1)), mathutils.Vector((0, 1, 0)), False, True)
            mat.translation = po.co

        elif self.translate_mode == 2:
            if self.gizmo_click:
                mat = self._orbit_ob.matrix_world.normalized()
                mat.translation = po.co
            else:
                mat = self._object.matrix_world.normalized()
                mat.translation = po.co

        for loop in po.loops:
            og_norm = self._mode_cache[2][p][loop.index]
            vec_local = mat.inverted() @ (self._object.matrix_world @
                                          (self._object.data.vertices[po.index].co+og_norm))

            if self.translate_axis == 0:
                rot_vec = rotate_2d([0, 0], vec_local.yz, angle)

                vec_local[1] = rot_vec[0]
                vec_local[2] = rot_vec[1]

            if self.translate_axis == 1:
                rot_vec = rotate_2d([0, 0], vec_local.xz, angle)

                vec_local[0] = rot_vec[0]
                vec_local[2] = rot_vec[1]

            if self.translate_axis == 2:
                rot_vec = rotate_2d([0, 0], vec_local.xy, angle)

                vec_local[0] = rot_vec[0]
                vec_local[1] = rot_vec[1]

            loop_norm_set(self, po, loop.index, og_norm, ((self._object.matrix_world.inverted(
            ) @ (mat @ vec_local)) - self._object.data.vertices[po.index].co).normalized())

    set_new_normals(self)
    return


#
# AXIS ALIGNMENT
#


def flatten_normals(self, po_inds, axis):
    update_filter_weights(self)
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for loop in po.loops:
                vec = loop.normal.copy()
                vec[axis] = 0.0

                if vec.length > 0.0:
                    loop_norm_set(self, po, loop.index, loop.normal, vec)
            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def align_to_axis_normals(self, po_inds, axis, dir):
    update_filter_weights(self)
    vec = mathutils.Vector((0, 0, 0))

    vec[axis] = 1.0*dir
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for loop in po.loops:
                loop_norm_set(self, po, loop.index, loop.normal, vec.copy())
            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# MANIPULATE NORMALS
#


def average_vertex_normals(self, po_inds):
    update_filter_weights(self)
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            vec = average_vecs([loop.normal for loop in po.loops])

            for loop in po.loops:
                loop_norm_set(self, po, loop.index, loop.normal, vec.copy())
            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def average_selected_normals(self, po_inds):
    update_filter_weights(self)
    avg_vec = mathutils.Vector((0, 0, 0))
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            vec = average_vecs([loop.normal for loop in po.loops])
            avg_vec += vec

            self.redraw = True

    avg_vec = (avg_vec/len(po_inds)).normalized()

    if avg_vec.length > 0.0:
        for ind in po_inds:
            po = self._points_container.points[ind]
            if po.valid:
                for loop in po.loops:
                    loop_norm_set(self, po, loop.index,
                                  loop.normal, avg_vec.copy())
        set_new_normals(self)
        add_to_undostack(self, 1)

    return


def smooth_normals(self, po_inds, fac):
    update_filter_weights(self)
    calc_norms = None
    for i in range(self._smooth_iterations):
        calc_norms = []
        for po in self._points_container.points:

            if len(po.loops) > 0 and po.valid:
                vec = mathutils.Vector((0, 0, 0))
                for loop in po.loops:
                    vec += loop.normal

                vec = vec/len(po.loops)

                calc_norms.append(vec)

            else:
                calc_norms.append(None)

        for ind in po_inds:
            po = self._points_container.points[ind]

            l_vs = [ed.other_vert(self._object_bm.verts[ind])
                    for ed in self._object_bm.verts[ind].link_edges]

            for loop in po.loops:
                smooth_vec = mathutils.Vector((0, 0, 0))

                cnt = 0
                for ov in l_vs:
                    if calc_norms[ov.index] != None:
                        smooth_vec += loop.normal.lerp(
                            calc_norms[ov.index], fac)
                        cnt += 1

                if cnt > 0:
                    smooth_vec = smooth_vec/cnt
                    loop_norm_set(self, po, loop.index, loop.normal, loop.normal.lerp(
                        smooth_vec, self._smooth_strength))

            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# NORMAL DIRECTION
#


def flip_normals(self, po_inds):
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for loop in po.loops:
                loop.normal *= -1
            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def set_outside_inside(self, po_inds, direction):
    update_filter_weights(self)
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            if self._object_smooth:
                poly_norm = mathutils.Vector((0, 0, 0))
                for loop in po.loops:
                    for loop in self._object_bm.verts[po.index].link_loops:
                        poly_norm += self._object.data.polygons[loop.face.index].normal * direction

                if poly_norm.length > 0.0:
                    for loop in po.loops:
                        loop_norm_set(
                            self, po, loop.index, loop.normal, poly_norm/len(po.loops))

            else:
                for loop in po.loops:
                    loop.normal = self._object_bm.loops[loop.loop_index].face.normal.copy(
                    ) * direction

            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def reset_normals(self, po_inds):
    for ind in po_inds:
        po = self._points_container.points[ind]
        po.reset_loops()

        self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# COPY/PASTE
#


def copy_active_to_selected(self, po_inds):
    update_filter_weights(self)
    if self._active_point != None:
        for ind in po_inds:
            if ind != self._active_point:
                po = self._points_container.points[ind]
                if po.valid:
                    inds = match_point_loops_index(
                        self, po, self._points_container.points[self._active_point])
                    for loop in po.loops:
                        loop_norm_set(
                            self, po, loop.index, loop.normal, self._points_container.points[self._active_point].loops[inds[loop.index]].normal.copy())

        self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def copy_active_normal(self):
    if self._active_point != None:
        po = self._points_container.points[self._active_point]
        if po.valid:
            self._copy_normals = [loop.normal for loop in po.loops]
            self._copy_normals_tangs = []
            self._copy_normal_ind = po.index

            for o_loop in self._object_bm.verts[po.index].link_loops:
                self._copy_normals_tangs.append(o_loop.calc_tangent())
    return


def paste_normal(self, po_inds):
    update_filter_weights(self)
    if self._copy_normals != None and self._copy_normals_tangs != None and self._copy_normal_ind != None:
        for ind in po_inds:
            po = self._points_container.points[ind]
            if po.valid:
                inds = match_point_loops_vecs(
                    self, po, self._copy_normals_tangs)
                for loop in po.loops:
                    loop_norm_set(
                        self, po, loop.index, loop.normal, self._copy_normals[inds[loop.index]].copy())

                self.redraw = True
    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
#


def translate_axis_draw(self):
    mat = None
    if self.translate_mode == 0:
        self.translate_draw_line.clear()

    elif self.translate_mode == 1:
        mat = generate_matrix(mathutils.Vector((0, 0, 0)), mathutils.Vector(
            (0, 0, 1)), mathutils.Vector((0, 1, 0)), False, True)
        mat.translation = self._mode_cache[1]

    elif self.translate_mode == 2:
        mat = self._object.matrix_world.normalized()
        mat.translation = self._mode_cache[1]

    if mat != None:
        self.translate_draw_line.clear()
        if self.translate_axis == 0:
            self.translate_draw_line.append(
                mat @ mathutils.Vector((1000, 0, 0)))
            self.translate_draw_line.append(
                mat @ mathutils.Vector((-1000, 0, 0)))
        if self.translate_axis == 1:
            self.translate_draw_line.append(
                mat @ mathutils.Vector((0, 1000, 0)))
            self.translate_draw_line.append(
                mat @ mathutils.Vector((0, -1000, 0)))
        if self.translate_axis == 2:
            self.translate_draw_line.append(
                mat @ mathutils.Vector((0, 0, 1000)))
            self.translate_draw_line.append(
                mat @ mathutils.Vector((0, 0, -1000)))
    self.batch_translate_line = batch_for_shader(
        self.shader_3d, 'LINES', {"pos": self.translate_draw_line})
    return


def clear_translate_axis_draw(self):
    self.batch_translate_line = batch_for_shader(
        self.shader_3d, 'LINES', {"pos": []})
    return


def translate_axis_change(self, text, axis):
    if self.translate_axis != axis:
        self.translate_axis = axis
        self.translate_mode = 1

    else:
        self.translate_mode += 1
        if self.translate_mode == 3:
            self.translate_mode = 0
            self.translate_axis = 2

    if self.translate_mode == 0:
        self._window.set_status('VIEW ' + text)
    elif self.translate_mode == 1:
        self._window.set_status('GLOBAL ' + text)
    else:
        self._window.set_status('LOCAL ' + text)

    translate_axis_draw(self)

    sel_pos = self._points_container.get_selected()
    for i, ind in enumerate(sel_pos):
        po = self._points_container.points[ind]

        for loop in po.loops:
            loop.normal = self._mode_cache[2][i][loop.index].copy()

    return


def translate_axis_side(self):
    view_vec = view3d_utils.region_2d_to_vector_3d(
        self.act_reg, self.act_rv3d, mathutils.Vector((self._mouse_reg_loc[0], self._mouse_reg_loc[1])))

    if self.translate_mode == 1:
        mat = generate_matrix(mathutils.Vector((0, 0, 0)), mathutils.Vector(
            (0, 0, 1)), mathutils.Vector((0, 1, 0)), False, True)
    else:
        mat = self._object.matrix_world.normalized()

    pos_vec = mathutils.Vector((0, 0, 0))
    neg_vec = mathutils.Vector((0, 0, 0))
    pos_vec[self.translate_axis] = 1.0
    neg_vec[self.translate_axis] = -1.0

    pos_vec = (mat @ pos_vec) - mat.translation
    neg_vec = (mat @ neg_vec) - mat.translation

    if pos_vec.angle(view_vec) < neg_vec.angle(view_vec):
        side = -1
    else:
        side = 1

    if self.translate_axis == 1:
        side *= -1
    return side


#
# MODAL
#


def cache_point_data(self):
    self._object.data.calc_normals_split()

    self.og_loop_norms = [loop.normal.copy()
                          for loop in self._object.data.loops]
    self.og_sharp_edges = [ed.use_edge_sharp for ed in self._object.data.edges]

    for v in self._object_bm.verts:
        ed_inds = [ed.index for ed in v.link_edges]
        if len(v.link_loops) > 0:
            loop_inds = [l.index for l in v.link_loops]
            loop_f_inds = [l.face.index for l in v.link_loops]
            loop_norms = [
                self._object.data.loops[l.index].normal for l in v.link_loops]

            loop_tri_cos = []
            for loop in v.link_loops:
                loop_cos = [v.co+v.normal*.001]
                for ed in loop.face.edges:
                    if ed.index in ed_inds:
                        ov = ed.other_vert(v)
                        vec = (ov.co+ov.normal*.001) - (v.co+v.normal*.001)

                        loop_cos.append((v.co+v.normal*.001) + vec * 0.5)
                loop_tri_cos.append(loop_cos)

            po = self._points_container.add_point(
                v.co, v.normal, loop_norms, loop_inds, loop_f_inds, loop_tri_cos)
        else:
            po = self._points_container.add_empty_point(
                v.co, mathutils.Vector((0, 0, 1)))

        po.set_hide(v.hide)
        po.set_select(v.select)

    return


def update_filter_weights(self):
    abn_props = bpy.context.scene.abnormal_props
    weights = None
    if abn_props.vertex_group != '':
        if abn_props.vertex_group in self._object.vertex_groups:
            weights = []

            for ind in range(len(self._points_container.points)):
                vg = self._object.vertex_groups[abn_props.vertex_group]

                try:
                    weights.append(vg.weight(ind))

                except:
                    weights.append(0.0)

        else:
            abn_props.vertex_group = ''

    self._filter_weights = weights
    return


def init_nav_list(self):
    self.nav_list = ['LEFTMOUSE', 'MOUSEMOVE',
                     'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'N']

    names = ['Zoom View', 'Rotate View', 'Pan View', 'Dolly View',
             'View Selected', 'View Camera Center', 'View All', 'View Axis',
             'View Orbit', 'View Roll', 'View Persp/Ortho', ]

    config = bpy.context.window_manager.keyconfigs.get('blender')
    if config:
        for item in config.keymaps['3D View'].keymap_items:
            if item.name in names:
                if item.type not in self.nav_list:
                    self.nav_list.append(item.type)

    config = bpy.context.window_manager.keyconfigs.get('blender user')
    if config:
        for item in config.keymaps['3D View'].keymap_items:
            if item.name in names:
                if item.type not in self.nav_list:
                    self.nav_list.append(item.type)

    return


def ob_data_structures(self, ob):
    if ob.data.shape_keys != None:
        for sk in ob.data.shape_keys.key_blocks:
            self._objects_sk_vis.append(sk.mute)
            sk.mute = True

    bm = create_simple_bm(self, ob)

    bvh = mathutils.bvhtree.BVHTree.FromBMesh(bm)

    kd = create_kd(bm)

    return bm, kd, bvh


def add_to_undostack(self, stack_type):
    if stack_type == 0:
        sel_status = self._points_container.get_selected()

        if self._history_position > 0:
            while self._history_position > 0:
                self._history_stack.pop(0)
                self._history_position -= 1

        if len(self._history_stack)+1 > self._history_steps:
            self._history_stack.pop(-1)
        self._history_stack.insert(0, [stack_type, sel_status])

    else:
        cur_normals = self._points_container.get_current_normals()
        if self._history_position > 0:
            while self._history_position > 0:
                self._history_stack.pop(0)
                self._history_position -= 1

        if len(self._history_stack)+1 > self._history_steps:
            self._history_stack.pop(-1)
        self._history_stack.insert(0, [stack_type, cur_normals])

    return


def move_undostack(self, dir):
    if dir > 0 and len(self._history_stack)-1 > self._history_position or dir < 0 and self._history_position > 0:
        self._history_position += dir

        state_type = self._history_stack[self._history_position][0]
        state = self._history_stack[self._history_position][1]

        if state_type == 0:
            for po in self._points_container.points:
                if po.index in state:
                    po.select = True
                else:
                    po.select = False

            if self._active_point != None:
                if self._points_container.points[self._active_point].select == False:
                    self._active_point = None

            update_orbit_empty(self)
            self.redraw = True

        if state_type == 1:
            for po in self._points_container.points:
                for loop in po.loops:
                    loop.normal = norms_state[po.index][loop.index].copy()

            self.redraw = True
            set_new_normals(self)

    return


def img_load(img_name, path):
    script_file = os.path.realpath(path)
    directory = os.path.dirname(script_file)

    img_fp = directory.replace('/', '\\') + '\\' + img_name

    not_there = True
    for img in bpy.data.images:
        if img.filepath == img_fp:
            not_there = False
            break

    if not_there:
        img = bpy.data.images.load(img_fp)
    img.colorspace_settings.name = 'Raw'

    if img.gl_load():
        raise Exception()

    return img


def finish_modal(self, restore):
    if bpy.context.area != None:
        if bpy.context.area.type == 'VIEW_3D':
            for space in bpy.context.area.spaces:
                if space.type == 'VIEW_3D':
                    space.show_region_toolbar = self._reg_header
                    space.show_region_ui = self._reg_ui
                    space.overlay.show_cursor = self._cursor
                    space.overlay.show_wireframes = self._wireframe
                    space.overlay.wireframe_threshold = self._thresh
                    space.overlay.show_text = self._text
    bpy.context.window.cursor_modal_set('DEFAULT')
    clear_drawing(self)
    delete_orbit_empty(self)
    if self._target_emp != None:
        try:
            bpy.data.objects.remove(self._target_emp)
        except:
            self._target_emp = None

    if restore:
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        # restore normals
        ob.data.normals_split_custom_set(self.og_loop_norms)

        for ed in self._object.data.edges:
            ed.use_edge_sharp = self.og_sharp_edges[ed.index]

    restore_modifiers(self)

    abn_props = bpy.context.scene.abnormal_props
    abn_props.object = ''

    self._object.select_set(True)
    bpy.context.view_layer.objects.active = self._object
    return


def restore_modifiers(self):
    if self._object.data.shape_keys != None:
        for s in range(len(self._object.data.shape_keys.key_blocks)):
            self._object.data.shape_keys.key_blocks[s].mute = self._objects_sk_vis[s]

    # restore modifier status
    for m, mod in enumerate(self._object.modifiers):
        mod.show_viewport = self._objects_mod_status[m][0]
        mod.show_render = self._objects_mod_status[m][1]

    return


def check_area(self):
    # # inside region check
    # if self._mouse_reg_loc[0] >= 0.0 and self._mouse_reg_loc[0] <= bpy.context.area.width and self._mouse_reg_loc[1] >= 0.0 and self._mouse_reg_loc[1] <= bpy.context.area.height:
    #     return bpy.context.region, bpy.context.region_data

    # # if not inside check other areas to find if we are in another region that is a valid view_3d and return that ones data
    # for area in bpy.context.screen.areas:
    #     if area.type == 'VIEW_3D' and area != self._draw_area:
    #         if area.spaces.active.type == 'VIEW_3D':
    #             if self._mouse_abs_loc[0] > area.x and self._mouse_abs_loc[0] < area.x+area.width and self._mouse_abs_loc[1] > area.y and self._mouse_abs_loc[1] < area.y+area.height:
    #                 for region in area.regions:
    #                     if region.type == 'WINDOW':
    #                         return region, area.spaces.active.region_3d

    return bpy.context.region, bpy.context.region_data


#
# GIZMO
#


def gizmo_click_init(self, event, giz_status):
    if self._use_gizmo:
        if event.alt == False:
            sel_pos = self._points_container.get_selected()
            if len(sel_pos) == 0:
                return True

        self._mode_cache.clear()

        if event.alt == False:
            cache_norms = self._points_container.get_current_normals(sel_pos)

            for gizmo in self._window.gizmo_sets[giz_status[1]].gizmos:
                if gizmo.index != giz_status[2]:
                    gizmo.active = False
                else:
                    gizmo.in_use = True

        view_vec = view3d_utils.region_2d_to_vector_3d(
            self.act_reg, self.act_rv3d, mathutils.Vector((self._mouse_reg_loc[0], self._mouse_reg_loc[1])))
        view_orig = view3d_utils.region_2d_to_origin_3d(
            self.act_reg, self.act_rv3d, mathutils.Vector((self._mouse_reg_loc[0], self._mouse_reg_loc[1])))
        line_a = view_orig
        line_b = view_orig + view_vec*10000
        if giz_status[0] == 'ROT_X':
            x_vec = self._orbit_ob.matrix_world @ mathutils.Vector(
                (1, 0, 0)) - self._orbit_ob.matrix_world.translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(
                line_a, line_b, self._orbit_ob.matrix_world.translation, x_vec)
        if giz_status[0] == 'ROT_Y':
            y_vec = self._orbit_ob.matrix_world @ mathutils.Vector(
                (0, 1, 0)) - self._orbit_ob.matrix_world.translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(
                line_a, line_b, self._orbit_ob.matrix_world.translation, y_vec)
        if giz_status[0] == 'ROT_Z':
            z_vec = self._orbit_ob.matrix_world @ mathutils.Vector(
                (0, 0, 1)) - self._orbit_ob.matrix_world.translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(
                line_a, line_b, self._orbit_ob.matrix_world.translation, z_vec)
        mouse_co_local = self._orbit_ob.matrix_world.inverted() @ mouse_co_3d

        if giz_status[0] == 'ROT_X':
            test_vec = mouse_co_local.yz
            ang_offset = mathutils.Vector(
                (0, 1)).angle_signed(test_vec)
            self._mode_cache.append(mouse_co_local.yz)
        if giz_status[0] == 'ROT_Y':
            test_vec = mouse_co_local.xz
            ang_offset = mathutils.Vector(
                (0, 1)).angle_signed(test_vec)
            self._mode_cache.append(mouse_co_local.xz)
        if giz_status[0] == 'ROT_Z':
            test_vec = mouse_co_local.xy
            ang_offset = mathutils.Vector(
                (0, 1)).angle_signed(test_vec)
            self._mode_cache.append(mouse_co_local.xy)

        if event.alt == False:
            self._window.update_gizmo_rot(0, -ang_offset)
            self._mode_cache.append(giz_status)
            self._mode_cache.append(cache_norms)
            self._mode_cache.append(0)
            self._mode_cache.append(-ang_offset)
            self._mode_cache.append(
                self._orbit_ob.matrix_world.copy())
            self._mode_cache.append(True)
        else:
            self._mode_cache.append(giz_status)
            self._mode_cache.append([])
            self._mode_cache.append(0)
            self._mode_cache.append(-ang_offset)
            self._mode_cache.append(
                self._orbit_ob.matrix_world.copy())
            self._mode_cache.append(False)

        self.gizmo_click = True

        return False
    return True


def relocate_gizmo_panel(self):
    rco = view3d_utils.location_3d_to_region_2d(
        self.act_reg, self.act_rv3d, self._orbit_ob.location)

    if rco != None:
        self._gizmo_panel.set_new_position(
            [rco[0]+self.gizmo_reposition_offset[0], rco[1]+self.gizmo_reposition_offset[1]], self._window.dimensions)
    return


def gizmo_update_hide(self, status):
    if self._use_gizmo == False:
        status = False

    self._gizmo_panel.set_visibility(status)
    self._rot_gizmo.set_visibility(status)
    return


#
# MODES
#


def add_target_empty(ob):
    emp = bpy.data.objects.new('ABN_Target Empty', None)
    emp.empty_display_size = 0.0
    emp.show_in_front = True
    emp.matrix_world = ob.matrix_world.copy()
    emp.empty_display_type = 'SPHERE'
    bpy.context.collection.objects.link(emp)

    return emp


def start_sphereize_mode(self):
    update_filter_weights(self)

    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)
    self._target_emp.location = avg_loc
    self._target_emp.empty_display_size = 0.5
    self._target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self._target_emp

    sel_pos = self._points_container.get_selected()
    cache_norms = self._points_container.get_current_normals(sel_pos)

    self._mode_cache.append(cache_norms)
    gizmo_update_hide(self, False)
    self.sphereize_mode = True
    keymap_target(self)
    # self._export_panel.set_visibility(False)
    self._tools_panel.set_visibility(False)
    self._sphere_panel.set_visibility(True)
    self._sphere_panel.set_new_position(
        self._mouse_reg_loc, window_dims=self._window.dimensions)

    sphereize_normals(self, sel_pos)
    return


def end_sphereize_mode(self, keep_normals):
    if keep_normals == False:
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for loop in po.loops:
                loop.normal = self._mode_cache[-1][i][loop.index].copy()

        set_new_normals(self)

    # self._export_panel.set_visibility(True)
    self._tools_panel.set_visibility(True)
    self._sphere_panel.set_visibility(False)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
    self.redraw = True
    self.sphereize_mode = False
    self.sphereize_move = False
    self._target_emp.empty_display_size = 0.0
    self._target_emp.select_set(False)
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    gizmo_update_hide(self, True)

    self._mode_cache.clear()
    keymap_refresh(self)
    return


def sphereize_normals(self, po_inds):
    for i, ind in enumerate(po_inds):
        po = self._points_container.points[ind]
        if po.valid:
            vec = (self._object.matrix_world.inverted() @ po.co) - \
                (self._object.matrix_world.inverted() @ self._target_emp.location)
            for loop in po.loops:
                loop_norm_set(
                    self, po, loop.index, self._mode_cache[-1][i][loop.index], self._mode_cache[-1][i][loop.index].lerp(vec, self.target_strength))

            self.redraw = True

    set_new_normals(self)
    return


def start_point_mode(self):
    update_filter_weights(self)

    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)
    self._target_emp.location = avg_loc
    self._target_emp.empty_display_size = 0.5
    self._target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self._target_emp

    sel_pos = self._points_container.get_selected()
    cache_norms = self._points_container.get_current_normals(sel_pos)

    self._mode_cache.append(cache_norms)
    gizmo_update_hide(self, False)
    self.point_mode = True
    keymap_target(self)
    # self._export_panel.set_visibility(False)
    self._tools_panel.set_visibility(False)
    self._point_panel.set_visibility(True)
    self._point_panel.set_new_position(
        self._mouse_reg_loc, window_dims=self._window.dimensions)

    point_normals(self, sel_pos)
    return


def end_point_mode(self, keep_normals):
    if keep_normals == False:
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for loop in po.loops:
                loop.normal = self._mode_cache[-1][i][loop.index].copy()

        set_new_normals(self)

    # self._export_panel.set_visibility(True)
    self._tools_panel.set_visibility(True)
    self._point_panel.set_visibility(False)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
    self.redraw = True
    self.point_mode = False
    self.point_move = False
    self._target_emp.empty_display_size = 0.0
    self._target_emp.select_set(False)
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    gizmo_update_hide(self, True)

    self._mode_cache.clear()
    keymap_refresh(self)
    return


def point_normals(self, po_inds):
    if self.point_align:
        sel_cos = self._points_container.get_selected_cos()
        avg_loc = average_vecs(sel_cos)
        vec = (self._object.matrix_world.inverted() @ self._target_emp.location) - \
            (self._object.matrix_world.inverted() @ avg_loc)

    for i, ind in enumerate(po_inds):
        po = self._points_container.points[ind]
        if po.valid:
            if self.point_align == False:
                vec = (self._object.matrix_world.inverted(
                ) @ self._target_emp.location) - (self._object.matrix_world.inverted() @ po.co)
            for loop in po.loops:
                loop_norm_set(
                    self, po, loop.index, self._mode_cache[-1][i][loop.index], self._mode_cache[-1][i][loop.index].lerp(vec, self.target_strength))

            self.redraw = True

    set_new_normals(self)
    return


def move_target(self, shift):
    offset = [self._mouse_reg_loc[0] - self._mode_cache[0]
              [0], self._mouse_reg_loc[1] - self._mode_cache[0][1]]

    if shift:
        offset[0] = offset[0]*.1
        offset[1] = offset[1]*.1

    self._mode_cache[3][0] = self._mode_cache[3][0] + offset[0]
    self._mode_cache[3][1] = self._mode_cache[3][1] + offset[1]

    new_co = view3d_utils.region_2d_to_location_3d(
        self.act_reg, self.act_rv3d, self._mode_cache[3], self._mode_cache[1])
    if self.translate_mode == 0:
        self._target_emp.location = new_co

    elif self.translate_mode == 1:
        self._target_emp.location = self._mode_cache[1].copy()
        self._target_emp.location[self.translate_axis] = new_co[self.translate_axis]

    elif self.translate_mode == 2:
        loc_co = self._object.matrix_world.inverted() @ new_co
        def_dist = loc_co[self.translate_axis]

        def_vec = mathutils.Vector((0, 0, 0))
        def_vec[self.translate_axis] = def_dist

        def_vec = (self._object.matrix_world @ def_vec) - \
            self._object.matrix_world.translation

        self._target_emp.location = self._mode_cache[1].copy()
        self._target_emp.location += def_vec

    return


#
# SELECTION
#


def selection_test(self, event, radius=6.0):
    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        0)

    change, unselect, new_active, new_sel, new_sel_status = click_points_selection_test(
        avail_cos, avail_sel_status, self._mouse_reg_loc, self.act_reg, self.act_rv3d, event.shift, self._x_ray_mode, self._object_bvh, active=self._active_point)

    sel_ind = None
    new_act = None
    if new_sel != None:
        sel_ind = avail_inds[new_sel]
    if new_active != None:
        new_act = avail_inds[new_active]

    if change:
        if unselect:
            for po in self._points_container.points:
                po.select = False

        self._points_container.points[sel_ind].select = new_sel_status

        self._active_point = new_act

    return change


def box_selection_test(self, event):
    add_rem_status = 0
    if event.ctrl:
        add_rem_status = 2
    else:
        if event.shift:
            add_rem_status = 1

    avail_cos = []
    avail_inds = []

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        add_rem_status)

    change, unselect, new_active, new_sel_add, new_sel_remove = box_points_selection_test(
        avail_cos, avail_sel_status, self._mouse_reg_loc, self._mode_cache[0], self.act_reg, self.act_rv3d, add_rem_status, self._x_ray_mode, self._object_bvh)

    if change:
        if unselect:
            for po in self._points_container.points:
                po.select = False

        for ind in new_sel_add:
            po_ind = avail_inds[ind]
            self._points_container.points[po_ind].select = True

        for ind in new_sel_remove:
            po_ind = avail_inds[ind]
            self._points_container.points[po_ind].select = False

        if self._active_point != None:
            if self._points_container.points[self._active_point].select == False:
                self._active_point = None

    return change


def circle_selection_test(self, event, radius):
    add_rem_status = 0
    if event.ctrl:
        add_rem_status = 2
    else:
        if event.shift:
            add_rem_status = 1

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        add_rem_status)

    change, unselect, new_active, new_sel, new_sel_status = circle_points_selection_test(
        avail_cos, avail_sel_status, self._mouse_reg_loc, radius, self.act_reg, self.act_rv3d, add_rem_status, self._x_ray_mode, self._object_bvh)

    if change:
        if unselect:
            for po in self._points_container.points:
                po.select = False

        for ind in new_sel:
            po_ind = avail_inds[ind]
            self._points_container.points[po_ind].select = new_sel_status

        if self._active_point != None:
            if self._points_container.points[self._active_point].select == False:
                self._active_point = None

    return change


def lasso_selection_test(self, event):
    add_rem_status = 0
    if event.ctrl:
        add_rem_status = 2
    else:
        if event.shift:
            add_rem_status = 1

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        add_rem_status)

    change, unselect, new_active, new_sel_add, new_sel_remove = lasso_points_selection_test(
        self._mode_cache, avail_cos, avail_sel_status, self._mouse_reg_loc, self.act_reg, self.act_rv3d, add_rem_status, self._x_ray_mode, self._object_bvh)

    if change:
        if unselect:
            for po in self._points_container.points:
                po.select = False

        for ind in new_sel_add:
            po_ind = avail_inds[ind]
            self._points_container.points[po_ind].select = True

        for ind in new_sel_remove:
            po_ind = avail_inds[ind]
            self._points_container.points[po_ind].select = False

        if self._active_point != None:
            if self._points_container.points[self._active_point].select == False:
                self._active_point = None

    return change


##
##
##
##
##


#
# ORBIT EMPTY
#


def add_orbit_empty(ob):
    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    emp = bpy.data.objects.new('ABN_Orbit Empty', None)
    emp.empty_display_size = 0.0
    emp.matrix_world = ob.matrix_world.copy()
    bpy.context.collection.objects.link(emp)
    bpy.context.view_layer.objects.active = emp
    return emp


def update_orbit_empty(self):

    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)

    if avg_loc != None:
        gizmo_update_hide(self, True)
        self._orbit_ob.matrix_world.translation = avg_loc
    else:
        gizmo_update_hide(self, False)
        self._orbit_ob.matrix_world.translation = self._object.location

    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    if self._use_gizmo:
        self._window.update_gizmo_pos(self._orbit_ob.matrix_world)
        relocate_gizmo_panel(self)

    return


def delete_orbit_empty(self):
    if self._orbit_ob != None:
        try:
            bpy.data.objects.remove(self._orbit_ob)
        except:
            self._orbit_ob = None

    return
