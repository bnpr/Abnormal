import bpy
import mathutils
import bgl
import gpu
import random
from gpu_extras.batch import batch_for_shader
from .functions_general import *


class ABNPoints:
    def __init__(self, mat):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

        self.points = []
        self.matrix = mat

        self.normal_scale = 1.0
        self.brightness = 1.0
        self.size = 1.0

        self.draw_unselected = False
        self.scale_selection = True

        self.color = (0.16, 0.4, 0.1, 1.0)
        self.color_sel = (0.16, 0.7, 0.9, 1.0)
        self.color_act = (0.0, 0.0, 1.0, 1.0)

        self.color_normal = (0.83, 0.3, 0.4, 1.0)
        self.color_normal_sel = (0.83, 0.7, 0.9, 1.0)
        self.color_normal_act = (0.0, 0.0, 0.9, 1.0)

        self.update_color_render()
        return

    def update(self):
        points = []
        sel_points = []
        act_points = []

        lines = []
        sel_lines = []
        act_lines = []

        po_co = None
        line_co = None
        for po in self.points:
            if po.hide == False and po.valid:
                po_co = po.co

                if po.active:
                    act_points.append(po_co)
                elif po.select:
                    sel_points.append(po_co)
                else:
                    points.append(po_co)

                for loop in po.loops:
                    fac = 1.0
                    if self.scale_selection and po.active == False:
                        fac = 0.666
                        if po.select == False:
                            fac = 0.333

                    world_norm = self.get_world_norm(loop.normal, po_co)

                    line_co = po_co + world_norm * self.normal_scale * fac

                    if po.active:
                        act_lines.append(po_co)
                        act_lines.append(line_co)
                    elif po.select:
                        sel_lines.append(po_co)
                        sel_lines.append(line_co)
                    elif not self.draw_unselected:
                        lines.append(po_co)
                        lines.append(line_co)

        self.batch_po = batch_for_shader(
            self.shader, 'POINTS', {"pos": points})
        self.batch_sel_po = batch_for_shader(
            self.shader, 'POINTS', {"pos": sel_points})
        self.batch_act_po = batch_for_shader(
            self.shader, 'POINTS', {"pos": act_points})
        self.batch_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        self.batch_sel_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": sel_lines})
        self.batch_act_normal = batch_for_shader(
            self.shader, 'LINES', {"pos": act_lines})
        return

    def update_color_render(self):
        self.color_render = hsv_to_rgb_list(self.color)
        self.color_sel_render = hsv_to_rgb_list(self.color_sel)
        self.color_act_render = hsv_to_rgb_list(self.color_act)

        self.color_normal_render = hsv_to_rgb_list(self.color_normal)
        self.color_normal_sel_render = hsv_to_rgb_list(self.color_normal_sel)
        self.color_normal_act_render = hsv_to_rgb_list(self.color_normal_act)
        return

    def draw(self):
        # Unselected points
        po_color = [self.color_render[0]*self.brightness, self.color_render[1] *
                    self.brightness, self.color_render[2]*self.brightness, self.color_render[3]]
        bgl.glPointSize(5*self.size)
        self.shader.bind()
        self.shader.uniform_float("color", po_color)
        self.batch_po.draw(self.shader)

        # Selected points
        sel_po_color = [self.color_sel_render[0]*self.brightness, self.color_sel_render[1] *
                        self.brightness, self.color_sel_render[2]*self.brightness, self.color_sel_render[3]]
        bgl.glPointSize(7*self.size)
        self.shader.bind()
        self.shader.uniform_float("color", sel_po_color)
        self.batch_sel_po.draw(self.shader)

        # Active points
        act_po_color = [self.color_act_render[0]*self.brightness, self.color_act_render[1] *
                        self.brightness, self.color_act_render[2]*self.brightness, self.color_act_render[3]]
        bgl.glPointSize(9*self.size)
        self.shader.bind()
        self.shader.uniform_float("color", act_po_color)
        self.batch_act_po.draw(self.shader)

        # Unselected normals
        line_color = [self.color_normal_render[0]*self.brightness, self.color_normal_render[1] *
                      self.brightness, self.color_normal_render[2]*self.brightness, self.color_normal_render[3]]
        bgl.glLineWidth(1)
        self.shader.bind()
        self.shader.uniform_float("color", line_color)
        self.batch_normal.draw(self.shader)

        # Selected normals
        sel_line_color = [self.color_normal_sel_render[0]*self.brightness, self.color_normal_sel_render[1] *
                          self.brightness, self.color_normal_sel_render[2]*self.brightness, self.color_normal_sel_render[3]]
        bgl.glLineWidth(1)
        self.shader.bind()
        self.shader.uniform_float("color", sel_line_color)
        self.batch_sel_normal.draw(self.shader)

        # Active normals
        act_line_color = [self.color_normal_act_render[0]*self.brightness, self.color_normal_act_render[1] *
                          self.brightness, self.color_normal_act_render[2]*self.brightness, self.color_normal_act_render[3]]
        bgl.glLineWidth(2)
        self.shader.bind()
        self.shader.uniform_float("color", act_line_color)
        self.batch_act_normal.draw(self.shader)

        return

    #
    #

    def add_point(self, co, norm, loop_norms, loop_inds):
        po = ABNPoint(len(self.points), co, norm, loop_norms, loop_inds, True)

        self.points.append(po)
        return po

    def add_empty_point(self, co, norm):
        po = ABNPoint(len(self.points), co, norm, [], [], False)

        self.points.append(po)
        return po

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

    def get_world_norm(self, norm, world_co):
        local_co = self.matrix.inverted() @ world_co

        norm_co = local_co+norm

        world_norm = self.matrix @ norm_co

        new_norm = (world_norm - world_co).normalized()

        return new_norm

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

    def set_point_size(self, size):
        self.size = size
        return

    def set_draw_unselected(self, status):
        self.draw_unselected = status
        return

    def set_active(self, index):
        self.points[index].set_active(True)
        return

    #
    #

    def __str__(self):
        return 'Object Vertex Points'


class ABNPoint:
    def __init__(self, index, position, norm, loop_norms, loop_inds, validity):
        self.index = index

        self.loops = []

        self.co = position
        self.normal = norm

        for i, ind in enumerate(loop_inds):
            self.add_loop(loop_norms[i], ind)

        self.select = False
        self.hide = False
        self.active = False
        self.valid = validity
        return

    #
    #

    def add_loop(self, loop_norm, loop_ind):
        loop = ABNLoop(len(self.loops), loop_norm, loop_ind)

        self.loops.append(loop)
        return loop

    def reset_loops(self):
        for loop in self.loops:
            loop.reset_normal()
        return

    #
    #

    def set_hide(self, status):
        self.hide = status
        return

    def set_select(self, status):
        self.select = status
        return

    def set_active(self, status):
        self.active = status
        return

    #
    #

    def __str__(self):
        return 'Object Vertex Point'


class ABNLoop:
    def __init__(self, index, norm, loop_ind):
        self.index = index

        self.normal = norm
        self.og_normal = norm

        self.loop_index = loop_ind

        self.select = False
        self.active = False
        return

    #
    #

    def reset_normal(self):
        self.normal = self.og_normal.copy()
        return

    #
    #

    def set_select(self, status):
        self.select = status
        return

    def set_active(self, status):
        self.active = status
        return

    #
    #

    def __str__(self):
        return 'Object Vertex Loop'
