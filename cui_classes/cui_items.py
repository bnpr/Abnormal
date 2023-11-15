import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from .cui_functions import *
from .cui_shapes import *
from bpy_extras import view3d_utils
from mathutils import bvhtree


#
#
#


class CUIItem(CUIRectWidget):
    #
    # Basic item class
    #
    def __init__(self, cont, height):
        self.color = (0.0, 0.0, 0.35, 0.5)
        self.color_hover = (0.0, 0.0, 0.4, 0.75)

        super().__init__()

        self.parts = []
        self.custom_id = None

        self.item_type = ''

        self.parent_container = cont

        self.set_height(height)
        self.hover_highlight = True
        self.click_down = False

        self.click_down_function = None
        self.click_up_function = None

        self.draw_box = False

        self.collapse_width = True

        self.tooltip_lines = []
        return

    #

    def update_batches(self, position):
        # super().update_batches(position)
        pos = self.scale_pos_offset + position

        self.final_pos[:] = pos

        for part in self.parts:
            part.update_batches(pos)
        return

    #

    def draw(self, color_override=None):
        # super().draw(color_override)
        for part in self.parts:
            part.draw(color_override, self.click_down)
        return

    #
    # TEST CLICK FUNCS
    #

    def click_down_func(self, mouse_co, shift, position, arguments=None):
        if self.click_down_function:
            insert_modal(arguments, self.parent_container.modal)
            click_status = self.click_down_function(self, arguments)
            if click_status:
                return [click_status, self.custom_id]
        return [self.item_type, self.custom_id]

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        if self.click_up_function:
            insert_modal(arguments, self.parent_container.modal)
            click_status = self.click_up_function(self, arguments)
            if click_status:
                return [click_status, self.custom_id]
        return [self.item_type, self.custom_id]

    def click_down_move(self, mouse_co, shift, position, arguments=None):
        self.test_hover(mouse_co, position)
        if self.hover == False:
            self.click_down = False
        return

    def test_hover(self, mouse_co, position):
        super().test_hover(mouse_co, position)
        if self.hover:
            pos = self.scale_pos_offset + position
            for part in self.parts:
                part.test_hover(
                    mouse_co, pos)
        return

    def get_tooltip_lines(self):
        return self.tooltip_lines

    #

    def add_tooltip_text_line(self, text_line):
        self.tooltip_lines.append(text_line)
        return

    #

    def reset_item_states(self, clear_hover):
        if clear_hover:
            self.clear_hover()

        self.click_down = False
        self.create_shape_data()
        return

    def clear_hover(self):
        self.hover = False
        for part in self.parts:
            part.hover = False
        return

    #

    def set_collapse_width(self, status):
        self.collapse_width = status
        return

    def set_scale(self, scale):
        super().set_scale(scale)
        for part in self.parts:
            part.set_scale(scale)
        return

    def set_custom_id(self, id):
        self.custom_id = id
        return

    def set_font_size(self, size):
        for part in self.parts:
            part.font_size = size
        return

    def set_color(self, color=None, color_hover=None, color_outline=None, color_click=None, color_font=None):
        super().set_color(
            color=color,
            color_hover=color_hover,
            color_outline=color_outline
        )
        for part in self.parts:
            part.set_color(
                color=color,
                color_hover=color_hover,
                color_outline=color_outline,
                color_click=color_click,
                color_font=color_font
            )

        return

    def set_click_up_func(self, func):
        self.click_up_function = func
        return

    def set_click_down_func(self, func):
        self.click_down_function = func
        return

    def set_enabled(self, status):
        super().set_enabled(status)
        for part in self.parts:
            part.set_enabled(status)

        return

    def set_text_alignment(self, align):
        for part in self.parts:
            part.text_alignment = align
        return

    #

    def __str__(self):
        return 'CUI Item Widget'


class CUIItemWidget(CUIRectWidget):
    #
    # Basic item widget class. Creates the smaller parts of the whole item
    #
    def __init__(self, height, text):
        self.color = (0.0, 0.0, 0.35, 0.5)
        self.color_hover = (0.0, 0.0, 0.4, 0.75)

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.color_font_render = None
        self.color_click_render = None

        super().__init__()

        self.shapes = []

        self.set_height(height)
        self.hover_highlight = True

        self.font_id = 0
        self.font_size = 12
        self.scale_font_size = 12

        self.text = text
        self.text_render = text
        self.text_pos = np.array([0.0, 0.0], dtype=np.float32)
        self.text_pos_offset = np.array([0.0, 0.0], dtype=np.float32)
        # self.text_vert_alignment = 'CENTER'
        # self.text_hor_alignment = 'CENTER'
        self.text_alignment = 'CENTER'
        self.text_auto_y = True
        self.text_margin = 2

        if bpy.app.version[0] >= 4:
            shader_img_str = 'IMAGE'
        else:
            shader_img_str = '2D_IMAGE'
        self.shader_img = gpu.shader.from_builtin(shader_img_str)

        self.icon_pos = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self.icon_pos_offset = np.array([0.0, 0.0], dtype=np.float32)
        self.icon_height = 20
        self.icon_width = 20
        self.icon_text_side = 'RIGHT'
        self.icon_visible = True
        self.icon_img = None
        self.icon_img_name = None
        self.icon_img_path = None
        return

    #

    def create_shape_data(self, value='', text=None):
        super().create_shape_data()

        # Get the width of the icon if there is one
        icon_w = 0
        if self.icon_img:
            icon_w = self.icon_width

        # Get center width and the avalable width after the side text margins are removed
        avail_wid = self.width-self.text_margin*2
        wid_mid = self.width/2

        # Icon is bigger than current width so no text or icon will be drawn
        # It favors the icon over text
        if icon_w > avail_wid:
            self.text_render = ''
            self.icon_visible = False

        # Enough room for the icon so test to find what else can fit
        else:
            self.icon_visible = True

            # Get current full text with value or overwrite if text is given
            self.text_render = self.text
            if value != '':
                self.text_render = self.text + ': ' + str(value)
            if text is not None:
                self.text_render = text

            size_width = 0
            size_height = 0
            cur_size = self.font_size
            # Test how much of the text can fit in the widget based on remaining width and scaleed font
            if self.text_render != '':
                cur_size = scale_font_size(
                    self.text_render, self.font_size, self.font_id, self.scale)
                if bpy.app.version[0] >= 4:
                    blf.size(self.font_id, cur_size)
                else:
                    blf.size(self.font_id, cur_size, 72)
                size_w = blf.dimensions(self.font_id, self.text_render)
                size_h = blf.dimensions(self.font_id, 'T')

                # Test that icon and text will fit in item width if not then clip text
                if size_w[0] + (icon_w)*self.scale > avail_wid*self.scale:

                    # Text needs to be clipped so starting from the first letter going up in size
                    # Test if the text with ellispes will fit and ends once it finds a size that does not fit
                    clip_width = 0
                    cur_pos = -1
                    while clip_width < avail_wid*self.scale:
                        cur_pos += 1
                        size_w = blf.dimensions(
                            self.font_id, self.text_render[:cur_pos] + '...')
                        clip_width = size_w[0] + (icon_w)*self.scale

                    # Now set the text down one so it will fit
                    cur_pos -= 1
                    size_w = blf.dimensions(
                        self.font_id, self.text_render[:cur_pos] + '...')

                    # Set the next text to what can fit with the ellipses
                    if cur_pos >= 0:
                        self.text_render = self.text_render[:cur_pos] + '...'
                    # or set the text to nothing
                    else:
                        self.text_render = ''
                        size_w = np.array([0.0, 0.0], dtype=np.float32)
                        size_h = np.array([0.0, 0.0], dtype=np.float32)

                size_width = size_w[0]/self.scale
                size_height = size_h[1]/self.scale
                if self.text_alignment == 'CENTER':
                    x_co = (wid_mid - (size_width + icon_w)/2)

                elif self.text_alignment == 'RIGHT':
                    x_co = self.width - self.text_margin - size_width - icon_w

                elif self.text_alignment == 'LEFT':
                    x_co = self.text_margin

                # Offset text if icn is on the right side
                if self.icon_text_side == 'RIGHT':
                    x_co += icon_w

                # Set text offset and scaled font size
                self.scale_font_size = cur_size
                self.text_pos_offset[:] = [
                    x_co,
                    -self.height/2 - size_height/2]

            # Get icon position coords
            if self.icon_img:
                x_co = wid_mid - (size_width + icon_w)/2
                y_co = -self.height/2 + self.icon_height/2

                if self.icon_text_side == 'LEFT':
                    x_co += size_width
                self.set_icon_pos_offset_x(x_co)
                self.set_icon_pos_offset_y(y_co)

                self.icon_pos = np.array([
                    [0.0, 0.0],
                    [icon_w, 0.0],
                    [icon_w, -self.icon_height],
                    [0.0, -self.icon_height],
                ], dtype=np.float32)

        for shape in self.shapes:
            shape.create_shape_data()

        return

    def update_batches(self, position):
        super().update_batches(position)
        pos = self.scale_pos_offset + position

        if self.icon_img:
            i_pos = self.icon_pos_offset * self.scale + pos

            points = (self.icon_pos * self.scale + i_pos).tolist()
            tex_cos = [[0, 0], [1, 0], [1, -1], [0, -1]]

            self.batch_icon = batch_for_shader(self.shader_img, 'TRI_FAN', {
                                               "pos": points, "texCoord": tex_cos})

        if self.text_render != '':
            self.text_pos = self.text_pos_offset * self.scale + pos

        for shape in self.shapes:
            shape.update_batches(pos)

        return

    def init_shape_data(self):
        self.icon_pos = []
        super().init_shape_data()
        return

    def check_icon_img(self):
        if None not in [self.icon_img, self.icon_img_name, self.icon_img_path]:
            try:
                self.icon_img, self.icon_img.name
            except:
                self.set_icon_image(self.icon_img_name, self.icon_img_path)
        return

    def add_poly_shape(self, coords):
        shape = CUIPolyWidget()
        shape.set_base_points(coords)
        shape.set_enabled(self.enabled)

        self.shapes.append(shape)
        return shape

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_font_render = get_enabled_color(
            self.color_font, self.enabled)
        self.color_click_render = get_enabled_color(
            self.color_click, self.enabled)

        return

    def draw(self, color_override=None, click_down=False):
        if color_override:
            super().draw(color_override)
        elif self.hover and click_down:
            super().draw(self.color_click_render)
        else:
            super().draw()

        for shape in self.shapes:
            shape.draw()

        self.icon_draw()
        self.text_draw()
        return

    def icon_draw(self):
        if self.visible and self.icon_img:
            icon_img = bpy.data.images[self.icon_img_name]

            if icon_img.gl_load():
                raise Exception()

            gpu.state.blend_set('ALPHA')
            texture = gpu.texture.from_image(icon_img)
            self.shader_img.bind()
            self.shader_img.uniform_sampler("image", texture)
            self.batch_icon.draw(self.shader_img)
            gpu.state.blend_set('NONE')
        return

    def text_draw(self):
        if self.visible and self.text_render != '':
            if bpy.app.version[0] >= 4:
                blf.size(self.font_id, self.scale_font_size)
            else:
                blf.size(self.font_id, self.scale_font_size, 72)
            blf.position(self.font_id, self.text_pos[0], self.text_pos[1], 0)
            blf.color(
                self.font_id, self.color_font_render[0], self.color_font_render[1], self.color_font_render[2], self.color_font_render[3])
            blf.draw(self.font_id, self.text_render)
        return

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        for shape in self.shapes:
            shape.set_scale(scale)
        return

    def set_text(self, text):
        self.text = text
        return

    def set_color(self, color=None, color_hover=None, color_outline=None, color_click=None, color_font=None):
        if color_font:
            self.color_font = color_font
        if color_click:
            self.color_click = color_click

        super().set_color(
            color=color,
            color_hover=color_hover,
            color_outline=color_outline
        )

        return

    def set_icon_image(self, image_name, image_path):
        self.icon_img_name = image_name
        self.icon_img_path = image_path
        self.icon_img = cui_img_load(image_name, image_path)
        return

    def set_icon_data(self, width=None, height=None, text_side=None):
        if width is not None:
            self.icon_width = width
        if height is not None:
            self.icon_height = height
        if text_side is not None:
            self.icon_text_side = text_side
        return

    def offset_icon_pos_offset(self, offset):
        self.icon_pos_offset[:] += offset
        return

    def offset_icon_pos_offset_x(self, x_val):
        self.icon_pos_offset[0] += x_val
        return

    def offset_icon_pos_offset_y(self, y_val):
        self.icon_pos_offset[1] += y_val
        return

    def set_icon_pos_offset(self, offset):
        self.icon_pos_offset[:] = offset
        return

    def set_icon_pos_offset_x(self, x_val):
        self.icon_pos_offset[0] = x_val
        return

    def set_icon_pos_offset_y(self, y_val):
        self.icon_pos_offset[1] = y_val
        return

    #

    def __str__(self):
        return 'CUI Item Widget'


class CUICheckWidget(CUIItemWidget):
    #
    # Checkmark widget. A checkmark inside of a square for the boolean item and others
    #
    def __init__(self, height, default_val=False):
        self.color_check = (0.0, 0.0, 1.0, 0.75)
        self.color_bool = (0.62, 0.5, 0.75, 0.75)

        self.color_check_render = None
        self.color_bool_render = None

        super().__init__(height, '')

        self.icon_img_false = None
        self.icon_img_false_name = None
        self.icon_img_false_path = None

        self.icon_img_true = None
        self.icon_img_true_name = None
        self.icon_img_true_path = None

        self.bool_val = default_val
        self.bool_box_size = height-6
        self.bool_thickness = 3

        self.draw_check = True
        self.text_margin = 0

        self.bevel_size = 4
        self.bevel_res = 3
        return

    #

    def create_shape_data(self):
        offset = (self.height-self.bool_box_size)/2

        super().create_shape_data()

        # Create the check lines based on the bool box size
        bool_fac = self.bool_box_size // 4
        self.check_lines = np.array([
            [self.bool_box_size-bool_fac, -offset-bool_fac],
            [self.bool_box_size // 2.5, -offset-self.bool_box_size+bool_fac],
            [self.bool_box_size // 2.5, -offset-self.bool_box_size+bool_fac],
            [bool_fac, -offset-self.bool_box_size + self.bool_box_size // 2]
        ], dtype=np.float32)

        return

    def update_batches(self, position):
        pos = self.scale_pos_offset + position

        lines = (self.check_lines * self.scale + pos).tolist()

        self.batch_check = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        super().update_batches(position)
        return

    def init_shape_data(self):
        self.check_lines = []
        super().init_shape_data()
        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_check_render = get_enabled_color(
            self.color_check, self.enabled)
        self.color_bool_render = get_enabled_color(
            self.color_bool, self.enabled)

        return

    def draw(self, color_override=None, click_down=False):
        if self.bool_val:
            super().draw(self.color_bool_render, click_down=click_down)
        else:
            super().draw(click_down=click_down)

        if self.bool_val and self.draw_check:

            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(self.bool_thickness)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_check_render)
            self.batch_check.draw(self.shader)
            gpu.state.blend_set('NONE')

        return

    #

    def set_color(self, color=None, color_hover=None, color_outline=None, color_click=None, color_font=None, color_check=None, color_bool=None):
        if color_check:
            self.color_check = color_check
        if color_bool:
            self.color_bool = color_bool

        super().set_color(
            color=color,
            color_hover=color_hover,
            color_outline=color_outline,
            color_click=color_click,
            color_font=color_font
        )

        return

    def set_true_icon_image(self, image_name, image_path):
        self.icon_img_true_name = image_name
        self.icon_img_true_path = image_path
        self.icon_img_true = cui_img_load(image_name, image_path)
        self.set_bool(self.bool_val)
        return

    def set_false_icon_image(self, image_name, image_path):
        self.icon_img_false_name = image_name
        self.icon_img_false_path = image_path
        self.icon_img_false = cui_img_load(image_name, image_path)
        self.set_bool(self.bool_val)
        return

    def check_icon_img(self):
        if None not in [self.icon_img_true, self.icon_img_true_name, self.icon_img_true_path]:
            try:
                self.icon_img_true, self.icon_img_true.name
            except:
                self.set_true_icon_image(self.icon_img_true_name,
                                         self.icon_img_true_path)

        if None not in [self.icon_img_false, self.icon_img_false_name, self.icon_img_false_path]:
            try:
                self.icon_img_false, self.icon_img_false.name
            except:
                self.set_false_icon_image(self.icon_img_false_name,
                                          self.icon_img_false_path)
        self.set_bool(self.bool_val)
        return

    def set_bool(self, status):
        self.bool_val = status
        if self.icon_img_true is not None and status:
            self.icon_img_name = self.icon_img_true_name
            self.icon_img_path = self.icon_img_true_path
            self.icon_img = self.icon_img_true

        if self.icon_img_false is not None and not status:
            self.icon_img_name = self.icon_img_false_name
            self.icon_img_path = self.icon_img_false_path
            self.icon_img = self.icon_img_false

        return

    #

    def __str__(self):
        return 'CUI Check Widget'


#
#
#


class CUIButton(CUIItem):
    #
    # Button class simple just click to execute the functions. Has a bool value to indicate on/off
    #
    def __init__(self, cont, height, text):
        self.color_bool = (0.62, 0.5, 0.75, 0.75)

        self.color_bool_render = None

        super().__init__(cont, height)

        self.item_type = 'BUTTON'

        self.bool = False

        button = CUIItemWidget(height, text)
        button.hover_highlight = self.hover_highlight

        self.parts.append(button)
        return

    #

    def create_shape_data(self):
        super().create_shape_data()
        for part in self.parts:
            part.set_height(self.height)
            part.set_width(self.width)
            part.create_shape_data()
        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_bool_render = get_enabled_color(
            self.color_bool, self.enabled)

        return

    def draw(self):
        if self.bool:
            for part in self.parts:
                part.draw(self.color_bool_render, click_down=self.click_down)
        else:
            for part in self.parts:
                part.draw(click_down=self.click_down)

        return

    #
    # TEST CLICK FUNCS
    #

    def test_hover(self, mouse_co, position):
        super().test_hover(mouse_co, position)
        status = None
        if self.hover:
            status = 'BUTTON'
        return status

    #

    def get_text(self):
        return self.parts[0].text

    #

    def set_bool(self, status):
        self.bool = status
        return

    def set_text(self, text=None):
        if text is not None:
            self.parts[0].set_text(text)
        return

    def set_draw_box(self, status):
        self.parts[0].draw_box = status
        return

    def set_bool_color(self, color):
        self.color_bool = color

        self.update_color_render()
        return

    def set_icon_image(self, image_name, image_path):
        self.parts[0].set_icon_image(image_name, image_path)
        return

    def set_icon_data(self, width=None, height=None, text_side=None):
        self.parts[0].set_icon_data(
            width=width, height=height, text_side=text_side)
        return

    def set_bev(self, size, res):
        self.parts[0].set_bev(size, res)
        return

    #

    def __str__(self):
        return 'CUI Button'


class CUIHoverButton(CUIItem):
    #
    # Hoverable Button class that opens a subpanel when hovered and closes when itself and the subpanel are no longer hovered
    #
    def __init__(self, cont, height, text):
        self.color_bool = (0.62, 0.5, 0.75, 0.75)

        self.color_bool_render = None

        super().__init__(cont, height)

        self.bool = False

        self.item_type = 'HOVER_BUTTON'

        self.hover_down_func = None
        self.hover_up_func = None

        button = CUIItemWidget(height, text)
        button.hover_highlight = self.hover_highlight

        self.parts.append(button)
        return

    #

    def create_shape_data(self):
        super().create_shape_data()
        for part in self.parts:
            part.set_height(self.height)
            part.set_width(self.width)
            part.create_shape_data()
        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_bool_render = get_enabled_color(
            self.color_bool, self.enabled)

        return

    def draw(self):
        for part in self.parts:
            part.draw(click_down=self.click_down)

        return

    #
    # TEST CLICK FUNCS
    #

    def test_hover(self, mouse_co, position):
        prev_status = self.hover

        super().test_hover(mouse_co, position)

        if self.hover != prev_status:
            arguments = []
            insert_modal(arguments, self.parent_container.modal)

            if self.hover and self.hover_down_func is not None:
                self.hover_down_func(self, arguments)

        status = None
        if self.hover:
            status = 'HOVER_BUTTON'
        return status

    def clear_hover(self):
        if self.hover and self.hover_up_func is not None:
            arguments = []
            insert_modal(arguments, self.parent_container.modal)

            self.hover_up_func(self, arguments)

        self.hover = False
        for part in self.parts:
            part.hover = False
        return

    #

    def get_text(self):
        return self.parts[0].text

    #

    def set_bool(self, status):
        self.bool = status
        return

    def set_hover_down_func(self, func):
        self.hover_down_func = func
        return

    def set_hover_up_func(self, func):
        self.hover_up_func = func
        return

    def set_text(self, text=None):
        if text is not None:
            self.parts[0].set_text(text)
        return

    def set_draw_box(self, status):
        self.parts[0].draw_box = status
        return

    def set_bool_color(self, color):
        self.color_bool = color

        self.update_color_render()
        return

    def set_icon_image(self, image_name, image_path):
        self.parts[0].set_icon_image(image_name, image_path)
        return

    def set_icon_data(self, width=None, height=None, text_side=None):
        self.parts[0].set_icon_data(
            width=width, height=height, text_side=text_side)
        return

    def set_bev(self, size, res):
        self.parts[0].set_bev(size, res)
        return

    #

    def __str__(self):
        return 'CUI Hover Button'


class CUIBoolProp(CUIItem):
    #
    # Boolean property. Has a check mark next to the main button
    #
    def __init__(self, cont, height, text, default_val=False):
        super().__init__(cont, height)

        self.item_type = 'BOOLEAN'

        self.bool_val = default_val
        self.use_button = True

        self.ui_enable_toggle_target = None

        check_box = CUICheckWidget(height, default_val)
        button = CUIItemWidget(height, text)
        check_box.hover_highlight = self.hover_highlight
        button.hover_highlight = self.hover_highlight

        self.parts.append(check_box)
        self.parts.append(button)
        return

    #

    def create_shape_data(self):
        # super().create_shape_data()
        offset = (self.height-self.parts[0].bool_box_size)/2

        for p, part in enumerate(self.parts):
            part.pos_offset = np.array([0.0, 0.0], dtype=np.float32)
            # If part is 0 it is the check icon so set to bool box size
            if p == 0:
                part.set_pos_offset_y(-offset)

                part.set_height(part.bool_box_size)
                part.set_width(part.bool_box_size)
            # If part is 1 it is the main button so offset to side of bool box
            if p == 1:
                part.set_pos_offset_x(self.parts[0].bool_box_size + offset)

                part.set_height(self.height)
                part.set_width(
                    self.width - self.parts[0].bool_box_size - offset)

            part.create_shape_data()
        return

    #

    def draw(self):
        if self.visible:
            for p, part in enumerate(self.parts):
                if p == 0:
                    part.draw(click_down=self.click_down)
                else:
                    if self.use_button:
                        part.draw(click_down=self.click_down)

        return

    #
    # TEST CLICK FUNCS
    #

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        self.toggle_bool()
        status = super().click_up_func(mouse_co, shift, position, arguments)
        return status

    def test_hover(self, mouse_co, position):
        super().test_hover(mouse_co, position)
        status = None
        if self.hover:
            status = 'BOOLEAN'
            self.parts[0].hover = True
            self.parts[1].hover = True
        else:
            self.parts[0].hover = False
            self.parts[1].hover = False
        return status

    #

    def toggle_bool(self):
        self.bool_val = not self.bool_val
        self.parts[0].set_bool(self.bool_val)

        if self.ui_enable_toggle_target is not None:
            self.ui_enable_toggle_target.set_enabled(self.bool_val)

        return

    #

    def set_draw_box(self, status):
        for p, part in enumerate(self.parts):
            if p != 0:
                part.draw_box = status
        return

    def set_check_false_icon(self, image_name, image_path):
        self.parts[0].set_false_icon_image(image_name, image_path)

        self.parts[0].set_icon_data(
            width=self.parts[0].bool_box_size-2, height=self.parts[0].bool_box_size-2)

        self.parts[0].draw_check = False
        return

    def set_check_true_icon(self, image_name, image_path):
        self.parts[0].set_true_icon_image(image_name, image_path)

        self.parts[0].set_icon_data(
            width=self.parts[0].bool_box_size-2, height=self.parts[0].bool_box_size-2)

        self.parts[0].draw_check = False
        return

    def set_use_button(self, status):
        self.use_button = status
        return

    def set_bool(self, status):
        self.bool_val = status
        self.parts[0].set_bool(status)
        return

    def set_ui_enable_target(self, target):
        self.ui_enable_toggle_target = target
        return

    #

    def __str__(self):
        return 'CUI Boolean Prop'


class CUINumProp(CUIItem):
    #
    # Number property. Can be typed into, the value slid, and has 2 arrows on the sides to iterate up/down. Both Int and Float
    #
    def __init__(self, cont, height, text, default, decimals, step, min, max):
        self.color_perc_bar = (0.0, 0.0, 0.3, 0.75)
        self.color_perc_bar_hover = (0.0, 0.0, 0.4, 0.75)
        self.color_arrow_box = (0.0, 0.0, 0.4, 1)
        self.color_arrow_box_hover = (0.0, 0.0, 0.5, 1)
        self.color_arrow = (0.0, 0.0, 1.0, 0.75)

        self.color_arrow_render = None

        super().__init__(cont, height)

        self.item_type = 'NUMBER'

        self.value_change_function = None

        self.arrow_width = self.height-8

        self.draw_box = True

        self.slidable = True

        self.init_click_loc = np.array([0.0, 0.0], dtype=np.float32)
        self.sliding = False
        self.typing = False

        self.type_string = ''
        self.type_pos = 0

        self.value = default
        self.round_decis = decimals
        self.value_min = min
        self.value_max = max
        self.slide_fac = 5.0
        self.value_step = step
        self.shift_value_step = step * 2
        self.slide_value_step = step * .1

        round_min = 1
        for i in range(decimals):
            round_min *= .1
        if self.slide_value_step < round_min:
            self.slide_value_step = round_min

        self.draw_backdrop = True

        perc_bar = CUIItemWidget(height, '')
        left_arrow = CUIItemWidget(height, '')
        right_arrow = CUIItemWidget(height, '')
        text_bar = CUIItemWidget(height, text)

        left_arrow.add_poly_shape(
            np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], dtype=np.float32).reshape(-1, 2))
        right_arrow.add_poly_shape(
            np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], dtype=np.float32).reshape(-1, 2))

        left_arrow.bevel_inds = [0, 3]
        right_arrow.bevel_inds = [1, 2]

        perc_bar.hover_highlight = self.hover_highlight
        left_arrow.hover_highlight = self.hover_highlight
        right_arrow.hover_highlight = self.hover_highlight
        text_bar.hover_highlight = self.hover_highlight

        text_bar.draw_box = False

        self.parts.append(perc_bar)
        self.parts.append(left_arrow)
        self.parts.append(right_arrow)
        self.parts.append(text_bar)
        return

    #

    def create_shape_data(self):
        arrow_box_size = self.height
        # Arrow box size is the height of of the number prop
        # But if 3 arrows cant fit then the size is evenly distributed of what width is available
        if self.width < self.height*3:
            arrow_box_size = self.width/3

        for p, part in enumerate(self.parts):
            part.set_height(self.height)
            part.pos_offset = np.array([0.0, 0.0], dtype=np.float32)

            # Part 0 is the percentage bar
            if p == 0:
                perc = (self.value-self.value_min) / \
                    (self.value_max-self.value_min)
                part.set_color(
                    color=self.color_perc_bar,
                    color_hover=self.color_perc_bar_hover
                )
                part.set_pos_offset_x(arrow_box_size)
                part.set_width((self.width - arrow_box_size*2) * perc)
                part.create_shape_data()

            # Part 1 is the left arrow box
            if p == 1:
                part.set_color(
                    color=self.color_arrow_box,
                    color_hover=self.color_arrow_box_hover
                )
                part.set_width(arrow_box_size)

                # Check if arrow can fit inside the arrow box size
                if arrow_box_size < self.arrow_width+2:
                    part.shapes[0].set_base_points(
                        [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])
                else:
                    offset = (arrow_box_size - self.arrow_width)/2
                    arrow_pos = [
                        [offset+self.arrow_width, -offset],
                        [offset, -self.height/2],
                        [offset+self.arrow_width, -self.height+offset]]

                    part.shapes[0].set_base_points(arrow_pos)

                part.create_shape_data()

            # Part 2 is the right arrow box
            if p == 2:
                part.set_color(
                    color=self.color_arrow_box,
                    color_hover=self.color_arrow_box_hover
                )
                part.set_pos_offset_x(self.width - arrow_box_size)
                part.set_width(arrow_box_size)

                # Check if arrow can fit inside the arrow box size
                if arrow_box_size < self.arrow_width+2:
                    part.shapes[0].set_base_points(
                        [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]])
                else:
                    offset = (arrow_box_size - self.arrow_width)/2
                    arrow_pos = [
                        [offset, -offset],
                        [arrow_box_size-offset, -self.height/2],
                        [offset, -self.height+offset]]

                    part.shapes[0].set_base_points(arrow_pos)

                part.create_shape_data()

            # Part 3 is the text box in the center bar
            if p == 3:
                part.set_pos_offset_x(arrow_box_size)
                part.set_width(self.width - arrow_box_size*2)
                if self.typing:
                    string = self.type_string[:self.type_pos] + \
                        '|' + self.type_string[self.type_pos:]
                    part.create_shape_data(
                        value=self.value, text=string)
                else:
                    part.create_shape_data(value=self.value)

        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_arrow_render = get_enabled_color(
            self.color_arrow, self.enabled)

        return

    def draw(self):
        if self.visible:
            # if self.parts[0].hover:
            #     super().draw(self.color_hover)
            # else:
            #     super().draw()

            for p, part in enumerate(self.parts):
                if p == 0:
                    if self.typing == False:
                        part.draw(click_down=self.click_down)
                elif p < 4:
                    part.draw(click_down=self.click_down)

        return

    #
    # TEST CLICK FUNCS
    #

    def click_down_func(self, mouse_co, shift, position, arguments=None):
        self.typing = False
        for p, part in enumerate(self.parts):
            if part.hover:
                self.init_click_loc[:] = mouse_co
                # perc bar
                if p == 0:
                    return ['NUMBER_BAR', self.custom_id]
                # left arrow
                if p == 1:
                    return ['NUMBER_L_ARROW', self.custom_id]
                # right arrow
                if p == 2:
                    return ['NUMBER_R_ARROW', self.custom_id]
        return None

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        insert_modal(arguments, self.parent_container.modal)

        for p, part in enumerate(self.parts):
            skip_update = False
            if part.hover:
                self.init_click_loc = np.array([0.0, 0.0], dtype=np.float32)

                # If sliding reset the cursor and the do 1 final value change func
                if self.sliding:
                    if self.value_change_function:
                        self.value_change_function(self, arguments)
                    self.sliding = False
                    bpy.context.window.cursor_modal_set('DEFAULT')
                    return ['NUMBER_SLIDE', self.custom_id]

                else:
                    # If releasing while not sliding on the percent bar then start typing
                    if p == 0:
                        self.typing = True
                        self.create_shape_data()
                        return ['NUMBER_BAR_TYPE', self.custom_id]

                    # If releasing on the arrows offset the value in the correct direction
                    if p == 1 or p == 2:
                        # Set the correct status and offset factor based on left/right arrow
                        fac = 1.0
                        status = 'NUMBER_R_ARROW'
                        if p == 1:
                            status = 'NUMBER_L_ARROW'
                            fac = -1.0

                        # Increment based on shift or not
                        if shift:
                            self.offset_value(self.shift_value_step * fac)
                        else:
                            self.offset_value(self.value_step * fac)

                        if self.value_change_function:
                            skip_update = self.value_change_function(
                                self, arguments)

                        if not skip_update:
                            self.create_shape_data()
                            self.update_batches(position)

                        return [status, self.custom_id]
        return None

    def click_down_move(self, mouse_co, shift, position, arguments=None):
        insert_modal(arguments, self.parent_container.modal)

        for p, part in enumerate(self.parts):
            if p == 3:
                continue
            skip_update = False
            if part.hover:
                if self.sliding == False:
                    # If mouse has moved more than 5 pixels enter sliding mode if it is on
                    if abs(self.init_click_loc[0] - mouse_co[0]) > 5 and self.slidable:
                        self.sliding = True
                    # Else just test hover
                    else:
                        self.test_hover(mouse_co, position)

                else:
                    # Hide the cursor while sliding to avoid the user seeing it jumping around
                    # If the cursor goes onto a second monitor it can come back so continuosly hide it
                    bpy.context.window.cursor_modal_set('NONE')

                    # Get the difference in mouse movement from init click
                    diff = mouse_co[0] - self.init_click_loc[0]

                    # Get the minimum value that the mouse must have moved to iterated based on slide fac
                    min_val = 1.0 * self.slide_fac

                    # Scale down movement based on precision shift
                    if shift:
                        diff *= .1

                    # If mouse move is far enough then offset the value based on how many iterations it has moved
                    if abs(diff) >= min_val:
                        # calculate the # of iterations and force it to be atleast 1
                        iters = abs(diff) // min_val
                        if iters == 0:
                            iters = 1

                        if diff >= 0:
                            self.offset_value(self.slide_value_step*iters)
                        else:
                            self.offset_value(-self.slide_value_step*iters)

                        if self.value_change_function:
                            skip_update = self.value_change_function(
                                self, arguments)

                        if not skip_update:
                            self.create_shape_data()
                            self.update_batches(position)

                        # Warp cursor back to initial location so the cursor wont go out of blender or hit edge of monitor and stop
                        bpy.context.window.cursor_warp(
                            int(bpy.context.region.x + self.init_click_loc[0]), int(bpy.context.region.y + self.init_click_loc[1]))

        return

    def test_hover(self, mouse_co, position):
        super().test_hover(mouse_co, position)
        status = None
        if self.hover:
            status = 'NUMBER'
            if self.parts[1].hover == False and self.parts[2].hover == False:
                self.parts[0].hover = True
        return status

    #

    def offset_value(self, offset):
        self.set_value(self.value + offset)
        return

    def reset_item_states(self, clear_hover):
        # if clear_hover:
        #     self.clear_hover()
        self.sliding = False
        # #bpy.context.window.cursor_modal_set('DEFAULT')
        self.type_string = ''
        self.type_pos = 0
        self.typing = False
        # self.click_down = False
        super().reset_item_states(clear_hover)
        return

    #
    # TYPE FUNCS
    #

    def type_add_key(self, key):
        if self.typing:
            change = False
            numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', ]
            operands = ['+', '-', '/', '*', ]

            if key in numbers:
                self.type_string = self.type_string[:self.type_pos] + \
                    key + self.type_string[self.type_pos:]
                change = True

            if key in operands:
                existing = False
                for op in operands:
                    if op in self.type_string:
                        existing = True

                if existing == False:
                    self.type_string = self.type_string[:self.type_pos] + \
                        key + self.type_string[self.type_pos:]
                    change = True

            if key == '.':
                op_found = False
                for op in operands:
                    if op in self.type_string:
                        op_found = True
                        sides = self.type_string.split(op)

                        if len(sides) >= self.type_pos:
                            if '.' not in sides[0]:
                                self.type_string = self.type_string[:self.type_pos] + \
                                    key + self.type_string[self.type_pos:]
                                change = True
                        else:
                            if '.' not in sides[1]:
                                self.type_string = self.type_string[:self.type_pos] + \
                                    key + self.type_string[self.type_pos:]
                                change = True

                if op_found == False:
                    if '.' not in self.type_string:
                        self.type_string = self.type_string[:self.type_pos] + \
                            key + self.type_string[self.type_pos:]
                        change = True

            if change:
                self.type_pos += 1
                self.create_shape_data()
        return

    def type_backspace_key(self):
        if self.typing:
            if self.type_pos > 0:
                self.type_string = self.type_string[:self.type_pos -
                                                    1] + self.type_string[self.type_pos:]
                self.type_pos -= 1
                self.create_shape_data()
        return

    def type_delete_key(self):
        if self.typing:
            if self.type_pos < len(self.type_string):
                self.type_string = self.type_string[:self.type_pos] + \
                    self.type_string[self.type_pos+1:]
                self.create_shape_data()
        return

    def type_move_pos(self, value):
        if self.typing:
            self.type_pos += value
            if self.type_pos < 0:
                self.type_pos = 0
            if self.type_pos > len(self.type_string):
                self.type_pos = len(self.type_string)
            self.create_shape_data()
        return

    def type_confirm(self, arguments=None):
        if self.typing and self.type_string:
            insert_modal(arguments, self.parent_container.modal)

            operands = ['+', '-', '/', '*', ]
            op_found = False
            for op in operands:
                if op in self.type_string:
                    op_found = True
                    sides = self.type_string.split(op)
                    value = self.value

                    if op == '+':
                        value = float(sides[0])+float(sides[1])

                    if op == '-':
                        value = float(sides[0])-float(sides[1])

                    if op == '/':
                        if float(sides[1]) != 0.0:
                            value = float(sides[0])/float(sides[1])

                    if op == '*':
                        value = float(sides[0])*float(sides[1])
                    self.set_value(value)
                    if self.value_change_function:
                        self.value_change_function(self, arguments)

            if op_found == False:
                value = float(self.type_string)
                self.set_value(value)
                if self.value_change_function:
                    self.value_change_function(self, arguments)

        self.type_string = ''
        self.type_pos = 0
        self.typing = False
        self.create_shape_data()
        return

    def type_cancel(self):
        self.type_string = ''
        self.type_pos = 0
        self.typing = False
        self.create_shape_data()
        return

    #

    def set_slidable(self, status):
        self.slidable = status
        return

    def set_value_step(self, step=None, shift_step=None):
        if step is not None:
            self.value_step = step
        if shift_step is not None:
            self.shift_value_step = shift_step
        return

    def set_slide_value_step(self, step):
        self.slide_value_step = step
        return

    def set_value(self, value):
        self.value = value

        if self.value_min is not None:
            if self.value < self.value_min:
                self.value = self.value_min

        if self.value_max is not None:
            if self.value > self.value_max:
                self.value = self.value_max

        self.value = round(self.value, self.round_decis)
        if self.round_decis == 0:
            self.value = int(self.value)
        return

    def set_slide_factor(self, fac):
        self.slide_fac = fac
        return

    def set_color_row(self, color_box=None, color_box_hover=None):
        for p, part in enumerate(self.parts):
            if p == 1 or p == 2:
                if color_box:
                    self.color = color_box
                if color_box_hover:
                    self.color_hover = color_box_hover

        self.update_color_render()
        return

    def set_bev(self, size, res):
        self.parts[1].set_bev(size, res)
        self.parts[2].set_bev(size, res)
        super().set_bev(size, res)
        return

    def set_value_change_func(self, func):
        self.value_change_function = func
        return

    #

    def __str__(self):
        return 'CUI Number Prop'


class CUILabel(CUIItem):
    #
    # Text label item. No interaction with it just a display text
    #
    def __init__(self, cont, height, text):
        super().__init__(cont, height)

        self.item_type = 'LABEL'

        txt_box = CUIItemWidget(height, text)
        txt_box.hover_highlight = False
        txt_box.draw_box = False

        self.parts.append(txt_box)
        return

    #

    def create_shape_data(self):
        # super().create_shape_data()
        for part in self.parts:
            part.set_height(self.height)
            part.set_width(self.width)
            part.create_shape_data()
        return

    #
    # TEST CLICK FUNCS
    #

    def click_down_func(self, mouse_co, shift, position, arguments=None):
        return None

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        return None

    def test_hover(self, mouse_co, position):
        return None

    #

    def reset_item_states(self, clear_hover):
        return

    #

    def set_icon_image(self, image_name, image_path):
        self.parts[0].set_icon_image(image_name, image_path)
        return

    def set_icon_data(self, width=None, height=None, text_side=None):
        self.parts[0].set_icon_data(
            width=width, height=height, text_side=text_side)
        return

    #

    def __str__(self):
        return 'CUI Button'


class CUISpacer(CUIItem):
    #
    # Empty item with a height only to space out other items
    #
    def __init__(self, cont, height, width):
        super().__init__(cont, height)
        self.set_width(width)
        self.max_width = width

        self.item_type = 'SPACER'
        return

    #

    def create_shape_data(self):
        return

    def update_batches(self, position):
        return

    def test_hover(self, mouse_co, position):
        return None

    #

    def draw(self):
        return

    #

    def click_down_func(self, mouse_co, shift, position, arguments=None):
        return None

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        return None

    #

    def reset_item_states(self, clear_hover):
        return

    def set_click_up_func(self, func):
        return

    def set_click_down_func(self, func):
        return

    #

    def __str__(self):
        return 'CUI Spacer'


#
#
#


class CUIGizmo3DContainer:
    def __init__(self, mat, size, scale):
        self.gizmos = []
        self.matrix = mat
        self.scale_factor = None
        self.size = size

        self.hover = False
        self.visible = False

        self.scale = scale

        return

    #

    def draw(self):
        if self.visible:
            for i in range(len(self.gizmos)):
                if self.gizmos[i*-1-1].active:
                    self.gizmos[i*-1-1].draw()
        return

    def create_shape_data(self, matrix):
        for gizmo in self.gizmos:
            gizmo.create_shape_data()

        self.update_position(matrix)
        return

    #

    def update_size(self, size):
        self.size = size
        for giz in self.gizmos:
            giz.size = self.size
        self.create_shape_data(self.matrix)
        return

    def update_position(self, matrix):
        self.matrix = matrix
        self.scale_factor = None
        for gizmo in self.gizmos:
            self.scale_factor = gizmo.update_position(
                matrix, self.scale_factor)
        return

    def update_rotation(self, ang, start_ang):
        for gizmo in self.gizmos:
            if gizmo.in_use:
                gizmo.update_rotation_fan(
                    self.matrix, self.scale_factor, ang, start_ang)
        return

    def update_orientation(self, matrix):
        self.matrix = matrix
        for gizmo in self.gizmos:
            gizmo.update_position(self.matrix, self.scale_factor)
        return

    #

    def clear_hover(self):
        for giz in self.gizmos:
            giz.hover = False
        return

    def test_hover(self, mouse_co):
        if self.visible:
            act_gizs = [i for i in range(
                len(self.gizmos)) if self.gizmos[i].active]

            # Get mouse coord ray casting vectors from view
            region = bpy.context.region
            rv3d = bpy.context.region_data

            # get the ray from the viewport and mouse
            view_vector = view3d_utils.region_2d_to_vector_3d(
                region, rv3d, mouse_co)
            ray_origin = view3d_utils.region_2d_to_origin_3d(
                region, rv3d, mouse_co)

            # Convert vectors into matrices space
            view_vector = self.matrix.inverted() @ view_vector + self.matrix.translation
            ray_origin = self.matrix.inverted() @ ray_origin

            ray_origin *= 1/self.scale_factor

            # Ray cast on bvh to find hover
            res = ray_cast_2d_loc(
                mouse_co, ray_origin, view_vector, [self.gizmos[i].bvh for i in act_gizs])

            if res is not None:
                self.gizmos[res[2]].hover = True
                self.hover = True
                return True
        return False

    #

    def set_scale(self, scale):
        self.scale = scale
        for giz in self.gizmos:
            giz.set_scale(self.scale)
        self.create_shape_data(self.matrix)
        return

    def set_visibility(self, status):
        self.visible = status
        if status == False:
            self.clear_hover()
        return

    #

    def __str__(self):
        return 'CUI Gizmo Set'


class CUIGizmo:
    def __init__(self, size, scale, axis, giz_type, color):
        if bpy.app.version[0] >= 4:
            shader_3d_str = 'UNIFORM_COLOR'
        else:
            shader_3d_str = '3D_UNIFORM_COLOR'
        self.shader = gpu.shader.from_builtin(shader_3d_str)

        self.axis = axis
        self.type = giz_type

        self.size = size
        self.scale = scale
        self.color = color

        self.active = True
        self.hover = False
        self.in_use = False

        self.prev_scale = 1.0

        self.bvh = None

        self.init_shape_data()
        return

    #

    def draw(self):
        if self.active:

            self.shader.bind()
            if self.hover and self.in_use == False:
                self.shader.uniform_float("color", [1.0, 1.0, 1.0, 1.0])
            else:
                self.shader.uniform_float("color", self.color)
            self.batch.draw(self.shader)

        return

    #

    def update_position(self, matrix, scale_fac):

        # No scale factor provided so we need to create the initial gizmo shape to find its current size in screen space
        # So we can figure out the scale it needs to be for the desired screen space size
        if scale_fac == None:
            # Get mouse coord ray casting vectors from view
            region = bpy.context.region
            rv3d = bpy.context.region_data

            # get the ray from the viewport and mouse
            ray_origin = view3d_utils.region_2d_to_origin_3d(
                region, rv3d, [region.width/2, region.height/2])

            view_vector = matrix.translation - ray_origin
            cross_vec = view_vector.cross([0.0, 0.0, 1.0]).normalized()

            cross_co = matrix.translation + cross_vec

            cent_rco = view3d_utils.location_3d_to_region_2d(
                region, rv3d, matrix.translation)
            cross_rco = view3d_utils.location_3d_to_region_2d(
                region, rv3d, cross_co)

            if cent_rco is not None and cross_rco is not None:
                screen_dist = (cross_rco - cent_rco).length

                scale_fac = self.size/screen_dist * 0.5

                self.prev_scale = scale_fac

            else:
                scale_fac = self.prev_scale

        #

        # Orient scaled points into matrices space
        self.mat_points = get_np_matrix_transformed_vecs(
            self.points * scale_fac, np.array(matrix))

        #

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_points.tolist()}, indices=self.tris.tolist())

        return scale_fac

    #

    def init_shape_data(self):
        self.points = np.array([], dtype=np.float32)
        self.tris = np.array([], dtype=np.int32)

        self.mat_points = np.array([], dtype=np.float32)
        return

    def create_shape_data(self):
        self.init_shape_data()
        return

    #

    def set_scale(self, scale):
        self.scale = scale
        return

    #

    def __str__(self):
        return 'CUI Base Gizmo'


class CUIRotateGizmo(CUIGizmo):
    def __init__(self, size, scale, axis, giz_type, color, thickness=6):
        self.resolution = 36
        self.thickness = thickness

        super().__init__(size, scale, axis, giz_type, color)
        return

    #

    def draw(self):
        if self.active:

            if self.in_use:
                self.shader.bind()
                self.shader.uniform_float(
                    "color", [self.color[0], self.color[1], self.color[2], 0.2])
                self.batch_fan.draw(self.shader)

                self.shader.bind()
                self.shader.uniform_float("color", [1.0, 1.0, 1.0, 1.0])
                self.batch_fan_lines.draw(self.shader)

            self.shader.bind()
            if self.hover and self.in_use == False:
                self.shader.uniform_float("color", [1.0, 1.0, 1.0, 1.0])
            else:
                self.shader.uniform_float("color", self.color)
            self.batch.draw(self.shader)

        return

    #

    def update_position(self, matrix, scale_fac):
        scale_fac = super().update_position(matrix, scale_fac)

        self.mat_fan_points = get_np_matrix_transformed_vecs(
            self.fan_points * scale_fac, np.array(matrix))
        self.mat_fan_lines = get_np_matrix_transformed_vecs(
            self.fan_lines * scale_fac, np.array(matrix))

        self.batch_fan = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_fan_points.tolist()}, indices=self.fan_tris.tolist())
        self.batch_fan_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": self.mat_fan_lines.tolist()})

        return scale_fac

    def update_rotation_fan(self, matrix, scale_fac, angle, start_ang=0):
        angs = angle * (np.arange(self.resolution,
                                  dtype=np.float32) / self.resolution) + start_ang + np.radians(90)

        self.fan_points[:] = 0.0
        self.fan_points[1:, 1] = 1.0

        self.fan_points[1:, 0] = np.cos(angs) * self.fan_points[1:, 1]
        self.fan_points[1:, 1] = np.sin(angs) * self.fan_points[1:, 1]

        if self.axis == 0:
            self.fan_points = self.fan_points[:, [2, 0, 1]]
        if self.axis == 1:
            self.fan_points = self.fan_points[:, [0, 2, 1]]
            self.fan_points[:, 1] *= -1

        self.fan_lines = self.fan_points[[0, 1, 0, -1]]

        #

        self.mat_fan_points = get_np_matrix_transformed_vecs(
            self.fan_points * scale_fac, np.array(matrix))
        self.mat_fan_lines = get_np_matrix_transformed_vecs(
            self.fan_lines * scale_fac, np.array(matrix))

        self.batch_fan = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_fan_points.tolist()}, indices=self.fan_tris.tolist())
        self.batch_fan_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": self.mat_fan_lines.tolist()})

        return

    #

    def init_shape_data(self):
        super().init_shape_data()

        self.fan_points = []
        self.fan_tris = []
        self.fan_lines = []

        self.mat_fan_points = []
        self.mat_fan_lines = []
        return

    def create_shape_data(self):
        self.init_shape_data()

        if self.resolution <= 12:
            self.resolution = 12

        thick = self.thickness/2

        angs = np.radians(360) * (np.arange(self.resolution,
                                            dtype=np.float32) / self.resolution)

        cos = np.zeros(self.resolution*3, dtype=np.float32).reshape(-1, 3)
        cos[:, 1] = 1.0

        self.points = np.tile(cos, 4)

        cos[:, 0] = np.cos(angs) * cos[:, 1]
        cos[:, 1] = np.sin(angs) * cos[:, 1]

        angs = np.tile(angs.reshape(-1, 1), 4).reshape(-1)

        self.points[:, 1] += thick
        self.points[:, 7] -= thick

        self.points[:, 5] = thick
        self.points[:, 11] = -thick

        self.points.shape = [-1, 3]

        self.points[:, 0] = np.cos(angs) * self.points[:, 1]
        self.points[:, 1] = np.sin(angs) * self.points[:, 1]

        #

        self.tris = np.tile(np.arange(self.resolution).reshape(-1, 1), 3*8) * 4
        self.tris[:, [0, 3, 7]] += 1
        self.tris[:, [6, 9, 13]] += 2
        self.tris[:, [12, 15, 19]] += 3
        self.tris[:, [2, 4, 23]] += 4
        self.tris[:, [5, 8, 10]] += 5
        self.tris[:, [11, 14, 16]] += 6
        self.tris[:, [17, 20, 22]] += 7

        self.tris[-1, [2, 4, 23]] = 0
        self.tris[-1, [5, 8, 10]] = 1
        self.tris[-1, [11, 14, 16]] = 2
        self.tris[-1, [17, 20, 22]] = 3

        self.tris.shape = [-1, 3]

        if self.axis == 0:
            self.points = self.points[:, [2, 1, 0]]
            self.tris[:] = self.tris[:, ::-1]
        if self.axis == 1:
            self.points = self.points[:, [0, 2, 1]]
            self.tris[:] = self.tris[:, ::-1]

        self.bvh = bvhtree.BVHTree.FromPolygons(
            self.points.tolist(), self.tris.tolist())

        #

        self.fan_points = np.vstack(
            (np.array([0.0, 0.0, 0.0], dtype=np.float32), cos))

        self.fan_tris = np.tile(
            np.arange(self.resolution-1).reshape(-1, 1), 3)
        self.fan_tris[:, 0] = 0
        self.fan_tris[:, 1] += 1
        self.fan_tris[:, 2] += 2

        if self.axis == 0:
            self.fan_points = self.fan_points[:, [2, 1, 0]]
        if self.axis == 1:
            self.fan_points = self.fan_points[:, [0, 2, 1]]

        self.fan_lines = self.fan_points[[0, 1, 0, -1]]

        return

    #

    def __str__(self):
        return 'CUI Rotation Gizmo'
