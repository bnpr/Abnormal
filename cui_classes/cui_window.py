import bpy
from .cui_functions import *
from .cui_shapes import *
from .cui_containers import *
from .cui_items import *

#
#
#


class CUIWindowContainer:
    #
    # The main container for all of the UI data
    #
    def __init__(self, modal, context, scale=1.0):
        self.modal = modal

        self.border = None
        self.panels = []
        self.gizmo_sets = []

        self.dimensions = [context.region.width, context.region.height]
        self.popup_mode = False

        self.status_text = ''
        self.status_pos = np.array([0.0, 0.0], dtype=np.float32)
        self.status_pos_offset = np.array([0.0, 0.0], dtype=np.float32)
        self.status_alignment = 'BL'
        self.status_size = 18
        self.status_font = 0
        self.color_status = (0.0, 1.0, 0.8, 1.0)
        self.color_status_render = hsv_to_rgb_list(self.color_status)

        self.key_text = ''
        self.key_pos = np.array([0.0, 0.0], dtype=np.float32)
        self.key_pos_offset = np.array([0.0, 0.0], dtype=np.float32)
        self.key_alignment = 'BR'
        self.key_size = 14
        self.key_font = 0
        self.color_key = (0.0, 0.0, 0.9, 1.0)
        self.color_key_render = hsv_to_rgb_list(self.color_key)

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_panel = (0.0, 0.0, 0.1, 0.7)
        self.color_box = (0.0, 0.0, 0.2, 1.0)
        self.color_row = (0.0, 0.0, 0.25, 1.0)
        self.color_item = (0.0, 0.0, 0.3, 0.7)
        self.color_hover = (0.0, 0.0, 0.5, 0.7)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.cont_darken_factor = 1.0

        self.tooltip_box = None

        self.vignette = None

        self.scale = scale
        return

    #

    def create_shape_data(self):
        if self.border:
            self.border.create_shape_data()

        for panel in self.panels:
            panel.create_shape_data()

        if self.tooltip_box is not None:
            self.tooltip_box.create_shape_data()
        return

    def update_batches(self):
        if self.border:
            self.border.update_batches()

        for panel in self.panels:
            panel.update_batches()

        if self.tooltip_box is not None:
            self.tooltip_box.update_batches()
        return

    #
    # DRAWING FUNCS
    #

    def draw(self):
        if self.vignette is not None:
            self.vignette.draw()

        for p in range(len(self.panels)):
            self.panels[(p*-1)-1].draw()

        if self.border:
            self.border.draw()

        self.status_draw()
        self.key_draw()
        if self.tooltip_box is not None:
            self.tooltip_box.draw()
        return

    def gizmo_draw(self):
        for i in range(len(self.gizmo_sets)):
            self.gizmo_sets[i*-1-1].draw()
        return

    def status_draw(self):
        if self.status_text != '':
            blf.position(self.status_font,
                         self.status_pos[0], self.status_pos[1], 0)
            blf.color(
                self.status_font, self.color_status_render[0], self.color_status_render[1], self.color_status_render[2], self.color_status_render[3])
            if bpy.app.version[0] >= 4:
                blf.size(self.status_font, self.status_size)
            else:
                blf.size(self.status_font, self.status_size, 72)
            blf.draw(self.status_font, self.status_text)

        return

    def key_draw(self):
        if self.key_text != '':
            blf.position(self.key_font,
                         self.key_pos[0], self.key_pos[1], 0)
            blf.color(
                self.key_font, self.color_key_render[0], self.color_key_render[1], self.color_key_render[2], self.color_key_render[3])
            if bpy.app.version[0] >= 4:
                blf.size(self.key_font, self.key_size)
            else:
                blf.size(self.key_font, self.key_size, 72)
            blf.draw(self.key_font, self.key_text)

        return

    #
    # ADD PANEL/BORDER FUNCS
    #

    def add_tooltip_box(self):
        self.tooltip_box = CUIToolTipBox(self.modal, [0.0, 0.0], 0.0)
        self.tooltip_box.set_horizontal_alignment('LEFT')
        self.tooltip_box.set_vertical_alignment('TOP')
        return self.tooltip_box

    def add_panel(self, position, width):
        pos = np.array([position[0], position[1]], dtype=np.float32)
        panel = CUIPanel(self.modal, pos, width)

        panel.set_style_color(
            color_box=self.color_box,
            color_row=self.color_row,
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        panel.set_color(
            color=self.color_panel,
            color_font=self.color_font
        )

        panel.set_cont_darken_factor(self.cont_darken_factor)

        self.panels.append(panel)
        return panel

    def add_popup(self, position, width):
        pos = np.array([position[0], position[1]], dtype=np.float32)
        panel = CUIPopup(self.modal, pos, width)

        panel.set_style_color(
            color_box=self.color_box,
            color_row=self.color_row,
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        panel.set_color(
            color=self.color_panel,
            color_font=self.color_font
        )

        panel.set_cont_darken_factor(self.cont_darken_factor)

        self.panels.append(panel)
        return panel

    def add_subpanel_popup(self, position, width):
        pos = np.array([position[0], position[1]], dtype=np.float32)
        panel = CUISubPanelPopup(self.modal, pos, width)

        panel.set_style_color(
            color_box=self.color_box,
            color_row=self.color_row,
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        panel.set_color(
            color=self.color_panel,
            color_font=self.color_font
        )

        panel.set_cont_darken_factor(self.cont_darken_factor)

        self.panels.append(panel)
        return panel

    def add_minimizable_panel(self, position, width):
        pos = np.array([position[0], position[1]], dtype=np.float32)
        panel = CUIMinimizablePanel(self.modal, pos, width)

        panel.set_style_color(
            color_box=self.color_box,
            color_row=self.color_row,
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        panel.set_color(
            color=self.color_panel,
            color_font=self.color_font
        )

        panel.set_cont_darken_factor(self.cont_darken_factor)

        self.panels.append(panel)
        return panel

    def add_border(self):
        border = CUIBorder(self.dimensions[0], self.dimensions[1])
        border.set_scale(self.scale)

        self.border = border
        return border

    def add_vignette(self):
        self.vignette = CUIItemWidget(self.dimensions[1], '')
        self.vignette.set_width(self.dimensions[0])
        self.vignette.text_margin = 0

        self.vignette.set_icon_image('CUI_Vignette.png', __file__)
        self.vignette.set_icon_data(
            width=self.dimensions[0], height=self.dimensions[1])
        self.vignette.create_shape_data()

        self.vignette.update_batches([0, self.dimensions[1]])
        return

    #

    def check_dimensions(self, context):
        #
        # Check if the dimensions of the draw area is still the same
        # If not recreate the border and reposition panels if out of the screen
        #
        if self.border:
            self.border.check_dimensions(
                context.region.width, context.region.height)

        if context.region.width != self.dimensions[0] or context.region.height != self.dimensions[1]:
            fac_x = context.region.width/self.dimensions[0]
            fac_y = context.region.height/self.dimensions[1]
            for panel in self.panels:
                new_pos = panel.position.copy()
                new_pos[0] *= fac_x
                new_pos[1] *= fac_y

                # if panel.max_height > context.region.height:
                #     panel.set_height_min_max(max= context.region.height-20)
                # if panel.max_width > context.region.width:
                #     panel.set_width_min_max(max= context.region.width-20)

                panel.set_new_position(new_pos)

            self.dimensions = [context.region.width, context.region.height]

            if self.vignette:
                self.vignette.set_width(self.dimensions[0])
                self.vignette.set_height(self.dimensions[1])
                self.vignette.set_icon_data(
                    width=self.dimensions[0], height=self.dimensions[1])
                self.vignette.create_shape_data()
                self.vignette.update_batches([0, self.dimensions[1]])

        return

    def check_in_window(self):
        #
        # Check for panels outside of the windows bounds and reposition
        #
        for panel in self.panels:
            panel.check_in_window(self.dimensions)
        return

    def scroll_panel(self, value):
        status = None
        for panel in self.panels:
            if panel.hover and panel.scrolling:
                panel.scroll_box(value)
                panel.update_batches()
                status = 'PANEL_SCROLLED'
        return status

    def tooltip_show(self, mouse_co):
        if self.tooltip_box != None:
            m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)

            lines = None
            for panel in self.panels:
                p_lines = panel.get_tooltip_lines()
                if p_lines is not None:
                    lines = p_lines

            if lines is not None and len(lines) > 0:
                self.tooltip_box.clear_rows()
                self.tooltip_box.set_visibility(True)

                width = self.tooltip_box.horizontal_margin*2
                height = self.tooltip_box.vertical_margin*2

                largest_width = 0.0

                # Test for max width of the text lines and the combined height of the text lines
                for line in lines:
                    label = self.tooltip_box.add_text_row(12,
                                                          line,
                                                          font_size=self.tooltip_box.font_size)
                    label.set_text_alignment('LEFT')

                if bpy.app.version[0] >= 4:
                    blf.size(self.tooltip_box.font_id,
                             self.tooltip_box.font_size)
                else:
                    blf.size(self.tooltip_box.font_id,
                             self.tooltip_box.font_size, 72)

                    size_w = blf.dimensions(self.tooltip_box.font_id, line)
                    size_h = blf.dimensions(self.tooltip_box.font_id, 'T')

                    if size_w[0] > largest_width:
                        largest_width = size_w[0]

                    height += size_h[1]
                    height += self.tooltip_box.container_separation

                width += largest_width
                height -= self.tooltip_box.container_separation

                width *= 1.1
                height *= 1.1

                self.tooltip_box.set_height(height)
                self.tooltip_box.set_width(width)

                self.tooltip_box.set_height_min_max(min=height)
                self.tooltip_box.set_width_min_max(min=width)

                self.tooltip_box.set_scale(self.scale)

                # Position tooltip box in window
                self.tooltip_box.create_shape_data()

                x_pos = m_co[0]-10
                y_pos = m_co[1]-15

                x_right = m_co[0] + self.tooltip_box.scale_width
                y_bot = m_co[1] - self.tooltip_box.scale_height

                if x_right > self.dimensions[0]:
                    x_pos -= ((x_right -
                              self.dimensions[0]) * (1/self.scale) + 10)

                if y_bot < 0.0:
                    y_pos += (-y_bot * (1/self.scale) + 10)

                pos = [x_pos, y_pos]

                self.tooltip_box.set_new_position(pos)
                self.tooltip_box.update_batches()

        return

    def tooltip_hide(self):
        if self.tooltip_box != None:
            self.tooltip_box.set_visibility(False)
        return

    #
    # CLICK INTERACTION FUNCS
    #

    def test_click_down(self, mouse_co, shift, arguments=None):
        #
        # Perform click down functions on the hovered panels
        #
        status = None
        m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)

        for panel in self.panels:
            if self.popup_mode and 'POPUP' not in panel.type:
                continue

            if panel.hover:
                panel_status = panel.test_click_down(
                    m_co, shift, arguments)
                if panel_status:
                    status = panel_status

        # No panel clicked so test gizmos for click
        if status == None:
            for g, giz_set in enumerate(self.gizmo_sets):
                for gg, gizmo in enumerate(giz_set.gizmos):
                    if gizmo.hover and gizmo.active:
                        status = ['GIZMO', [gizmo.type, g, gg]]

        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        #
        # Perform click up functionson the hovered panels
        #
        status = None
        m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)
        for panel in self.panels:
            if self.popup_mode and 'POPUP' not in panel.type:
                continue

            if panel.hover:
                panel_status = panel.test_click_up(
                    m_co, shift, arguments)
                if panel_status:
                    status = panel_status

        return status

    def click_down_move(self, mouse_co, shift=False, arguments=None):
        #
        # Perform click down movement functions on the hovered panels
        #
        m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)
        for panel in self.panels:
            if self.popup_mode and 'POPUP' not in panel.type:
                continue

            if panel.hover:
                panel.click_down_move(
                    m_co, shift, arguments, window_dims=self.dimensions)
        return

    def test_hover(self, mouse_co):
        #
        # Test which panels and items in those panels are being hovered
        # Returns a list with status for the user to respond accordingly
        #
        status = None
        cursor_change = False
        m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)

        for panel in self.panels:
            # If a panel already found or in popup_mode and panel is not a popup then skip it
            if status or (self.popup_mode and 'POPUP' not in panel.type):
                if panel.hover:
                    panel.clear_hover()
                panel_status = None
                continue

            else:
                panel_status = panel.test_hover(m_co)
                if panel_status:
                    status = panel_status

            # Change cursor for edge/header/minimized hover
            if panel.click_down == False:
                if panel_status == 'PANEL_EDGE':
                    cursor_change = True
                    bpy.context.window.cursor_modal_set('MOVE_X')
                else:
                    if panel_status == 'PANEL_HEADER' or panel_status == 'MINIMIZED':
                        cursor_change = True
                        bpy.context.window.cursor_modal_set('HAND')

        # No panel hovered so test any gizmos for hover
        if status is None:
            for giz_set in self.gizmo_sets:

                hov = giz_set.test_hover(mouse_co)
                if hov:
                    status = 'GIZMO'
                    break

                else:
                    if giz_set.hover:
                        giz_set.clear_hover()

        # Reset cursor
        if status == None or cursor_change == False:
            bpy.context.window.cursor_modal_set('DEFAULT')

        # Do a safety check if in popup mode for a popup panel that is visible
        # If not then return a closed status for user to break out of a potential lock
        if self.popup_mode:
            one_valid = False
            for panel in self.panels:
                if 'POPUP' in panel.type and panel.visible and panel.enabled:
                    one_valid = True
                    break

            if one_valid == False:
                status = 'CLOSED'
                self.popup_mode = False

        return status

    def clear_hover(self):
        for panel in self.panels:
            panel.clear_hover()

        for giz_set in self.gizmo_sets:
            giz_set.clear_hover()
        return

    #
    # NUMBER TYPING FUNCS
    #

    def type_add_key(self, key):
        for panel in self.panels:
            panel.type_add_key(key)
        return

    def type_delete_key(self):
        for panel in self.panels:
            panel.type_delete_key()
        return

    def type_move_pos(self, value):
        for panel in self.panels:
            panel.type_move_pos(value)
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
    # GRAPH BOX FUNCS
    #

    def graph_box_delete_points(self, arguments=None):
        status = None
        panel_id = None
        for panel in self.panels:
            if panel.hover:
                panel_status, panel_id = panel.graph_box_delete_points(
                    arguments)
                if panel_status:
                    status = panel_status
        return status, panel_id

    def graph_box_sharpen_points(self, offset, arguments=None):
        status = False
        hov_status = False
        bez_id = None
        for panel in self.panels:
            if panel.hover:
                hov_status, bez_id, panel_status = panel.graph_box_sharpen_points(
                    offset, arguments)
                if panel_status:
                    status = panel_status
        return hov_status, bez_id, status

    def graph_box_rotate_points(self, angle, arguments=None):
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        for panel in self.panels:
            if panel.hover:
                hov_status, bez_id, panel_status, mid_co = panel.graph_box_rotate_points(
                    angle, arguments)
                if panel_status:
                    status = panel_status
        return hov_status, bez_id, status, mid_co

    def graph_box_clear_sharpness(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_clear_sharpness(arguments)
        return hov_status

    def graph_box_clear_rotation(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_clear_rotation(arguments)
        return hov_status

    def graph_box_store_data(self, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_store_data(
                    arguments, coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
        return hov_status

    def graph_box_restore_stored_data(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_restore_stored_data(arguments)
        return hov_status

    def graph_box_clear_stored_data(self):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_clear_stored_data()
        return hov_status

    def graph_box_select_points(self, status):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_select_points(status)
        return hov_status

    def graph_box_pan(self, mouse_co, start=False):
        hov_status = False
        m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_pan(m_co, start=start)
        return hov_status

    def graph_box_zoom(self, mouse_co, factor):
        hov_status = False
        m_co = np.array([mouse_co[0], mouse_co[1]], dtype=np.float32)
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_zoom(m_co, factor)
        return hov_status

    def graph_box_home(self):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.graph_box_home()
        return hov_status

    #
    # GIZMOS
    #

    def add_rot_gizmo(self, mat, size, axis, thickness):
        gizmo_cont = CUIGizmo3DContainer(mat, size, self.scale)

        if axis[0]:
            giz = CUIRotateGizmo(size,
                                 self.scale,
                                 0,
                                 'ROT_X',
                                 [0.8, 0.0, 0.0, 0.35],
                                 thickness)
            gizmo_cont.gizmos.append(giz)

        if axis[1]:
            giz = CUIRotateGizmo(size,
                                 self.scale,
                                 1,
                                 'ROT_Y',
                                 [0.0, 0.8, 0.0, 0.35],
                                 thickness)
            gizmo_cont.gizmos.append(giz)

        if axis[2]:
            giz = CUIRotateGizmo(size,
                                 self.scale,
                                 2,
                                 'ROT_Z',
                                 [0.0, 0.0, 0.8, 0.35],
                                 thickness)
            gizmo_cont.gizmos.append(giz)

        self.gizmo_sets.append(gizmo_cont)

        gizmo_cont.create_shape_data(mat)
        return gizmo_cont

    def add_scale_gizmo(self, mat, size, axis, thickness):
        gizmo_cont = CUIGizmo3DContainer(mat, size, self.scale)

        if axis[0]:
            giz = CUIRotateGizmo(size,
                                 self.scale,
                                 0,
                                 [0.8, 0.0, 0.0, 0.5],
                                 thickness)
            gizmo_cont.gizmos.append(giz)

        if axis[1]:
            giz = CUIRotateGizmo(size,
                                 self.scale,
                                 1,
                                 [0.0, 0.8, 0.0, 0.5],
                                 thickness)
            gizmo_cont.gizmos.append(giz)

        if axis[2]:
            giz = CUIRotateGizmo(size,
                                 self.scale,
                                 2,
                                 [0.0, 0.0, 0.8, 0.5],
                                 thickness)
            gizmo_cont.gizmos.append(giz)

        self.gizmo_sets.append(gizmo_cont)

        gizmo_cont.create_shape_data(mat)
        return

    def update_gizmo_pos(self, matrix):
        for giz_set in self.gizmo_sets:
            giz_set.update_position(matrix)
        return

    def update_gizmo_rot(self, ang, start_ang):
        for giz_set in self.gizmo_sets:
            giz_set.update_rotation(ang, start_ang)
        return

    def update_gizmo_orientation(self, matrix):
        for giz_set in self.gizmo_sets:
            giz_set.update_orientation(matrix)
        return

    #
    # CURVE BOX FUNCS
    #

    def curve_box_delete_points(self, arguments=None):
        status = None
        panel_id = None
        for panel in self.panels:
            if panel.hover:
                panel_status, panel_id = panel.curve_box_delete_points(
                    arguments)
                if panel_status:
                    status = panel_status
        return status, panel_id

    def curve_box_sharpen_points(self, offset, arguments=None):
        status = False
        hov_status = False
        bez_id = None
        for panel in self.panels:
            if panel.hover:
                hov_status, bez_id, panel_status = panel.curve_box_sharpen_points(
                    offset, arguments)
                if panel_status:
                    status = panel_status
        return hov_status, bez_id, status

    def curve_box_rotate_points(self, angle, arguments=None):
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        for panel in self.panels:
            if panel.hover:
                hov_status, bez_id, panel_status, mid_co = panel.curve_box_rotate_points(
                    angle, arguments)
                if panel_status:
                    status = panel_status
        return hov_status, bez_id, status, mid_co

    def curve_box_clear_sharpness(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.curve_box_clear_sharpness(arguments)
        return hov_status

    def curve_box_clear_rotation(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.curve_box_clear_rotation(arguments)
        return hov_status

    def curve_box_store_data(self, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.curve_box_store_data(
                    arguments, coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
        return hov_status

    def curve_box_restore_stored_data(self, arguments=None):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.curve_box_restore_stored_data(arguments)
        return hov_status

    def curve_box_clear_stored_data(self):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.curve_box_clear_stored_data()
        return hov_status

    def curve_box_select_points(self, status):
        hov_status = False
        for panel in self.panels:
            if panel.hover:
                hov_status = panel.curve_box_select_points(status)
        return hov_status

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
        if color_panel is not None:
            self.color_panel = color_panel
        if color_box is not None:
            self.color_box = color_box
        if color_row is not None:
            self.color_row = color_row
        if color_item is not None:
            self.color_item = color_item
        if color_hover is not None:
            self.color_hover = color_hover
        if color_click is not None:
            self.color_click = color_click
        return

    def set_cont_darken_factor(self, factor):
        self.cont_darken_factor = factor
        for panel in self.panels:
            panel.set_cont_darken_factor(factor)
        return

    def set_popup_mode(self, status):
        self.popup_mode = status
        return

    #
    # SCREEN STATUS TEXT FUNCS
    #

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
        if bpy.app.version[0] >= 4:
            blf.size(self.status_font, self.status_size)
        else:
            blf.size(self.status_font, self.status_size, 72)
        size = blf.dimensions(self.status_font, self.status_text)

        self.status_size = size * self.scale
        self.place_status_text()
        return

    def set_status_offset(self, offset):
        self.status_pos_offset[:] = offset
        self.place_status_text()
        return

    def set_status_alignment(self, alignment):
        self.status_alignment = alignment
        return

    def place_status_text(self):
        if bpy.app.version[0] >= 4:
            blf.size(self.status_font, self.status_size)
        else:
            blf.size(self.status_font, self.status_size, 72)
        size = blf.dimensions(self.status_font, self.status_text)

        if 'T' in self.status_alignment:
            self.status_pos[1] = round(bpy.context.region.height - size[1])
            self.status_pos[1] -= self.status_pos_offset[1]
        if 'B' in self.status_alignment:
            self.status_pos[1] = 0
            self.status_pos[1] += self.status_pos_offset[1]
        if 'L' in self.status_alignment:
            self.status_pos[0] = 0
            self.status_pos[0] += self.status_pos_offset[0]
        if 'R' in self.status_alignment:
            self.status_pos[0] = round(bpy.context.region.width - size[0])
            self.status_pos[0] -= self.status_pos_offset[0]
        if 'C' in self.status_alignment:
            self.status_pos[0] = round(bpy.context.region.width/2 - size[0]/2)
            self.status_pos[0] -= self.status_pos_offset[0]

        return

    #

    def set_key_color(self, color):
        self.color_key = color
        self.color_key_render = hsv_to_rgb_list(self.color_key)
        return

    def clear_key(self):
        self.key_text = ''
        return

    def set_key(self, text):
        self.key_text = text
        self.place_key_text()
        return

    def set_key_size(self, size):
        if bpy.app.version[0] >= 4:
            blf.size(self.key_font, self.key_size)
        else:
            blf.size(self.key_font, self.key_size, 72)
        size = blf.dimensions(self.key_font, self.key_text)

        self.key_size = size * self.scale
        self.place_key_text()
        return

    def set_key_offset(self, offset):
        self.key_pos_offset[:] = offset
        self.place_key_text()
        return

    def set_key_alignment(self, alignment):
        self.key_alignment = alignment
        return

    def place_key_text(self):
        if bpy.app.version[0] >= 4:
            blf.size(self.key_font, self.key_size)
        else:
            blf.size(self.key_font, self.key_size, 72)
        size = blf.dimensions(self.key_font, self.key_text)

        if 'T' in self.key_alignment:
            self.key_pos[1] = round(bpy.context.region.height - size[1])
            self.key_pos[1] -= self.key_pos_offset[1]
        if 'B' in self.key_alignment:
            self.key_pos[1] = 0
            self.key_pos[1] += self.key_pos_offset[1]
        if 'L' in self.key_alignment:
            self.key_pos[0] = 0
            self.key_pos[0] += self.key_pos_offset[0]
        if 'R' in self.key_alignment:
            self.key_pos[0] = round(bpy.context.region.width - size[0])
            self.key_pos[0] -= self.key_pos_offset[0]
        if 'C' in self.key_alignment:
            self.key_pos[0] = round(bpy.context.region.width/2 - size[0]/2)
            self.key_pos[0] -= self.key_pos_offset[0]

        return

    #

    def __str__(self):
        return 'CUI Window Container'


#
#


class CUIPanel(CUIBoxContainer):
    #
    # Basic Panel which is persistent and on screen unless set invisible
    #
    def __init__(self, modal, position, width):
        super().__init__(modal)
        self.alignment = 'TL'

        self.set_width(width)

        self.type = 'PANEL'

        self.pre_moving = False
        self.moving = False
        self.resizing = False
        self.resize_sel_width = 6
        self.resize_side = 0
        self.edge_hover = False

        self.click_down = False

        self.resizable = True
        self.movable = True

        self.prev_mouse = np.array([0.0, 0.0], dtype=np.float32)
        self.min_width = 100
        self.max_width = bpy.context.region.width - 20
        self.max_height = bpy.context.region.height - 20

        pos = np.array(position, dtype=np.float32)
        self.position = np.round(pos)
        self.bounding_corner = np.round(pos)

        self.scale_resize_sel_width = 6
        return

    #

    def create_shape_data(self):
        # Create the overall panel shape unscaled and in neutral positions
        # The shapes height is a result of all the subpanels and items added width is set by the user
        super().create_shape_data()

        # Horizontal offsets based on alignment
        if 'L' in self.alignment:
            self.set_pos_offset_x(0)
        elif 'R' in self.alignment:
            self.set_pos_offset_x(-self.width)
        elif 'C' in self.alignment:
            self.set_pos_offset_x(-self.width/2)

        # Vertical offsets based on alignment
        if 'T' in self.alignment:
            self.set_pos_offset_y(0)
        elif 'B' in self.alignment:
            self.set_pos_offset_y(self.height)

        # Set the scale and position the batches
        self.set_scale(self.scale)
        self.update_batches()
        return

    def update_batches(self):
        # Set anchor point for panel based on alignment
        self.bounding_corner = np.round(self.position+self.scale_pos_offset)

        super().update_batches(self.position)
        return

    #

    def draw(self):
        super().draw()
        return

    #

    def test_click_down(self, mouse_co, shift, arguments=None):
        status = None
        self.click_down = True
        self.test_hover(mouse_co)
        super().reset_item_states(False)
        if self.hover:
            status = super().test_click_down(
                mouse_co, shift, self.position, arguments)
            if status:
                # if we are on a panel header or the base panel and
                # edge is not hovered and panel is movable
                # set data for moving
                if status[0] == 'PANEL_HEADER' or status[0] == 'PANEL':
                    if self.edge_hover == False and self.movable:
                        self.prev_mouse[:] = mouse_co
                        self.pre_moving = True

                # If on the edge and the panel is resizble then find which side we are on
                # and set data for resizing
                if self.edge_hover and self.resizable:
                    center = self.position[0] + \
                        self.scale_pos_offset[0]+self.width/2

                    if mouse_co[0] < center:
                        self.resize_side = 0
                    else:
                        self.resize_side = 1

                    self.prev_mouse[:] = mouse_co
                    self.resizing = True

        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        status = None
        self.click_down = False

        # Set the status based on what the click was doing moving, resizing, or clicking
        if self.moving:
            status = ['PANEL_MOVE', None]
            # Unset click down on a header
            if self.header:
                self.header.click_down = False

        elif self.resizing:
            status = ['PANEL_RESIZE', None]

        # Test the click up function and if on the header recreate shape data as it may have collapsed
        else:
            status = super().test_click_up(mouse_co, shift, self.position, arguments)
            if status:
                if status[0] == 'BOX_HEADER' or status[0] == 'PANEL_HEADER':
                    self.create_shape_data()
                    self.update_batches()

        self.pre_moving = False
        self.moving = False
        self.resizing = False
        self.prev_mouse = np.array([0.0, 0.0], dtype=np.float32)
        return status

    def click_down_move(self, mouse_co, shift=False, arguments=None, window_dims=None):
        # Not yet moving so test if we have moved more than a pixel to start a move
        if self.pre_moving:
            offset = mouse_co-self.prev_mouse

            if abs(offset[0]) > 0 or abs(offset[1]) > 0:
                self.moving = True
                self.pre_moving = False

        # We are moving so set new position
        elif self.moving:
            offset = mouse_co-self.prev_mouse

            if abs(offset[0]) > 0 or abs(offset[1]) > 0:
                self.set_new_position(self.position + offset, window_dims, 0)
                self.prev_mouse[:] = mouse_co

        # We are resizing so resize accordingly and update shape data
        elif self.resizing:
            offset = mouse_co-self.prev_mouse

            if abs(int(offset[0])) > 0:
                self.prev_mouse[:] = mouse_co

                if self.resize_side == 0:
                    if 'L' in self.alignment:
                        self.resize_width(self.width - offset[0], -1.0)
                    elif 'R' in self.alignment:
                        self.resize_width(self.width - offset[0], 0.0)
                    else:
                        self.resize_width(self.width - offset[0]*2, 0.0)
                else:
                    if 'L' in self.alignment:
                        self.resize_width(self.width + offset[0], 0.0)
                    elif 'R' in self.alignment:
                        self.resize_width(self.width + offset[0], 1.0)
                    else:
                        self.resize_width(self.width + offset[0]*2, 0.0)

                self.create_shape_data()
                self.set_scale(self.scale)
                self.update_batches()

        # Else do the click down move function
        else:
            if self.visible:
                super().click_down_move(mouse_co, shift, self.position, arguments)
        return

    def test_hover(self, mouse_co):
        prev_hov = self.hover

        status = super().test_hover(mouse_co, self.position)
        if self.hover:
            self.edge_hover = True

            # Test if hover is on the edge of the panel for resizing
            pos = self.bounding_corner
            if pos[0]+self.scale_width-self.scale_resize_sel_width > mouse_co[0] > pos[0]+self.scale_resize_sel_width:
                if pos[1]-self.scale_height < mouse_co[1] < pos[1]:
                    self.edge_hover = False

            if self.edge_hover:
                status = 'PANEL_EDGE'

        else:
            if self.hover != prev_hov:
                self.clear_hover()

        return status

    #

    def check_in_window(self, dimensions, padding=25):
        #
        # Check if panel is inside of the draw area window
        # Reposition accordingly if it is not
        #
        # if self.scale_width > dimensions[0]:
        #     self.scale_width = dimensions[0]-20
        # if self.scale_height > dimensions[1]:
        #     self.scale_height = dimensions[1]-20

        new_pos = self.position.copy()

        if self.scale_width < dimensions[0]:
            if self.bounding_corner[0] < 0:
                new_pos[0] -= self.bounding_corner[0] - padding
            elif self.bounding_corner[0]+self.scale_width > dimensions[0]:
                new_pos[0] -= self.bounding_corner[0] + \
                    self.scale_width - dimensions[0] + padding

        if self.scale_height < dimensions[1]:
            if self.bounding_corner[1] > dimensions[1]:
                new_pos[1] -= self.bounding_corner[1] - dimensions[1] + padding
            elif self.bounding_corner[1]-self.scale_height < 0:
                new_pos[1] -= self.bounding_corner[1] - \
                    self.scale_height - padding

        self.set_new_position(new_pos)
        return

    #
    # TYPING FUNCS
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
    # CURVE BOX FUNCS
    #

    def curve_box_delete_points(self, arguments=None):
        status = None
        bez_id = None
        if self.hover:
            status, bez_id = super().curve_box_delete_points(self.position, arguments)
        return status, bez_id

    def curve_box_sharpen_points(self, offset, arguments=None):
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            hov_status, bez_id, status = super().curve_box_sharpen_points(
                self.position, offset, arguments)
        return hov_status, bez_id, status

    def curve_box_rotate_points(self, angle, arguments=None):
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            hov_status, bez_id, status, mid_co = super(
            ).curve_box_rotate_points(self.position, angle, arguments)
        return hov_status, bez_id, status, mid_co

    def curve_box_clear_sharpness(self, arguments=None):
        hov_status = False
        if self.hover:
            hov_status, status = super().curve_box_clear_sharpness(self.position, arguments)
        return hov_status

    def curve_box_clear_rotation(self, arguments=None):
        hov_status = False
        if self.hover:
            hov_status, status = super().curve_box_clear_rotation(self.position, arguments)
        return hov_status

    def curve_box_store_data(self, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        hov_status = False
        if self.hover:
            hov_status, status = super().curve_box_store_data(self.position, arguments, coords=coords,
                                                              handles=handles, sharpness=sharpness, rotations=rotations)
        return hov_status

    def curve_box_restore_stored_data(self, arguments=None):
        hov_status = False
        if self.hover:
            hov_status, status = super().curve_box_restore_stored_data(self.position, arguments)
        return hov_status

    def curve_box_clear_stored_data(self):
        hov_status = False
        if self.hover:
            hov_status = super().curve_box_clear_stored_data()
        return hov_status

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        self.scale_resize_sel_width = self.resize_sel_width*scale

        return

    def set_horizontal_alignment(self, align):
        #
        # Set horizontal alignment.
        # Options are L for left, R for right, C for center
        #
        if 'B' in self.alignment:
            vert_align = 'B'
        else:
            vert_align = 'T'

        if align == 'LEFT':
            self.alignment = vert_align + 'L'
        if align == 'RIGHT':
            self.alignment = vert_align + 'R'
        if align == 'CENTER':
            self.alignment = vert_align + 'C'

    def set_vertical_alignment(self, align):
        #
        # Set vertical alignment.
        # Options are T for top, B for bottom
        #
        if 'L' in self.alignment:
            hor_align = 'L'
        elif 'C' in self.alignment:
            hor_align = 'C'
        else:
            hor_align = 'R'

        if align == 'TOP':
            self.alignment = 'T' + hor_align
        if align == 'BOT':
            self.alignment = 'B' + hor_align

    def set_new_position(self, position, window_dims=None, padding=25):
        # Reposition panel without recreating base shape data just offseting it
        pos = np.array([position[0], position[1]], dtype=np.float32)

        self.position = np.round(pos)
        self.bounding_corner = np.round(self.position+self.scale_pos_offset)

        if window_dims:
            self.check_in_window(window_dims, padding)

        self.update_batches()
        return

    def set_movable(self, status):
        self.movable = status
        return

    def set_resizable(self, status):
        self.resizable = status
        return

    def set_visibility(self, status):
        super().set_visibility(status)
        if status == False:
            self.clear_hover()
        return

    #

    def __str__(self):
        return 'CUI Panel'


class CUIPopup(CUIPanel):
    #
    # Adds a panel that is visible when the user sets it to be
    # And will become invisible when the user mouses away if enabled
    #
    def __init__(self, modal, position, width):
        super().__init__(modal, position, width)

        self.close_on_click = True
        self.keep_open = False
        self.close_margin = 35

        self.type = 'POPUP'

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
        status = None

        if self.visible and self.enabled:
            status = super().test_hover(mouse_co)
            # If no longer hovering and keep open is not on then test if we need to close this panel
            if self.hover == False and self.keep_open == False:
                close_it = self.test_popup_close(mouse_co)
                if close_it:
                    return 'CLOSED'

        return status

    def test_popup_close(self, mouse_co):
        #
        # Test if mouse is far enough outside of the panel to close it
        #
        min_x = self.bounding_corner[0]-self.scale_close_margin
        max_x = self.bounding_corner[0] + \
            self.scale_width+self.scale_close_margin
        min_y = self.bounding_corner[1] - \
            self.scale_height-self.scale_close_margin
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


class CUISubPanelPopup(CUIPopup):
    #
    # Adds a panel that is visible when the user sets it to be
    # And will become invisible when the user mouses away if enabled
    #
    def __init__(self, modal, position, width):
        super().__init__(modal, position, width)

        self.type = 'SUB_PANEL_POPUP'

        self.hover_ref = None

        return

    #

    def test_popup_close(self, mouse_co):
        #
        # Test if mouse is far enough outside of the panel to close it
        #
        min_x = self.bounding_corner[0]-self.scale_close_margin
        max_x = self.bounding_corner[0] + \
            self.scale_width+self.scale_close_margin
        min_y = self.bounding_corner[1] - \
            self.scale_height-self.scale_close_margin
        max_y = self.bounding_corner[1]+self.scale_close_margin

        if mouse_co[0] < min_x or mouse_co[0] > max_x or mouse_co[1] < min_y or mouse_co[1] > max_y:
            close = True

            if self.hover_ref is not None:
                min_x = self.hover_ref.final_pos[0] - \
                    self.scale_close_margin
                max_x = self.hover_ref.final_pos[0] + \
                    self.hover_ref.scale_width+self.scale_close_margin
                min_y = self.hover_ref.final_pos[1] - \
                    self.hover_ref.scale_height-self.scale_close_margin
                max_y = self.hover_ref.final_pos[1] + \
                    self.scale_close_margin

                if min_x <= mouse_co[0] <= max_x and min_y <= mouse_co[1] <= max_y:
                    close = False

            if close:
                self.set_visibility(False)
                self.reset_item_states(True)
                return True
        return False

    def set_hover_ref(self, ref):
        self.hover_ref = ref
        return

    #

    def __str__(self):
        return 'CUI Sub Panel Popup'


class CUIToolTipBox(CUIPanel):
    #
    # Adds a panel that is visible when the user sets it to be
    # And will become invisible when the user mouses away if enabled
    #
    def __init__(self, modal, position, width):
        super().__init__(modal, position, width)

        self.font_id = 0
        self.font_size = 12
        return

    #

    def test_click_down(self, mouse_co, shift, arguments=None):
        return None

    def test_click_up(self, mouse_co, shift, arguments=None):
        return None

    def click_down_move(self, mouse_co, shift=False, arguments=None, window_dims=None):
        return

    def test_hover(self, mouse_co):
        return None

    #

    def set_font_id(self, id):
        self.font_id = id
        return

    def set_font_size(self, size):
        self.font_size = size
        return

    #

    def __str__(self):
        return 'CUI Tooltip Box'


class CUIMinimizablePanel(CUIPanel):
    #
    # Adds a panel that is minimzed to a small icon when not being hovered
    #
    def __init__(self, modal, position, width):
        super().__init__(modal, position, width)
        self.open_on_hover = False

        self.minimized_width = 35
        self.minimized_height = 35
        self.minimized_icon = None
        self.minimized = True

        self.minimized_button = CUIButton(
            self, self.minimized_height, '')
        self.minimized_button.set_color(
            color=self.color,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )

        self.minimized_button.set_click_up_func(self.toggle_minimize)

        w_offset = self.minimized_width // 10
        h_offset = self.minimized_height // 10
        thick = (self.minimized_width+self.minimized_height) // 8
        poly = self.minimized_button.parts[0].add_poly_shape([
            [w_offset, -h_offset],
            [self.minimized_width-w_offset, -h_offset],
            [self.minimized_width-w_offset-thick, -h_offset-thick],
            [w_offset+thick, -h_offset-thick],
            [w_offset+thick, -self.minimized_height+h_offset+thick],
            [w_offset, -self.minimized_height+h_offset],
        ])
        poly.set_color(
            color=[0.0, 0.0, 0.1, 1.0]
        )
        return

    #

    def create_shape_data(self):

        self.minimized_button.set_width(self.minimized_width)
        self.minimized_button.set_height(self.minimized_height)
        self.minimized_button.pos_offset = np.array(
            [0.0, 0.0], dtype=np.float32)
        self.minimized_button.create_shape_data()
        self.minimized_button.set_scale(self.scale)

        super().create_shape_data()
        return

    def update_batches(self):
        super().update_batches()
        self.minimized_button.update_batches(self.position)
        return

    #

    def draw(self):
        if self.visible:
            if self.minimized:
                self.minimized_button.draw()
            else:
                super().draw()
        return

    #

    def test_click_down(self, mouse_co, shift, arguments=None):
        status = super().test_click_down(mouse_co, shift, arguments)
        return status

    def test_click_up(self, mouse_co, shift, arguments=None):
        status = None
        if self.minimized:
            if self.minimized_button.hover:
                # If not moving the panel then execute the click u pfunction
                if self.moving == False:
                    status = self.minimized_button.click_up_func(
                        mouse_co, shift, self.position, arguments)

                self.click_down = False
                if self.header is not None:
                    self.header.click_down = False
                self.moving = False
        else:
            status = super().test_click_up(mouse_co, shift, arguments)
        return status

    def click_down_move(self, mouse_co, shift=False, arguments=None, window_dims=None):
        status = super().click_down_move(mouse_co, shift, arguments, window_dims)
        return

    def test_hover(self, mouse_co):
        status = super().test_hover(mouse_co)
        # If panel is being hovered and it is minimized and it is set to be opened when clicked then
        # Test if the minimized button is hovered
        if self.minimized and not self.open_on_hover:
            status = None
            self.minimized_button.test_hover(mouse_co, self.position)
            if self.minimized_button.hover:
                status = 'MINIMIZED'

        # If open on ohover then unminimize
        if self.open_on_hover:
            self.minimized = not self.hover
        return status

    #

    def toggle_minimize(self, modal, arguments=None):
        self.minimized = not self.minimized
        return

    #

    def set_open_on_hover(self, status):
        self.open_on_hover = status
        return

    def set_minimized_data(self, height=None, width=None, icon=None):
        if height is not None:
            self.minimized_width = height
        if width is not None:
            self.minimized_height = width
        if icon is not None:
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
    #
    # Create a colored border around the edge of the draw area with an option header and text
    #
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
        header_text.set_width(self.header_width)
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
        self.set_scale(self.scale)

        width = self.dimensions[0]
        height = self.dimensions[1]

        thick = self.scale_thickness

        # Set the outer shape points based on the set thickness of the border
        self.parts[0].set_base_points([
            [0.0, 0.0],
            [0.0, height],
            [thick, height-thick],
            [thick, thick]])

        self.parts[1].set_base_points([
            [0.0, height],
            [width, height],
            [width-thick, height-thick],
            [thick, height-thick]])

        self.parts[2].set_base_points([
            [width-thick, height-thick],
            [width, height],
            [width, 0.0],
            [width-thick, thick]])

        self.parts[3].set_base_points([
            [0.0, 0.0],
            [thick, thick],
            [width-thick, thick],
            [width, 0.0]])

        for part in self.parts:
            part.create_shape_data()

        # Create the header shape if used and set the header text
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

            self.header_text.set_width(self.header_width)
            self.header_text.set_height(self.header_height)
            self.header_text.create_shape_data()
            self.header_text.pos_offset[:] = [
                center-self.header_width/2, self.dimensions[1]-self.thickness]
            self.header_text.scale_pos_offset[:] = [
                center-width_half, self.dimensions[1]-thick]

        self.update_batches()
        return

    def update_batches(self):
        self.header.update_batches([0.0, 0.0])
        for part in self.parts:
            part.update_batches([0.0, 0.0])
        self.header_text.update_batches([0.0, 0.0])

        return

    #

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
    # HEADER FUNCS
    #

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
        if width is not None:
            self.header_width = width
        if bot_width is not None:
            self.header_bot_width = bot_width
        if height is not None:
            self.header_height = height
        if bev_size is not None:
            self.header_bev_size = bev_size
        if bev_res is not None:
            self.header_bev_res = bev_res
        return

    #

    def __str__(self):
        return 'CUI Border'
