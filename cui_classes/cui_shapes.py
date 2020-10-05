import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from .cui_functions import *


#
#
#


class CUIShapeWidget:
    def __init__(self):
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        self.color = (0.0, 0.0, 0.5, 0.75)
        self.color_outline = (0.0, 0.0, 1.0, 1.0)
        self.color_render = None
        self.color_outline_render = None

        self.bevel_inds = []
        self.bevel_size = 0
        self.bevel_res = 0

        self.use_outline = False
        self.outline_thickness = 1

        self.base_points = []

        self.scale = 1.0

        self.scale_outline_thickness = 1

        self.init_shape_data()
        self.update_color_render()
        return

    #

    def update_batches(self, position):
        self.batch_box = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.points}, indices=self.tris)
        self.batch_box_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": self.lines})
        return

    def update_color_render(self):
        self.color_render = hsv_to_rgb_list(self.color)
        self.color_outline_render = hsv_to_rgb_list(self.color_outline)
        return

    def create_shape_data(self):
        self.init_shape_data()

        self.points, self.tris = bevel_ui(
            self.base_points, self.bevel_inds, 0, self.bevel_size, self.bevel_res)

        for p, po in enumerate(self.points):
            self.lines.append(self.points[p])

            if p < len(self.points)-1:
                self.lines.append(self.points[p+1])
            else:
                self.lines.append(self.points[0])

        return

    def init_shape_data(self):
        self.points = []
        self.tris = []
        self.lines = []
        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)
        self.shader.bind()
        self.shader.uniform_float("color", self.color_render)
        self.batch_box.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

        if self.use_outline:
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glLineWidth(self.scale_outline_thickness)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_outline_render)
            self.batch_box_lines.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)
        return

    #

    def set_scale(self, scale):
        self.scale = scale
        self.scale_outline_thickness = self.outline_thickness * scale
        return

    def set_color(self, color=None, color_outline=None):
        if color:
            self.color = color
        if color_outline:
            self.color_outline = color_outline

        self.update_color_render()
        return

    def set_bevel_data(self, inds=None, size=None, res=None):
        if inds:
            self.bevel_inds = inds
        if size != None:
            self.bevel_size = size
        if res != None:
            self.bevel_res = res
        return

    def set_base_points(self, points):
        self.base_points.clear()
        self.base_points = points
        return

    #

    def __str__(self):
        return 'CUI Shape Widget'


class CUIRectWidget:
    def __init__(self):
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        self.pos_offset = [0, 0]

        self.draw_box = True

        self.width = 0
        self.height = 0
        self.min_width = None
        self.min_height = None
        self.max_width = None
        self.max_height = None

        self.use_outline = False
        self.outline_thickness = 1
        self.outline_scale_in_dist = 0

        self.visible = True
        self.hover = False
        self.hover_highlight = False

        self.color = (0.0, 0.0, 0.15, 0.5)
        self.color_hover = (0.0, 0.0, 0.25, 0.5)
        self.color_outline = (0.0, 0.0, 1.0, 0.25)

        self.color_render = None
        self.color_hover_render = None
        self.color_outline_render = None

        self.bevel_inds = []
        self.bevel_size = 0
        self.bevel_res = 0

        self.scale = 1.0
        self.scale_pos_offset = [0, 0]
        self.scale_outline_thickness = 1
        self.scale_width = 0
        self.scale_height = 0

        self.init_shape_data()
        self.update_color_render()
        return

    #

    def update_batches(self, position):
        pos = [position[0]+self.scale_pos_offset[0],
               position[1]+self.scale_pos_offset[1]]
        points = draw_cos_offset(pos, self.scale, self.points)
        lines = draw_cos_offset(pos, self.scale, self.lines)

        self.batch_box = batch_for_shader(
            self.shader, 'TRIS', {"pos": points}, indices=self.tris)
        self.batch_box_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        return

    def update_color_render(self):
        self.color_render = hsv_to_rgb_list(self.color)
        self.color_hover_render = hsv_to_rgb_list(self.color_hover)
        self.color_outline_render = hsv_to_rgb_list(self.color_outline)
        return

    def create_shape_data(self):
        self.init_shape_data()

        self.check_height_in_range()
        self.check_width_in_range()
        self.points, self.tris, self.lines = calc_box(
            0, 0, self.width, self.height, self.bevel_inds, self.bevel_size, self.bevel_res)
        return

    def init_shape_data(self):
        self.points = []
        self.tris = []
        self.lines = []
        return

    def draw(self, color_override=None):
        if self.visible == True:
            if self.draw_box:
                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()

                if color_override:
                    self.shader.uniform_float("color", color_override)
                else:
                    if self.hover and self.hover_highlight:
                        self.shader.uniform_float(
                            "color", self.color_hover_render)
                    else:
                        self.shader.uniform_float("color", self.color_render)

                self.batch_box.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

            if self.use_outline:
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glLineWidth(self.scale_outline_thickness)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_outline_render)
                self.batch_box_lines.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)
        return

    #

    def check_height_in_range(self):
        if self.min_height != None:
            if self.height < self.min_height:
                self.height = self.min_height
        if self.max_height != None:
            max_height = self.max_height/self.scale
            if self.height > max_height:
                self.height = max_height
        return

    def check_width_in_range(self):
        if self.min_width != None:
            if self.width < self.min_width:
                self.width = self.min_width
        if self.max_width != None:
            if self.width > self.max_width:
                self.width = self.max_width
        return

    def test_hover(self, mouse_co, position):
        if self.visible:
            pos = [position[0]+self.scale_pos_offset[0],
                   position[1]+self.scale_pos_offset[1]]

            box_x_min = pos[0]
            box_x_max = pos[0]+self.scale_width

            box_y_min = pos[1]-self.scale_height
            box_y_max = pos[1]
            if box_x_max > mouse_co[0] > box_x_min and box_y_max > mouse_co[1] > box_y_min:
                self.hover = True
            else:
                self.hover = False
        return

    #

    def set_height_min_max(self, min=None, max=None):
        if min:
            self.min_height = min
        if max:
            self.max_height = max
        return

    def set_width_min_max(self, min=None, max=None):
        if min:
            self.min_width = min
        if max:
            self.max_width = max
        return

    def set_height(self, height):
        self.height = height
        self.create_shape_data()
        return

    def set_width(self, width):
        self.width = width
        self.create_shape_data()
        return

    def set_bev(self, size, res):
        self.bevel_size = size
        self.bevel_res = res
        return

    def set_scale(self, scale):
        self.scale = scale
        self.scale_pos_offset = [self.pos_offset[0]
                                 * scale, self.pos_offset[1] * scale]
        self.scale_width = self.width * scale
        self.scale_height = self.height * scale
        return

    def set_color(self, color=None, color_hover=None, color_outline=None):
        if color:
            self.color = color
        if color_hover:
            self.color_hover = color_hover
        if color_outline:
            self.color_outline = color_outline

        self.update_color_render()
        return

    #

    def __str__(self):
        return 'CUI Rect Widget'


class CUIPolyWidget:
    def __init__(self):
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        self.base_points = []
        self.points = []
        self.tris = []

        self.color = (0.0, 0.0, 0.75, 0.5)
        self.color_render = None

        self.scale = 1.0

        self.init_shape_data()
        self.update_color_render()
        return

    #

    def update_batches(self, position):
        points = draw_cos_offset(position, self.scale, self.points)

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": points}, indices=self.tris)
        return

    def update_color_render(self):
        self.color_render = hsv_to_rgb_list(self.color)
        return

    def create_shape_data(self):
        self.init_shape_data()

        self.points, self.tris = bevel_ui(
            self.base_points, [], 0, 0, 0)
        return

    def init_shape_data(self):
        self.points = []
        self.tris = []
        return

    def draw(self, color_override=None):
        bgl.glEnable(bgl.GL_BLEND)
        self.shader.bind()

        if color_override:
            self.shader.uniform_float("color", color_override)
        else:
            self.shader.uniform_float("color", self.color_render)

        self.batch.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        return

    #

    def set_base_points(self, points):
        self.base_points.clear()
        self.base_points = points
        return

    def set_color(self, color=None):
        if color:
            self.color = color

        self.update_color_render()
        return

    def set_scale(self, scale):
        self.scale = scale
        return

    #

    def __str__(self):
        return 'CUI Poly Widget'
