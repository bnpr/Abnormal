from math import nan
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_line_plane
import numpy as np
import os
from bpy_extras import view3d_utils
from .functions_general import *
from .functions_drawing import *
from .functions_modal_keymap import *
from .classes import *
from .keymap import addon_keymaps


def match_loops_vecs(source_vecs, target_vecs, target_inds):
    #
    # Match the list of vectors with the target list
    # matches by smallest angle
    # Source vecs should be a 2d array Nx3 of just 3d vectors
    # Target vecs should be a 3d array NxIx3 where it is a list of lists of 3d vectors for the source vec to be tested against
    # Each I of the NxIx3 array is a list of vectors to test against the N vectors of source
    #

    # Get the dot product from the matched cos tangents to the original loops tangent
    # and filter out -1 loops from the matched co
    dots = np.sum(source_vecs[:, np.newaxis] * target_vecs, axis=2)

    dots *= -1
    dots[target_inds < 0] = nan

    sort = np.argsort(dots)[:, 0]

    indeces = np.arange(sort.size)

    return target_inds[indeces, sort]


#
#


def set_new_normals(self):
    self._object.data.edges.foreach_set(
        'use_edge_sharp', self._container.og_sharp)

    # Lerp between cached and new normals by the filter weights
    self._container.new_norms = self._container.cache_norms * \
        (1.0-self._container.filter_weights) + \
        self._container.new_norms * self._container.filter_weights

    # Get the scale factor to normalized new normals
    scale = 1 / np.sqrt(np.sum(np.square(self._container.new_norms), axis=1))
    self._container.new_norms = self._container.new_norms*scale[:, None]

    if self._mirror_x:
        sel_norms = self._container.new_norms[self._container.sel_status]
        sel_norms[:, 0] *= -1
        self._container.new_norms[self.mir_loops_x[self._container.sel_status]] = sel_norms
    if self._mirror_y:
        sel_norms = self._container.new_norms[self._container.sel_status]
        sel_norms[:, 1] *= -1
        self._container.new_norms[self.mir_loops_y[self._container.sel_status]] = sel_norms
    if self._mirror_z:
        sel_norms = self._container.new_norms[self._container.sel_status]
        sel_norms[:, 2] *= -1
        self._container.new_norms[self.mir_loops_z[self._container.sel_status]] = sel_norms

    # self._container.new_norms.shape = [len(self._object.data.loops), 3]
    self._object.data.normals_split_custom_set(self._container.new_norms)

    self.redraw = True
    return


def mirror_normals(self, axis):
    sel_norms = self._container.new_norms[self._container.sel_status]

    sel_norms[:, axis] *= -1
    if axis == 0:
        self._container.new_norms[self.mir_loops_x[self._container.sel_status]] = sel_norms
    if axis == 1:
        self._container.new_norms[self.mir_loops_y[self._container.sel_status]] = sel_norms
    if axis == 2:
        self._container.new_norms[self.mir_loops_z[self._container.sel_status]] = sel_norms

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def incremental_rotate_vectors(self, axis, direction):
    self.translate_mode = 2
    self.translate_axis = axis
    rotate_vectors(self, math.radians(direction * self._rot_increment))
    self.translate_mode = 0
    self.translate_axis = 2

    self._container.cache_norms[:] = self._container.new_norms

    self.redraw = True
    return


def rotate_vectors(self, angle):
    if self.translate_axis == 0:
        axis = 'X'
    if self.translate_axis == 1:
        axis = 'Y'
    if self.translate_axis == 2:
        axis = 'Z'

    rot = np.array(Matrix.Rotation(angle, 3, axis))

    # Viewspace rotation matrix
    if self.translate_mode == 0:
        persp_mat = bpy.context.region_data.view_matrix.to_3x3().normalized()
        loc_mat = self._object.matrix_world.to_3x3().normalized()

        self._container.new_norms[self._container.sel_status] = (np.array(
            loc_mat) @ self._container.cache_norms[self._container.sel_status].T).T
        self._container.new_norms[self._container.sel_status] = (np.array(
            persp_mat) @ self._container.new_norms[self._container.sel_status].T).T
        self._container.new_norms[self._container.sel_status] = (
            rot @ self._container.new_norms[self._container.sel_status].T).T
        self._container.new_norms[self._container.sel_status] = (np.array(
            persp_mat.inverted()) @ self._container.new_norms[self._container.sel_status].T).T
        self._container.new_norms[self._container.sel_status] = (np.array(
            loc_mat.inverted()) @ self._container.new_norms[self._container.sel_status].T).T

    # World space rotation matrix
    elif self.translate_mode == 1:
        loc_mat = self._object.matrix_world.to_3x3().normalized()

        self._container.new_norms[self._container.sel_status] = (np.array(
            loc_mat) @ self._container.cache_norms[self._container.sel_status].T).T
        self._container.new_norms[self._container.sel_status] = (
            rot @ self._container.new_norms[self._container.sel_status].T).T
        self._container.new_norms[self._container.sel_status] = (np.array(
            loc_mat.inverted()) @ self._container.new_norms[self._container.sel_status].T).T

    # Local space roatation matrix
    elif self.translate_mode == 2:
        if self.gizmo_click:
            orb_mat = self._orbit_ob.matrix_world.to_3x3().normalized()
            loc_mat = self._object.matrix_world.to_3x3().normalized()

            self._container.new_norms[self._container.sel_status] = (np.array(
                loc_mat) @ self._container.cache_norms[self._container.sel_status].T).T
            self._container.new_norms[self._container.sel_status] = (np.array(
                orb_mat.inverted()) @ self._container.new_norms[self._container.sel_status].T).T
            self._container.new_norms[self._container.sel_status] = (
                rot @ self._container.new_norms[self._container.sel_status].T).T
            self._container.new_norms[self._container.sel_status] = (
                np.array(orb_mat) @ self._container.new_norms[self._container.sel_status].T).T
            self._container.new_norms[self._container.sel_status] = (np.array(
                loc_mat.inverted()) @ self._container.new_norms[self._container.sel_status].T).T

        else:
            self._container.new_norms[self._container.sel_status] = (
                rot @ self._container.cache_norms[self._container.sel_status].T).T

    set_new_normals(self)
    return


#
# AXIS ALIGNMENT
#
def flatten_normals(self, axis):
    update_filter_weights(self)

    norms = self._container.new_norms[self._container.sel_status]
    norms[:, axis] = 0.0

    # Check for zero length vector after flattening
    # If zero then set it back to 1.0 on flattened axis
    zero_len = np.sum(norms, axis=1) == 0.0

    # All vecs are zero length so no change occurs
    if zero_len.all():
        return

    if zero_len.any():
        norms[zero_len] = self._container.new_norms[self._container.sel_status][zero_len]

    self._container.new_norms[self._container.sel_status] = norms

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def align_to_axis_normals(self, axis, dir):
    update_filter_weights(self)

    vec = [0, 0, 0]
    vec[axis] = dir
    self._container.new_norms[self._container.sel_status] = vec

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# MANIPULATE NORMALS
#
def average_vertex_normals(self):
    update_filter_weights(self)

    sel_pos = get_selected_points(self, any_selected=True)
    sel_loops = self._container.vert_link_ls[sel_pos]

    loop_status = self._container.sel_status[sel_loops]
    loop_status[sel_loops < 0] = False

    cur_norms = self._container.new_norms[sel_loops]
    cur_norms[~loop_status] = nan
    cur_norms = np.nanmean(cur_norms, axis=1)[:, np.newaxis]

    new_norms = self._container.new_norms[sel_loops]
    new_norms[:] = cur_norms
    sel_loops = sel_loops[loop_status]
    new_norms = new_norms[loop_status]

    self._container.new_norms[sel_loops] = new_norms

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def average_selected_normals(self):
    update_filter_weights(self)

    avg_norm = np.mean(
        self._container.new_norms[self._container.sel_status], axis=0)

    self._container.new_norms[self._container.sel_status] = avg_norm

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def smooth_normals(self, fac):
    update_filter_weights(self)

    sel_pos = get_selected_points(self, any_selected=True)
    conn_pos = self._container.vert_link_vs[sel_pos]
    sel_loops = self._container.vert_link_ls[sel_pos]
    sel_mask = sel_loops >= 0

    for i in range(self._smooth_iterations):

        conn_norms = self._container.new_norms[self._container.vert_link_ls[conn_pos]]
        conn_norms[self._container.vert_link_ls[conn_pos] < 0] = nan
        conn_norms[conn_pos < 0] = nan
        conn_norms = np.nanmean(conn_norms, axis=(1, 2))[:, np.newaxis]
        conn_norms = self._container.new_norms[sel_loops] * (
            1.0-fac*self._smooth_strength) + conn_norms*(fac*self._smooth_strength)

        conn_norms = conn_norms[sel_mask]

        self._container.new_norms[sel_loops[sel_mask]] = conn_norms

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# NORMAL DIRECTION
#
def flip_normals(self):
    self._container.new_norms[self._container.sel_status] *= -1

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def set_outside_inside(self, direction):
    update_filter_weights(self)

    if self._object_smooth:
        sel_pos = get_selected_points(self, any_selected=True)
        sel_loops = self._container.vert_link_ls[sel_pos]

        f_norms = self._container.face_normals[self._container.loop_faces[sel_loops]]
        f_norms[sel_loops < 0] = nan

        loop_status = self._container.sel_status[sel_loops]
        loop_status[sel_loops < 0] = False

        f_norms[~loop_status] = nan
        f_norms = np.nanmean(f_norms, axis=1)[:, np.newaxis]
        new_norms = self._container.new_norms[sel_loops]

        new_norms[:] = f_norms

        sel_loops = sel_loops[loop_status]
        new_norms = new_norms[loop_status]

        self._container.new_norms[sel_loops] = new_norms

    else:
        self._container.new_norms[self._container.sel_status] = self._container.face_normals[
            self._container.loop_faces[self._container.sel_status]]

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def reset_normals(self):
    self._container.new_norms[self._container.sel_status] = self._container.og_norms[self._container.sel_status]

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def set_normals_from_faces(self):
    update_filter_weights(self)

    # Get all faces that have all loops selected
    sel_fs = self._container.sel_status[self._container.face_link_ls]
    sel_fs[self._container.face_link_ls < 0] = True
    sel_fs = sel_fs.all(axis=1).nonzero()[0]

    # Get the unique vertices of these faces in a flat array
    face_vs = self._container.face_link_vs[sel_fs].ravel()
    face_vs = np.unique(face_vs[face_vs >= 0])

    # Get the loops of each vert
    vert_ls = self._container.vert_link_ls[face_vs]

    # Get the faces fand face normals of these loops
    loop_fs = self._container.loop_faces[vert_ls]
    face_l_norms = self._container.face_normals[loop_fs]

    # Find which of these loops is valid based on if its face is apart of the fully selected faces
    loop_status = np.in1d(loop_fs, sel_fs)
    loop_status.shape = [face_l_norms.shape[0], face_l_norms.shape[1]]
    loop_status[vert_ls < 0] = False

    # Remove loop face normals for non valid loops and average per vertex
    face_l_norms[~loop_status] = nan
    face_l_norms = np.nanmean(face_l_norms, axis=1)

    # Create array of vertex averaged normals for all of the loops connected to the verts
    new_norms = self._container.new_norms[vert_ls]
    new_norms[:] = face_l_norms[:, np.newaxis]

    # Filter out loops that should not be set
    # Filter by verts if individual loops is off and by loops if it is on
    if self._individual_loops:
        new_norms = new_norms[loop_status]
        vert_ls = vert_ls[loop_status]
    else:
        new_norms = new_norms[vert_ls >= 0]
        vert_ls = vert_ls[vert_ls >= 0]

    self._container.new_norms[vert_ls] = new_norms

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


#
# COPY/PASTE
#
def copy_active_to_selected(self):
    update_filter_weights(self)

    act_loops = self._container.act_status.nonzero()[0]

    # 1 active loop so paste it onto all selected
    if act_loops.size == 1:
        self._container.new_norms[self._container.sel_status] = self._container.new_norms[act_loops[0]]

    # Find active po and match the tangents of this po to the selected loops
    else:
        act_po = get_active_point(self)
        act_ls = self._container.vert_link_ls[act_po]
        act_ls = act_ls[act_ls >= 0]

        sel_loops = self._container.sel_status
        sel_loops[act_ls] = False

        match_pos = [act_po]*sel_loops.nonzero()[0].size
        target_tans = self._container.loop_tangents[self._container.vert_link_ls[match_pos]]

        loop_matches = match_loops_vecs(
            self._container.loop_tangents[sel_loops], target_tans, self._container.vert_link_ls[match_pos])

        self._container.new_norms[sel_loops] = self._container.new_norms[loop_matches]

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


def store_active_normal(self):
    act_loops = self._container.act_status.nonzero()[0]

    # 1 active loop so paste it onto all selected
    if act_loops.size == 1:
        self._copy_normals = act_loops

    # Find active po and match the tangents of this po to the selected loops
    else:
        act_po = get_active_point(self)
        act_ls = self._container.vert_link_ls[act_po]
        act_ls = act_ls[act_ls >= 0]

        self._copy_normals = act_ls
    return


def paste_normal(self):
    update_filter_weights(self)

    if self._copy_normals.size > 0:
        # 1 active loop so paste it onto all selected
        if self._copy_normals.size == 1:
            self._container.new_norms[self._container.sel_status] = self._container.new_norms[self._copy_normals[0]]

        # Find active po and match the tangents of this po to the selected loops
        else:
            sel_loops = self._container.sel_status
            sel_loops[self._copy_normals] = False

            target_tans = np.tile(
                self._container.loop_tangents[self._copy_normals], (sel_loops.nonzero()[0].size, 1, 1))
            target_inds = np.tile(self._copy_normals,
                                  (sel_loops.nonzero()[0].size, 1))

            loop_matches = match_loops_vecs(
                self._container.loop_tangents[sel_loops], target_tans, target_inds)

            self._container.new_norms[sel_loops] = self._container.new_norms[loop_matches]

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
        mat = generate_matrix(Vector((0, 0, 0)), Vector(
            (0, 0, 1)), Vector((0, 1, 0)), False, True)
        mat.translation = self._mode_cache[0]

    elif self.translate_mode == 2:
        mat = self._object.matrix_world.normalized()
        mat.translation = self._mode_cache[0]

    if mat != None:
        self.translate_draw_line.clear()

        if self.translate_axis == 0:
            vec = Vector((1000, 0, 0))
        if self.translate_axis == 1:
            vec = Vector((0, 1000, 0))
        if self.translate_axis == 2:
            vec = Vector((0, 0, 1000))

        self.translate_draw_line.append(mat @ vec)
        self.translate_draw_line.append(mat @ -vec)

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

    return


def translate_axis_side(self):
    view_vec = view3d_utils.region_2d_to_vector_3d(
        self.act_reg, self.act_rv3d, Vector(self._mouse_reg_loc))

    if self.translate_mode == 1:
        mat = generate_matrix(Vector((0, 0, 0)), Vector(
            (0, 0, 1)), Vector((0, 1, 0)), False, True)
    else:
        mat = self._object.matrix_world.normalized()

    pos_vec = Vector((0, 0, 0))
    neg_vec = Vector((0, 0, 0))
    pos_vec[self.translate_axis] = 1.0
    neg_vec[self.translate_axis] = -1.0

    pos_vec = (mat @ pos_vec) - mat.translation
    neg_vec = (mat @ neg_vec) - mat.translation

    if pos_vec.angle(view_vec) < neg_vec.angle(view_vec):
        side = -1
    else:
        side = 1

    # if self.translate_axis == 1:
    #     side *= -1
    return side


#
# MODAL
#
def cache_point_data(self):
    self._object.data.calc_normals_split()

    vert_amnt = len(self._object.data.vertices)
    edge_amnt = len(self._object.data.edges)
    loop_amnt = len(self._object.data.loops)
    face_amnt = len(self._object.data.polygons)

    self._container.og_sharp = np.zeros(edge_amnt, dtype=bool)
    self._object.data.edges.foreach_get(
        'use_edge_sharp', self._container.og_sharp)

    self._container.og_seam = np.zeros(edge_amnt, dtype=bool)
    self._object.data.edges.foreach_get('use_seam', self._container.og_seam)

    self._container.og_norms = np.zeros(loop_amnt*3, dtype=np.float32)
    self._object.data.loops.foreach_get('normal', self._container.og_norms)
    self._container.og_norms.shape = [loop_amnt, 3]

    self._container.new_norms = self._container.og_norms.copy()
    self._container.cache_norms = self._container.og_norms.copy()

    max_link_eds = max([len(v.link_edges) for v in self._object_bm.verts])
    max_link_loops = max([len(v.link_loops) for v in self._object_bm.verts])
    max_link_f_vs = max([len(f.verts) for f in self._object_bm.faces])
    max_link_f_loops = max([len(f.loops) for f in self._object_bm.faces])
    max_link_f_eds = max([len(f.edges) for f in self._object_bm.faces])

    #

    link_vs = []
    link_ls = []
    link_fs = [None for i in range(loop_amnt)]
    for v in self._object_bm.verts:
        l_v_inds = [-1] * max_link_eds
        l_l_inds = [-1] * max_link_loops

        for e, ed in enumerate(v.link_edges):
            l_v_inds[e] = ed.other_vert(v).index

        for l, loop in enumerate(v.link_loops):
            l_l_inds[l] = loop.index
            link_fs[loop.index] = loop.face.index

        link_vs += l_v_inds
        link_ls += l_l_inds

    self._container.vert_link_vs = np.array(link_vs, dtype=np.int32)
    self._container.vert_link_vs.shape = [vert_amnt, max_link_eds]

    self._container.vert_link_ls = np.array(link_ls, dtype=np.int32)
    self._container.vert_link_ls.shape = [vert_amnt, max_link_loops]

    self._container.loop_faces = np.array(link_fs, dtype=np.int32)
    self._container.filter_weights = np.zeroes(loop_amnt, dtype=np.float32)

    #

    link_f_vs = []
    link_f_ls = []
    link_f_eds = []
    face_normals = []
    l_tangents = [None for i in range(loop_amnt)]
    for f in self._object_bm.faces:
        l_v_inds = [-1] * max_link_f_vs
        l_l_inds = [-1] * max_link_f_loops
        l_e_inds = [-1] * max_link_f_eds

        for v, vert in enumerate(f.verts):
            l_v_inds[v] = vert.index

        for l, loop in enumerate(f.loops):
            l_l_inds[l] = loop.index
            l_tangents[loop.index] = loop.calc_tangent()

        face_normals.append(f.normal)

        link_f_vs += l_v_inds
        link_f_ls += l_l_inds
        link_f_eds += l_e_inds

    self._container.face_link_vs = np.array(link_f_vs, dtype=np.int32)
    self._container.face_link_vs.shape = [face_amnt, max_link_f_vs]

    self._container.face_link_ls = np.array(link_f_ls, dtype=np.int32)
    self._container.face_link_ls.shape = [face_amnt, max_link_f_loops]

    self._container.face_link_eds = np.array(link_f_eds, dtype=np.int32)
    self._container.face_link_eds.shape = [face_amnt, max_link_f_eds]

    self._container.loop_tangents = np.array(l_tangents, dtype=np.float32)
    self._container.loop_tangents.shape = [loop_amnt, 3]

    self._container.face_normals = np.array(face_normals, dtype=np.float32)
    self._container.face_normals.shape = [face_amnt, 3]

    #

    link_ed_vs = []
    for ed in self._object_bm.edges:
        link_ed_vs.append([ed.verts[0].index, ed.verts[1].index])

    self._container.edge_link_vs = np.array(link_ed_vs, dtype=np.int32)
    self._container.edge_link_vs.shape = [edge_amnt, 2]

    #

    self._container.po_coords = np.array(
        [v.co for v in self._object_bm.verts], dtype=np.float32)
    self._container.loop_coords = np.array(
        [self._object_bm.verts[l.vertex_index].co for l in self._object.data.loops], dtype=np.float32)

    loop_tri_cos = [[] for i in range(loop_amnt)]
    for v in self._object_bm.verts:
        ed_inds = [ed.index for ed in v.link_edges]
        for loop in v.link_loops:
            loop_cos = [v.co+v.normal*.001]
            for ed in loop.face.edges:
                if ed.index in ed_inds:
                    ov = ed.other_vert(v)
                    vec = (ov.co+ov.normal*.001) - (v.co+v.normal*.001)

                    loop_cos.append((v.co+v.normal*.001) + vec * 0.5)

            loop_tri_cos[loop.index] = loop_cos

    self._container.loop_tri_coords = np.array(loop_tri_cos, dtype=np.float32)

    #
    #

    loop_sel = [False] * loop_amnt
    loop_hide = [True] * loop_amnt
    loop_act = [False] * loop_amnt
    for v in self._object_bm.verts:
        for loop in v.link_loops:
            # Vertex selection
            if bpy.context.tool_settings.mesh_select_mode[0]:
                loop_sel[loop.index] = v.select

            loop_hide[loop.index] = v.hide

    # Edge selection
    if bpy.context.tool_settings.mesh_select_mode[1]:
        for ed in self._object_bm.edges:
            if ed.select:
                for v in ed.verts:
                    for loop in v.link_loops:
                        loop_sel[loop.index] = True

    # Face selection
    if bpy.context.tool_settings.mesh_select_mode[2]:
        for f in self._object_bm.faces:
            if f.select:
                if self._individual_loops:
                    for loop in f.loops:
                        loop_sel[loop.index] = True
                else:
                    for v in f.verts:
                        for loop in v.link_loops:
                            loop_sel[loop.index] = True

    self._container.hide_status = np.array(loop_hide, dtype=bool)
    self._container.sel_status = np.array(loop_sel, dtype=bool)
    self._container.act_status = np.array(loop_act, dtype=bool)

    cache_mirror_data(self)
    return


def cache_mirror_data(self):
    mat = np.array(self._object.matrix_world)
    mat_inv = np.array(self._object.matrix_world.inverted())

    loc = mat[:3, 3]
    loop_cos = (mat_inv[:3, :3] @ (self._container.loop_coords-loc).T).T

    self.mir_loops_x = find_coord_mirror(self._container.po_coords, loop_cos.copy(
    ), self._container.loop_tangents.copy(), self._container.vert_link_ls, 0, mat)

    self.mir_loops_y = find_coord_mirror(self._container.po_coords, loop_cos.copy(
    ), self._container.loop_tangents.copy(), self._container.vert_link_ls, 1, mat)

    self.mir_loops_z = find_coord_mirror(self._container.po_coords, loop_cos.copy(
    ), self._container.loop_tangents.copy(), self._container.vert_link_ls, 2, mat)
    return


def find_coord_mirror(po_coords, l_coords, loop_tangs, vert_link_ls, mir_axis, mat):
    #
    # Match the list of loops with their mirror on the set axis
    # detect the proper loop on the mirror point by getting the smallest angle
    #

    # Get the loop coords on the mirrored axis
    l_coords[:, mir_axis] *= -1
    l_coords = (mat[:3, :3] @ l_coords.T).T+mat[:3, 3]

    # Test distance for nearest points from the loops mirroed coord
    po_match = get_np_vecs_ordered_dists(po_coords, l_coords)[:, 0]

    # Get the tangents of the matched mirror coord
    tans = loop_tangs[vert_link_ls[po_match]]

    loop_tangs[:, mir_axis] *= -1

    # Test the dot products for the smallest of the current loop to the matched points loops
    # filters out -1 mathc loop indices
    match_tans = match_loops_vecs(loop_tangs, tans, vert_link_ls[po_match])

    return match_tans


def update_filter_weights(self):
    abn_props = bpy.context.scene.abnormal_props

    weights = [1.0] * len(self._object.data.loops)
    if abn_props.vertex_group != '' and abn_props.vertex_group != self._current_filter:
        if abn_props.vertex_group in self._object.vertex_groups:
            for v in self._object_bm.verts:
                vg = self._object.vertex_groups[abn_props.vertex_group]
                self._current_filter = abn_props.vertex_group

                try:
                    weight = vg.weight(v.index)
                    self._container.filter_weights[self._container.vert_link_ls[v.index]] = weight

                except:
                    self._container.filter_weights[self._container.vert_link_ls[v.index]] = 0.0

        else:
            self._current_filter = ''
            abn_props.vertex_group = ''

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

    bvh = BVHTree.FromBMesh(bm)

    kd = create_kd(bm)

    return bm, kd, bvh


def add_to_undostack(self, stack_type):
    if stack_type == 0:
        sel_status = (self._container.sel_status).nonzero()[0]
        vis_status = self._container.hide_status.nonzero()[0]

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
        cur_normals = self._container.new_norms.copy()
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
            for po in self._container.points:
                po.set_hide(True)

            for ind in vis_state:
                po = self._container.points[ind[0]]
                if po.valid:
                    loop = po.loops[ind[1]]
                    loop.set_hide(False)

                po.set_hidden_from_loops()

            for po in self._container.points:
                po.set_select(False)

            for ind in state:
                po = self._container.points[ind[0]]
                if po.hide == False and po.valid:
                    loop = po.loops[ind[1]]
                    if loop.hide == False:
                        loop.set_select(True)

                po.set_selection_from_loops()

            if self._active_point != None:
                if self._active_point.select == False:
                    self._active_point = None

            update_orbit_empty(self)
            self.redraw = True

        if state_type == 1:
            for po in self._container.points:
                for loop in po.loops:
                    loop.normal = state[po.index][loop.index].copy()

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

        self._object.data.edges.foreach_set(
            'use_edge_sharp', self._container.og_sharp)

        # restore normals
        ob.data.normals_split_custom_set(self._container.og_norms)

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
            if self._container.sel_status.any() == False:
                return True

        self._mode_cache.clear()

        # Cache current normals before rotation starts and setup gizmo as being used
        if event.alt == False:

            for gizmo in self._window.gizmo_sets[giz_status[1]].gizmos:
                if gizmo.index != giz_status[2]:
                    gizmo.active = False
                else:
                    gizmo.in_use = True

        orb_mat = self._orbit_ob.matrix_world

        view_vec = view3d_utils.region_2d_to_vector_3d(self.act_reg, self.act_rv3d, Vector(
            (self._mouse_reg_loc[0], self._mouse_reg_loc[1])))
        view_orig = view3d_utils.region_2d_to_origin_3d(
            self.act_reg, self.act_rv3d, Vector((self._mouse_reg_loc[0], self._mouse_reg_loc[1])))

        line_a = view_orig
        line_b = view_orig + view_vec*10000

        # Project cursor from view onto the rotation axis plane
        if giz_status[0] == 'ROT_X':
            giz_vec = orb_mat @ Vector((1, 0, 0)) - orb_mat.translation
            self.translate_axis = 0

        if giz_status[0] == 'ROT_Y':
            giz_vec = orb_mat @ Vector((0, 1, 0)) - orb_mat.translation
            self.translate_axis = 1

        if giz_status[0] == 'ROT_Z':
            giz_vec = orb_mat @ Vector((0, 0, 1)) - orb_mat.translation
            self.translate_axis = 2

        mouse_co_3d = intersect_line_plane(
            line_a, line_b, orb_mat.translation, giz_vec)
        mouse_co_local = orb_mat.inverted() @ mouse_co_3d

        # Get start angle for rotation
        if giz_status[0] == 'ROT_X':
            test_vec = mouse_co_local.yz

        if giz_status[0] == 'ROT_Y':
            test_vec = mouse_co_local.xz

        if giz_status[0] == 'ROT_Z':
            test_vec = mouse_co_local.xy

        self.translate_mode = 2
        ang_offset = Vector((0, 1)).angle_signed(test_vec)
        self._mode_cache.append(test_vec)
        # Add cache data for tool mode
        if event.alt == False:
            self._window.update_gizmo_rot(0, -ang_offset)
            self._mode_cache.append(0)
            self._mode_cache.append(-ang_offset)
            self._mode_cache.append(orb_mat.copy())
            self._mode_cache.append(True)
        else:
            self._mode_cache.append(0)
            self._mode_cache.append(-ang_offset)
            self._mode_cache.append(orb_mat.copy())
            self._mode_cache.append(False)

        self._container.cache_norms[:] = self._container.new_norms

        self.gizmo_click = True
        self._current_tool = self._gizmo_tool
        self.tool_mode = True
        start_active_drawing(self)

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

    avg_loc = np.mean(
        self._container.loop_coords[self._container.sel_status], axis=0)
    self._target_emp.location = avg_loc
    self._target_emp.empty_display_size = 0.5
    self._target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self._target_emp

    self._mode_cache.append(avg_loc)

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

    sphereize_normals(self)
    return


def end_sphereize_mode(self, keep_normals):
    if keep_normals == False:
        set_new_normals(self)

    # self._export_panel.set_visibility(True)
    self._tools_panel.set_visibility(True)
    self._sphere_panel.set_visibility(False)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
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


def sphereize_normals(self):
    for i, ind in enumerate(sel_inds):
        po = self._container.points[ind[0]]
        loop = po.loops[ind[1]]

        if po.valid:
            vec = (self._object.matrix_world.inverted() @ po.co) - \
                (self._object.matrix_world.inverted() @ self._target_emp.location)

            loop_norm_set(
                self, loop, loop.cached_normal, loop.cached_normal.lerp(vec, self.target_strength))

            self.redraw_active = True

    set_new_normals(self)
    return


def start_point_mode(self):
    update_filter_weights(self)

    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    avg_loc = np.mean(
        self._container.loop_coords[self._container.sel_status], axis=0)
    self._target_emp.location = avg_loc
    self._target_emp.empty_display_size = 0.5
    self._target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self._target_emp

    self._mode_cache.append(avg_loc)

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

    point_normals(self)
    return


def end_point_mode(self, keep_normals):
    if keep_normals == False:
        set_new_normals(self)

    # self._export_panel.set_visibility(True)
    self._tools_panel.set_visibility(True)
    self._point_panel.set_visibility(False)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
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


def point_normals(self):
    if self.point_align:
        avg_loc = np.mean(
            self._container.loop_coords[self._container.sel_status], axis=0)
        vec = (self._object.matrix_world.inverted() @ self._target_emp.location) - \
            (self._object.matrix_world.inverted() @ avg_loc)

    for i, ind in enumerate(sel_inds):
        po = self._container.points[ind[0]]
        loop = po.loops[ind[1]]

        if po.valid:
            if self.point_align == False:
                vec = (self._object.matrix_world.inverted(
                ) @ self._target_emp.location) - (self._object.matrix_world.inverted() @ po.co)

            loop_norm_set(
                self, loop, loop.cached_normal, loop.cached_normal.lerp(vec, self.target_strength))

            self.redraw_active = True

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

        def_vec = Vector((0, 0, 0))
        def_vec[self.translate_axis] = def_dist

        def_vec = (self._object.matrix_world @ def_vec) - \
            self._object.matrix_world.translation

        self._target_emp.location = self._mode_cache[3].copy()
        self._target_emp.location += def_vec

    return


#
# SELECTION
#
def get_hidden_faces(self):
    if self._individual_loops:
        # Get indices of faces that all connected loops are hidden
        hid_faces = self._container.hide_status[self._container.face_link_ls]
        hid_faces[self._container.face_link_ls < 0] = False
        hid_faces = hid_faces.any(axis=1)
        hid_faces = list(hid_faces.nonzero()[0])

    else:
        # Get indices of faces that all connected vert loops are hidden
        face_ls = self._container.vert_link_ls[self._container.face_link_vs]

        hid_faces = self._container.hide_status[face_ls]
        hid_faces[face_ls < 0] = False
        hid_faces = hid_faces.any(axis=1)
        hid_faces = list(hid_faces.nonzero()[0])

    return hid_faces


def get_hidden_points(self):
    # Get indices of points that all connected loops are hidden
    hid_pos = self._container.hide_status[self._container.vert_link_ls]
    hid_pos[self._container.vert_link_ls < 0] = True
    hid_pos = hid_pos.all(axis=1)
    hid_pos = hid_pos.nonzero()[0]

    return hid_pos


def get_hidden_loops(self):
    # Get indices of loops that are hidden
    hid_ls = self._container.hide_status.nonzero()[0]
    return hid_ls


def get_visible_points(self):
    # Get indices of points that all connected loops are visible
    vis_pos = self._container.hide_status[self._container.vert_link_ls]
    vis_pos[self._container.vert_link_ls < 0] = False
    vis_pos = vis_pos.all(axis=1)
    vis_pos = (~vis_pos).nonzero()[0]

    return vis_pos


def get_selected_points(self, any_selected=False):
    # Get indices of points that all connected loops are visible
    vis_pos = self._container.sel_status[self._container.vert_link_ls]
    if any_selected:
        vis_pos[self._container.vert_link_ls < 0] = False
        vis_pos = vis_pos.any(axis=1)
    else:
        vis_pos[self._container.vert_link_ls < 0] = True
        vis_pos = vis_pos.all(axis=1)
    vis_pos = vis_pos.nonzero()[0]

    return vis_pos


def get_active_point(self):
    # Find active point to find a vert path from if no active then do nothing
    act_point = None
    loop_act_status = self._container.act_status[self._container.vert_link_ls]
    loop_act_status[self._container.vert_link_ls < 0] = False
    loop_act_status = loop_act_status.any(axis=1)
    act_points = loop_act_status.nonzero()[0]

    if act_points.size > 0:
        act_point = act_points[0]

    return act_point


def get_active_face(self):
    # Find active face by testing every face for a face with all loops being active
    act_face = None
    face_act_status = self._container.act_status[self._container.face_link_ls]
    face_act_status[self._container.face_link_ls < 0] = True
    face_act_status = face_act_status.all(axis=1)
    act_faces = face_act_status.nonzero()[0]

    if act_faces.size > 0:
        act_face = act_faces[0]

    return act_face


def get_face_ls(self, face_inds):
    if self._individual_loops:
        sel_loops = self._container.face_link_ls[face_inds]
    else:
        face_vs = self._container.face_link_vs[face_inds]
        face_vs = face_vs[face_vs >= 0]

        sel_loops = self._container.vert_link_ls[face_vs]

    sel_loops = sel_loops[sel_loops >= 0]
    loops = filter_hidden_loops(self, sel_loops)
    return loops


def get_vert_ls(self, vert_inds):
    sel_loops = self._container.vert_link_ls[vert_inds]
    sel_loops = sel_loops[sel_loops >= 0]

    loops = filter_hidden_loops(self, sel_loops)
    return loops


def get_edge_ls(self, edge_inds):
    sel_loops = self._container.vert_link_ls[self._container.edge_link_vs[edge_inds]]
    sel_loops = sel_loops[sel_loops >= 0]

    loops = filter_hidden_loops(self, sel_loops)
    return loops


def filter_hidden_verts(self, mask):
    v_ls = self._container.vert_link_ls

    hidden = ~self._container.hide_status[v_ls[mask]].all(axis=1)
    mask = mask[hidden]
    return mask


def filter_hidden_faces(self, mask):
    if self._individual_loops:
        sel_loops = self._container.face_link_ls[mask]
        hidden = ~self._container.hide_status[sel_loops]
        hidden[sel_loops < 0] = False
        hidden = hidden.any(axis=1)
    else:
        face_vs = self._container.face_link_vs[mask]
        sel_loops = self._container.vert_link_ls[face_vs]
        hidden = ~self._container.hide_status[sel_loops]
        hidden[face_vs < 0] = False
        hidden[sel_loops < 0] = False
        hidden = hidden.any(axis=1).any(axis=1)

    mask = mask[hidden]
    return mask


def filter_hidden_loops(self, mask):
    hidden = ~self._container.hide_status[mask]
    mask = mask[hidden]
    return mask


def set_click_selection(self, shift, mask):
    # New selection so clear act and sel and set current as sel/act
    if shift == False:
        self._container.sel_status[:] = False
        self._container.act_status[:] = False

        self._container.sel_status[mask] = True
        self._container.act_status[mask] = True

    # Adding to selection
    else:
        l_sel = self._container.sel_status[mask]
        l_act = self._container.act_status[mask]

        # Check if any point loops are not sel/act if so make all sel/act
        if l_sel.all() == False or l_act.all() == False:
            self._container.sel_status[mask] = True
            self._container.act_status[:] = False
            self._container.act_status[mask] = True

        # If all loops neither act/sel then all loops are sel/act so clear both
        else:
            self._container.sel_status[mask] = False
            self._container.act_status[:] = False

    return


def set_multi_selection(self, shift, mask, act_mask):
    self._container.act_status[:] = False
    if shift == False:
        self._container.sel_status[:] = False

    if self._container.sel_status[mask].all():
        self._container.sel_status[mask] = False
    else:
        self._container.sel_status[mask] = True
        self._container.act_status[act_mask] = True
    return


def set_group_selection(self, shift, ctrl, mask):
    if shift == False and ctrl == False:
        self._container.sel_status[:] = False

    if ctrl:
        self._container.sel_status[mask] = False
    else:
        self._container.sel_status[mask] = True

    # Check if active point/face lost is no longer selected
    act_face = get_active_face(self)
    if act_face != None:
        act_ls = get_face_ls(self, [act_face])
        if self._container.sel_status[act_ls].all() == False:
            self._container.act_status[:] = False

    act_point = get_active_point(self)
    if act_point != None:
        act_ls = get_vert_ls(self, [act_point])

        if self._individual_loops:
            if self._container.sel_status[act_ls].all() == False:
                self._container.act_status[:] = False
        else:
            self._container.act_status[act_ls] = self._container.sel_status[act_ls]

    return


#


def selection_test(self, shift):
    # Get coords in region space
    rcos = get_np_region_cos(self._container.po_coords,
                             self.act_reg, self.act_rv3d)

    # Get ordered list of closest points within the threshold
    d_order = get_np_vec_ordered_dists(
        rcos, [self._mouse_reg_loc[0], self._mouse_reg_loc[1], 0.0], threshold=15.0)

    d_order = filter_hidden_verts(self, d_order)

    change = False
    # Point selection
    if d_order.size > 0:
        # Test for first point that is non occluded if xray off
        if self._x_ray_mode == False:
            po_ind = None
            for ind in d_order:
                valid_po = not ray_cast_view_occlude_test(
                    Vector(self._container.po_coords[ind]), self._mouse_reg_loc, self._object_bvh, self.act_reg, self.act_rv3d)
                if valid_po:
                    po_ind = ind
                    break
        else:
            po_ind = d_order[0]

        if po_ind != None:
            mask = get_vert_ls(self, po_ind)
            set_click_selection(self, shift, mask)
            change = True

    # Face/Loop Tri selection
    if change == False:
        face_res = ray_cast_to_mouse(self)

        if face_res != None:
            hidden = filter_hidden_faces(self, np.array([face_res[1]]))
            if hidden.size > 0:
                # If using individual loops first test for loop a tri selection
                if self._individual_loops:
                    mask = get_face_ls(self, face_res[1])

                    tri_cos = self._container.loop_tri_coords[mask]
                    tri_cos.shape = [tri_cos.shape[0] *
                                     tri_cos.shape[1], tri_cos.shape[2]]

                    rcos = get_np_region_cos(
                        tri_cos, self.act_reg, self.act_rv3d)
                    rcos.shape = [mask.size, 3, 3]

                    for c, co_set in enumerate(rcos):
                        intersect = intersect_point_tri_2d(
                            self._mouse_reg_loc, Vector(co_set[0]), Vector(co_set[1]), Vector(co_set[2]))
                        if intersect:
                            set_click_selection(self, shift, mask[c])
                            change = True
                            break

                # If still haven't gotten a selection then select the face loops/verts
                if change == False:
                    mask = get_face_ls(self, face_res[1])
                    set_click_selection(self, shift, mask)
                    change = True

    return change


def loop_selection_test(self, shift):
    change = False
    face_res = ray_cast_to_mouse(self)
    if face_res != None:
        # Get edges of clicked face
        face_edges = self._container.face_link_eds[face_res[1]]
        face_edges = face_edges[face_edges >= 0]

        # Get coords of the 2 verts of the faces edges
        po_inds = self._container.edge_link_vs[face_edges]
        edge_cos = self._container.po_coords[po_inds]

        # Get region coords of face edges
        shape = [edge_cos.shape[0], edge_cos.shape[1]]
        edge_cos.shape = [shape[0]*shape[1], 3]
        rcos = get_np_region_cos(edge_cos, self.act_reg, self.act_rv3d)

        rcos.shape = [shape[0], shape[1], 3]

        face_co = get_np_region_cos([face_res[0]], self.act_reg, self.act_rv3d)

        # Get nearest edge to the click location
        ed_dists = get_np_dist_to_edge(rcos, face_co)
        ed_order = np.argsort(ed_dists)
        ed_dists = ed_dists[ed_order]
        if ed_order.size > 0:
            # Edge loop selection
            if ed_dists[0] < 10.0:
                # Get indices of points that all connected loops are hidden
                skip_vs = list(get_hidden_points(self))

                face_edge = self._container.face_link_eds[face_res[1]
                                                          ][ed_order[0]]
                sel_eds = get_edge_loop(
                    self._object_bm, self._object_bm.edges[face_edge], skip_verts=skip_vs)

                edge_vs = self._container.edge_link_vs[face_edge]
                v_order = get_np_vec_ordered_dists(
                    self._container.po_coords[edge_vs], face_res[0])
                near_vert = edge_vs[v_order[0]]

                sel_loops = get_edge_ls(self, sel_eds)
                act_ls = get_vert_ls(self, near_vert)

                set_multi_selection(self, shift, sel_loops, act_ls)
                change = True

            # Face loop selection
            else:
                skip_fs = list(get_hidden_faces(self))

                face_edge = self._container.face_link_eds[face_res[1]
                                                          ][ed_order[0]]
                sel_loop = get_face_loop(
                    self._object_bm, self._object_bm.edges[face_edge], skip_fs=list(skip_fs))

                sel_loops = get_face_ls(self, sel_loop)
                act_ls = get_face_ls(self, face_res[1])

                set_multi_selection(self, shift, sel_loops, act_ls)
                change = True

    return change


def path_selection_test(self, shift):
    change = False
    face_res = ray_cast_to_mouse(self)
    if face_res != None:
        act_face = get_active_face(self)

        # Test for face path
        if act_face != None:
            self._container.act_status[:] = False
            if shift == False:
                self._container.sel_status[:] = False

            skip_faces = list(get_hidden_faces(self))

            path_f = find_path_between_faces(
                [act_face, face_res[1]], self._object_bm, skip_fs=skip_faces)

            sel_loops = get_face_ls(self, path_f)
            act_ls = get_face_ls(self, face_res[1])

            set_multi_selection(self, shift, sel_loops, act_ls)
            change = True

        # Test for vert path
        else:
            act_point = get_active_point(self)

            if act_point != None:
                near_ind = self._object_kd.find(face_res[0])

                if near_ind[1] != act_point:
                    skip_verts = list(get_hidden_points(self))

                    path_v, path_ed = find_path_between_verts(
                        [act_point, near_ind[1]], self._object_bm, skip_verts=skip_verts)

                    sel_loops = get_vert_ls(self, path_v)
                    act_ls = get_vert_ls(self, near_ind[1])

                    set_multi_selection(self, shift, sel_loops, act_ls)
                    change = True

    return change


def group_vert_selection_test(self, vert_ind_array, shift, ctrl):
    change = False
    # Vertex selection
    if vert_ind_array.size > 0:
        # Test for occlusion
        if self._x_ray_mode == False:
            valid_pos = []

            for ind in vert_ind_array:
                valid_po = not ray_cast_view_occlude_test(
                    Vector(self._container.po_coords[ind]), self._mouse_reg_loc, self._object_bvh, self.act_reg, self.act_rv3d)
                if valid_po:
                    valid_pos.append(ind)

            valid_pos = np.array(valid_pos)
        else:
            valid_pos = vert_ind_array

        if valid_pos.size > 0:
            sel_loops = get_vert_ls(self, valid_pos)
            if sel_loops.size > 0:
                set_group_selection(self, shift, ctrl, sel_loops)
                change = True
    return change


def group_loop_selection_test(self, loop_ind_array, tri_cos, shift, ctrl):
    change = False

    if loop_ind_array.size > 0:
        # Test for occlusion
        if self._x_ray_mode == False:
            sel_loops = []

            for ind in loop_ind_array:
                valid_po = not ray_cast_view_occlude_test(
                    Vector(tri_cos[ind]), self._mouse_reg_loc, self._object_bvh, self.act_reg, self.act_rv3d)
                if valid_po:
                    sel_loops.append(ind)

            sel_loops = np.array(sel_loops)
        else:
            sel_loops = loop_ind_array

        if sel_loops.size > 0:
            set_group_selection(self, shift, ctrl, sel_loops)
            change = True
    return change


def box_selection_test(self, shift, ctrl):
    # Get coords in region space
    rcos = get_np_region_cos(self._container.po_coords,
                             self.act_reg, self.act_rv3d)

    x_cos = np.array([self._mouse_reg_loc[0], self._mode_cache[0][0][0]])
    y_cos = np.array([self._mouse_reg_loc[1], self._mode_cache[0][0][1]])
    in_range = np_box_selection_test(rcos, x_cos, y_cos)
    in_range = filter_hidden_verts(self, in_range)

    change = group_vert_selection_test(self, in_range, shift, ctrl)

    # Test loop tris for selection
    if self._individual_loops:
        loop_tri_cos = self._container.loop_tri_coords.mean(axis=1)

        # Get coords in region space
        rcos = get_np_region_cos(loop_tri_cos, self.act_reg, self.act_rv3d)

        in_range = np_box_selection_test(rcos, x_cos, y_cos)
        in_range = filter_hidden_loops(self, in_range)

        l_change = group_loop_selection_test(
            self, in_range, loop_tri_cos, shift, ctrl)
        if l_change:
            change = l_change

    return change


def circle_selection_test(self, shift, ctrl, radius):
    # Get coords in region space
    rcos = get_np_region_cos(self._container.po_coords,
                             self.act_reg, self.act_rv3d)

    # Get ordered list of closest points within the threshold
    in_range = get_np_vec_ordered_dists(
        rcos, [self._mouse_reg_loc[0], self._mouse_reg_loc[1], 0.0], threshold=radius)
    in_range = filter_hidden_verts(self, in_range)

    change = group_vert_selection_test(self, in_range, True, ctrl)

    # Test loop tris for selection
    if self._individual_loops:
        loop_tri_cos = self._container.loop_tri_coords.mean(axis=1)

        # Get coords in region space
        rcos = get_np_region_cos(loop_tri_cos, self.act_reg, self.act_rv3d)

        in_range = get_np_vec_ordered_dists(
            rcos, [self._mouse_reg_loc[0], self._mouse_reg_loc[1], 0.0], threshold=radius)
        in_range = filter_hidden_loops(self, in_range)

        l_change = group_loop_selection_test(
            self, in_range, loop_tri_cos, True, ctrl)
        if l_change:
            change = l_change

    return change


def lasso_selection_test(self, shift, ctrl):
    # Get coords in region space
    rcos = get_np_region_cos(self._container.po_coords,
                             self.act_reg, self.act_rv3d)

    # Get ordered list of closest points within the threshold
    lasso_shape = np.array(self._mode_cache[0])
    in_range = np_test_cos_in_shape(rcos, lasso_shape)
    in_range = filter_hidden_verts(self, in_range)

    change = group_vert_selection_test(self, in_range, shift, ctrl)

    # Test loop tris for selection
    if self._individual_loops:
        loop_tri_cos = self._container.loop_tri_coords.mean(axis=1)

        # Get coords in region space
        rcos = get_np_region_cos(loop_tri_cos, self.act_reg, self.act_rv3d)

        in_range = np_test_cos_in_shape(rcos, lasso_shape)
        in_range = filter_hidden_loops(self, in_range)

        l_change = group_loop_selection_test(
            self, in_range, loop_tri_cos, shift, ctrl)
        if l_change:
            change = l_change

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

    if self._container.sel_status.any():
        avg_loc = np.mean(
            self._container.loop_coords[self._container.sel_status], axis=0)
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
