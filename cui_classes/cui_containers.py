import bgl
from .cui_shapes import *
from .cui_bezier_box import *
from .cui_items import *

#
#
#


class CUIContainer(CUIRectWidget):
    def __init__(self):
        super().__init__()

        self.horizontal_margin = 0
        self.vertical_margin = 0

        self.draw_backdrop = True
        return

    #

    def draw(self, color_override=None):
        if self.draw_backdrop:
            if color_override:
                super().draw(color_override)
            else:
                super().draw()

    #

    def set_margins(self, horizontal=None, vertical=None):
        if horizontal != None:
            self.horizontal_margin = horizontal
        if vertical != None:
            self.vertical_margin = vertical
        return

    #

    def __str__(self):
        return 'CUI Container'


class CUIBoxContainer(CUIContainer):
    def __init__(self):
        super().__init__()

        self.containers = []

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_box = (0.0, 0.0, 0.2, 1.0)
        self.color_row = (0.0, 0.0, 0.25, 1.0)
        self.color_item = (0.0, 0.0, 0.3, 0.7)
        self.color_hover = (0.0, 0.0, 0.5, 0.7)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.scroll_offset = 0
        self.scrolling = False
        self.scroll_bar_size = 14
        self.scroll_max_dist = 0
        self.scroll_max_move = 0
        self.scroll_bar = None
        self.scroll_click = False
        self.scroll_prev_mouse = [0, 0]

        self.horizontal_margin = 4
        self.vertical_margin = 4

        self.collapse = False
        self.header_box = None
        self.header = None

        self.type = 'BOX'

        self.container_separation = 4
        return

    #

    def create_shape_data(self):
        total_height = 0
        total_height += self.vertical_margin

        for c, cont in enumerate(self.containers):
            cont.width = self.width - self.horizontal_margin*2
            cont.create_shape_data()
            cont.pos_offset[0] = self.horizontal_margin
            cont.pos_offset[1] = -total_height

            if self.header:
                if len(self.header.shapes) > 0:
                    height = self.header.height
                    arrow_size = height*0.333
                    if self.collapse:
                        self.header.shapes[0].set_base_points([[arrow_size*0.5, -height/2+arrow_size/2], [
                                                              arrow_size*1.5, -height/2], [arrow_size*0.5, -height/2-arrow_size/2]])
                    else:
                        self.header.shapes[0].set_base_points([[arrow_size*0.5, -height/2+arrow_size/2], [
                                                              arrow_size*1.5, -height/2+arrow_size/2], [arrow_size, -height/2-arrow_size/2]])

                self.header_box.width = self.width - self.horizontal_margin*2
                self.header_box.create_shape_data()

            total_height += cont.height

            if c < len(self.containers)-1:
                total_height += self.container_separation

        max_height = None
        if self.max_height != None and self.type == 'PANEL':
            max_height = self.max_height/self.scale

        if max_height != None:
            if total_height > max_height:
                self.scrolling = True
            else:
                self.scrolling = False
                self.scroll_offset = 0

        total_height += self.vertical_margin
        self.height = total_height

        if self.scrolling and self.type == 'PANEL':
            self.scroll_max_dist = self.height - max_height
            if self.scroll_offset > self.scroll_max_dist:
                self.scroll_offset = self.scroll_max_dist

            for cont in self.containers:
                cont.resize_width(
                    self.width-self.horizontal_margin*2-self.scroll_bar_size-4, 0.0)
                cont.create_shape_data()
                cont.set_scale(self.scale)

            self.scroll_bar = CUIButton(
                max_height*(max_height/self.height), '')
            self.scroll_bar.width = self.scroll_bar_size

            self.scroll_bar.set_color(color=self.color_item, color_hover=self.color_hover,
                                      color_click=self.color_click, color_font=self.color_font)

            self.scroll_bar.pos_offset[0] = self.width - \
                self.scroll_bar_size - self.horizontal_margin
            self.scroll_bar.pos_offset[1] = -self.vertical_margin

            self.scroll_max_move = max_height - \
                self.vertical_margin*2 - self.scroll_bar.height
            self.scroll_bar.create_shape_data()

        if self.collapse:
            self.height = self.vertical_margin*2
            if self.header:
                self.height += self.header_box.height

            if self.scrolling and self.type == 'PANEL':
                self.scroll_bar.height = self.height - self.vertical_margin * 2
                self.scroll_bar.create_shape_data()

        super().create_shape_data()
        return

    def update_batches(self, position=[0, 0]):
        super().update_batches(position)
        pos = [position[0]+self.scale_pos_offset[0],
               position[1]+self.scale_pos_offset[1]]
        if self.scroll_bar:
            scroll_offset = int(
                (self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist)) * self.scale)
            self.scroll_bar.update_batches([pos[0], pos[1]-scroll_offset])

        for cont in self.containers:
            cont.update_batches(
                [pos[0], pos[1]+self.scroll_offset * self.scale])
        return

    def draw(self, position=[0, 0]):
        if self.visible:
            super().draw()
            if self.scroll_bar and self.scrolling:
                self.scroll_bar.draw()

            if self.scrolling and self.type == 'PANEL':
                # cur_scissor = None
                # if bgl.glIsEnabled(bgl.GL_SCISSOR_TEST) == 1:
                #     cur_scissor = bgl.Buffer(bgl.GL_INT, 4)
                #     bgl.glGetIntegerv(bgl.GL_SCISSOR_BOX, cur_scissor)
                #     bgl.glDisable(bgl.GL_SCISSOR_TEST)

                pos = [position[0]+self.scale_pos_offset[0],
                       position[1]+self.scale_pos_offset[1]]
                clip_pos = [pos[0]+self.horizontal_margin,
                            pos[1]-self.vertical_margin]

                offset = 0
                # if pos[1]+self.scroll_offset > position[1]:
                #     offset = pos[1]+self.scroll_offset-position[1]

                bgl.glEnable(bgl.GL_SCISSOR_TEST)
                bgl.glScissor(
                    round(pos[0]+self.horizontal_margin*self.scale),
                    round(pos[1]-self.height*self.scale +
                          self.vertical_margin*self.scale),
                    round((self.width-self.horizontal_margin*2)*self.scale),
                    round((self.height-self.vertical_margin*2-offset)*self.scale)
                )

            for cont in self.containers:
                if self.collapse == False or cont == self.header_box:
                    cont.draw()

            if self.scrolling and self.type == 'PANEL':
                bgl.glDisable(bgl.GL_SCISSOR_TEST)
                # if cur_scissor:
                #     bgl.glEnable(bgl.GL_SCISSOR_TEST)
                #     bgl.glScissor(cur_scissor[0],cur_scissor[1],cur_scissor[2],cur_scissor[3])
        return

    #

    def add_box(self, color=None):
        box = CUIBoxContainer()
        box.set_color(color=self.color_box,
                      color_outline=self.color_outline, color_font=self.color_font)
        box.set_style_color(color_box=self.color_box, color_row=self.color_row,
                            color_item=self.color_item, color_hover=self.color_hover, color_click=self.color_click)
        if color:
            box.set_color(color=color)
        box.width = self.width - self.horizontal_margin*2
        self.containers.append(box)
        return box

    def add_header(self, collapsable, header_text, height, use_backdrop, hor_marg=4, vert_marg=4, backdrop_color=None, button_color=None):
        box = CUIBoxContainer()
        box.set_color(color=self.color_box,
                      color_outline=self.color_outline, color_font=self.color_font)
        box.set_style_color(color_box=self.color_box, color_row=self.color_row,
                            color_item=self.color_item, color_hover=self.color_hover, color_click=self.color_click)
        if backdrop_color:
            box.set_color(color=backdrop_color)
        box.width = self.width - self.horizontal_margin*2

        box.horizontal_margin = hor_marg
        box.vertical_margin = vert_marg
        box.draw_backdrop = use_backdrop

        row = CUIRowContainer()
        row.width = box.width - box.horizontal_margin*2
        row.set_color(color=self.color_row,
                      color_outline=self.color_outline, color_font=self.color_font)
        row.set_style_color(color_item=self.color_item,
                            color_hover=self.color_hover, color_click=self.color_click)

        header = CUIButton(height, header_text)
        header.set_color(color=self.color_item, color_hover=self.color_hover,
                         color_click=self.color_click, color_font=self.color_font)
        if button_color:
            header.set_color(color=button_color)

        if collapsable:
            header.set_click_up_func(self.toggle_collapse)

            arrow_size = height*0.333
            poly = header.add_poly_shape([[arrow_size/2, -height/2+arrow_size/2],
                                          [arrow_size*1.5, -height/2], [arrow_size/2, -height/2-arrow_size/2]])
            poly.set_color(color=[0.0, 0.0, 0.9, 1.0])

        row.items.append(header)
        box.containers.append(row)
        self.header_box = box
        self.header = header

        self.containers.insert(0, box)
        return

    def add_text_row(self, height, text, font_size=10):
        row = CUIRowContainer()
        row.width = self.width - self.horizontal_margin*2

        row.set_color(color=self.color_row,
                      color_outline=self.color_outline, color_font=self.color_font)
        row.set_style_color(color_item=self.color_item,
                            color_hover=self.color_hover, color_click=self.color_click)

        label = row.add_label(height, text)
        label.set_font_size(font_size)

        self.containers.append(row)
        return row

    def add_row(self):
        row = CUIRowContainer()
        row.width = self.width - self.horizontal_margin*2
        row.set_color(color=self.color_row,
                      color_outline=self.color_outline, color_font=self.color_font)
        row.set_style_color(color_item=self.color_item,
                            color_hover=self.color_hover, color_click=self.color_click)
        self.containers.append(row)
        return row

    #

    def test_click_down(self, mouse_co, shift, pos, arguments=None):
        status = None
        if self.hover:
            if self.scroll_bar and self.scrolling:
                if self.scroll_bar.hover:
                    scroll_offset = int(
                        self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist))
                    self.scroll_click = True
                    self.scroll_prev_mouse = mouse_co
                    status = ['BOX_SCROLL', None]

            for cont in self.containers:
                if cont.hover:
                    status = cont.test_click_down(mouse_co, shift, [
                        pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if self.header and self.header_box == cont:
                        if self.header_box.hover:
                            if self.type == 'PANEL':
                                status = ['PANEL_HEADER', None]
                            else:
                                status = ['BOX_HEADER', None]

            if status == None:
                status = ['PANEL', None]

        return status

    def test_click_up(self, mouse_co, shift, pos, arguments=None):
        status = None
        if self.hover:
            if self.scroll_bar and self.scrolling:
                if self.scroll_bar.hover:
                    scroll_offset = int(
                        self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist))
                    self.scroll_click = False
                    self.scroll_prev_mouse = [0, 0]
                    status = ['BOX_SCROLL', None]

            for cont in self.containers:
                if cont.hover:
                    status = cont.test_click_up(mouse_co, shift, [
                        pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if self.header and self.header_box == cont:
                        if self.header_box.hover:
                            if self.type == 'PANEL':
                                status = ['PANEL_HEADER', None]
                            else:
                                status = ['BOX_HEADER', None]

            if status == None:
                status = ['PANEL', None]
        return status

    def click_down_move(self, mouse_co, shift, pos, arguments=None):
        if self.hover:
            test_containers = True
            if self.scroll_bar and self.scrolling:
                if self.scroll_bar.hover and self.scroll_click:
                    test_containers = False

                    scroll_offset = int(
                        self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist))
                    fac = self.scroll_max_dist/self.scroll_max_move
                    offset = int(
                        (self.scroll_prev_mouse[1] - mouse_co[1]) * fac)
                    new_offset = int(
                        self.scroll_max_move*((self.scroll_offset+offset)/self.scroll_max_dist))

                    if abs(new_offset-scroll_offset) > 0:
                        self.scroll_box(offset)
                        self.update_batches()
                        self.scroll_prev_mouse = mouse_co

            if test_containers:
                for cont in self.containers:
                    cont.click_down_move(mouse_co, shift, [
                                         pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
        return

    #

    def toggle_collapse(self, modal, arguments=None):
        self.collapse = not self.collapse
        self.scroll_offset = 0
        return

    def test_hover(self, mouse_co, pos):
        self.clear_hover()
        status = None
        if self.visible:
            super().test_hover(mouse_co, [pos[0], pos[1]])
            if self.hover:
                position = [pos[0]+self.scale_pos_offset[0],
                            pos[1]+self.scale_pos_offset[1]]
                status = 'PANEL'
                if self.scroll_bar and self.scrolling:
                    scroll_offset = int(
                        (self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist)) * self.scale)
                    self.scroll_bar.test_hover(
                        mouse_co, [position[0], position[1]-scroll_offset])
                    if self.scroll_bar.hover:
                        return 'PANEL_SCROLL'

                test_containers = False
                if self.scrolling and self.type == 'PANEL':
                    clip_pos = [position[0]+self.horizontal_margin *
                                self.scale, position[1]-self.vertical_margin*self.scale]
                    if clip_pos[0] < mouse_co[0] < clip_pos[0]+(self.width-self.horizontal_margin*2)*self.scale:
                        if clip_pos[1] > mouse_co[1] > clip_pos[1]-(self.height+self.vertical_margin*2)*self.scale:
                            test_containers = True
                else:
                    test_containers = True

                if test_containers:
                    for cont in self.containers:
                        c_status = cont.test_hover(
                            mouse_co, [position[0], position[1]+self.scroll_offset * self.scale])
                        if c_status:
                            if self.header and self.header_box == cont and self.header.hover:
                                status = 'PANEL_HEADER'
                            else:
                                status = c_status

        return status

    def resize_width(self, width, move_fac):
        prev_width = self.width*self.scale
        self.width = width
        if self.min_width != None:
            if self.width < self.min_width:
                self.width = self.min_width

        if self.max_width != None:
            if self.width > self.max_width:
                self.width = self.max_width

        if self.type == 'PANEL':
            self.set_new_position(
                [self.position[0] + (self.width*self.scale - prev_width)*move_fac, self.position[1]])

        for cont in self.containers:
            cont.resize_width(self.width-self.horizontal_margin*2, move_fac)

        return

    def scroll_box(self, value):
        self.scroll_offset += value
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        elif self.scroll_offset > self.scroll_max_dist and self.collapse == False:
            self.scroll_offset = self.scroll_max_dist
        elif self.scroll_offset > 0 and self.collapse:
            self.scroll_offset = 0
        return

    #

    def remove_container(self, index):
        if index < len(self.containers):
            self.containers.pop(index)
        return

    def clear_rows(self):
        self.containers.clear()
        return

    def reset_item_states(self, clear_hover):
        for cont in self.containers:
            cont.reset_item_states(clear_hover)
        return

    def filter_change_custom_id(self, tar_id, new_id):
        for cont in self.containers:
            cont.filter_change_custom_id(tar_id, new_id)
        return

    def clear_hover(self):
        self.hover = False
        if self.scroll_bar:
            self.scroll_bar.clear_hover()

        for cont in self.containers:
            cont.clear_hover()
        return

    #

    def type_add_key(self, key):
        for cont in self.containers:
            cont.type_add_key(key)
        return

    def type_delete_key(self):
        for cont in self.containers:
            cont.type_delete_key()
        return

    def type_move_pos(self, value):
        for cont in self.containers:
            cont.type_move_pos(value)
        return

    def type_confirm(self, arguments=None):
        for cont in self.containers:
            cont.type_confirm(arguments)
        return

    def type_cancel(self):
        for cont in self.containers:
            cont.type_cancel()
        return

    def type_backspace_key(self):
        for cont in self.containers:
            cont.type_backspace_key()
        return

    #

    def bezier_box_delete_points(self, pos, arguments=None):
        status = None
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    status, bez_id = cont.bezier_box_delete_points(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if status:
                        break
        return status, bez_id

    def bezier_box_sharpen_points(self, pos, offset, arguments=None):
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, bez_id, status = cont.bezier_box_sharpen_points(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], offset, arguments)
                    if status:
                        break
        return hov_status, bez_id, status

    def bezier_box_rotate_points(self, pos, angle, arguments=None):
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, bez_id, status, mid_co = cont.bezier_box_rotate_points(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], angle, arguments)
                    if status:
                        break
        return hov_status, bez_id, status, mid_co

    def bezier_box_clear_sharpness(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.bezier_box_clear_sharpness(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if status:
                        break
        return hov_status, status

    def bezier_box_clear_rotation(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.bezier_box_clear_rotation(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if status:
                        break
        return hov_status, status

    def bezier_box_reset_sharpness(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.bezier_box_reset_sharpness(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if status:
                        break
        return hov_status, status

    def bezier_box_reset_rotation(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.bezier_box_reset_rotation(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]+self.scroll_offset * self.scale], arguments)
                    if status:
                        break
        return hov_status, status

    def bezier_box_confirm_sharpness(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.bezier_box_confirm_sharpness()
                    if hov_status:
                        break
        return hov_status

    def bezier_box_confirm_rotation(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.bezier_box_confirm_rotation()
                    if hov_status:
                        break
        return hov_status

    def bezier_box_select_points(self, status):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.bezier_box_select_points(status)
                    break
        return hov_status

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        if self.scroll_bar:
            self.scroll_bar.set_scale(scale)

        for cont in self.containers:
            cont.set_scale(scale)
        return

    def set_header_bev(self, size, res):
        if self.header:
            self.header.set_bev(size, res)
        return

    def set_header_color(self, color=None, color_hover=None, color_click=None, color_font=None):
        if self.header:
            self.header.set_color(color=color, color_hover=color_hover,
                                  color_click=color_click, color_font=color_font)
        return

    def set_header_font_size(self, size):
        if self.header:
            self.header.set_font_size(size)
        return

    def set_separation(self, sep):
        self.container_separation = sep
        return

    def set_collapsed(self, status):
        self.collapse = status
        return

    def set_button_bool(self, status, custom_id_filter=None):
        for cont in self.containers:
            cont.set_button_bool(status, custom_id_filter)
        return

    def set_color(self, color=None, color_outline=None, color_font=None):
        if color_font:
            self.color_font = color_font
        super().set_color(color=color, color_outline=color_outline)
        return

    def set_style_color(self, color_box=None, color_row=None, color_item=None, color_hover=None, color_click=None):
        if color_box != None:
            self.color_box = color_box
        if color_row != None:
            self.color_row = color_row
        if color_item != None:
            self.color_item = color_item
        if color_hover != None:
            self.color_hover = color_hover
        if color_click != None:
            self.color_click = color_click
        return

    def set_header_icon_data(self, image=None, width=None, height=None, text_side=None):
        if self.header != None:
            self.header.set_icon_data(
                image=image, width=width, height=height, text_side=text_side)
        return

    #

    def __str__(self):
        return 'CUI Box Container'


class CUIRowContainer(CUIContainer):
    def __init__(self):
        super().__init__()

        self.items = []

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_item = (0.0, 0.0, 0.3, 0.7)
        self.color_hover = (0.0, 0.0, 0.5, 0.7)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.type = 'ROW'

        self.items_separations = 4
        self.draw_backdrop = False
        return

    #

    def create_shape_data(self):
        total_height = 0
        total_height += self.vertical_margin

        x_pos = 0
        x_pos += self.horizontal_margin

        highest = 0

        # calc width of buttons
        # if even divisions is bigger than max width then remove that from total and recongifure for non maxed items
        avail_width = self.width - self.horizontal_margin * \
            2 - self.items_separations*(len(self.items)-1)
        widths = []
        max_widths = 0
        rem_items = 0
        for i, item in enumerate(self.items):
            if item.item_type == 'BOOLEAN' and item.use_button == False:
                if avail_width/len(self.items) > item.parts[0].bool_box_size:
                    widths.append(item.parts[0].bool_box_size)
                    max_widths += item.parts[0].bool_box_size
                else:
                    widths.append(None)
                    rem_items += 1

            elif item.max_width != None:
                if avail_width/len(self.items) > item.max_width:
                    widths.append(item.max_width)
                    max_widths += item.max_width
                else:
                    widths.append(None)
                    rem_items += 1
            else:
                widths.append(None)
                rem_items += 1

        new_avail = avail_width - max_widths

        # place items in row
        for i, item in enumerate(self.items):
            if widths[i] != None:
                item.width = widths[i]
                # Not sure what this was here for but caused issues with max width button
                # x_pos += new_avail/2
            else:
                item.width = new_avail/rem_items

            item.pos_offset[0] = x_pos
            item.pos_offset[1] = -total_height
            item.create_shape_data()

            x_pos += item.width
            if i < len(self.items)-1:
                x_pos += self.items_separations

            if item.height > highest:
                highest = item.height

        if self.width-self.horizontal_margin > x_pos:
            for i, item in enumerate(self.items):
                item.pos_offset[0] += (self.width -
                                       self.horizontal_margin-x_pos)/2

        # check for items that have a smaller size than highest and replace in middle of row vertically
        for i, item in enumerate(self.items):
            if item.height < highest:
                offset = int((highest-item.height)/2)
                item.pos_offset[1] -= offset

        total_height += highest
        total_height += self.vertical_margin
        self.height = total_height

        super().create_shape_data()
        return

    def update_batches(self, position=[0, 0]):
        super().update_batches(position)
        for item in self.items:
            item.update_batches(
                [position[0]+self.scale_pos_offset[0], position[1]+self.scale_pos_offset[1]])
        return

    def draw(self):
        super().draw()
        if self.visible:
            for item in self.items:
                item.draw()
        return

    #

    def add_button(self, height, text):
        but = CUIButton(height, text)
        but.set_color(color=self.color_item, color_hover=self.color_hover,
                      color_click=self.color_click, color_font=self.color_font)
        self.items.append(but)
        return but

    def add_bool(self, height, text, default=False):
        boolean = CUIBoolProp(height, text, default_val=default)
        boolean.set_color(color=self.color_item, color_hover=self.color_hover,
                          color_click=self.color_click, color_font=self.color_font)
        self.items.append(boolean)
        return boolean

    def add_label(self, height, text):
        label = CUILabel(height, text)
        label.set_color(color=self.color_item, color_hover=self.color_hover,
                        color_click=self.color_click, color_font=self.color_font)
        self.items.append(label)
        return label

    def add_number(self, height, text, default, decimals, step, min, max):
        num = CUINumProp(height, text, default, decimals, step, min, max)
        num.set_color(color=self.color_item, color_hover=self.color_hover,
                      color_click=self.color_click, color_font=self.color_font)
        num.set_value(default)
        self.items.append(num)
        return num

    def add_bezier_box(self, height, type, points=None):
        use_default = False
        if points == None:
            use_default = True
        if points != None:
            if len(points) < 2:
                use_default = True

        if use_default:
            bez = CUIBezierBox(height, type, [(0, 1), (1, 0)])
        else:
            bez = CUIBezierBox(height, type, points)

        self.items.append(bez)
        return bez

    #

    def test_click_down(self, mouse_co, shift, pos, arguments=None):
        status = None
        if self.hover:
            for item in self.items:
                if item.hover:
                    item.click_down = True
                    status = item.click_down_func(mouse_co, shift, [
                        pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
        return status

    def test_click_up(self, mouse_co, shift, pos, arguments=None):
        status = None
        if self.hover:
            for item in self.items:
                if item.hover:
                    item.click_down = False
                    status = item.click_up_func(mouse_co, shift, [
                                                pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
        return status

    def click_down_move(self, mouse_co, shift, pos, arguments=None):
        if self.hover:
            for item in self.items:
                item.click_down_move(mouse_co, shift, [
                                     pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
        return

    #

    def resize_width(self, width, move_fac):
        self.width = width
        return

    def test_hover(self, mouse_co, pos):
        self.clear_hover()
        status = None
        super().test_hover(mouse_co, [pos[0], pos[1]])
        if self.hover:
            for item in self.items:
                i_status = item.test_hover(
                    mouse_co, [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]])
                if i_status:
                    status = i_status

        return status

    def filter_change_custom_id(self, tar_id, new_id):
        for item in self.items:
            if item.custom_id == tar_id:
                item.custom_id = new_id
        return

    #

    def clear_hover(self):
        self.hover = False
        for item in self.items:
            item.clear_hover()
        return

    def reset_item_states(self, clear_hover):
        for item in self.items:
            item.reset_item_states(clear_hover)
        return

    def remove_item(self, index):
        if index < len(self.items):
            self.items.pop(index)
        return

    #

    def type_add_key(self, key):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_add_key(key)
        return

    def type_delete_key(self):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_delete_key()
        return

    def type_move_pos(self, value):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_move_pos(value)
        return

    def type_confirm(self, arguments=None):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_confirm(arguments)
        return

    def type_cancel(self):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_cancel()
        return

    def type_backspace_key(self):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_backspace_key()
        return

    #

    def bezier_box_delete_points(self, pos, arguments=None):
        status = None
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    item.bezier_box_delete_points(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
                    status = True
                    bez_id = item.custom_id
                    break
        return status, bez_id

    def bezier_box_sharpen_points(self, pos, offset, arguments=None):
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    status = item.bezier_box_sharpen_points(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], offset, arguments)
                    hov_status = True
                    bez_id = item.custom_id
                    break
        return hov_status, bez_id, status

    def bezier_box_rotate_points(self, pos, angle, arguments=None):
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    status, mid_co = item.bezier_box_rotate_points(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], angle, arguments)
                    hov_status = True
                    bez_id = item.custom_id
                    break
        return hov_status, bez_id, status, mid_co

    def bezier_box_clear_sharpness(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    status = item.bezier_box_clear_sharpness(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
                    hov_status = True
                    break
        return hov_status, status

    def bezier_box_clear_rotation(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    status = item.bezier_box_clear_rotation(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
                    hov_status = True
                    break
        return hov_status, status

    def bezier_box_reset_sharpness(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    status = item.bezier_box_reset_sharpness(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
                    hov_status = True
                    break
        return hov_status, status

    def bezier_box_reset_rotation(self, pos, arguments=None):
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    status = item.bezier_box_reset_rotation(
                        [pos[0]+self.scale_pos_offset[0], pos[1]+self.scale_pos_offset[1]], arguments)
                    hov_status = True
                    break
        return hov_status, status

    def bezier_box_confirm_sharpness(self):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    item.bezier_box_confirm_sharpness()
                    hov_status = True
                    break
        return hov_status

    def bezier_box_confirm_rotation(self):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    item.bezier_box_confirm_rotation()
                    hov_status = True
                    break
        return hov_status

    def bezier_box_select_points(self, status):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'BEZIER_BOX':
                    item.bezier_box_select_points(status)
                    hov_status = True
                    break
        return hov_status

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        for item in self.items:
            item.set_scale(scale)
        return

    def set_button_bool(self, status, custom_id_filter=None):
        for item in self.items:
            if item.item_type == 'BUTTON':
                if custom_id_filter != None:
                    if item.custom_id == custom_id_filter:
                        item.set_bool(status)
                else:
                    item.set_bool(status)
        return

    def set_color(self, color=None, color_outline=None, color_font=None):
        if color_font:
            self.color_font = color_font
        super().set_color(color=color, color_outline=color_outline)
        return

    def set_style_color(self, color_item=None, color_hover=None, color_click=None):
        if color_item != None:
            self.color_item = color_item
        if color_hover != None:
            self.color_hover = color_hover
        if color_click != None:
            self.color_click = color_click
        return
    #

    def __str__(self):
        return 'CUI Row Container'
