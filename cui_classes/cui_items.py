import bpy
import blf
import bgl
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Euler
from .cui_functions import *
from .cui_shapes import *

#
#
#


class CUIItem(CUIRectWidget):
    def __init__(self, height):
        self.color = (0.0, 0.0, 0.35, 0.5)
        self.color_hover = (0.0, 0.0, 0.4, 0.75)

        super().__init__()

        self.parts = []
        self.shapes = []
        self.custom_id = None

        self.item_type = ''

        self.height = height
        self.hover_highlight = True
        self.click_down = False

        self.click_down_function = None
        self.click_up_function = None

        self.draw_box = False

        return

    #

    def update_batches(self, position):
        super().update_batches(position)
        for part in self.parts:
            part.update_batches(
                [position[0]+self.scale_pos_offset[0], position[1]+self.scale_pos_offset[1]])
        for shape in self.shapes:
            shape.update_batches(
                [position[0]+self.scale_pos_offset[0], position[1]+self.scale_pos_offset[1]])
        return

    def draw(self, color_override=None):
        super().draw(color_override)
        for part in self.parts:
            part.draw(color_override, self.click_down)

        return

    #

    def click_down_move(self, mouse_co, shift, pos, arguments=None):
        self.test_hover(mouse_co, pos)
        if self.hover == False:
            self.click_down = False
        return

    def click_down_func(self, mouse_co, shift, pos, arguments=None):
        if self.click_down_function:
            click_status = self.click_down_function(self, arguments)
            if click_status:
                return [click_status, self.custom_id]
        return [self.item_type, self.custom_id]

    def click_up_func(self, mouse_co, shift, pos, arguments=None):
        if self.click_up_function:
            click_status = self.click_up_function(self, arguments)
            if click_status:
                return [click_status, self.custom_id]
        return [self.item_type, self.custom_id]

    def test_hover(self, mouse_co, pos):
        super().test_hover(mouse_co, [pos[0], pos[1]])
        if self.hover:
            for part in self.parts:
                part.test_hover(
                    mouse_co, [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]])
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

    def set_scale(self, scale):
        super().set_scale(scale)
        for part in self.parts:
            part.set_scale(scale)
        for shape in self.shapes:
            shape.set_scale(scale)
        return

    def set_custom_id(self, id):
        self.custom_id = id
        return

    def set_font_size(self, size):
        for part in self.parts:
            part.font_size = size
        return

    def set_color(self, color=None, color_hover=None, color_outline=None, color_click=None, color_font=None):
        super().set_color(color=color, color_hover=color_hover, color_outline=color_outline)
        for part in self.parts:
            part.set_color(color=color, color_hover=color_hover, color_outline=color_outline,
                           color_click=color_click, color_font=color_font)

        return

    def set_click_up_func(self, func):
        self.click_up_function = func
        return

    def set_click_down_func(self, func):
        self.click_down_function = func
        return

    #

    def __str__(self):
        return 'CUI Item Widget'


class CUIItemWidget(CUIRectWidget):
    def __init__(self, height, text):
        self.color = (0.0, 0.0, 0.35, 0.5)
        self.color_hover = (0.0, 0.0, 0.4, 0.75)

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.color_font_render = None
        self.color_click_render = None

        super().__init__()

        self.height = height
        self.hover_highlight = True

        self.font_id = 0
        self.font_size = 12
        self.scale_font_size = 12

        self.text = text
        self.text_render = text
        self.text_pos = [0, 0]
        self.text_pos_offset = [0, 0]
        # self.text_vert_alignment = 'CENTER'
        # self.text_hor_alignment = 'CENTER'
        self.text_auto_y = True
        self.text_margin = 2

        self.shader_img = gpu.shader.from_builtin('2D_IMAGE')

        self.icon_pos = [0, 0]
        self.icon_pos_offset = [0, 0]
        self.icon_height = 20
        self.icon_width = 20
        self.icon_img = None
        self.icon_text_side = 'RIGHT'
        self.icon_visible = True
        return

    #

    def create_shape_data(self, value='', text=None, text_pos=0):
        super().create_shape_data()
        # TEXT
        wid_mid = self.width/2
        icon_w = 0
        if self.icon_img:
            icon_w = self.icon_width

        # Icon is bigger than current width so no text or icon will be drawn
        avail_wid = self.width-self.text_margin*2
        if icon_w > avail_wid:
            self.text_render = ''
            self.icon_visible = False

        else:
            self.icon_visible = True

            # Get current text
            self.text_render = self.text
            if value != '':
                self.text_render = self.text + ': ' + str(value)
            if text != None:
                self.text_render = text

            size_width = 0
            size_height = 0
            cur_size = self.font_size
            if self.text_render != '':
                blf.size(self.font_id, self.font_size, 72)
                blf.position(self.font_id, 0, 0, 0)
                size_w = blf.dimensions(self.font_id, self.text_render)
                size_h = blf.dimensions(self.font_id, 'T')

                targ_width = size_w[0] * self.scale
                cur_size = self.font_size
                if targ_width != 0 and self.scale != 1.0:
                    cur_width = 0
                    cur_size = 0
                    while cur_width <= targ_width:
                        cur_size += 1

                        blf.size(self.font_id, cur_size, 72)
                        cur_width, cur_height = blf.dimensions(
                            self.font_id, self.text_render)
                    cur_size -= 1
                    blf.size(self.font_id, cur_size, 72)
                    size_w = blf.dimensions(self.font_id, self.text_render)
                    size_h = blf.dimensions(self.font_id, 'T')

                # Test that icon and text will fit in item width if not then clip text
                if size_w[0] + (icon_w)*self.scale > avail_wid*self.scale:
                    clip_width = 0
                    cur_pos = -1
                    while clip_width < avail_wid*self.scale:
                        cur_pos += 1
                        size_w = blf.dimensions(
                            self.font_id, self.text_render[:cur_pos] + '...')
                        clip_width = size_w[0] + (icon_w)*self.scale
                    cur_pos -= 1
                    size_w = blf.dimensions(
                        self.font_id, self.text_render[:cur_pos] + '...')

                    if cur_pos >= 0:
                        self.text_render = self.text_render[:cur_pos] + '...'
                    else:
                        self.text_render = ''
                        size_w = [0, 0]
                        size_h = [0, 0]
                size_width = size_w[0]/self.scale
                size_height = size_h[1]/self.scale
                x_co = (wid_mid - (size_width + icon_w)/2)

                if self.icon_text_side == 'RIGHT':
                    x_co += icon_w

                self.scale_font_size = cur_size
                self.text_pos_offset = [x_co, -self.height/2 - size_height/2]
            # ICON
            if self.icon_img:
                x_co = wid_mid - (size_width + icon_w)/2
                y_co = -self.height/2 + self.icon_height/2

                if self.icon_text_side == 'LEFT':
                    x_co += size_width
                self.icon_pos_offset[0] = x_co
                self.icon_pos_offset[1] = y_co

                self.icon_pos = [
                    [0, 0],
                    [icon_w, 0],
                    [icon_w, -self.icon_height],
                    [0, -self.icon_height],
                ]

        return

    def update_batches(self, position):
        super().update_batches(position)
        pos = [position[0]+self.scale_pos_offset[0],
               position[1]+self.scale_pos_offset[1]]
        if self.icon_img:
            i_pos = [pos[0]+self.icon_pos_offset[0]*self.scale,
                     pos[1]+self.icon_pos_offset[1]*self.scale]
            points = draw_cos_offset(i_pos, self.scale, self.icon_pos)
            tex_cos = [[0, 0], [1, 0], [1, -1], [0, -1]]

            self.batch_icon = batch_for_shader(self.shader_img, 'TRI_FAN', {
                                               "pos": points, "texCoord": tex_cos})

        if self.text_render != '':

            self.text_pos = [pos[0]+self.text_pos_offset[0] *
                             self.scale, pos[1]+self.text_pos_offset[1]*self.scale]

        return

    def update_color_render(self):
        super().update_color_render()
        self.color_font_render = hsv_to_rgb_list(self.color_font)
        self.color_click_render = hsv_to_rgb_list(self.color_click)
        return

    def init_shape_data(self):
        self.icon_pos = []
        super().init_shape_data()
        return

    def draw(self, color_override=None, click_down=False):
        if color_override:
            super().draw(color_override)
        elif self.hover and click_down:
            super().draw(self.color_click_render)
        else:
            super().draw()

        self.icon_draw()
        self.text_draw()
        return

    def icon_draw(self):
        if self.visible == True and self.icon_img:
            if self.icon_img.gl_load():
                raise Exception()

            disable = bgl.glIsEnabled(bgl.GL_BLEND)
            if disable == False:
                bgl.glEnable(bgl.GL_BLEND)
            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.icon_img.bindcode)
            self.shader_img.bind()
            self.shader_img.uniform_int("image", 0)
            self.batch_icon.draw(self.shader_img)
            if disable == False:
                bgl.glDisable(bgl.GL_BLEND)
        return

    def text_draw(self):
        if self.visible == True and self.text_render != '':
            blf.size(self.font_id, self.scale_font_size, 72)
            blf.position(self.font_id, self.text_pos[0], self.text_pos[1], 0)
            blf.color(
                self.font_id, self.color_font_render[0], self.color_font_render[1], self.color_font_render[2], self.color_font_render[3])
            blf.draw(self.font_id, self.text_render)
        return

    #

    def clear_hover(self):
        self.hover = False
        return

    #

    def set_custom_id(self, id):
        self.custom_id = id
        return

    def set_text(self, text):
        self.text = text
        return

    def set_color(self, color=None, color_hover=None, color_outline=None, color_click=None, color_font=None):
        if color_font:
            self.color_font = color_font
        if color_click:
            self.color_click = color_click

        super().set_color(color=color, color_hover=color_hover, color_outline=color_outline)

        return

    def set_icon_data(self, image=None, width=None, height=None, text_side=None):
        if image != None:
            self.icon_img = image
        if width != None:
            self.icon_width = width
        if height != None:
            self.icon_height = height
        if text_side != None:
            self.icon_text_side = text_side
        return

    #

    def __str__(self):
        return 'CUI Item Widget'


class CUICheckWidget(CUIItemWidget):
    def __init__(self, height, default_val=False):
        self.color_check = (0.0, 0.0, 1.0, 0.75)
        self.color_bool = (0.62, 0.5, 0.75, 0.75)

        self.color_check_render = None
        self.color_bool_render = None

        super().__init__(height, '')

        self.item_type = 'CHECKBOX'

        self.icon_img_false = None
        self.icon_img_true = None

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

        bool_fac = int(self.bool_box_size*0.25)
        self.check_lines = [
            [self.bool_box_size-bool_fac, -offset-bool_fac],
            [int(self.bool_box_size*.4), -offset-self.bool_box_size+bool_fac],
            [int(self.bool_box_size*.4), -offset-self.bool_box_size+bool_fac],
            [bool_fac, -offset-self.bool_box_size+int(self.bool_box_size*.5)]
        ]

        return

    def init_shape_data(self):
        self.check_lines = []
        super().init_shape_data()
        return

    def update_batches(self, position):
        pos = [position[0]+self.scale_pos_offset[0],
               position[1]+self.scale_pos_offset[1]]

        lines = draw_cos_offset(pos, self.scale, self.check_lines)

        self.batch_check = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        super().update_batches(position)
        return

    def update_color_render(self):
        super().update_color_render()
        self.color_check_render = hsv_to_rgb_list(self.color_check)
        self.color_bool_render = hsv_to_rgb_list(self.color_bool)
        return

    def draw(self, color_override=None, click_down=False):
        if self.bool_val:
            super().draw(self.color_bool_render, click_down=click_down)
        else:
            super().draw(click_down=click_down)
        if self.bool_val and self.draw_check:

            bgl.glLineWidth(self.bool_thickness)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_check_render)
            self.batch_check.draw(self.shader)

        return

    #

    def set_color(self, color=None, color_hover=None, color_outline=None, color_click=None, color_font=None, color_check=None, color_bool=None):
        if color_check:
            self.color_check = color_check
        if color_bool:
            self.color_bool = color_bool

        super().set_color(color=color, color_hover=color_hover,
                          color_outline=color_outline, color_click=color_click, color_font=color_font)

        return

    def set_true_icon(self, image):
        self.icon_img_true = image
        return

    def set_false_icon(self, image):
        self.icon_img_false = image
        return

    def set_bool(self, status):
        self.bool_val = status
        if self.icon_img_true != None and status:
            super().set_icon_data(image=self.icon_img_true)

        if self.icon_img_false != None and not status:
            super().set_icon_data(image=self.icon_img_false)

        return

    #

    def __str__(self):
        return 'CUI Check Widget'


#
#
#


class CUIButton(CUIItem):
    def __init__(self, height, text):
        self.color_bool = (0.62, 0.5, 0.75, 0.75)

        self.color_bool_render = None

        super().__init__(height)

        self.item_type = 'BUTTON'

        self.bool = False

        button = CUIItemWidget(height, text)
        button.hover_highlight = self.hover_highlight

        self.parts.append(button)
        return

    #

    def update_color_render(self):
        super().update_color_render()
        self.color_bool_render = hsv_to_rgb_list(self.color_bool)
        return

    def create_shape_data(self, value='', text=None, text_pos=0, x_offset=0):
        super().create_shape_data()
        for part in self.parts:
            part.height = self.height
            part.width = self.width
            part.create_shape_data()
        for shape in self.shapes:
            shape.create_shape_data()
        return

    def draw(self):
        if self.bool:
            for part in self.parts:
                part.draw(self.color_bool_render, click_down=self.click_down)
        else:
            for part in self.parts:
                part.draw(click_down=self.click_down)

        for shape in self.shapes:
            shape.draw()

        return

    #

    def add_poly_shape(self, coords):
        shape = CUIPolyWidget()
        shape.set_base_points(coords)

        self.shapes.append(shape)
        return shape

    #

    def get_text(self):
        return self.parts[0].text

    #

    def set_bool(self, status):
        self.bool = status
        return

    def test_hover(self, mouse_co, pos):
        super().test_hover(mouse_co, [pos[0], pos[1]])
        status = None
        if self.hover:
            status = 'BUTTON'
        return status

    def set_text(self, text=None):
        if text != None:
            self.parts[0].set_text(text)
        return

    def set_draw_box(self, status):
        self.parts[0].draw_box = status
        return

    def set_bool_color(self, color):
        self.color_bool = color

        self.update_color_render()
        return

    def set_icon_data(self, image=None, width=None, height=None, text_side=None):
        self.parts[0].set_icon_data(
            image=image, width=width, height=height, text_side=text_side)
        return

    #

    def __str__(self):
        return 'CUI Button'


class CUIBoolProp(CUIItem):
    def __init__(self, height, text, default_val=False):
        super().__init__(height)

        self.item_type = 'BOOLEAN'

        self.bool_val = default_val
        self.use_button = True

        check_box = CUICheckWidget(height, default_val)
        button = CUIItemWidget(height, text)
        check_box.hover_highlight = self.hover_highlight
        button.hover_highlight = self.hover_highlight

        self.parts.append(check_box)
        self.parts.append(button)
        return

    #

    def create_shape_data(self):
        super().create_shape_data()
        offset = (self.height-self.parts[0].bool_box_size)/2

        for p, part in enumerate(self.parts):
            part.pos_offset = [0, 0]
            if p == 0:
                part.pos_offset[1] = -offset

                part.height = part.bool_box_size
                part.width = part.bool_box_size
            if p == 1:
                part.pos_offset[0] = self.parts[0].bool_box_size + offset

                part.height = self.height
                part.width = self.width - self.parts[0].bool_box_size - offset

            part.create_shape_data()
        return

    def draw(self):
        if self.visible == True:
            for p, part in enumerate(self.parts):
                if p == 0:
                    part.draw(click_down=self.click_down)
                else:
                    if self.use_button:
                        part.draw(click_down=self.click_down)

        return

    #

    def click_up_func(self, mouse_co, shift, pos, arguments=None):
        self.toggle_bool()
        status = super().click_up_func(mouse_co, shift, pos, arguments)
        return status

    def test_hover(self, mouse_co, pos):
        super().test_hover(mouse_co, [pos[0], pos[1]])
        status = None
        if self.hover:
            status = 'BOOLEAN'
            self.parts[0].hover = True
            self.parts[1].hover = True
        else:
            self.parts[0].hover = False
            self.parts[1].hover = False
        return status

    def toggle_bool(self):
        self.bool_val = not self.bool_val
        self.parts[0].set_bool(self.bool_val)
        return

    #

    def set_check_icon(self, image_true=None, image_false=None):
        if image_true != None:
            self.parts[0].set_true_icon(image_true)
        if image_false != None:
            self.parts[0].set_false_icon(image_false)

        if self.bool_val:
            self.parts[0].set_icon_data(
                image=image_true, width=self.parts[0].bool_box_size-2, height=self.parts[0].bool_box_size-2)
        else:
            self.parts[0].set_icon_data(
                mage=image_false, width=self.parts[0].bool_box_size-2, height=self.parts[0].bool_box_size-2)

        self.parts[0].draw_check = False
        return

    def set_use_button(self, status):
        self.use_button = status
        return

    def set_bool(self, status):
        self.bool_val = status
        self.parts[0].set_bool(status)
        return

    #

    def __str__(self):
        return 'CUI Boolean Prop'


class CUINumProp(CUIItem):
    def __init__(self, height, text, default, decimals, step, min, max):
        self.color_perc_bar = (0.0, 0.0, 0.3, 0.75)
        self.color_perc_bar_hover = (0.0, 0.0, 0.4, 0.75)
        self.color_arrow_box = (0.0, 0.0, 0.4, 1)
        self.color_arrow_box_hover = (0.0, 0.0, 0.5, 1)
        self.color_arrow = (0.0, 0.0, 1.0, 0.75)

        self.color_arrow_render = None

        super().__init__(height)

        self.item_type = 'NUMBER'

        self.value_change_function = None

        self.arrow_width = self.height-8

        self.draw_box = True

        self.slidable = True

        self.init_click_loc = [0, 0]
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
        self.init_shape_data()

        arrow_box_size = self.height
        if self.width < self.height*3:
            arrow_box_size = self.width/3

        for p, part in enumerate(self.parts):
            part.height = self.height
            part.pos_offset = [0, 0]
            if p == 0:
                perc = (self.value-self.value_min) / \
                    (self.value_max-self.value_min)
                part.set_color(color=self.color_perc_bar,
                               color_hover=self.color_perc_bar_hover)
                part.pos_offset[0] = arrow_box_size
                part.width = (self.width - arrow_box_size*2) * perc
                part.create_shape_data()
            if p == 1:
                part.set_color(color=self.color_arrow_box,
                               color_hover=self.color_arrow_box_hover)
                part.width = arrow_box_size
                part.create_shape_data()
            if p == 2:
                part.set_color(color=self.color_arrow_box,
                               color_hover=self.color_arrow_box_hover)
                part.pos_offset[0] = self.width - arrow_box_size
                part.width = arrow_box_size
                part.create_shape_data()
            if p == 3:
                part.pos_offset[0] = arrow_box_size
                part.width = self.width - arrow_box_size*2
                if self.typing:
                    string = self.type_string[:self.type_pos] + \
                        '|' + self.type_string[self.type_pos:]
                    part.create_shape_data(
                        value=self.value, text=string, text_pos=self.type_pos)
                else:
                    part.create_shape_data(value=self.value)

        if arrow_box_size < self.arrow_width+2:
            self.arrow_pos = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], ]
        else:
            offset = (arrow_box_size - self.arrow_width)/2
            self.arrow_pos = [[offset+self.arrow_width, -offset], [offset, -self.height/2], [offset+self.arrow_width, -self.height+offset],
                              [self.width-arrow_box_size+offset, -offset], [self.width-offset, -self.height/2], [self.width-arrow_box_size+offset, -self.height+offset], ]
        return

    def init_shape_data(self):
        self.arrow_pos = []
        self.arrow_tris = [[0, 1, 2], [3, 4, 5]]
        super().init_shape_data()
        return

    def update_batches(self, position):
        pos = [position[0]+self.scale_pos_offset[0],
               position[1]+self.scale_pos_offset[1]]

        arrows = draw_cos_offset(pos, self.scale, self.arrow_pos)

        self.batch_arrows = batch_for_shader(
            self.shader, 'TRIS', {"pos": arrows}, indices=self.arrow_tris)
        super().update_batches(position)
        return

    def update_color_render(self):
        super().update_color_render()

        self.color_arrow_render = hsv_to_rgb_list(self.color_arrow)
        return

    def draw(self):
        if self.visible == True:
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

            self.shader.bind()
            self.shader.uniform_float("color", self.color_arrow_render)
            self.batch_arrows.draw(self.shader)

        return

    #

    def click_down_func(self, mouse_co, shift, pos, arguments=None):
        self.typing = False
        for p, part in enumerate(self.parts):
            if part.hover:
                self.init_click_loc = mouse_co
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

    def click_up_func(self, mouse_co, shift, pos, arguments=None):
        for p, part in enumerate(self.parts):
            skip_update = False
            if part.hover:
                self.init_click_loc = [0, 0]

                if self.sliding:
                    if self.value_change_function:
                        self.value_change_function(self, arguments)
                    self.sliding = False
                    bpy.context.window.cursor_modal_set('DEFAULT')
                    return ['NUMBER_SLIDE', self.custom_id]

                else:
                    if p == 0:
                        self.typing = True
                        self.create_shape_data()
                        return ['NUMBER_BAR_TYPE', self.custom_id]

                    if p == 1:
                        if shift:
                            self.offset_value(-self.shift_value_step)
                        else:
                            self.offset_value(-self.value_step)

                        if self.value_change_function:
                            skip_update = self.value_change_function(
                                self, arguments)

                        if not skip_update:
                            self.create_shape_data()
                            self.update_batches(pos)
                        return ['NUMBER_L_ARROW', self.custom_id]

                    if p == 2:
                        if shift:
                            self.offset_value(self.shift_value_step)
                        else:
                            self.offset_value(self.value_step)

                        if self.value_change_function:
                            skip_update = self.value_change_function(
                                self, arguments)

                        if not skip_update:
                            self.create_shape_data()
                            self.update_batches(pos)
                        return ['NUMBER_R_ARROW', self.custom_id]
        return None

    def click_down_move(self, mouse_co, shift, pos, arguments=None):
        for p, part in enumerate(self.parts):
            if p == 3:
                continue
            skip_update = False
            if part.hover:
                if self.sliding == False:
                    if abs(self.init_click_loc[0] - mouse_co[0]) > 5 and self.slidable:
                        self.sliding = True
                        bpy.context.window.cursor_modal_set('NONE')
                    else:
                        self.test_hover(mouse_co, pos)

                else:
                    # calc if slide is far enough to iterate
                    diff = mouse_co[0] - self.init_click_loc[0]

                    min_val = 1.0 * self.slide_fac

                    if shift:
                        diff *= .1

                    if abs(diff) >= min_val:
                        iters = int(abs(diff)/min_val)
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
                            self.update_batches(pos)

                        bpy.context.window.cursor_warp(
                            int(bpy.context.region.x + self.init_click_loc[0]), int(bpy.context.region.y + self.init_click_loc[1]))

        return

    def test_hover(self, mouse_co, pos):
        super().test_hover(mouse_co, [pos[0], pos[1]])
        status = None
        if self.hover:
            status = 'NUMBER'
            if self.parts[1].hover == False and self.parts[2].hover == False:
                self.parts[0].hover = True
        return status

    def offset_value(self, offset):
        self.set_value(self.value + offset)
        return

    #

    def reset_item_states(self, clear_hover):
        # if clear_hover:
        #     self.clear_hover()
        self.sliding = False
        # bpy.context.window.cursor_modal_set('DEFAULT')
        self.type_string = ''
        self.type_pos = 0
        self.typing = False
        # self.click_down = False
        super().reset_item_states(clear_hover)
        return

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
                        if flaot(sides[1]) != 0.0:
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
        if step != None:
            self.value_step = step
        if shift_step != None:
            self.shift_value_step = shift_step
        return

    def set_slide_value_step(self, step):
        self.slide_value_step = step
        return

    def set_value(self, value):
        self.value = value

        if self.value_min != None:
            if self.value < self.value_min:
                self.value = self.value_min

        if self.value_max != None:
            if self.value > self.value_max:
                self.value = self.value_max

        self.value = round(self.value, self.round_decis)
        if self.round_decis == 0:
            self.value = int(self.value)
        return

    def set_slide_factor(self, fac):
        self.slide_fac = fac
        return

    def set_arcolor_row(self, color_box=None, color_box_hover=None):
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
    def __init__(self, height, text):
        super().__init__(height)

        self.item_type = 'LABEL'

        txt_box = CUIItemWidget(height, text)
        txt_box.hover_highlight = False
        txt_box.draw_box = False

        self.parts.append(txt_box)
        return

    #

    def create_shape_data(self, value='', text=None, text_pos=0, x_offset=0):
        super().create_shape_data()
        for part in self.parts:
            part.height = self.height
            part.width = self.width
            part.create_shape_data()
        return

    #

    def click_down_func(self, mouse_co, shift, pos, arguments=None):
        return None

    def click_up_func(self, mouse_co, shift, pos, arguments=None):
        return None

    def test_hover(self, mouse_co, pos):
        return None

    #

    def reset_item_states(self, clear_hover):
        return

    #

    def draw(self):
        super().draw()
        return

    def set_text(self, text):
        self.parts[0].set_text(text)
        return

    def set_icon_data(self, image=None, width=None, height=None, text_side=None):
        self.parts[0].set_icon_data(
            image=image, width=width, height=height, text_side=text_side)
        return

    #

    def __str__(self):
        return 'CUI Button'


#
#
#


class UIGizmoContainer:
    def __init__(self, index, mat, size, axis, scale):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.index = index
        self.gizmos = []
        self.matrix = mat
        self.scale_factor = None
        self.size = size

        self.visible = False

        self.scale = scale

        return

    def update_size(self, size):
        self.size = size
        for giz in self.gizmos:
            giz.size = self.size
        self.create_shape_data(self.matrix)
        return

    def create_shape_data(self, matrix):
        for gizmo in self.gizmos:
            gizmo.create_shape_data()

        self.update_position(matrix)
        return

    def update_position(self, matrix, ang=0):
        self.matrix = matrix
        self.scale_factor = None
        for gizmo in self.gizmos:
            self.scale_factor = gizmo.update_position(
                matrix, self.scale_factor, ang)
        return

    def update_rot(self, ang, start_ang):
        for gizmo in self.gizmos:
            if gizmo.in_use:
                gizmo.update_rot_fan(
                    self.matrix, self.scale_factor, ang, start_ang)
        return

    def update_orientation(self, matrix):
        self.matrix = matrix
        for gizmo in self.gizmos:
            gizmo.update_position(self.matrix, self.scale_factor)
        return

    def draw(self):
        if self.visible:
            for i in range(len(self.gizmos)):
                if self.gizmos[i*-1-1].active:
                    self.gizmos[i*-1-1].draw()
        return

    def clear_hover(self):
        for giz in self.gizmos:
            giz.hover = False
        return

    def test_hover(self, mouse_co):
        if self.visible:

            for giz in self.gizmos:
                if giz.active:
                    hov = giz.test_hover(mouse_co)
                    if hov:
                        return True
        return False

    def set_scale(self, scale):
        self.scale = scale
        for giz in self.gizmos:
            giz.set_scale(self.scale)
        self.create_shape_data(self.matrix)
        return

    def set_visibility(self, status):
        self.visible = status
        return


class UIRotateGizmo:
    def __init__(self, index, size, scale, axis, giz_type, color, thickness=6):
        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.index = index

        self.size = size
        self.scale = scale
        self.resolution = 36
        self.points = []
        self.mat_points = []
        self.axis = axis
        self.color = color
        self.active = True
        self.hover = False
        self.thickness = thickness
        self.type = giz_type
        self.in_use = False
        self.prev_screen_size = size

        return

    def test_hover(self, mouse_co):
        region = bpy.context.region
        rv3d = bpy.context.region_data

        mouse_co = Vector((mouse_co[0], mouse_co[1]))

        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0
        rcos = []
        for c, co in enumerate(self.mat_points):
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            if rco == None:
                rcos.append(None)
                continue

            if c == 0:
                min_x = rco[0]
                max_x = rco[0]
                min_y = rco[1]
                max_y = rco[1]
            else:
                if rco[0] < min_x:
                    min_x = rco[0]
                if rco[0] > max_x:
                    max_x = rco[0]
                if rco[1] < min_y:
                    min_y = rco[1]
                if rco[1] > max_y:
                    max_y = rco[1]

            rcos.append(rco)

        self.hover = False
        if min_x < mouse_co[0] < max_x and min_y < mouse_co[1] < max_y:
            for tri in self.tris:
                co1 = rcos[tri[0]]
                co2 = rcos[tri[1]]
                co3 = rcos[tri[2]]

                if co1 == None or co2 == None or co3 == None:
                    continue

                vec1 = mouse_co - co1
                vec2 = mouse_co - co2
                vec3 = mouse_co - co3

                tri_vec1 = co2-co1
                tri_vec2 = co3-co1
                tri_vec3 = co2-co3

                t_ang = tri_vec1.angle_signed(tri_vec2)
                m_ang = tri_vec1.angle_signed(vec1)
                if t_ang < 0.0:
                    if m_ang < t_ang or m_ang > 0.0:
                        continue
                else:
                    if m_ang > t_ang or m_ang < 0.0:
                        continue

                t_ang = tri_vec3.angle_signed(-tri_vec2)
                m_ang = tri_vec3.angle_signed(vec3)
                if t_ang < 0.0:
                    if m_ang < t_ang or m_ang > 0.0:
                        continue
                else:
                    if m_ang > t_ang or m_ang < 0.0:
                        continue

                self.hover = True
                return self.hover

        return self.hover

    def init_shape_data(self):
        self.points = []
        self.tris = []
        self.mat_points = []
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
        ang = 360/self.resolution
        co1 = [0, (1+self.thickness/2)*self.scale]
        co2 = [0, 1*self.scale]
        co3 = [0, (1-self.thickness/2)*self.scale]
        co4 = [0, 1*self.scale]
        for i in range(self.resolution):
            new_co1 = rotate_2d([0, 0], co1, math.radians(ang*i)).to_3d()
            new_co2 = rotate_2d([0, 0], co2, math.radians(ang*i)).to_3d()
            new_co3 = rotate_2d([0, 0], co3, math.radians(ang*i)).to_3d()
            new_co4 = rotate_2d([0, 0], co4, math.radians(ang*i)).to_3d()

            new_co2[2] += self.thickness/2*self.scale
            new_co4[2] -= self.thickness/2*self.scale

            new_co1 *= .01
            new_co2 *= .01
            new_co3 *= .01
            new_co4 *= .01

            if self.axis == 0:
                self.points.append(new_co1.zyx)
                self.points.append(new_co2.zyx)
                self.points.append(new_co3.zyx)
                self.points.append(new_co4.zyx)
            if self.axis == 1:
                self.points.append(new_co1.xzy)
                self.points.append(new_co2.xzy)
                self.points.append(new_co3.xzy)
                self.points.append(new_co4.xzy)
            if self.axis == 2:
                self.points.append(new_co1)
                self.points.append(new_co2)
                self.points.append(new_co3)
                self.points.append(new_co4)

            if i < self.resolution-1:
                self.tris += [
                    [i*4+1, i*4, i*4+4], [i*4+1, i*4+4, i*4+5], [i *
                                                                 4+2, i*4+1, i*4+5], [i*4+2, i*4+5, i*4+6],
                    [i*4+3, i*4+2, i*4+6], [i*4+3, i*4+6, i*4 +
                                            7], [i*4, i*4+3, i*4+7], [i*4, i*4+7, i*4+4]
                ]
            else:
                self.tris += [
                    [i*4+1, i*4, 0], [i*4+1, 0, 1], [i *
                                                     4+2, i*4+1, 1], [i*4+2, 1, 2],
                    [i*4+3, i*4+2, 2], [i*4+3, 2, 7], [i*4, i*4+3, 7], [i*4, 3, 0]
                ]

        ang = 180/(int(self.resolution/2)-1)
        co = [0, 1*self.scale]
        self.fan_points.append(Vector((0, 0, 0)))
        for i in range(int(self.resolution/2)+1):
            new_co = rotate_2d([0, 0], co, math.radians(ang*i)).to_3d()
            new_co *= .01

            if self.axis == 0:
                self.fan_points.append(new_co.zyx)
            if self.axis == 1:
                self.fan_points.append(new_co.xzy)
            if self.axis == 2:
                self.fan_points.append(new_co)

            if i < int(self.resolution/2):
                self.fan_tris.append([0, i+1, i+2])

        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[1])
        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[-1])
        return

    def update_position(self, matrix, scale_fac, angle=0):
        region = bpy.context.region
        rv3d = bpy.context.region_data

        self.mat_points.clear()
        for p in range(len(self.points)):
            self.mat_points.append(matrix @ self.points[p])

        if scale_fac == None:
            region = bpy.context.region
            rv3d = bpy.context.region_data

            min_x = 0
            max_x = 0
            min_y = 0
            max_y = 0
            for c, co in enumerate(self.mat_points):
                rco = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
                if rco == None:
                    continue

                if c == 0:
                    min_x = rco[0]
                    max_x = rco[0]
                    min_y = rco[1]
                    max_y = rco[1]
                else:
                    if rco[0] < min_x:
                        min_x = rco[0]
                    if rco[0] > max_x:
                        max_x = rco[0]
                    if rco[1] < min_y:
                        min_y = rco[1]
                    if rco[1] > max_y:
                        max_y = rco[1]

            height = max_y - min_y
            width = max_x - min_x

            if height > width:
                max_size = height
            else:
                max_size = width

            if max_size == 0:
                max_size = self.prev_screen_size

            self.prev_screen_size = max_size
            max_size += 1

            scale_fac = self.size/max_size

        self.mat_points.clear()
        for p in range(len(self.points)):
            co = matrix @ (self.points[p]*scale_fac)
            self.mat_points.append(co)

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_points}, indices=self.tris)

        self.update_rot_fan(matrix, scale_fac, angle)
        return scale_fac

    def update_rot_fan(self, matrix, scale_fac, angle, start_ang=0):
        region = bpy.context.region
        rv3d = bpy.context.region_data

        if self.resolution <= 12:
            self.resolution = 12

        point_per_rot = int(360/(self.resolution/2))
        rotations = int(math.degrees(abs(angle))/360)
        point_num = point_per_rot*(rotations+1)
        ang = angle/point_num

        co = [0, 1*self.scale]
        self.fan_points.clear()
        self.fan_tris.clear()
        self.fan_points.append(Vector((0, 0, 0)))
        for i in range(point_num+1):
            new_co = rotate_2d([0, 0], co, ang*i+start_ang).to_3d()
            new_co *= .01

            if self.axis == 0:
                eul = Euler((math.radians(90.0), 0.0,
                             math.radians(90.0)), 'XYZ')
                new_co.rotate(eul)
                self.fan_points.append(new_co)
            if self.axis == 1:
                eul = Euler((math.radians(90.0), 0.0, 0.0), 'XYZ')
                new_co.rotate(eul)
                self.fan_points.append(new_co)
            if self.axis == 2:
                self.fan_points.append(new_co)

            if i < point_num:
                self.fan_tris.append([0, i+1, i+2])

        self.fan_lines.clear()
        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[1])
        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[-1])

        self.mat_fan_points.clear()
        for p in range(len(self.fan_points)):
            self.mat_fan_points.append(matrix @ (self.fan_points[p]*scale_fac))

        self.mat_fan_lines.clear()
        for p in range(len(self.fan_lines)):
            self.mat_fan_lines.append(matrix @ (self.fan_lines[p]*scale_fac))

        self.batch_fan = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_fan_points}, indices=self.fan_tris)
        self.batch_fan_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": self.mat_fan_lines})

        return

    def draw(self):
        if self.active:
            bgl.glDepthRange(0, 0.01)

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

            bgl.glDepthRange(0, 1.0)

        return

    def set_scale(self, scale):
        self.scale = scale
        return
