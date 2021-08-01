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

        self.matrix = np.array(mat)

        self.loop_scale = 1.0
        self.normal_scale = 1.0
        self.brightness = 1.0
        self.size = 1.0

        self.draw_tris = False
        self.draw_only_selected = False
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

        self.vert_link_vs = None
        self.vert_link_ls = None
        self.face_link_vs = None
        self.face_link_ls = None
        self.face_link_eds = None
        self.edge_link_vs = None
        self.loop_faces = None
        self.loop_verts = None

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
            out vec4 fragColor;

            void main()
            {
                fragColor  = vec4(rgba.xyz * brightness, rgba.a);
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
            out vec4 fragColor;

            void main()
            {
                fragColor  = vec4(rgba.xyz * brightness, rgba.a);
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
        norm_lines.shape = [po_cos.shape[0] * 2, 3]

        #

        cols = np.array([self.rcol_normal_sel] * po_cos.shape[0])
        cols.shape = [po_cos.shape[0], 4]
        cols[act_status] = self.rcol_normal_act

        norm_colors = np.array(list(zip(cols, cols)))
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

        if self.draw_only_selected:
            po_cos = po_cos[sel_mask]
            world_norms = world_norms[sel_mask]
            n_colors = n_colors[sel_mask]

        norms = np.array(list(zip(po_cos, world_norms)))
        norms.shape = [po_cos.shape[0] * 2, 3]

        norm_colors = np.array(list(zip(n_colors, n_colors)))
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

    #
    #

    def __str__(self):
        return 'Object Vertex Points'
