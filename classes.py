import bpy
import bgl
import gpu
import numpy as np
from gpu_extras.batch import batch_for_shader
from .functions_general import *


class ABNContainer:
    def __init__(self, mat, mac_shader=False):
        self.mac_shader = mac_shader

        if mac_shader:
            self.create_mac_shader()
        else:
            self.create_shader()
            self.create_point_shader()

        self.matrix = np.array(mat)

        self.loop_scale = 1.0
        self.normal_scale = 1.0
        self.brightness = 1.0
        self.size = 1.0

        self.draw_tris = False
        self.draw_only_selected = False
        self.draw_weights = True
        self.scale_selection = True

        # NP ARRAYS
        self.og_sharp = None
        self.og_seam = None

        self.po_coords = None
        self.loop_coords = None
        self.loop_tangents = None
        self.loop_tri_coords = None
        self.face_normals = None

        self.og_norms = None
        self.new_norms = None
        self.cache_norms = None

        self.hide_status = None
        self.sel_status = None
        self.act_status = None
        self.filter_weights = None
        self.filter_mask = None

        self.vert_link_vs = None
        self.vert_link_ls = None
        self.face_link_vs = None
        self.face_link_ls = None
        self.face_link_eds = None
        self.edge_link_vs = None
        self.edge_link_fs = None
        self.loop_faces = None
        self.loop_verts = None
        self.loop_edges = None

        self.color_tri = (0.16, 0.55, 0.7, 0.2)
        self.color_tri_sel = (0.16, 0.7, 0.9, 0.5)
        self.color_tri_act = (0.0, 0.0, 1.0, 0.75)

        self.color_po = (0.1, 0.4, 0.1, 1.0)
        self.color_po_sel = (0.1, 0.7, 0.9, 1.0)
        self.color_po_act = (0.0, 0.0, 1.0, 1.0)

        self.color_po_zero_weight = (0.66, 1.0, 1.0, 1.0)
        self.color_po_full_weight = (0.0, 1.0, 1.0, 1.0)

        self.color_normal = (0.83, 0.3, 0.4, 1.0)
        self.color_normal_sel = (0.83, 0.7, 0.9, 1.0)
        self.color_normal_act = (0.0, 0.0, 0.9, 1.0)

        self.update_color_render()
        return

    def create_mac_shader(self):
        self.shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
        return

    def create_shader(self):
        vertex_shader = '''
            uniform mat4 viewProjectionMatrix;

            in vec3 pos;
            in vec4 color;
            out vec4 rgba;

            void main()
            {
                rgba = color;
                gl_Position = viewProjectionMatrix * vec4(pos, 1.0f);
            }
        '''

        fragment_shader = '''
            uniform float brightness;

            in vec4 rgba;
            layout(location = 0) out vec4 diffuseColor;

            void main()
            {
                diffuseColor  = vec4(rgba.xyz * brightness, rgba.a);
            }
        '''

        self.shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        return

    def create_point_shader(self):
        vertex_shader = '''
            uniform mat4 viewProjectionMatrix;

            in float size;
            in vec3 pos;
            in vec4 color;
            out vec4 rgba;

            void main()
            {
                rgba = color;
                gl_PointSize = size;
                gl_Position = viewProjectionMatrix * vec4(pos, 1.0f);
            }
        '''

        fragment_shader = '''
            uniform float brightness;

            in vec4 rgba;
            layout(location = 0) out vec4 diffuseColor;

            void main()
            {
                diffuseColor  = vec4(rgba.xyz * brightness, rgba.a);
            }
        '''

        self.point_shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        return

    def clear_batches(self):
        if self.mac_shader:
            self.batch_po = batch_for_shader(
                self.shader, 'POINTS', {"pos": [], "color": []})
            self.batch_po_sel = batch_for_shader(
                self.shader, 'POINTS', {"pos": [], "color": []})
            self.batch_po_act = batch_for_shader(
                self.shader, 'POINTS', {"pos": [], "color": []})
        else:
            self.batch_po = batch_for_shader(
                self.point_shader, 'POINTS', {"pos": [], "size": [], "color": []})

        self.batch_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": [], "color": []})
        self.batch_tri = batch_for_shader(
            self.shader, 'TRIS', {"pos": [], "color": []})
        self.batch_active_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": [], "color": []})

        return

    def clear_active_batches(self):
        self.batch_active_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": [], "color": []})
        return

    def update_active(self):
        po_cos = self.loop_coords[self.sel_status]
        po_norms = self.new_norms[self.sel_status]
        act_status = self.act_status[self.sel_status]
        filt_mask = self.filter_mask[self.sel_status]
        weight_mask = self.filter_weights[self.sel_status][filt_mask]

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
        norm_lines.shape = [po_cos.shape[0] * 2, 3]

        #

        cols = np.array([self.rcol_normal_sel] * po_cos.shape[0])
        cols.shape = [po_cos.shape[0], 4]
        cols[act_status] = self.rcol_normal_act

        # Draw filter weights on norms
        if self.draw_weights:
            w_cols = np.zeros(filt_mask.nonzero()[0].size * 4,
                              dtype=np.float32).reshape(-1, 4)
            f_cols = w_cols.copy()

            w_cols[:] = self.color_po_zero_weight
            f_cols[:] = self.color_po_full_weight

            w_cols = w_cols * (1.0 - weight_mask.reshape(-1, 1)) + \
                f_cols * weight_mask.reshape(-1, 1)

            w_cols = hsv_to_rgb_array(w_cols)

            cols[filt_mask] = w_cols

        norm_colors = np.array(list(zip(cols, cols)))
        norm_colors.shape = [po_cos.shape[0] * 2, 4]

        if self.mac_shader:
            norm_colors[:, [0, 1, 2]] *= self.brightness

        #

        self.batch_active_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": list(norm_lines), "color": list(norm_colors)})

        return

    def update_static(self, exclude_active=False):
        # POINTS
        # all points are static
        sel_mask = self.sel_status[~self.hide_status]
        act_mask = self.act_status[~self.hide_status]
        filt_mask = self.filter_mask[~self.hide_status]
        weight_mask = self.filter_weights[~self.hide_status][filt_mask]

        points = self.loop_coords[~self.hide_status]

        sizes = np.array([5*self.size]*points.shape[0])
        sizes[sel_mask] = 8*self.size
        sizes[act_mask] = 11*self.size

        po_colors = np.array([self.rcol_po]*points.shape[0])
        po_colors.shape = [points.shape[0], 4]
        po_colors[sel_mask] = self.rcol_po_sel
        po_colors[act_mask] = self.rcol_po_act

        # Draw filter weights on points
        if self.draw_weights:
            w_cols = np.zeros(filt_mask.nonzero()[0].size * 4,
                              dtype=np.float32).reshape(-1, 4)
            f_cols = w_cols.copy()

            w_cols[:] = self.color_po_zero_weight
            f_cols[:] = self.color_po_full_weight

            w_cols = w_cols * (1.0 - weight_mask.reshape(-1, 1)) + \
                f_cols * weight_mask.reshape(-1, 1)

            w_cols = hsv_to_rgb_array(w_cols)

            po_colors[filt_mask] = w_cols

        if self.mac_shader:
            po_colors[:, [0, 1, 2]] *= self.brightness

            self.batch_po = batch_for_shader(
                self.shader, 'POINTS', {"pos": list(points[~sel_mask]), "color": list(po_colors[~sel_mask])})
            self.batch_po_sel = batch_for_shader(
                self.shader, 'POINTS', {"pos": list(points[sel_mask]), "color": list(po_colors[sel_mask])})
            self.batch_po_act = batch_for_shader(
                self.shader, 'POINTS', {"pos": list(points[act_mask]), "color": list(po_colors[act_mask])})
        else:
            self.batch_po = batch_for_shader(
                self.point_shader, 'POINTS', {"pos": list(points), "size": list(sizes), "color": list(po_colors)})

        #
        #
        #

        # LOOP TRIS
        # all loop tris are static if used
        tris = []
        tri_colors = []
        if self.draw_tris:
            tris = self.loop_tri_coords[~self.hide_status]
            tris[:, 1] = (tris[:, 1]-tris[:, 0]) * self.loop_scale + tris[:, 0]
            tris[:, 2] = (tris[:, 2]-tris[:, 0]) * self.loop_scale + tris[:, 0]

            t_colors = np.array([self.rcol_tri]*tris.shape[0])
            t_colors.shape = [tris.shape[0], 4]
            t_colors[sel_mask] = self.rcol_tri_sel
            t_colors[act_mask] = self.rcol_tri_act

            # Draw filter weights on loop tris
            if self.draw_weights:
                t_colors[filt_mask] = w_cols

            tri_colors = np.array(list(zip(t_colors, t_colors, t_colors)))
            tri_colors.shape = [tris.shape[0]*3, 4]

            tris.shape = [tris.shape[0]*3, 3]

            if self.mac_shader:
                tri_colors[:, [0, 1, 2]] *= self.brightness

        self.batch_tri = batch_for_shader(
            self.shader, 'TRIS', {"pos": list(tris), "color": list(tri_colors)})

        #
        #
        #

        # NORMALS
        # only non selected loop normals are static if exclude_active is true otherwise all loop normals are static
        if exclude_active:
            non_sel_status = np.ones(self.loop_coords.shape[0], dtype=bool)
            non_sel_status[self.sel_status] = False
            non_sel_status = non_sel_status[~self.hide_status]

            w_cols = w_cols[non_sel_status[filt_mask]]
            filt_mask = filt_mask[non_sel_status]

            po_cos = self.loop_coords[~self.hide_status][non_sel_status]
            po_norms = self.new_norms[~self.hide_status][non_sel_status]
            sel_mask = []
            act_mask = []
        else:
            po_cos = self.loop_coords[~self.hide_status]
            po_norms = self.new_norms[~self.hide_status]

        #

        if self.scale_selection:
            world_norms = po_cos + \
                (po_norms * 0.333 * self.normal_scale) @ self.matrix[:3, :3].T

            if exclude_active == False:
                world_norms[sel_mask] = po_cos[sel_mask] + \
                    (po_norms[sel_mask] * 0.666 *
                        self.normal_scale) @ self.matrix[:3, :3].T
                world_norms[act_mask] = po_cos[act_mask] + \
                    (po_norms[act_mask] *
                        self.normal_scale) @ self.matrix[:3, :3].T
        else:
            world_norms = po_cos + \
                (po_norms * self.normal_scale) @ self.matrix[:3, :3].T

        n_colors = np.array([self.rcol_normal]*po_cos.shape[0])
        n_colors.shape = [po_cos.shape[0], 4]
        n_colors[sel_mask] = self.rcol_normal_sel
        n_colors[act_mask] = self.rcol_normal_act

        # Draw filter weights on normals
        if self.draw_weights:
            n_colors[filt_mask] = w_cols

        if self.draw_only_selected:
            po_cos = po_cos[sel_mask]
            world_norms = world_norms[sel_mask]
            n_colors = n_colors[sel_mask]

        norms = np.array(list(zip(po_cos, world_norms)))
        norms.shape = [po_cos.shape[0] * 2, 3]

        norm_colors = np.array(list(zip(n_colors, n_colors)))
        norm_colors.shape = [n_colors.shape[0] * 2, 4]

        if self.mac_shader:
            norm_colors[:, [0, 1, 2]] *= self.brightness

        self.batch_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": list(norms), "color": list(norm_colors)})

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

        if self.mac_shader:
            if self.draw_tris:
                # Static Tris
                self.shader.bind()
                self.batch_tri.draw(self.shader)

            bgl.glPointSize(5*self.size)
            # Static Non Sel Points
            self.shader.bind()
            self.batch_po.draw(self.shader)

            # Static Sel Points
            bgl.glPointSize(8*self.size)
            self.shader.bind()
            self.batch_po_sel.draw(self.shader)

            # Static Act Points
            bgl.glPointSize(11*self.size)
            self.shader.bind()
            self.batch_po_act.draw(self.shader)

            # Static Normals
            self.shader.bind()
            self.batch_normal.draw(self.shader)

            # Active Normals
            self.shader.bind()
            self.batch_active_normal.draw(self.shader)

        else:
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

    def set_draw_weights(self, status):
        self.draw_weights = status
        return

    def set_draw_tris(self, status):
        self.draw_tris = status
        return

    #
    #

    def __str__(self):
        return 'Object Vertex Points'
