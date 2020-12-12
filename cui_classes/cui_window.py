import bpy
from .cui_functions import *
from .cui_shapes import *
from .cui_containers import *
from .cui_items import *


#
#
#


class CUIWindowContainer:
    def __init__(self, modal, context, scale=1.0):
        self.modal = modal

        self.border = None
        self.panels = []
        self.gizmo_sets = []
        self.dimensions = [context.region.width, context.region.height]

        self.status_text = ''
        self.status_pos = [0, 0]
        self.status_size = 18
        self.status_font = 0
        self.color_status = (0.0, 0.8, 1.0, 1.0)
        self.color_status_render = hsv_to_rgb_list(self.color_status)

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_panel = (0.0, 0.0, 0.1, 0.7)
        self.color_box = (0.0, 0.0, 0.2, 1.0)
        self.color_row = (0.0, 0.0, 0.25, 1.0)
        self.color_item = (0.0, 0.0, 0.3, 0.7)
        self.color_hover = (0.0, 0.0, 0.5, 0.7)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.scale = scale
        return

    #

    def create_shape_data(self):
        if self.border:
            self.border.create_shape_data()

        for panel in self.panels:
            panel.create_shape_data()
        return

    def update_batches(self):
        if self.border:
            self.border.update_batches()

        for panel in self.panels:
            panel.update_batches()
        return

    def draw(self):

        for p in range(len(self.panels)):
            self.panels[(p*-1)-1].draw()

        if self.border:
            self.border.draw()

        self.status_draw()
        return

    def gizmo_draw(self):
        for i in range(len(self.gizmo_sets)):
            self.gizmo_sets[i*-1-1].draw()

    def status_draw(self):
        if self.status_text != '':
            blf.position(self.status_font,
                         self.status_pos[0], self.status_pos[1], 0)
            blf.color(
                self.status_font, self.color_status_render[0], self.color_status_render[1], self.color_status_render[2], self.color_status_render[3])
            blf.size(self.status_font, self.status_size, 72)
            blf.draw(self.status_font, self.status_text)

        return

    #

    def add_panel(self, pos, width):
        panel = CUIPanel(self.modal, pos, width)
        panel.set_style_color(color_box=self.color_box,
                              color_row=self.color_row,
                              color_item=self.color_item,
                              color_hover=self.color_hover,
                              color_click=self.color_click)
        panel.set_color(color=self.color_panel, color_font=self.color_font)

        self.panels.append(panel)
        return panel

    def add_popup(self, pos, width):
        panel = CUIPopup(self.modal, pos, width)
        panel.set_style_color(color_box=self.color_box,
                              color_row=self.color_row,
                              color_item=self.color_item,
                              color_hover=self.color_hover,
                              color_click=self.color_click)
        panel.set_color(color=self.color_panel, color_font=self.color_font)

        self.panels.append(panel)
        return panel

    def add_minimizable_panel(self, pos, width):
        panel = CUIMinimizablePanel(self.modal, pos, width)
        panel.set_style_color(color_box=self.color_box,
                              color_row=self.color_row,
                              color_item=self.color_item,
                              color_hover=self.color_hover,
                              color_click=self.color_click)
        panel.set_color(color=self.color_panel, color_font=self.color_font)

        self.panels.append(panel)
        return panel

    def add_border(self):
        border = CUIBorder(self.dimensions[0], self.dimensions[1])

        self.border = border
        return border

    #

    def check_dimensions(self, context):
        if self.border:
            self.border.check_dimensions(
                context.region.width, context.region.height)

        if context.region.width != self.dimensions[0] or context.region.height != self.dimensions[1]:
            fac_x = context.region.width/self.dimensions[0]
            fac_y = context.region.height/self.dimensions[1]
            for panel in self.panels:
                pos_x = panel.position[0]*fac_x
                pos_y = panel.position[1]*fac_y

                # if panel.max_height > context.region.height:
                #     panel.set_height_min_max(max= context.region.height-20)
                # if panel.max_width > context.region.width:
                #     panel.set_width_min_max(max= context.region.width-20)

                panel.set_new_position([pos_x, pos_y])

            self.dimensions = [context.region.width, context.region.height]

        return

    def check_in_window(self):
        for panel in self.panels:
            panel.check_in_window(self.dimensions)
        return

    def test_hover(self, mouse_co):
        status = None
        cursor_change = False

        giz_status = self.test_gizmo_hover(mouse_co)
        if giz_status == False:
            for panel in self.panels:
                if status:
                    panel.clear_hover()
                else:
                    panel_status = panel.test_hover(mouse_co)
                    if panel_status:
                        status = panel_status

                if panel.click_down == False:
                    if panel_status == 'PANEL_EDGE':
                        bpy.context.window.cursor_modal_set('MOVE_X')
                        cursor_change = True
                    else:
                        if panel_status == 'PANEL_HEADER' or panel_status == 'MINIMIZED':
                            bpy.context.window.cursor_modal_set('HAND')
                            cursor_change = True
        else:
            status = 'GIZMO'

        if status == None or cursor_change == False:
            bpy.context.window.cursor_modal_set('DEFAULT')
        return status

    def scroll_panel(self, value):
        status = None
        for panel in self.panels:
            if panel.hover and panel.scrolling:
                panel.scroll_box(value)
                panel.update_batches()
                status = 'PANEL_SCROLLED'
        return status

    #

    def click_down_move(self, mouse_co, shift=False, arguments=None):
        for panel in self.panels:
            if panel.hover:
                panel.click_down_move(
                    mouse_co, shift, arguments, window_dims=self.dimensions)
        return

    def test_click_down(self, mouse_co, shift, arguments=None):
        status = None
        giz_status = self.test_gizmo_click()
        if giz_status != None:
            status = giz_status
        else:
            for panel in self.panels:
                if panel.hover:
                    panel_status = panel.test_click_down(
                        mouse_co, shift, arguments)
                    if panel_status:
                        status = panel_status

        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        status = None
        for panel in self.panels:
            if panel.hover:
                panel_status = panel.test_click_up(mouse_co, shift, arguments)
                if panel_status:
                    status = panel_status
        return status

    #

    def type_add_key(self, key):
        for panel in self.panels:
            panel.type_add_key(key)
        return

    def type_delete_key(self):
        for panel in self.panels:
            panel.type_delete_key(key)
        return

    def type_move_pos(self, value):
        for panel in self.panels:
            panel.type_move_pos(key)
        return

    def type_confirm(self, arguments=None):
        for panel in self.panels:
            panel.type_confirm(arguments)
        return

    def type_cancel(self):
        for panel in self.panels:
            panel.type_cancel()
        return

    def type_backspace_key(self):
        for panel in self.panels:
            panel.type_backspace_key()
        return

    #

    def bezier_box_delete_points(self, arguments=None):
        status = None
        panel_id = None
        for panel in self.panels:
            if panel.hover:
                panel_status, panel_id = panel.bezier_box_delete_points(
                    arguments)
                if panel_status:
                    status = panel_status
        return status, panel_id

    def bezier_box_sharpen_points(self, offset, arguments=None):
        status = False
        hov_status = False
        bez_id = None
        for panel in self.panels:
            if panel.hover:
                hov_status, bez_id, panel_status = panel.bezier_box_sharpen_points(
                    offset, arguments)
                if panel_status:
                    status = panel_status
        return hov_status, bez_id, status

    def bezier_box_rotate_points(self, angle, arguments=None):
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        for panel in self.panels:
            if panel.hover:
                hov_status, bez_id, panel_status, mid_co = panel.bezier_box_rotate_points(
                    angle, arguments)
                if panel_status:
                    status = panel_status
        return hov_status, bez_id, status, mid_co

    def bezier_box_clear_sharpness(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_clear_sharpness(arguments)
        return hov_status

    def bezier_box_clear_rotation(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_clear_rotation(arguments)
        return hov_status

    def bezier_box_reset_sharpness(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_reset_sharpness(arguments)
        return hov_status

    def bezier_box_reset_rotation(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_reset_rotation(arguments)
        return hov_status

    def bezier_box_confirm_sharpness(self):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_confirm_sharpness()
        return hov_status

    def bezier_box_confirm_rotation(self):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_confirm_rotation()
        return hov_status

    def bezier_box_select_points(self, status):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.bezier_box_select_points(status)
        return hov_status

    #

    def add_rot_gizmo(self, mat, size, axis, thickness):
        gizmo_cont = UIGizmoContainer(
            len(self.gizmo_sets), mat, size, axis, self.scale)

        if axis[0]:
            giz = UIRotateGizmo(len(gizmo_cont.gizmos), size, self.scale, 0, 'ROT_X', [
                                0.8, 0.0, 0.0, 0.35], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[1]:
            giz = UIRotateGizmo(len(gizmo_cont.gizmos), size, self.scale, 1, 'ROT_Y', [
                                0.0, 0.8, 0.0, 0.35], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[2]:
            giz = UIRotateGizmo(len(gizmo_cont.gizmos), size, self.scale, 2, 'ROT_Z', [
                                0.0, 0.0, 0.8, 0.35], thickness)
            gizmo_cont.gizmos.append(giz)
        self.gizmo_sets.append(gizmo_cont)

        gizmo_cont.create_shape_data(mat)
        return gizmo_cont

    def add_scale_gizmo(self, mat, size, axis, thickness):
        gizmo_cont = UIGizmoContainer(
            len(gizmo_cont.gizmos), mat, size, axis, self.scale)

        if axis[0]:
            giz = UIRotateGizmo(len(gizmo_cont.gizmos), size, self.scale, 0, [
                                0.8, 0.0, 0.0, 0.5], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[1]:
            giz = UIRotateGizmo(len(gizmo_cont.gizmos), size, self.scale, 1, [
                                0.0, 0.8, 0.0, 0.5], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[2]:
            giz = UIRotateGizmo(len(gizmo_cont.gizmos), size, self.scale, 2, [
                                0.0, 0.0, 0.8, 0.5], thickness)
            gizmo_cont.gizmos.append(giz)
        self.gizmo_sets.append(gizmo_cont)

        gizmo_cont.create_shape_data(mat)
        return

    def update_gizmo_pos(self, matrix, ang=0):
        for giz_set in self.gizmo_sets:
            giz_set.update_position(matrix, ang=ang)
        return

    def update_gizmo_rot(self, ang, start_ang):
        for giz_set in self.gizmo_sets:
            giz_set.update_rot(ang, start_ang)
        return

    def update_gizmo_orientation(self, matrix):
        for giz_set in self.gizmo_sets:
            giz_set.update_orientation(matrix)
        return

    def test_gizmo_hover(self, mouse_co):
        for giz_set in self.gizmo_sets:
            giz_set.clear_hover()

            hov = giz_set.test_hover(mouse_co)
            if hov:
                return True
        return False

    def test_gizmo_click(self):
        for giz_set in self.gizmo_sets:
            for gizmo in giz_set.gizmos:
                if gizmo.hover and gizmo.active:
                    return ['GIZMO', [gizmo.type, giz_set.index, gizmo.index]]
        return None

    #

    def set_scale(self, scale):
        self.scale = scale

        for panel in self.panels:
            panel.set_scale(scale)

        for giz_set in self.gizmo_sets:
            giz_set.set_scale(scale)

        if self.border:
            self.border.set_scale(scale)
        return

    def set_style_color(self, color_panel=None, color_box=None, color_row=None, color_item=None, color_hover=None, color_click=None):
        if color_panel != None:
            self.color_panel = color_panel
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

    def set_status_color(self, color):
        self.color_status = color
        self.color_status_render = hsv_to_rgb_list(self.color_status)
        return

    def clear_status(self):
        self.status_text = ''
        return

    def set_status(self, text):
        self.status_text = text
        self.place_status_text()
        return

    def set_status_size(self, size):
        blf.size(self.status_font, self.status_size, 72)
        size = text_size_int(self.status_font, self.status_text)

        self.status_size = size * self.scale
        self.place_status_text()
        return

    def place_status_text(self):
        blf.size(self.status_font, self.status_size, 72)
        size = blf.dimensions(self.status_font, self.status_text)

        self.status_pos[0] = round(bpy.context.region.width/2 - size[0]/2)
        self.status_pos[1] = 15
        return

    #

    def __str__(self):
        return 'CUI Window Container'


#
#


class CUIPanel(CUIBoxContainer):
    def __init__(self, modal, position, width):
        super().__init__()
        self.alignment = 'TL'

        self.modal = modal

        self.width = width

        self.type = 'PANEL'

        self.pre_moving = False
        self.moving = False
        self.resizing = False
        self.resize_sel_width = 2
        self.resize_side = 0
        self.edge_hover = False

        self.click_down = False

        self.resizable = True
        self.movable = True

        self.prev_mouse = [0, 0]
        self.min_width = 100
        self.max_width = bpy.context.region.width - 20
        self.max_height = bpy.context.region.height - 20

        self.position = round_array(position)
        self.bounding_corner = round_array(position)

        self.scale_resize_sel_width = 2
        return

    #

    def create_shape_data(self):
        super().create_shape_data()

        # ALIGNMENT OFFSETS
        if 'L' in self.alignment:
            self.pos_offset[0] = 0
        elif 'R' in self.alignment:
            self.pos_offset[0] = -self.width
        elif 'C' in self.alignment:
            self.pos_offset[0] = -self.width/2

        if 'T' in self.alignment:
            self.pos_offset[1] = 0
        elif 'B' in self.alignment:
            self.pos_offset[1] = self.height

        self.bounding_corner = round_array(
            [self.position[0]+self.pos_offset[0], self.position[1]+self.pos_offset[1]])

        self.set_scale(self.scale)
        self.update_batches()
        return

    def update_batches(self):
        self.bounding_corner = round_array(
            [self.position[0]+self.scale_pos_offset[0], self.position[1]+self.scale_pos_offset[1]])

        super().update_batches(self.position)
        return

    def draw(self):
        super().draw(self.position)
        return

    #

    def test_click_down(self, mouse_co, shift, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        status = None
        self.click_down = True
        self.test_hover(mouse_co)
        super().reset_item_states(False)
        if self.hover:
            status = super().test_click_down(mouse_co, shift, self.position, arguments)
            if status:

                if status[0] == 'PANEL_HEADER' or status[0] == 'PANEL':
                    if self.edge_hover == False and self.movable:
                        self.prev_mouse = mouse_co
                        self.pre_moving = True

                if self.edge_hover and self.resizable:
                    center = self.position[0] + \
                        self.scale_pos_offset[0]+self.width/2

                    if mouse_co[0] < center:
                        self.resize_side = 0
                    else:
                        self.resize_side = 1

                    self.prev_mouse = mouse_co
                    self.resizing = True

        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        status = None
        self.click_down = False
        if self.moving:
            status = ['PANEL_MOVE', None]
            if self.header:
                self.header.click_down = False

        elif self.resizing:
            status = ['PANEL_RESIZE', None]

        else:
            status = super().test_click_up(mouse_co, shift, self.position, arguments)
            if status:
                if status[0] == 'BOX_HEADER' or status[0] == 'PANEL_HEADER':
                    self.create_shape_data()
                    self.update_batches()

        self.pre_moving = False
        self.moving = False
        self.resizing = False
        self.prev_mouse = [0, 0]
        return status

    def click_down_move(self, mouse_co, shift=False, arguments=None, window_dims=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        if self.pre_moving:
            offset_x = mouse_co[0]-self.prev_mouse[0]
            offset_y = mouse_co[1]-self.prev_mouse[1]

            if abs(offset_x) > 0 or abs(offset_y) > 0:
                self.moving = True
                self.pre_moving = False

        elif self.moving:
            offset_x = mouse_co[0]-self.prev_mouse[0]
            offset_y = mouse_co[1]-self.prev_mouse[1]

            if abs(offset_x) > 0 or abs(offset_y) > 0:
                self.set_new_position(
                    [self.position[0]+offset_x, self.position[1]+offset_y], window_dims, 0)
                self.prev_mouse = mouse_co

        elif self.resizing:
            offset_x = int((mouse_co[0]-self.prev_mouse[0]))

            if abs(offset_x) > 0:
                self.prev_mouse = mouse_co

                if self.resize_side == 0:
                    if 'L' in self.alignment:
                        self.resize_width(self.width - offset_x, -1.0)
                    elif 'R' in self.alignment:
                        self.resize_width(self.width - offset_x, 0.0)
                    else:
                        self.resize_width(self.width - offset_x, 0.0)
                else:
                    if 'L' in self.alignment:
                        self.resize_width(self.width + offset_x, 0.0)
                    elif 'R' in self.alignment:
                        self.resize_width(self.width + offset_x, 1.0)
                    else:
                        self.resize_width(self.width + offset_x, 0.0)

                self.create_shape_data()
                self.set_scale(self.scale)
                self.update_batches()

        else:
            if self.visible:
                super().click_down_move(mouse_co, shift, self.position, arguments)
        return

    def test_hover(self, mouse_co):
        self.clear_hover()
        status = super().test_hover(mouse_co, self.position)
        if self.hover:
            self.edge_hover = True

            pos = self.bounding_corner
            if pos[0]+self.scale_width-self.scale_resize_sel_width > mouse_co[0] > pos[0]+self.scale_resize_sel_width:
                if pos[1]-self.scale_height < mouse_co[1] < pos[1]:
                    self.edge_hover = False

            if self.edge_hover:
                status = 'PANEL_EDGE'

        return status

    def check_in_window(self, dimensions, padding=25):
        # if self.scale_width > dimensions[0]:
        #     self.scale_width = dimensions[0]-20
        # if self.scale_height > dimensions[1]:
        #     self.scale_height = dimensions[1]-20

        new_x = self.position[0]
        new_y = self.position[1]

        if self.bounding_corner[0]+self.scale_width > dimensions[0]:
            new_x = self.position[0] - (self.bounding_corner[0] +
                                        self.scale_width - dimensions[0] + padding)
        elif self.bounding_corner[0] < 0:
            new_x = self.position[0] - (self.bounding_corner[0] - padding)

        if self.bounding_corner[1]-self.scale_height < 0:
            new_y = self.position[1] - \
                (self.bounding_corner[1]-self.scale_height - padding)
        elif self.bounding_corner[1] > dimensions[1]:
            new_y = self.position[1] - \
                (self.bounding_corner[1]-dimensions[1] + padding)

        self.set_new_position([new_x, new_y])

        self.bounding_corner = round_array(
            [self.position[0]+self.scale_pos_offset[0], self.position[1]+self.scale_pos_offset[1]])
        return

    #

    def type_add_key(self, key):
        if self.visible and self.hover:
            super().type_add_key(key)
            self.update_batches()
        return

    def type_delete_key(self):
        if self.visible and self.hover:
            super().type_delete_key()
            self.update_batches()
        return

    def type_move_pos(self, value):
        if self.visible and self.hover:
            super().type_move_pos(value)
            self.update_batches()
        return

    def type_confirm(self, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        if self.visible and self.hover:
            super().type_confirm(arguments)
            self.update_batches()
        return

    def type_cancel(self):
        if self.visible and self.hover:
            super().type_cancel()
            self.update_batches()
        return

    def type_backspace_key(self):
        if self.visible and self.hover:
            super().type_backspace_key()
            self.update_batches()
        return

    #

    def bezier_box_delete_points(self, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        status = None
        bez_id = None
        if self.hover:
            status, bez_id = super().bezier_box_delete_points(self.position, arguments)
        return status, bez_id

    def bezier_box_sharpen_points(self, offset, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            hov_status, bez_id, status = super().bezier_box_sharpen_points(
                self.position, offset, arguments)
        return hov_status, bez_id, status

    def bezier_box_rotate_points(self, angle, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            hov_status, bez_id, status, mid_co = super(
            ).bezier_box_rotate_points(self.position, angle, arguments)
        return hov_status, bez_id, status, mid_co

    def bezier_box_clear_sharpness(self, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        hov_status = False
        if self.hover:
            hov_status, status = super().bezier_box_clear_sharpness(self.position, arguments)
        return hov_status

    def bezier_box_clear_rotation(self, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        hov_status = False
        if self.hover:
            hov_status, status = super().bezier_box_clear_rotation(self.position, arguments)
        return hov_status

    def bezier_box_reset_sharpness(self, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        hov_status = False
        if self.hover:
            hov_status, status = super().bezier_box_reset_sharpness(self.position, arguments)
        return hov_status

    def bezier_box_reset_rotation(self, arguments=None):
        if arguments != None:
            arguments.insert(0, self.modal)
        else:
            arguments = [self.modal]

        hov_status = False
        if self.hover:
            hov_status, status = super().bezier_box_reset_rotation(self.position, arguments)
        return hov_status

    def bezier_box_confirm_sharpness(self):
        hov_status = False
        if self.hover:
            hov_status = super().bezier_box_confirm_sharpness()
        return hov_status

    def bezier_box_confirm_rotation(self):
        hov_status = False
        if self.hover:
            hov_status = super().bezier_box_confirm_rotation()
        return hov_status

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        self.scale_resize_sel_width = self.resize_sel_width*scale

        return

    def set_horizontal_alignment(self, align):
        if 'B' in self.alignment:
            vert_align = 'B'
        if 'T' in self.alignment:
            vert_align = 'T'

        if align == 'LEFT':
            self.alignment = vert_align + 'L'
        if align == 'RIGHT':
            self.alignment = vert_align + 'R'
        if align == 'CENTER':
            self.alignment = vert_align + 'C'

    def set_vertical_alignment(self, align):
        if 'L' in self.alignment:
            hor_align = 'L'
        if 'C' in self.alignment:
            hor_align = 'C'
        if 'R' in self.alignment:
            hor_align = 'R'

        if align == 'TOP':
            self.alignment = 'T' + hor_align
        if align == 'BOT':
            self.alignment = 'B' + hor_align

    def set_new_position(self, pos, window_dims=None, padding=25):
        self.position = round_array(pos)
        self.bounding_corner = round_array(
            [self.position[0]+self.scale_pos_offset[0], self.position[1]+self.scale_pos_offset[1]])
        if window_dims:
            self.check_in_window(window_dims, padding)

        self.update_batches()
        return

    def set_visibility(self, vis):
        self.visible = vis
        return

    def set_movable(self, status):
        self.movable = status
        return

    def set_resizable(self, status):
        self.resizable = status
        return

    #

    def __str__(self):
        return 'CUI Panel'


class CUIPopup(CUIPanel):
    def __init__(self, modal, position, width):
        super().__init__(modal, position, width)

        self.close_on_click = True
        self.keep_open = False
        self.close_margin = 35

        self.scale_close_margin = 35
        return

    #

    def test_click_down(self, mouse_co, shift, arguments=None):
        status = super().test_click_down(mouse_co, shift, arguments)
        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        status = super().test_click_up(mouse_co, shift, arguments)
        if self.close_on_click:
            if status:
                if status[0] != 'PANEL_MOVE' and status[0] != 'PANEL_HEADER' and status[0] != 'PANEL_RESIZE':
                    self.visible = False
        return status

    def test_hover(self, mouse_co):
        self.clear_hover()
        status = None

        if self.visible:
            status = super().test_hover(mouse_co)
            if self.hover == False and self.keep_open == False:
                close_it = self.test_popup_close(mouse_co)
                if close_it:
                    return 'CLOSED'

        return status

    def test_popup_close(self, mouse_co):
        min_x = self.bounding_corner[0]-self.scale_close_margin
        max_x = self.bounding_corner[0]+self.width+self.scale_close_margin
        min_y = self.bounding_corner[1]-self.height-self.scale_close_margin
        max_y = self.bounding_corner[1]+self.scale_close_margin
        if mouse_co[0] < min_x or mouse_co[0] > max_x or mouse_co[1] < min_y or mouse_co[1] > max_y:
            self.set_visibility(False)
            self.reset_item_states(True)
            return True
        return False

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        self.scale_close_margin = self.close_margin*scale
        return

    def set_keep_open(self, status):
        self.keep_open = status
        return

    def set_close_on_click(self, status):
        self.close_on_click = status
        return

    def set_close_margin(self, margin):
        self.close_margin = margin
        return
    #

    def __str__(self):
        return 'CUI Popup'


class CUIMinimizablePanel(CUIPanel):
    def __init__(self, modal, position, width):
        super().__init__(modal, position, width)
        self.open_on_hover = False

        self.minimized_width = 35
        self.minimized_height = 35
        self.minimized_icon = None
        self.minimized = True

        self.minimized_button = CUIButton(self.minimized_height, '')
        self.minimized_button.set_color(color=self.color, color_hover=self.color_hover,
                                        color_click=self.color_click, color_font=self.color_font)

        self.minimized_button.set_click_up_func(self.toggle_minimize)

        w_offset = int(self.minimized_width*0.1)
        h_offset = int(self.minimized_height*0.1)
        thick = int((self.minimized_width+self.minimized_height)/2*.25)
        poly = self.minimized_button.add_poly_shape([
            [w_offset, -h_offset],
            [self.minimized_width-w_offset, -h_offset],
            [self.minimized_width-w_offset-thick, -h_offset-thick],
            [w_offset+thick, -h_offset-thick],
            [w_offset+thick, -self.minimized_height+h_offset+thick],
            [w_offset, -self.minimized_height+h_offset],
        ])
        poly.set_color(color=[0.0, 0.0, 0.1, 1.0])
        return

    #

    def create_shape_data(self):

        self.minimized_button.width = self.minimized_width
        self.minimized_button.height = self.minimized_height
        self.minimized_button.pos_offset = [0, 0]
        self.minimized_button.create_shape_data()
        self.minimized_button.set_scale(self.scale)

        super().create_shape_data()
        return

    def update_batches(self):
        super().update_batches()
        self.minimized_button.update_batches(self.position)
        return

    def draw(self):
        if self.visible:
            if self.minimized:
                self.minimized_button.draw()
            else:
                super().draw()
        return

    #

    def click_down_move(self, mouse_co, shift=False, arguments=None, window_dims=None):
        status = super().click_down_move(mouse_co, shift, arguments, window_dims)
        return

    def test_click_down(self, mouse_co, shift, arguments=None):
        status = super().test_click_down(mouse_co, shift, arguments)
        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        status = None
        if self.minimized:
            if self.minimized_button.hover:
                if self.moving == False:
                    status = self.minimized_button.click_up_func(
                        mouse_co, shift, self.position, arguments)

                self.click_down = False
                if self.header != None:
                    self.header.click_down = False
                self.moving = False
        else:
            status = super().test_click_up(mouse_co, shift, arguments)
        return status

    def test_hover(self, mouse_co):
        status = super().test_hover(mouse_co)
        if self.minimized and not self.open_on_hover:
            self.minimized_button.clear_hover()
            status = None
            self.minimized_button.test_hover(mouse_co, self.position)
            if self.minimized_button.hover:
                status = 'MINIMIZED'

        if self.open_on_hover:
            self.minimized = not self.hover
        return status

    def toggle_minimize(self, modal, arguments=None):
        self.minimized = not self.minimized
        return

    #

    def set_open_on_hover(self, status):
        self.open_on_hover = status
        return

    def set_minimized_data(self, height=None, width=None, icon=None):
        if height != None:
            self.minimized_width = height
        if width != None:
            self.minimized_height = width
        if icon != None:
            self.minimized_icon = icon
        return

    def set_minimized(self, status):
        self.minimized = status
        return

    #

    def __str__(self):
        return 'CUI Minimizable Panel'


#
#


class CUIBorder:
    def __init__(self, width, height):
        self.thickness = 4

        self.use_header = True

        self.header_width = 200
        self.header_height = 50
        self.header_bot_width = 150

        self.header_bev_size = 15
        self.header_bev_res = 5

        self.dimensions = [width, height]
        self.color = (0.0, 0.0, 0.5, 0.75)
        self.color_font = (0.0, 0.0, 1.0, 1.0)

        self.scale = 1.0

        self.parts = []
        box_l = CUIShapeWidget()
        box_l.set_color(self.color)
        self.parts.append(box_l)

        box_t = CUIShapeWidget()
        box_t.set_color(self.color)
        self.parts.append(box_t)

        box_r = CUIShapeWidget()
        box_r.set_color(self.color)
        self.parts.append(box_r)

        box_b = CUIShapeWidget()
        box_b.set_color(self.color)
        self.parts.append(box_b)

        header = CUIShapeWidget()
        header.set_color(self.color)
        self.header = header

        header_text = CUIItemWidget(self.header_height, '')
        header_text.width = self.header_width
        header_text.hover_highlight = False
        header_text.draw_box = False
        self.header_text = header_text

        self.scale_thickness = 4
        self.scale_header_width = 200
        self.scale_header_height = 50
        self.scale_header_bot_width = 150

        self.scale_header_bev_size = 15

        return

    #

    def create_shape_data(self):
        width = self.dimensions[0]
        height = self.dimensions[1]

        thick = self.scale_thickness

        self.parts[0].set_base_points(
            [[0, 0], [0, height], [thick, height-thick], [thick, thick]])
        self.parts[1].set_base_points([[0, height], [width, height], [
                                      width-thick, height-thick], [thick, height-thick]])
        self.parts[2].set_base_points(
            [[width-thick, height-thick], [width, height], [width, 0], [width-thick, thick]])
        self.parts[3].set_base_points(
            [[0, 0], [thick, thick], [width-thick, thick], [width, 0]])

        for part in self.parts:
            part.create_shape_data()

        if self.use_header:
            center = self.dimensions[0]/2
            width_half = self.scale_header_width/2
            bot_diff = (self.scale_header_width-self.scale_header_bot_width)/2

            self.header.set_base_points([
                [center-width_half, self.dimensions[1]-thick],
                [center+width_half, self.dimensions[1]-thick],
                [center+width_half-bot_diff, self.dimensions[1] -
                    thick-self.scale_header_height],
                [center-width_half+bot_diff, self.dimensions[1] -
                    thick-self.scale_header_height]
            ])

            self.header.set_bevel_data(
                inds=[2, 3], size=self.scale_header_bev_size, res=self.header_bev_res)
            self.header.create_shape_data()

            self.header_text.width = self.header_width
            self.header_text.height = self.header_height
            self.header_text.create_shape_data()
            self.header_text.pos_offset = [
                center-self.header_width/2, self.dimensions[1]-self.thickness]
            self.header_text.scale_pos_offset = [
                center-width_half, self.dimensions[1]-thick]

        self.update_batches()
        return

    def update_batches(self):
        self.header.update_batches([0, 0])
        for part in self.parts:
            part.update_batches([0, 0])
        self.header_text.update_batches([0, 0])

        return

    def draw(self):
        for part in self.parts:
            part.draw()

        if self.use_header:
            self.header.draw()
            self.header_text.draw()
        return

    #

    def check_dimensions(self, width, height):
        if width != self.dimensions[0] or height != self.dimensions[1]:
            self.dimensions = [width, height]
            self.set_scale(self.scale)
            self.create_shape_data()
        return
    #

    def set_scale(self, scale):
        self.scale = scale

        self.scale_thickness = self.thickness * scale
        self.scale_header_width = self.header_width * scale
        self.scale_header_height = self.header_height * scale
        self.scale_header_bot_width = self.header_bot_width * scale

        self.scale_header_bev_size = self.header_bev_size * scale

        self.header.set_scale(scale)
        self.header_text.set_scale(scale)
        for part in self.parts:
            part.set_scale(scale)
        return

    def set_use_header(self, status):
        self.use_header = status
        return

    def set_header_text(self, text):
        self.header_text.set_text(text)
        self.create_shape_data()
        return

    def set_header_font_size(self, size):
        self.header_text.font_size = size
        return

    def set_header_data(self, width=None, bot_width=None, height=None, bev_size=None, bev_res=None):
        if width != None:
            self.header_width = width
        if bot_width != None:
            self.header_bot_width = bot_width
        if height != None:
            self.header_height = height
        if bev_size != None:
            self.header_bev_size = bev_size
        if bev_res != None:
            self.header_bev_res = bev_res
        return

    def set_color(self, color=None, color_font=None):
        if color:
            self.color = color
            for part in self.parts:
                part.set_color(self.color)
            self.header.set_color(self.color)

        if color_font:
            self.color_font = color_font
        return

    #

    def __str__(self):
        return 'CUI Border'
