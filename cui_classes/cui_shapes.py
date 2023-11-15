import gpu
from gpu_extras.batch import batch_for_shader
from .cui_functions import *


#
#
#


class CUIBaseWidgetData:
    #
    # Creates base data used by all widgets
    #
    def __init__(self):
        if bpy.app.version[0] >= 4:
            shader_2d_str = 'UNIFORM_COLOR'
        else:
            shader_2d_str = '2D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(shader_2d_str)

        self.scale = 1.0

        self.enabled = True
        self.visible = True
        return

    #

    def set_scale(self, scale):
        self.scale = scale
        return

    def set_enabled(self, status):
        self.enabled = status
        self.update_color_render()
        return

    def set_visibility(self, status):
        self.visible = status
        return

    #

    def __str__(self):
        return 'CUI Base Widget Data'


class CUIShapeWidget(CUIBaseWidgetData):
    #
    # Creates an enclosed shape structured like a cyclic line
    # Corners of the edges can be beveled
    # The shapes are not offset based on a position
    #
    def __init__(self):
        super().__init__()

        self.color = (0.0, 0.0, 0.5, 0.75)
        self.color_outline = (0.0, 0.0, 1.0, 1.0)
        self.color_render = None
        self.color_outline_render = None

        self.base_points = np.array([], dtype=np.float32)

        self.bevel_inds = []
        self.bevel_size = 0
        self.bevel_res = 0

        self.face_method = 'TRI_FAN'

        self.use_outline = False
        self.outline_thickness = 1

        self.scale_outline_thickness = 1

        self.init_shape_data()
        self.update_color_render()
        return

    #

    def create_shape_data(self):
        self.init_shape_data()

        # Bevel shapes points and fill shape with triangles
        self.points = bevel_ui(
            self.base_points, self.bevel_inds, 0, self.bevel_size, self.bevel_res)

        self.lines = np.roll(self.points, -1, axis=0) - self.points

        return

    def update_batches(self, position):
        if self.points.size == 0:
            points = []
            lines = []
        else:
            points = self.points.tolist()
            lines = self.lines.tolist()

        self.batch_box = batch_for_shader(
            self.shader, self.face_method, {"pos": points})
        self.batch_box_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        return

    def init_shape_data(self):
        self.points = np.array([], dtype=np.float32)
        self.lines = np.array([], dtype=np.float32)
        return

    #

    def update_color_render(self):
        self.color_render = get_enabled_color(
            self.color, self.enabled)
        self.color_outline_render = get_enabled_color(
            self.color_outline, self.enabled)

        return

    def draw(self):
        if self.visible:
            gpu.state.blend_set('ALPHA')
            self.shader.bind()
            self.shader.uniform_float("color", self.color_render)
            self.batch_box.draw(self.shader)
            gpu.state.blend_set('NONE')

            if self.use_outline:
                gpu.state.blend_set('ALPHA')
                gpu.state.line_width_set(self.scale_outline_thickness)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_outline_render)
                self.batch_box_lines.draw(self.shader)
                gpu.state.blend_set('NONE')
        return

    #

    def set_face_method(self, method):
        self.face_method = method
        return

    def set_scale(self, scale):
        super().set_scale(scale)
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
        if size is not None:
            self.bevel_size = size
        if res is not None:
            self.bevel_res = res
        return

    def set_base_points(self, points):
        self.base_points = np.array(points, dtype=np.float32).reshape(-1, 2)
        return

    #

    def __str__(self):
        return 'CUI Shape Widget'


class CUIRectWidget(CUIBaseWidgetData):
    #
    # Creates a rectangle widget with a width and height
    # Corners can be beveled
    # Shape is offset based on a position from parent container
    #
    def __init__(self):
        super().__init__()

        self.pos_offset = np.array([0.0, 0.0], dtype=np.float32)

        self.final_pos = np.array([0.0, 0.0], dtype=np.float32)

        self.draw_box = True

        self.set_width(0)
        self.set_height(0)
        self.min_width = None
        self.min_height = None
        self.max_width = None
        self.max_height = None

        self.use_outline = False
        self.outline_thickness = 1
        self.outline_scale_in_dist = 0

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

        self.scale_pos_offset = np.array([0.0, 0.0], dtype=np.float32)
        self.scale_outline_thickness = 1
        self.scale_width = 0
        self.scale_height = 0

        self.init_shape_data()
        self.update_color_render()
        return

    #

    def create_shape_data(self):
        self.init_shape_data()

        # Check that width and height are in range of the min/max
        self.check_height_in_range()
        self.check_width_in_range()
        self.points, self.lines = calc_box(
            0, 0, self.width, self.height, self.bevel_inds, self.bevel_size, self.bevel_res)
        return

    def update_batches(self, position):
        if self.points.size == 0:
            points = []
            lines = []
        else:
            pos = self.scale_pos_offset + position

            # Offset draw data based on scale and position of parent containers
            points = (self.points * self.scale + pos).tolist()
            lines = (self.points * self.scale + pos).tolist()

            # if len(points) < 5:
            #     points = []

        self.final_pos[:] = self.scale_pos_offset + position

        self.batch_box = batch_for_shader(
            self.shader, 'TRI_FAN', {"pos": points})
        self.batch_box_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        return

    def init_shape_data(self):
        self.points = np.array([], dtype=np.float32)
        self.lines = np.array([], dtype=np.float32)
        return

    #

    def update_color_render(self):
        self.color_render = get_enabled_color(
            self.color, self.enabled)
        self.color_hover_render = get_enabled_color(
            self.color_hover, self.enabled)
        self.color_outline_render = get_enabled_color(
            self.color_outline, self.enabled)

        return

    def draw(self, color_override=None):
        if self.visible:
            if self.draw_box:
                gpu.state.blend_set('ALPHA')
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
                gpu.state.blend_set('NONE')

            if self.use_outline:
                gpu.state.blend_set('ALPHA')
                gpu.state.line_width_set(self.scale_outline_thickness)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_outline_render)
                self.batch_box_lines.draw(self.shader)
                gpu.state.blend_set('NONE')
        return

    #

    def check_height_in_range(self):
        if self.min_height is not None:
            if self.height < self.min_height:
                self.set_height(self.min_height)
        if self.max_height is not None:
            max_height = self.max_height/self.scale
            if self.height > max_height:
                self.set_height(max_height)
        return

    def check_width_in_range(self):
        if self.min_width is not None:
            if self.width < self.min_width:
                self.set_width(self.min_width)
        if self.max_width is not None:
            if self.width > self.max_width:
                self.set_width(self.max_width)
        return

    def test_hover(self, mouse_co, position):
        if self.visible and self.enabled:
            pos = self.scale_pos_offset + position

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
        self.scale_height = self.scale * height
        return

    def set_width(self, width):
        self.width = width
        self.scale_width = self.scale * width
        return

    def offset_height(self, height):
        self.height += height
        self.scale_height = self.scale * height
        return

    def offset_width(self, width):
        self.width += width
        self.scale_width = self.scale * width
        return

    def set_pos_offset(self, pos_offset):
        self.pos_offset[:] = pos_offset
        self.scale_pos_offset = self.scale * self.pos_offset
        return

    def set_pos_offset_x(self, x_val):
        self.pos_offset[0] = x_val
        self.scale_pos_offset = self.scale * self.pos_offset
        return

    def set_pos_offset_y(self, y_val):
        self.pos_offset[1] = y_val
        self.scale_pos_offset = self.scale * self.pos_offset
        return

    def offset_pos_offset(self, pos_offset):
        self.pos_offset[:] += pos_offset
        self.scale_pos_offset = self.scale * self.pos_offset
        return

    def offset_pos_offset_x(self, x_val):
        self.pos_offset[0] += x_val
        self.scale_pos_offset = self.scale * self.pos_offset
        return

    def offset_pos_offset_y(self, y_val):
        self.pos_offset[1] += y_val
        self.scale_pos_offset = self.scale * self.pos_offset
        return

    def set_bev(self, size, res):
        self.bevel_size = size
        self.bevel_res = res
        return

    def set_scale(self, scale):
        super().set_scale(scale)
        self.scale_pos_offset = self.pos_offset * scale
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


class CUIPolyWidget(CUIBaseWidgetData):
    #
    # Creates a polygon shape filled with triangles
    # Beveling is not used but the function is used to fill with triangles
    # Shapes are offset by a position
    #
    def __init__(self):
        super().__init__()

        self.base_points = np.array([], dtype=np.float32)

        self.color = (0.0, 0.0, 0.75, 0.5)
        self.color_render = None

        self.face_method = 'TRI_FAN'

        self.init_shape_data()
        self.update_color_render()
        return

    #

    def create_shape_data(self):
        self.init_shape_data()

        self.points = self.base_points.copy()
        return

    def update_batches(self, position):
        if self.points.size == 0:
            points = []

        else:
            # Offset shape based on parent container
            pos = np.array(position, dtype=np.float32)
            points = (self.points * self.scale + pos).tolist()

        self.batch = batch_for_shader(
            self.shader, self.face_method, {"pos": points})
        return

    def init_shape_data(self):
        self.points = []
        return

    #

    def update_color_render(self):
        self.color_render = get_enabled_color(
            self.color, self.enabled)
        return

    def draw(self, color_override=None):
        if self.visible:
            gpu.state.blend_set('ALPHA')
            self.shader.bind()

            if color_override:
                self.shader.uniform_float("color", color_override)
            else:
                self.shader.uniform_float("color", self.color_render)

            self.batch.draw(self.shader)
            gpu.state.blend_set('NONE')
        return

    #

    def set_face_method(self, method):
        self.face_method = method
        return

    def set_base_points(self, points):
        self.base_points = np.array(points, dtype=np.float32).reshape(-1, 2)
        return

    def set_color(self, color=None):
        if color:
            self.color = color

        self.update_color_render()
        return

    #

    def __str__(self):
        return 'CUI Poly Widget'
