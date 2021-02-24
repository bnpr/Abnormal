import bpy
import mathutils
import os
from bpy_extras import view3d_utils
from .functions_general import *
from .functions_drawing import *
from .functions_modal_keymap import *
from .classes import *
from .keymap import addon_keymaps


def match_loops_vecs(self, loop, o_tangs, flip_axis=None):
    tang = self._object_bm.verts[loop.point.index].link_loops[loop.index].calc_tangent(
    )

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

    return small_ind


#
#


def set_new_normals(self):
    for ed in self._object.data.edges:
        ed.use_edge_sharp = self.og_sharp_edges[ed.index]

    new_l_norms = [None for l in self._object.data.loops]
    for po in self._points_container.points:
        for loop in po.loops:
            new_l_norms[loop.loop_index] = loop.normal.normalized()

    self._object.data.normals_split_custom_set(new_l_norms)

    return


def loop_norm_set(self, loop, og_vec, to_vec):
    weight = None
    if self._filter_weights != None:
        weight = self._filter_weights[loop.point.index]

    if weight == None:
        new_vec = get_locked_normal(
            self, loop.normal, to_vec).normalized()
    else:
        new_vec = get_locked_normal(
            self, loop.normal, og_vec.lerp(to_vec, weight)).normalized()

    loop.normal = new_vec

    axis = []
    if self._mirror_x:
        axis.append(0)
    if self._mirror_y:
        axis.append(1)
    if self._mirror_z:
        axis.append(2)

    for ind in axis:
        if ind == 0:
            mir_loop = loop.x_mirror
        if ind == 1:
            mir_loop = loop.y_mirror
        if ind == 2:
            mir_loop = loop.z_mirror

        if mir_loop != None:
            mir_norm = loop.normal.copy()
            mir_norm[ind] *= -1

            mir_loop.normal = get_locked_normal(
                self, mir_loop.normal, mir_norm)
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


def mirror_normals(self, sel_inds, axis):

    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]

            if axis == 0:
                mir_loop = loop.x_mirror
            if axis == 1:
                mir_loop = loop.y_mirror
            if axis == 2:
                mir_loop = loop.z_mirror

            if mir_loop != None:
                mir_norm = loop.normal.copy()
                mir_norm[axis] *= -1

                mir_loop.normal = get_locked_normal(
                    self, mir_loop.normal, mir_norm)

                self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def incremental_rotate_vectors(self, sel_inds, axis, increment):
    sel_cos = self._points_container.get_selected_loop_cos()
    avg_loc = average_vecs(sel_cos)

    self._points_container.cache_current_normals()

    self._mode_cache.clear()
    self._mode_cache.append(self._mouse_reg_loc)
    self._mode_cache.append(avg_loc)
    self._mode_cache.append(0)

    self.translate_mode = 2
    self.translate_axis = axis
    rotate_vectors(self, math.radians(increment * self._rot_increment))
    self.translate_mode = 0
    self.translate_axis = 2
    self._mode_cache.clear()
    return


def rotate_vectors(self, angle):
    sel_inds = self._points_container.get_selected_loops()

    for i, ind_set in enumerate(sel_inds):
        po = self._points_container.points[ind_set[0]]
        loop = po.loops[ind_set[1]]

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

        po_local = self._object.matrix_world.inverted() @ po.co
        loop_w = self._object.matrix_world @ (loop.cached_normal+po_local)

        vec_local = mat.inverted() @ loop_w
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

        rot_w = mat @ vec_local
        loop_local = self._object.matrix_world.inverted() @ rot_w

        loop_norm_set(self, loop, loop.cached_normal,
                      (loop_local-po_local).normalized())

    set_new_normals(self)
    self.redraw = True
    return


#
# AXIS ALIGNMENT
#
def flatten_normals(self, sel_inds, axis):
    update_filter_weights(self)
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]

            vec = loop.normal.copy()
            vec[axis] = 0.0

            if vec.length > 0.0:
                loop_norm_set(self, loop, loop.normal, vec)
        self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def align_to_axis_normals(self, sel_inds, axis, dir):
    update_filter_weights(self)
    vec = mathutils.Vector((0, 0, 0))

    vec[axis] = 1.0*dir
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]

            loop_norm_set(self, loop, loop.normal, vec.copy())

            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# MANIPULATE NORMALS
#
def average_vertex_normals(self, sel_inds):
    update_filter_weights(self)

    new_norms = []
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]

            vec = average_vecs(
                [loop.normal for loop in po.loops if loop.select])

            new_norms.append(vec)
        else:
            new_norms.append(None)

    for i, ind in enumerate(sel_inds):
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]
            loop_norm_set(self, loop, loop.normal, new_norms[i])

            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def average_selected_normals(self, sel_inds):
    update_filter_weights(self)
    avg_vec = mathutils.Vector((0, 0, 0))
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            vec = average_vecs(
                [loop.normal for loop in po.loops if loop.select])
            avg_vec += vec

            self.redraw = True

    avg_vec = (avg_vec/len(sel_inds)).normalized()

    if avg_vec.length > 0.0:
        for ind in sel_inds:
            po = self._points_container.points[ind[0]]
            if po.valid:
                loop = po.loops[ind[1]]

                loop_norm_set(self, loop, loop.normal, avg_vec.copy())

        set_new_normals(self)
        add_to_undostack(self, 1)

    return


def smooth_normals(self, sel_inds, fac):
    update_filter_weights(self)

    calc_norms = None
    for i in range(self._smooth_iterations):
        calc_norms = []
        for po in self._points_container.points:
            if len(po.loops) > 0 and po.valid:
                vec = average_vecs([loop.normal for loop in po.loops])
                calc_norms.append(vec)
            else:
                calc_norms.append(None)

        for ind in sel_inds:
            po = self._points_container.points[ind[0]]
            if po.valid:
                loop = po.loops[ind[1]]

                l_vs = [ed.other_vert(self._object_bm.verts[po.index])
                        for ed in self._object_bm.verts[po.index].link_edges]

                smooth_vec = mathutils.Vector((0, 0, 0))
                smooth_vec = average_vecs(
                    [loop.normal.lerp(calc_norms[ov.index], fac) for ov in l_vs])

                if smooth_vec.length > 0:
                    loop_norm_set(self, loop, loop.normal, loop.normal.lerp(
                        smooth_vec, self._smooth_strength))

    self.redraw = True
    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# NORMAL DIRECTION
#
def flip_normals(self, sel_inds):
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]
            loop.normal *= -1
            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def set_outside_inside(self, sel_inds, direction):
    update_filter_weights(self)
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]

            if self._object_smooth:
                poly_norm = mathutils.Vector((0, 0, 0))
                for bm_loop in self._object_bm.verts[po.index].link_loops:
                    poly_norm += self._object.data.polygons[bm_loop.face.index].normal * direction

                if poly_norm.length > 0.0:
                    loop_norm_set(self, loop, loop.normal,
                                  poly_norm/len(po.loops))

            else:
                loop.normal = self._object_bm.loops[loop.loop_index].face.normal.copy(
                ) * direction

            self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def reset_normals(self, sel_inds):
    for ind in sel_inds:
        po = self._points_container.points[ind[0]]
        if po.valid:
            loop = po.loops[ind[1]]
            loop.reset_normal()
        self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# COPY/PASTE
#
def copy_active_to_selected(self, sel_inds):
    update_filter_weights(self)
    if self._active_point != None:
        norms, tangs = get_po_loop_data(self, self._active_point)

        for ind in sel_inds:
            po = self._points_container.points[ind[0]]
            if po.valid:
                loop = po.loops[ind[1]]

                m_ind = match_loops_vecs(self, loop, tangs)

                loop_norm_set(
                    self, loop, loop.normal, norms[m_ind].copy())

        self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def get_po_loop_data(self, po_loop):
    norms = None
    tangs = None

    if po_loop != None:
        if po_loop.type == 'POINT':
            norms = [loop.normal for loop in po_loop.loops]
            tangs = []

            for o_loop in self._object_bm.verts[po_loop.index].link_loops:
                tangs.append(o_loop.calc_tangent())

        elif po_loop.type == 'LOOP':
            norms = [po_loop.normal]
            tangs = [
                self._object_bm.verts[po_loop.point.index].link_loops[po_loop.index].calc_tangent()]

    return norms, tangs


def paste_normal(self, sel_inds):
    update_filter_weights(self)
    if self._copy_normals != None and self._copy_normals_tangs != None:
        for ind in sel_inds:
            po = self._points_container.points[ind[0]]
            if po.valid:
                loop = po.loops[ind[1]]

                m_ind = match_loops_vecs(
                    self, loop, self._copy_normals_tangs)

                loop_norm_set(
                    self, loop, loop.normal, self._copy_normals[m_ind].copy())

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

    self._points_container.restore_cached_normals()
    self._points_container.cache_current_normals()
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

    cache_mirror_data(self)
    return


def cache_mirror_data(self):
    for po in self._points_container.points:
        if po.valid:
            mir_pos = []
            for i in range(3):
                co = self._object.matrix_world.inverted() @ po.co
                co[i] *= -1
                co = self._object.matrix_world @ co

                result = self._object_kd.find_range(co, self._mirror_range)

                m_po = None
                for res in result:
                    o_po = self._points_container.points[res[1]]
                    if o_po.valid:
                        m_po = o_po
                        break

                mir_pos.append(m_po)

            norms, tangs = get_po_loop_data(self, po)

            for i in range(3):
                if mir_pos[i] != None:
                    for m_loop in mir_pos[i].loops:
                        m_ind = match_loops_vecs(
                            self, m_loop, tangs, flip_axis=i)

                        if i == 0:
                            m_loop.x_mirror = po.loops[m_ind]
                        if i == 1:
                            m_loop.y_mirror = po.loops[m_ind]
                        if i == 2:
                            m_loop.z_mirror = po.loops[m_ind]

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
    self.nav_list = [['LEFTMOUSE', 'CLICK', True, False, False, False],
                     ['LEFTMOUSE', 'PRESS', True, False, False, False],
                     ['LEFTMOUSE', 'RELEASE', True, False, False, False],
                     ['MOUSEMOVE', 'PRESS', True, False, False, False],
                     ['MOUSEMOVE', 'RELEASE', True, False, False, False],
                     ['WHEELUPMOUSE', 'PRESS', True, False, False, False],
                     ['WHEELDOWNMOUSE', 'PRESS', True, False, False, False],
                     ['N', 'PRESS', True, False, False, False],
                     ['MIDDLEMOUSE', 'PRESS', True, False, False, False], ]

    names = ['Zoom View', 'Rotate View', 'Pan View', 'Dolly View',
             'View Selected', 'View Camera Center', 'View All', 'View Axis',
             'View Orbit', 'View Roll', 'View Persp/Ortho', 'Frame Selected']

    config = bpy.context.window_manager.keyconfigs.get('blender')
    if config:
        for item in config.keymaps['3D View'].keymap_items:
            if item.name in names:
                item_dat = [item.type, item.value, item.any,
                            item.ctrl, item.shift, item.alt]
                if item_dat not in self.nav_list:
                    self.nav_list.append(item_dat)

    config = bpy.context.window_manager.keyconfigs.get('blender user')
    if config:
        for item in config.keymaps['3D View'].keymap_items:
            if item.name in names:
                item_dat = [item.type, item.value, item.any,
                            item.ctrl, item.shift, item.alt]
                if item_dat not in self.nav_list:
                    self.nav_list.append(item_dat)

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
        sel_status = self._points_container.get_selected_loops()
        vis_status = self._points_container.get_visible_loops()

        if self._history_position > 0:
            while self._history_position > 0:
                self._history_stack.pop(0)
                self._history_position -= 1

        if len(self._history_stack)+1 > self._history_steps:
            self._history_stack.pop(-1)
        self._history_stack.insert(0, [stack_type, sel_status, vis_status])

        self.redraw = True
        update_orbit_empty(self)

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
            vis_state = self._history_stack[self._history_position][2]
            for po in self._points_container.points:
                po.set_hide(True)

            for ind in vis_state:
                po = self._points_container.points[ind[0]]
                if po.valid:
                    loop = po.loops[ind[1]]
                    loop.set_hide(False)

                po.set_hidden_from_loops()

            for po in self._points_container.points:
                po.set_select(False)

            for ind in state:
                po = self._points_container.points[ind[0]]
                if po.hide == False and po.valid:
                    loop = po.loops[ind[1]]
                    if loop.hide == False:
                        loop.set_select(True)

                po.set_selection_from_loops()

            if self._active_point != None:
                if self._active_point.select == False:
                    self._points_container.clear_active()
                    self._active_point = None

            update_orbit_empty(self)
            self.redraw = True

        if state_type == 1:
            for po in self._points_container.points:
                for loop in po.loops:
                    loop.normal = state[po.index][loop.index].copy()

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
    self._behavior_prefs.rotate_gizmo_use = self._use_gizmo
    self._display_prefs.gizmo_size = self._gizmo_size
    self._display_prefs.normal_size = self._normal_size
    self._display_prefs.line_brightness = self._line_brightness
    self._display_prefs.point_size = self._point_size
    self._display_prefs.loop_tri_size = self._loop_tri_size
    self._display_prefs.selected_only = self._selected_only
    self._display_prefs.selected_scale = self._selected_scale
    self._behavior_prefs.individual_loops = self._individual_loops
    self._display_prefs.ui_scale = self._ui_scale
    self._display_prefs.display_wireframe = self._use_wireframe_overlay

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

    if restore:
        ob = self._object
        if ob.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        for ed in self._object.data.edges:
            ed.use_edge_sharp = self.og_sharp_edges[ed.index]

        # restore normals
        og_norms = [None for l in ob.data.loops]
        for po in self._points_container.points:
            for loop in po.loops:
                og_norms[loop.loop_index] = loop.og_normal.normalized()
        ob.data.normals_split_custom_set(og_norms)

    restore_modifiers(self)

    abn_props = bpy.context.scene.abnormal_props
    abn_props.object = ''

    delete_orbit_empty(self)
    if self._target_emp != None:
        try:
            bpy.data.objects.remove(self._target_emp)
        except:
            self._target_emp = None

    self._object.select_set(True)
    bpy.context.view_layer.objects.active = self._object
    return


def restore_modifiers(self):
    if self._object.data.shape_keys != None:
        for s in range(len(self._object.data.shape_keys.key_blocks)):
            self._object.data.shape_keys.key_blocks[s].mute = self._objects_sk_vis[s]

    # restore modifier status
    for m, mod_dat in enumerate(self._objects_mod_status):
        for mod in self._object.modifiers:
            if mod.name == self._objects_mod_status[m][2]:
                mod.show_viewport = self._objects_mod_status[m][0]
                mod.show_render = self._objects_mod_status[m][1]
                break

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
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) == 0:
                return True

        self._mode_cache.clear()

        if event.alt == False:
            self._points_container.cache_current_normals()

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
            self._mode_cache.append(0)
            self._mode_cache.append(-ang_offset)
            self._mode_cache.append(
                self._orbit_ob.matrix_world.copy())
            self._mode_cache.append(True)
        else:
            self._mode_cache.append(giz_status)
            self._mode_cache.append(0)
            self._mode_cache.append(-ang_offset)
            self._mode_cache.append(
                self._orbit_ob.matrix_world.copy())
            self._mode_cache.append(False)

        self.gizmo_click = True
        self._current_tool = self._gizmo_tool
        self.tool_mode = True

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

    sel_cos = self._points_container.get_selected_loop_cos()
    avg_loc = average_vecs(sel_cos)
    self._target_emp.location = avg_loc
    self._target_emp.empty_display_size = 0.5
    self._target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self._target_emp

    sel_inds = self._points_container.get_selected_loops()
    self._mode_cache.append(sel_inds)
    self._mode_cache.append(avg_loc)

    self._points_container.cache_current_normals()

    gizmo_update_hide(self, False)
    self.sphereize_mode = True
    self.tool_mode = True
    self._current_tool = self._sphereize_tool

    keymap_target(self)
    # self._export_panel.set_visibility(False)
    self._tools_panel.set_visibility(False)
    self._sphere_panel.set_visibility(True)
    self._sphere_panel.set_new_position(
        self._mouse_reg_loc, window_dims=self._window.dimensions)

    sphereize_normals(self, sel_inds)
    return


def end_sphereize_mode(self, keep_normals):
    if keep_normals == False:
        self._points_container.restore_cached_normals()
        set_new_normals(self)

    # self._export_panel.set_visibility(True)
    self._tools_panel.set_visibility(True)
    self._sphere_panel.set_visibility(False)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
    self.redraw = True
    self._target_emp.empty_display_size = 0.0
    self._target_emp.select_set(False)
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    gizmo_update_hide(self, True)

    self.sphereize_mode = False
    self.tool_mode = False
    self._mode_cache.clear()
    keymap_refresh(self)
    return


def sphereize_normals(self, sel_inds):
    for i, ind in enumerate(sel_inds):
        po = self._points_container.points[ind[0]]
        loop = po.loops[ind[1]]

        if po.valid:
            vec = (self._object.matrix_world.inverted() @ po.co) - \
                (self._object.matrix_world.inverted() @ self._target_emp.location)

            loop_norm_set(
                self, loop, loop.cached_normal, loop.cached_normal.lerp(vec, self.target_strength))

            self.redraw = True

    set_new_normals(self)
    return


def start_point_mode(self):
    update_filter_weights(self)

    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    sel_cos = self._points_container.get_selected_loop_cos()
    avg_loc = average_vecs(sel_cos)
    self._target_emp.location = avg_loc
    self._target_emp.empty_display_size = 0.5
    self._target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self._target_emp

    sel_inds = self._points_container.get_selected_loops()
    self._mode_cache.append(sel_inds)
    self._mode_cache.append(avg_loc)

    self._points_container.cache_current_normals()

    gizmo_update_hide(self, False)
    self.point_mode = True
    self.tool_mode = True
    self._current_tool = self._point_tool

    keymap_target(self)
    # self._export_panel.set_visibility(False)
    self._tools_panel.set_visibility(False)
    self._point_panel.set_visibility(True)
    self._point_panel.set_new_position(
        self._mouse_reg_loc, window_dims=self._window.dimensions)

    point_normals(self, sel_inds)
    return


def end_point_mode(self, keep_normals):
    if keep_normals == False:
        self._points_container.restore_cached_normals()
        set_new_normals(self)

    # self._export_panel.set_visibility(True)
    self._tools_panel.set_visibility(True)
    self._point_panel.set_visibility(False)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
    self.redraw = True
    self._target_emp.empty_display_size = 0.0
    self._target_emp.select_set(False)
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    gizmo_update_hide(self, True)

    self.point_mode = False
    self.tool_mode = False
    self._mode_cache.clear()
    keymap_refresh(self)
    return


def point_normals(self, sel_inds):
    if self.point_align:
        sel_cos = self._points_container.get_selected_loop_cos()
        avg_loc = average_vecs(sel_cos)
        vec = (self._object.matrix_world.inverted() @ self._target_emp.location) - \
            (self._object.matrix_world.inverted() @ avg_loc)

    for i, ind in enumerate(sel_inds):
        po = self._points_container.points[ind[0]]
        loop = po.loops[ind[1]]

        if po.valid:
            if self.point_align == False:
                vec = (self._object.matrix_world.inverted(
                ) @ self._target_emp.location) - (self._object.matrix_world.inverted() @ po.co)

            loop_norm_set(
                self, loop, loop.cached_normal, loop.cached_normal.lerp(vec, self.target_strength))

            self.redraw = True

    set_new_normals(self)
    return


def move_target(self, shift):
    offset = [self._mouse_reg_loc[0] - self._mode_cache[2]
              [0], self._mouse_reg_loc[1] - self._mode_cache[2][1]]

    if shift:
        offset[0] = offset[0]*.1
        offset[1] = offset[1]*.1

    self._mode_cache[4][0] = self._mode_cache[4][0] + offset[0]
    self._mode_cache[4][1] = self._mode_cache[4][1] + offset[1]

    new_co = view3d_utils.region_2d_to_location_3d(
        self.act_reg, self.act_rv3d, self._mode_cache[4], self._mode_cache[3])
    if self.translate_mode == 0:
        self._target_emp.location = new_co

    elif self.translate_mode == 1:
        self._target_emp.location = self._mode_cache[3].copy()
        self._target_emp.location[self.translate_axis] = new_co[self.translate_axis]

    elif self.translate_mode == 2:
        loc_co = self._object.matrix_world.inverted() @ new_co
        def_dist = loc_co[self.translate_axis]

        def_vec = mathutils.Vector((0, 0, 0))
        def_vec[self.translate_axis] = def_dist

        def_vec = (self._object.matrix_world @ def_vec) - \
            self._object.matrix_world.translation

        self._target_emp.location = self._mode_cache[3].copy()
        self._target_emp.location += def_vec

    return


#
# SELECTION
#
def get_active_point_index(indeces, active):
    if active == None or active.type != 'POINT':
        return None

    for i, ind in enumerate(indeces):
        if active.index == ind:
            return i

    return None


def get_active_loop_index(indeces, active):
    if active == None or active.type != 'LOOP':
        return None

    for i, ind_set in enumerate(indeces):
        if active.point.index == ind_set[0] and active.index == ind_set[1]:
            return i

    return None


def selection_test(self, shift, radius=6.0):
    test_face = False

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        0)

    active_ind = get_active_point_index(avail_inds, self._active_point)

    change, unselect, new_active, new_sel, new_sel_status = click_points_selection_test(
        avail_cos, avail_sel_status, self._mouse_reg_loc, self.act_reg, self.act_rv3d, shift, self._x_ray_mode, self._object_bvh, active=active_ind)

    sel_ind = None
    new_act = None
    if new_sel != None:
        sel_ind = avail_inds[new_sel]
    if new_active != None:
        new_act = avail_inds[new_active]

    # Vertex selection
    if change:
        if unselect:
            for po in self._points_container.points:
                po.set_select(False)

        self._points_container.points[sel_ind].set_select(new_sel_status)

        if new_act != None:
            self._points_container.set_active_point(new_act)
            self._active_point = self._points_container.points[new_act]
        else:
            self._points_container.clear_active()
            self._active_point = None

    # No vertex selection so test loop triangle selection
    else:
        if self._individual_loops:
            avail_tri_cos, avail_sel_status, avail_inds = self._points_container.get_loop_tri_selection_available(
                0)

            active_ind = get_active_loop_index(avail_inds, self._active_point)

            change, unselect, new_active, new_sel, new_sel_status = click_tris_selection_test(
                avail_tri_cos, avail_sel_status, self._mouse_reg_loc, self.act_reg, self.act_rv3d, shift, self._x_ray_mode, self._object_bvh, active=active_ind)

            sel_ind = None
            new_act = None
            if new_sel != None:
                sel_ind = avail_inds[new_sel]
            if new_active != None:
                new_act = avail_inds[new_active]

            # If selection change made then do it
            if change:
                if unselect:
                    for po in self._points_container.points:
                        po.set_select(False)

                self._points_container.points[sel_ind[0]].set_loop_select(
                    sel_ind[1], new_sel_status)
                self._points_container.points[sel_ind[0]
                                              ].set_selection_from_loops()

                if new_act != None:
                    self._points_container.set_active_loop(
                        new_act[0], new_act[1])
                    self._active_point = self._points_container.points[new_act[0]
                                                                       ].loops[new_act[1]]
                else:
                    self._points_container.clear_active()
                    self._active_point = None

            # No vertex or loop selection so try for selecting a face with ray cast
            else:
                test_face = True

        # No vertex selection or loop testing so try for selecting a face with ray cast
        else:
            test_face = True

    if test_face:
        face_res = ray_cast_to_mouse(self)
        if face_res != None:
            if shift == False:
                self._points_container.clear_active()
                for po in self._points_container.points:
                    po.set_select(False)

            if self._individual_loops:
                self._points_container.select_face_loops(face_res[1])
            else:
                self._points_container.select_face_verts(face_res[1])
            for po in self._points_container.points:
                po.set_selection_from_loops()
            change = True

    return change


def loop_selection_test(self, shift, radius=6.0):
    change = False

    face_res = ray_cast_to_mouse(self)
    if face_res != None:
        if shift == False:
            for po in self._points_container.points:
                po.set_select(False)

        sel_ed = None
        small_dist = 0.0
        for ed in self._object_bm.faces[face_res[1]].edges:
            # then find nearest point on those edges that are in range
            nearest_point_co, nearest_point_dist = nearest_co_on_line(
                face_res[0], ed.verts[0].co, ed.verts[1].co)

            if nearest_point_dist < small_dist or sel_ed == None:
                sel_ed = ed
                small_dist = nearest_point_dist

        if sel_ed != None:
            sel_loop = get_edge_loop(
                self._object_bm, sel_ed)
            v_inds = []
            for ed_ind in sel_loop:
                for v in self._object_bm.edges[ed_ind].verts:
                    if v.index not in v_inds:
                        v_inds.append(v.index)

            cur_sel = [
                self._points_container.points[ind].select for ind in v_inds]

            loop_status = False in cur_sel
            for ind in v_inds:
                self._points_container.points[ind].set_select(
                    loop_status)
                change = True

    return change


def box_selection_test(self, shift, ctrl):
    add_rem_status = 0
    if ctrl:
        add_rem_status = 2
    else:
        if shift:
            add_rem_status = 1

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        add_rem_status)

    loop_switch_pont = len(avail_inds)
    # Add in loop selection data if enabled
    if self._individual_loops:
        avail_tri_cos, avail_loop_sel_status, avail_loop_inds = self._points_container.get_loop_selection_available(
            add_rem_status)
        avail_cos += avail_tri_cos
        avail_sel_status += avail_loop_sel_status
        avail_inds += avail_loop_inds

    change, unselect, new_active, new_sel_add, new_sel_remove = box_points_selection_test(
        avail_cos, avail_sel_status, self._mouse_reg_loc, self._mode_cache[0], self.act_reg, self.act_rv3d, add_rem_status, self._x_ray_mode, self._object_bvh)

    if change:
        if unselect:
            for po in self._points_container.points:
                po.set_select(False)

        for ind in new_sel_add:
            if ind < loop_switch_pont:
                po_ind = avail_inds[ind]
                self._points_container.points[po_ind].set_select(True)
            else:
                sel_ind = avail_inds[ind]
                self._points_container.points[sel_ind[0]
                                              ].loops[sel_ind[1]].set_select(True)
                self._points_container.points[sel_ind[0]
                                              ].set_selection_from_loops()

        for ind in new_sel_remove:
            if ind < loop_switch_pont:
                po_ind = avail_inds[ind]
                self._points_container.points[po_ind].set_select(False)
            else:
                sel_ind = avail_inds[ind]
                self._points_container.points[sel_ind[0]
                                              ].loops[sel_ind[1]].set_select(False)
                self._points_container.points[sel_ind[0]
                                              ].set_selection_from_loops()

        if self._active_point != None:
            if self._active_point.select == False:
                self._points_container.clear_active()
                self._active_point = None

                # if self._points_container.points[self._active_point[0]].select == False:
                #     self._active_point = None

    return change


def circle_selection_test(self, shift, ctrl, radius):
    add_rem_status = 0
    if ctrl:
        add_rem_status = 2
    else:
        if shift:
            add_rem_status = 1

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        add_rem_status)

    loop_switch_pont = len(avail_inds)
    # Add in loop selection data if enabled
    if self._individual_loops:
        avail_loop_cos, avail_loop_sel_status, avail_loop_inds = self._points_container.get_loop_selection_available(
            add_rem_status)

        avail_cos += avail_loop_cos
        avail_sel_status += avail_loop_sel_status
        avail_inds += avail_loop_inds

    change, unselect, new_active, new_sel, new_sel_status = circle_points_selection_test(
        avail_cos, avail_sel_status, self._mouse_reg_loc, radius, self.act_reg, self.act_rv3d, add_rem_status, self._x_ray_mode, self._object_bvh)

    if change:
        for ind in new_sel:
            if ind < loop_switch_pont:
                po_ind = avail_inds[ind]
                self._points_container.points[po_ind].set_select(
                    new_sel_status)
            else:
                sel_ind = avail_inds[ind]
                self._points_container.points[sel_ind[0]
                                              ].loops[sel_ind[1]].set_select(new_sel_status)
                self._points_container.points[sel_ind[0]
                                              ].set_selection_from_loops()

        if self._active_point != None:
            if self._active_point.select == False:
                self._points_container.clear_active()
                self._active_point = None

    return change


def lasso_selection_test(self, shift, ctrl):
    add_rem_status = 0
    if ctrl:
        add_rem_status = 2
    else:
        if shift:
            add_rem_status = 1

    avail_cos, avail_sel_status, avail_inds = self._points_container.get_selection_available(
        add_rem_status)

    loop_switch_pont = len(avail_inds)
    # Add in loop selection data if enabled
    if self._individual_loops:
        avail_tri_cos, avail_loop_sel_status, avail_loop_inds = self._points_container.get_loop_selection_available(
            add_rem_status)
        avail_cos += avail_tri_cos
        avail_sel_status += avail_loop_sel_status
        avail_inds += avail_loop_inds

    change, unselect, new_active, new_sel_add, new_sel_remove = lasso_points_selection_test(
        self._mode_cache, avail_cos, avail_sel_status, self._mouse_reg_loc, self.act_reg, self.act_rv3d, add_rem_status, self._x_ray_mode, self._object_bvh)

    if change:
        if unselect:
            for po in self._points_container.points:
                po.set_select(False)

        for ind in new_sel_add:
            if ind < loop_switch_pont:
                po_ind = avail_inds[ind]
                self._points_container.points[po_ind].set_select(True)
            else:
                sel_ind = avail_inds[ind]
                self._points_container.points[sel_ind[0]
                                              ].loops[sel_ind[1]].set_select(True)
                self._points_container.points[sel_ind[0]
                                              ].set_selection_from_loops()

        for ind in new_sel_remove:
            if ind < loop_switch_pont:
                po_ind = avail_inds[ind]
                self._points_container.points[po_ind].set_select(False)
            else:
                sel_ind = avail_inds[ind]
                self._points_container.points[sel_ind[0]
                                              ].loops[sel_ind[1]].set_select(False)
                self._points_container.points[sel_ind[0]
                                              ].set_selection_from_loops()

        if self._active_point != None:
            if self._active_point.select == False:
                self._points_container.clear_active()
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
    # Reset selection to only orbit object
    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    sel_cos = self._points_container.get_selected_loop_cos()
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


#
# KEYMAP TEST/LOAD
#
def load_keymap(self):
    # self.keymap = {}

    # for item in addon_keymaps[0][0].keymap_items:
    #     self.keymap[item.name] = item

    self.keymap = addon_keymaps[0]
    return


def keys_find(keymap_items, event):
    scroll_up = ['WHEELINMOUSE', 'WHEELUPMOUSE']
    scroll_down = ['WHEELOUTMOUSE', 'WHEELDOWNMOUSE']

    key_val = []
    for key in keymap_items:
        if key.type == event.type or (key.type in scroll_up and event.type in scroll_up) or (key.type in scroll_down and event.type in scroll_down):
            if (key.alt == event.alt and key.ctrl == event.ctrl and key.shift == event.shift) or key.any:
                if key.value == event.value:
                    key_val.append(key.name)

    # if len(key_val) == 0:
    #     key_val = None
    return key_val


def test_navigation_key(nav_list, event):
    nav_status = False

    scroll_up = ['WHEELINMOUSE', 'WHEELUPMOUSE']
    scroll_down = ['WHEELOUTMOUSE', 'WHEELDOWNMOUSE']

    nav_inds = [i for i in range(
        len(nav_list)) if (nav_list[i][0] == event.type and nav_list[i][1] == event.value) or (nav_list[i][0] in scroll_up and event.type in scroll_up) or (nav_list[i][0] in scroll_down and event.type in scroll_down)]
    if len(nav_inds) > 0:
        for ind in nav_inds:
            nav_key = nav_list[ind]
            if nav_key[2] or (event.ctrl == nav_key[3] and event.shift == nav_key[4] and event.alt == nav_key[5]):
                nav_status = True

    return nav_status
