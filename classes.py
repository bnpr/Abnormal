import bpy
import bgl
import gpu
import numpy as np
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from .functions_general import *


class ABNContainer:
    def __init__(self, mat):
        self.create_shader()
        self.create_point_shader()

        self.points = []
        self.matrix = np.array(mat)

        self.loop_scale = 1.0
        self.normal_scale = 1.0
        self.brightness = 1.0
        self.size = 1.0

        self.og_sharp = None
        self.og_seam = None

        self.po_coords = None
        self.loop_coords = None
        self.loop_tri_coords = None

        self.og_norms = None
        self.new_norms = None
        self.cache_norms = None

        self.hide_status = None
        self.sel_status = None
        self.act_status = None
        self.filter_weights = None

        self.active_inds = []
        self.static_inds = []

        self.vert_link_vs = None
        self.vert_link_ls = None
        self.face_link_vs = None
        self.face_link_ls = None

        self.draw_tris = False
        self.draw_only_selected = False
        self.scale_selection = True

        self.color_tri = (0.16, 0.55, 0.7, 0.2)
        self.color_tri_sel = (0.16, 0.7, 0.9, 0.5)
        self.color_tri_act = (0.0, 0.0, 1.0, 0.75)

        self.color_po = (0.1, 0.4, 0.1, 1.0)
        self.color_po_sel = (0.1, 0.7, 0.9, 1.0)
        self.color_po_act = (0.0, 0.0, 1.0, 1.0)

        self.color_normal = (0.83, 0.3, 0.4, 1.0)
        self.color_normal_sel = (0.83, 0.7, 0.9, 1.0)
        self.color_normal_act = (0.0, 0.0, 0.9, 1.0)

        self.update_color_render()
        return

    def create_shader(self):
        vertex_shader = '''
            uniform mat4 viewProjectionMatrix;

            in vec3 pos;
            in vec4 colors;
            out vec4 rgba;

            void main()
            {
                rgba = colors;
                gl_Position = viewProjectionMatrix * vec4(pos, 1.0f);
            }
        '''

        fragment_shader = '''
            uniform float brightness;

            in vec4 rgba;

            void main()
            {
                gl_FragColor = vec4(rgba.xyz * brightness, rgba.a);
            }
        '''

        self.shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        return

    def create_point_shader(self):
        vertex_shader = '''
            uniform mat4 viewProjectionMatrix;

            in float size;
            in vec3 pos;
            in vec4 colors;
            out vec4 rgba;

            void main()
            {
                rgba = colors;
                gl_PointSize = size;
                gl_Position = viewProjectionMatrix * vec4(pos, 1.0f);
            }
        '''

        fragment_shader = '''
            uniform float brightness;

            in vec4 rgba;

            void main()
            {
                gl_FragColor = vec4(rgba.xyz * brightness, rgba.a);
            }
        '''

        self.point_shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        return

    def clear_batches(self):
        self.batch_po = batch_for_shader(
            self.point_shader, 'POINTS', {"pos": [], "size": [], "colors": []})
        self.batch_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": [], "colors": []})
        self.batch_tri = batch_for_shader(
            self.shader, 'TRIS', {"pos": [], "colors": []})
        self.batch_active_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": [], "colors": []})
        return

    def clear_active_batches(self):
        self.batch_active_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": [], "colors": []})
        return

    def update_active(self):
        po_cos = self.loop_coords[self.sel_status]
        po_norms = self.new_norms[self.sel_status]
        act_status = self.act_status[self.sel_status]

        if self.scale_selection:
            world_norms = po_cos + \
                (po_norms * 0.666 * self.normal_scale) @ self.matrix[:3, :3].T
            world_norms[act_status] = po_cos[act_status] + \
                (po_norms[act_status] *
                 self.normal_scale) @ self.matrix[:3, :3].T
        else:
            world_norms = po_cos + \
                (po_norms * self.normal_scale) @ self.matrix[:3, :3].T

        norm_lines = np.array(list(zip(po_cos, world_norms)))
        norm_lines.ravel()
        norm_lines.shape = [po_cos.shape[0] * 2, 3]

        #

        cols = np.array([self.rcol_normal_sel] * po_cos.shape[0])
        cols.shape = [po_cos.shape[0], 4]
        cols[act_status] = self.rcol_normal_act

        norm_colors = np.array(list(zip(cols, cols)))
        norm_colors.ravel()
        norm_colors.shape = [po_cos.shape[0] * 2, 4]

        #

        self.batch_active_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": list(norm_lines), "colors": list(norm_colors)})
        return

    def update_static(self, exclude_active=False):
        # POINTS
        # all points are static
        sel_mask = self.sel_status[~self.hide_status]
        act_mask = self.act_status[~self.hide_status]

        points = self.loop_coords[~self.hide_status]

        sizes = np.array([5*self.size]*points.shape[0])
        sizes[sel_mask] = 8*self.size
        sizes[act_mask] = 11*self.size

        po_colors = np.array([self.rcol_po]*points.shape[0])
        po_colors.shape = [points.shape[0], 4]
        po_colors[sel_mask] = self.rcol_po_sel
        po_colors[act_mask] = self.rcol_po_act

        #

        tris = []
        tri_colors = []
        # LOOP TRIS
        # all loop tris are static if used
        if self.draw_tris:
            tris = self.loop_tri_coords[~self.hide_status]
            tris[:, 1] = (tris[:, 1]-tris[:, 0]) * self.loop_scale + tris[:, 0]
            tris[:, 2] = (tris[:, 2]-tris[:, 0]) * self.loop_scale + tris[:, 0]

            t_colors = np.array([self.rcol_tri]*tris.shape[0])
            t_colors.shape = [tris.shape[0], 4]
            t_colors[sel_mask] = self.rcol_tri_sel
            t_colors[act_mask] = self.rcol_tri_act

            tri_colors = np.array(list(zip(t_colors, t_colors, t_colors)))
            tri_colors.ravel()
            tri_colors.shape = [tris.shape[0]*3, 4]

            tris.shape = [tris.shape[0]*3, 3]

        #

        # NORMALS
        # only non selected loop normals are static if exclude_active is true otherwise all loop normals are static
        if exclude_active:
            non_sel_status = np.ones(self.loop_coords.shape[0], dtype=bool)
            non_sel_status[self.sel_status] = False
            non_sel_status = non_sel_status[~self.hide_status]

            po_cos = self.loop_coords[~self.hide_status][non_sel_status]
            po_norms = self.new_norms[~self.hide_status][non_sel_status]
            sel_mask = []
            act_mask = []

        else:
            po_cos = self.loop_coords[~self.hide_status]
            po_norms = self.new_norms[~self.hide_status]

        if self.scale_selection:
            world_norms = po_cos + \
                (po_norms * 0.333 * self.normal_scale) @ self.matrix[:3, :3].T
            world_norms[sel_mask] = po_cos[sel_mask] + \
                (po_norms[sel_mask] * 0.666 *
                 self.normal_scale) @ self.matrix[:3, :3].T
            world_norms[act_mask] = po_cos[act_mask] + \
                (po_norms[act_mask] *
                 self.normal_scale) @ self.matrix[:3, :3].T
        else:
            world_norms = po_cos + \
                (po_norms * self.normal_scale) @ self.matrix[:3, :3].T

        norms = np.array(list(zip(po_cos, world_norms)))
        norms.ravel()
        norms.shape = [po_cos.shape[0] * 2, 3]

        n_colors = np.array([self.rcol_normal]*po_cos.shape[0])
        n_colors.shape = [po_cos.shape[0], 4]
        n_colors[sel_mask] = self.rcol_normal_sel
        n_colors[act_mask] = self.rcol_normal_act

        norm_colors = np.array(list(zip(n_colors, n_colors)))
        norm_colors.ravel()
        norm_colors.shape = [n_colors.shape[0] * 2, 4]

        #

        self.batch_po = batch_for_shader(
            self.point_shader, 'POINTS', {"pos": list(points), "size": list(sizes), "colors": list(po_colors)})
        self.batch_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": list(norms), "colors": list(norm_colors)})
        self.batch_tri = batch_for_shader(
            self.shader, 'TRIS', {"pos": list(tris), "colors": list(tri_colors)})
        return

    def update_color_render(self):
        self.rcol_tri = hsv_to_rgb_list(self.color_tri)
        self.rcol_tri_sel = hsv_to_rgb_list(self.color_tri_sel)
        self.rcol_tri_act = hsv_to_rgb_list(self.color_tri_act)

        self.rcol_po = hsv_to_rgb_list(self.color_po)
        self.rcol_po_sel = hsv_to_rgb_list(self.color_po_sel)
        self.rcol_po_act = hsv_to_rgb_list(self.color_po_act)

        self.rcol_normal = hsv_to_rgb_list(self.color_normal)
        self.rcol_normal_sel = hsv_to_rgb_list(self.color_normal_sel)
        self.rcol_normal_act = hsv_to_rgb_list(self.color_normal_act)
        return

    def draw(self):
        matrix = bpy.context.region_data.perspective_matrix

        if self.draw_tris:
            # Static Tris
            self.shader.bind()
            self.shader.uniform_float("viewProjectionMatrix", matrix)
            self.shader.uniform_float("brightness", self.brightness)
            # self.shader.uniform_float("opacity", self.opacity)
            # self.shader.uniform_float("color", tri_color)
            self.batch_tri.draw(self.shader)

        # Static Points
        self.point_shader.bind()
        self.point_shader.uniform_float("viewProjectionMatrix", matrix)
        self.point_shader.uniform_float("brightness", self.brightness)
        # self.point_shader.uniform_float("opacity", self.opacity)
        # self.point_shader.uniform_float("color", po_color)
        self.batch_po.draw(self.point_shader)

        # Static Normals
        self.shader.bind()
        self.shader.uniform_float("viewProjectionMatrix", matrix)
        self.shader.uniform_float("brightness", self.brightness)
        # self.shader.uniform_float("opacity", self.opacity)
        # self.shader.uniform_float("color", line_color)
        self.batch_normal.draw(self.shader)

        # Active Normals
        self.shader.bind()
        self.shader.uniform_float("viewProjectionMatrix", matrix)
        self.shader.uniform_float("brightness", self.brightness)
        # self.shader.uniform_float("opacity", self.opacity)
        # self.shader.uniform_float("color", line_color)
        self.batch_active_normal.draw(self.shader)

        return

    def cache_current_normals(self):
        self.cache_norms = self.new_norms.copy()
        return

    #
    #

    def add_point(self, co, norm, loop_norms, loop_inds, loop_f_inds, loop_tri_cos):
        po = ABNPoint(len(self.points), co, norm, loop_norms,
                      loop_inds, loop_f_inds, loop_tri_cos, True)

        self.points.append(po)
        return po

    def add_empty_point(self, co, norm):
        po = ABNPoint(len(self.points), co, norm, [], [], [], [], False)

        self.points.append(po)
        return po

    def cache_current_normals(self):
        for po in self.points:
            for loop in po.loops:
                loop.cache_normal()
        return

    def restore_cached_normals(self):
        for po in self.points:
            for loop in po.loops:
                loop.restore_cached()
        return

    def clear_cached_normals(self):
        for po in self.points:
            for loop in po.loops:
                loop.clear_cached()
        return

    #
    #

    def get_visible(self):
        vis_pos = [
            po.index for po in self.points if po.valid and po.hide == False]
        return vis_pos

    def get_selected(self):
        sel_pos = [
            po.index for po in self.points if po.select and po.valid and po.hide == False]
        return sel_pos

    def get_selected_cos(self):
        sel_pos = [
            po.index for po in self.points if po.select and po.valid and po.hide == False]
        sel_cos = [po.co for po in self.points if po.index in sel_pos]

        return sel_cos

    def get_unselected(self):
        sel_pos = [po.index for po in self.points if po.select ==
                   False and po.valid and po.hide == False]
        return sel_pos

    def get_current_normals(self, selection=None):
        cache_norms = []
        if selection == None:
            selection = [i for i in range(len(self.points))]

        for ind in selection:
            po = self.points[ind]

            norms = []
            for loop in po.loops:
                norms.append(loop.normal)
            cache_norms.append(norms)

        return cache_norms

    def get_visible_loops(self):
        vis_loops = []
        for po in self.points:
            if po.valid and po.hide == False:
                if po.valid and po.hide == False:
                    for loop in po.loops:
                        if loop.hide == False:
                            vis_loops.append([po.index, loop.index])
        return vis_loops

    def get_selected_loops(self):
        sel_loops = []
        for po in self.points:
            if po.valid and po.hide == False:
                if po.valid and po.hide == False:
                    for loop in po.loops:
                        if loop.hide == False and loop.select:
                            sel_loops.append([po.index, loop.index])
        return sel_loops

    def get_selected_loop_cos(self):
        sel_loops = []
        for po in self.points:
            if po.valid and po.hide == False:
                if po.valid and po.hide == False:
                    for loop in po.loops:
                        if loop.hide == False and loop.select:
                            sel_loops.append(po.co)
        return sel_loops

    def get_unselected_loops(self):
        sel_loops = []
        for po in self.points:
            if po.valid and po.hide == False:
                if po.valid and po.hide == False:
                    for loop in po.loops:
                        if loop.hide == False and loop.select == False:
                            sel_loops.append([po.index, loop.index])
        return sel_loops

    def get_current_loop_normals(self, selection=None):
        cache_norms = []
        if selection == None:
            selection = []
            for po in self.points:
                for loop in po.loops:
                    selection.append([po.index, loop.index])

        for ind in selection:
            loop = self.points[ind[0]].loops[ind[1]]

            cache_norms.append(loop.normal)

        return cache_norms

    def get_selection_available(self, add_rem_status):
        avail_cos = []
        avail_sel_status = []
        avail_inds = []
        for po in self.points:
            if po.hide == False and po.valid:
                add = False
                if add_rem_status == 2 and po.select:
                    add = True
                if add_rem_status == 1 and po.select == False:
                    add = True
                if add_rem_status == 0:
                    add = True

                if add:
                    avail_cos.append(po.co)
                    avail_inds.append(po.index)
                    avail_sel_status.append(po.select)

        return avail_cos, avail_sel_status, avail_inds

    def get_loop_selection_available(self, add_rem_status):
        avail_cos = []
        avail_sel_status = []
        avail_inds = []
        for po in self.points:
            if po.hide == False and po.valid:
                for loop in po.loops:
                    if loop.hide == False:
                        add = False
                        if add_rem_status == 2 and loop.select:
                            add = True
                        if add_rem_status == 1 and loop.select == False:
                            add = True
                        if add_rem_status == 0:
                            add = True

                        if add:
                            avail_cos.append(loop.tri_center)
                            avail_inds.append([po.index, loop.index])
                            avail_sel_status.append(loop.select)

        return avail_cos, avail_sel_status, avail_inds

    def get_loop_tri_selection_available(self, add_rem_status):
        avail_cos = []
        avail_sel_status = []
        avail_inds = []
        for po in self.points:
            if po.hide == False and po.valid:
                for loop in po.loops:
                    if loop.hide == False:
                        add = False
                        if add_rem_status == 2 and loop.select:
                            add = True
                        if add_rem_status == 1 and loop.select == False:
                            add = True
                        if add_rem_status == 0:
                            add = True

                        if add:
                            avail_cos.append(loop.tri_verts)
                            avail_inds.append([po.index, loop.index])
                            avail_sel_status.append(loop.select)

        return avail_cos, avail_sel_status, avail_inds

    #
    #

    def set_scale_selection(self, status):
        self.scale_selection = status
        return

    def set_brightess(self, value):
        self.brightness = value
        return

    def set_normal_scale(self, scale):
        self.normal_scale = scale
        return

    def set_loop_scale(self, scale):
        self.loop_scale = scale
        return

    def set_point_size(self, size):
        self.size = size
        return

    def set_draw_only_selected(self, status):
        self.draw_only_selected = status
        return

    def set_draw_tris(self, status):
        self.draw_tris = status
        return

    def select_face_loops(self, face_ind, set_active=False):
        cur_sel = []
        loops = []
        for po in self.points:
            for loop in po.loops:
                if loop.face_index == face_ind:
                    cur_sel.append(loop.select)
                    loops.append([po.index, loop.index])

        if False in cur_sel:
            for inds in loops:
                self.points[inds[0]].loops[inds[1]].set_select(True)
                if set_active:
                    self.points[inds[0]].loops[inds[1]].set_active(True)
        else:
            for inds in loops:
                self.points[inds[0]].loops[inds[1]].set_select(False)
                self.points[inds[0]].loops[inds[1]].set_active(False)
        return

    def select_face_verts(self, face_ind, set_active=False):
        cur_sel = []
        pos = []
        for po in self.points:
            for loop in po.loops:
                if loop.face_index == face_ind:
                    cur_sel.append(po.select)
                    pos.append(po.index)
                    break

        if False in cur_sel:
            for ind in pos:
                self.points[ind].set_select(True)
                if set_active:
                    self.points[ind].set_active(True)
        else:
            for ind in pos:
                self.points[ind].set_select(False)
                self.points[ind].set_active(False)
        return

    def set_face_loops_select(self, face_ind, status, set_active=False):
        loops = []
        for po in self.points:
            for loop in po.loops:
                if loop.face_index == face_ind:
                    loops.append([po.index, loop.index])

        for inds in loops:
            self.points[inds[0]].loops[inds[1]].set_select(status)
            if set_active or status == False:
                self.points[inds[0]].loops[inds[1]].set_active(status)
            self.points[inds[0]].set_selection_from_loops()
        return

    def set_face_verts_select(self, face_ind, status, set_active=False):
        pos = []
        for po in self.points:
            for loop in po.loops:
                if loop.face_index == face_ind:
                    pos.append(po.index)
                    break

        for ind in pos:
            self.points[ind].set_select(status)
            if set_active or status == False:
                self.points[ind].set_active(status)
        return

    def clear_active(self):
        for po in self.points:
            po.set_active(False)
            for loop in po.loops:
                loop.set_active(False)
        return

    def set_active_point(self, po_index):
        self.clear_active()
        self.points[po_index].set_active(True)
        return

    def set_active_loop(self, po_index, loop_index):
        self.clear_active()
        self.points[po_index].loops[loop_index].set_active(True)
        return

    #
    #

    def __str__(self):
        return 'Object Vertex Points'


class ABNPoint:
    def __init__(self, index, position, norm, loop_norms, loop_inds, loop_f_inds, loop_tri_cos, validity):
        self.index = index

        self.type = 'POINT'

        self.loops = []

        self.co = position
        self.normal = norm

        for i, ind in enumerate(loop_inds):
            self.add_loop(loop_norms[i], ind, loop_f_inds[i], loop_tri_cos[i])

        self.select = False
        self.hide = False
        self.active = False
        self.valid = validity
        return

    #
    #

    def add_loop(self, loop_norm, loop_ind, face_ind, vert_cos):
        loop = ABNLoop(len(self.loops), self, loop_norm,
                       loop_ind, face_ind, vert_cos)

        self.loops.append(loop)
        return loop

    def reset_loops(self):
        for loop in self.loops:
            loop.reset_normal()
        return

    #
    #

    def set_hide(self, status, include_loops=True):
        if self.valid:
            self.hide = status
            if include_loops:
                for loop in self.loops:
                    loop.set_hide(status)
        return

    def set_select(self, status, include_loops=True):
        if self.valid and self.hide == False:
            self.select = status
            if include_loops:
                for loop in self.loops:
                    loop.set_select(status)
        return

    def set_loop_select(self, loop_ind, status):
        if self.valid:
            self.loops[loop_ind].set_select(status)
            self.set_selection_from_loops()
        return

    def set_active(self, status):
        if self.valid:
            self.active = status
        return

    def set_selection_from_loops(self):
        if self.valid and self.hide == False:
            loop_sel = [loop.select for loop in self.loops]
            if False in loop_sel:
                self.set_select(False, include_loops=False)
            else:
                self.set_select(True, include_loops=False)

        return

    def set_hidden_from_loops(self):
        if self.valid:
            loop_hide = [loop.hide for loop in self.loops]
            if False in loop_hide:
                self.set_hide(False, include_loops=False)
            else:
                self.set_hide(True, include_loops=False)

        return

    #
    #

    def __str__(self):
        return 'Object Vertex Point'


class ABNLoop:
    def __init__(self, index, point, norm, loop_ind, face_ind, vert_cos):
        self.index = index
        self.point = point

        self.type = 'LOOP'

        self.normal = norm
        self.cached_normal = None
        self.og_normal = norm

        self.tri_verts = vert_cos

        center = Vector((0, 0, 0))
        for co in vert_cos:
            center += co/len(vert_cos)

        self.tri_center = center

        self.loop_index = loop_ind
        self.face_index = face_ind

        self.select = False
        self.active = False
        self.hide = False
        return

    #
    #

    def reset_normal(self):
        self.normal = self.og_normal.copy()
        return

    def cache_normal(self):
        self.cached_normal = self.normal.copy()
        return

    def restore_cached(self):
        if self.cached_normal != None:
            self.normal = self.cached_normal.copy()
            self.cached_normal = None
        return

    def clear_cached(self):
        self.cached_normal = None
        return

    #
    #

    def set_hide(self, status):
        self.hide = status
        return

    def set_select(self, status):
        if self.hide == False:
            self.select = status
        return

    def set_active(self, status):
        self.active = status
        return

    #
    #

    def __str__(self):
        return 'Object Vertex Loop'


class ABNFace:
    def __init__(self, index, point, norm, loop_ind, face_ind, vert_cos):
        self.index = index
        self.points = []
        self.loops = []

        self.type = 'FACE'

        center = Vector((0, 0, 0))
        for co in vert_cos:
            center += co/len(vert_cos)

        self.center = center

        self.select = False
        self.active = False
        self.hide = False
        return

    #
    #

    def set_hide(self, status):
        self.hide = status
        return

    def set_select(self, status):
        if self.hide == False:
            self.select = status
        return

    def set_active(self, status):
        self.active = status
        return

    #
    #

    def __str__(self):
        return 'Object Face'
