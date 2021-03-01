import bpy
from .functions_modal import *
from .cui_classes.cui_window import *


def init_ui_panels(self, rw, rh, scale):
    self._window = CUIWindowContainer(self, bpy.context, scale)
    self._window.set_style_color(color_panel=(0.0, 0.0, 0.1, 0.2), color_box=(0.0, 0.0, 0.1, 0.8), color_row=(
        0.0, 0.0, 0.2, 1.0), color_item=(0.0, 0.0, 0.2, 1.0), color_hover=(0.0, 0.0, 0.37, 1.0), color_click=(0.0, 0.0, 0.5, 1.0))

    self._rot_gizmo = self._window.add_rot_gizmo(
        self._object.matrix_world, self._display_prefs.gizmo_size, [True, True, True], 0.045)

    # INITIALIZE BORDER
    if True:
        self._border = self._window.add_border()
        self._border.set_use_header(False)
        self._border.set_color(color=(0.72, 0.77, 0.70, 0.75))
        self._border.thickness = 2

    # RESET UI PANEL
    if True:
        self._reset_panel = self._window.add_panel([rw-10, 50], 150)
        self._reset_panel.set_movable(False)
        self._reset_panel.set_resizable(False)
        self._reset_panel.set_horizontal_alignment('RIGHT')
        self._reset_panel.set_vertical_alignment('BOTTOM')

        box = self._reset_panel.add_box()
        box.set_margins(0, 0)

        row = box.add_row()
        but = row.add_button(20, 'Reset UI')
        but.set_click_up_func(reset_ui)

    # GIZMO PANEL
    if True:
        x_icon = img_load('XAxis.png', __file__)
        y_icon = img_load('YAxis.png', __file__)
        z_icon = img_load('ZAxis.png', __file__)

        self._gizmo_panel = self._window.add_minimizable_panel(
            [int(rw/2), int(rh/2)], 250)
        self._gizmo_panel.set_separation(8)
        self._gizmo_panel.set_horizontal_alignment('LEFT')
        self._gizmo_panel.add_header(
            False, 'Incremental Rotations', 30, False)
        self._gizmo_panel.set_header_font_size(20)
        self._gizmo_panel.set_height_min_max(
            max=self.act_reg.height*0.95)
        self._gizmo_panel.header.set_draw_box(False)
        self._gizmo_panel.set_open_on_hover(True)
        self.gizmo_reposition_offset = [
            self._rot_gizmo.size/2+25, self._rot_gizmo.size/2]
        self._gizmo_panel.set_visibility(False)

        box = self._gizmo_panel.add_box()

        self._rot_increment_row = box.add_row()
        bool = self._rot_increment_row.add_bool(
            20, '+/-1°', default=self._rot_increment_one)
        bool.set_custom_id([0])
        bool.set_click_up_func(change_rotation_increment)
        bool = self._rot_increment_row.add_bool(
            20, '+/-5°', default=self._rot_increment_five)
        bool.set_custom_id([1])
        bool.set_click_up_func(change_rotation_increment)
        bool = self._rot_increment_row.add_bool(
            20, '+/-10°', default=self._rot_increment_ten)
        bool.set_custom_id([2])
        bool.set_click_up_func(change_rotation_increment)

        row = box.add_row()
        label = row.add_label(20, 'X ')
        label.set_icon_data(image=x_icon, width=15, height=15)

        but = row.add_button(20, '-')
        but.set_custom_id([0, -1])
        but.set_click_up_func(rotate_normals_incremental)
        but = row.add_button(20, '+')
        but.set_custom_id([0, 1])
        but.set_click_up_func(rotate_normals_incremental)

        row = box.add_row()
        label = row.add_label(20, 'Y ')
        label.set_icon_data(image=y_icon, width=15, height=15)

        but = row.add_button(20, '-')
        but.set_custom_id([1, -1])
        but.set_click_up_func(rotate_normals_incremental)
        but = row.add_button(20, '+')
        but.set_custom_id([1, 1])
        but.set_click_up_func(rotate_normals_incremental)

        row = box.add_row()
        label = row.add_label(20, 'Z ')
        label.set_icon_data(image=z_icon, width=15, height=15)

        but = row.add_button(20, '-')
        but.set_custom_id([2, -1])
        but.set_click_up_func(rotate_normals_incremental)
        but = row.add_button(20, '+')
        but.set_custom_id([2, 1])
        but.set_click_up_func(rotate_normals_incremental)

    # POINT AT PANEL
    if True:
        self._point_panel = self._window.add_panel(self._mouse_reg_loc, 250)
        self._point_panel.set_separation(8)
        self._point_panel.set_horizontal_alignment('LEFT')
        self._point_panel.add_header(
            False, 'Point Normals at Target', 30, False)
        self._point_panel.set_header_font_size(20)
        self._point_panel.set_height_min_max(
            max=self.act_reg.height*0.95)
        self._point_panel.header.set_draw_box(False)
        self._point_panel.set_visibility(False)

        box = self._point_panel.add_box()
        row = box.add_row()

        but = row.add_button(20, 'Confirm Point')
        but.set_custom_id([0])
        but.set_click_up_func(finish_point_mode)
        but = row.add_button(20, 'Cancel Point')
        but.set_custom_id([1])
        but.set_click_up_func(finish_point_mode)

        row = box.add_row()
        num = row.add_number(
            20, 'Point Strength', self.target_strength, 2, .01, .01, 1.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_target_strength)

        row = box.add_row()
        bool = row.add_bool(20, 'Align Vectors', default=self.point_align)
        bool.set_click_up_func(toggle_align_vectors)

    # SPHEREIZE PANEL
    if True:
        self._sphere_panel = self._window.add_panel(self._mouse_reg_loc, 250)
        self._sphere_panel.set_separation(8)
        self._sphere_panel.set_horizontal_alignment('LEFT')
        self._sphere_panel.add_header(
            False, 'Sphereize Normals', 30, False)
        self._sphere_panel.set_header_font_size(20)
        self._sphere_panel.set_height_min_max(
            max=self.act_reg.height*0.95)
        self._sphere_panel.header.set_draw_box(False)
        self._sphere_panel.set_visibility(False)

        box = self._sphere_panel.add_box()
        row = box.add_row()

        but = row.add_button(20, 'Confirm Sphereize')
        but.set_custom_id([0])
        but.set_click_up_func(finish_sphereize_mode)
        but = row.add_button(20, 'Cancel Sphereize')
        but.set_custom_id([1])
        but.set_click_up_func(finish_sphereize_mode)

        row = box.add_row()
        num = row.add_number(
            20, 'Sphereize Strength', self.target_strength, 2, .01, .01, 1.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_target_strength)

    # EXPORT PANEL
    if True:
        self._export_panel = self._window.add_panel(
            [rw-25, rh-75], 250)
        self._export_panel.set_separation(8)
        self._export_panel.set_horizontal_alignment('RIGHT')
        self._export_panel.add_header(
            True, 'Addon Settings', 30, False)
        self._export_panel.set_header_font_size(20)
        self._export_panel.set_height_min_max(
            max=self.act_reg.height*0.95)
        self._export_panel.header.set_draw_box(False)

        box = self._export_panel.add_box()
        box.add_header(True, 'Finish Modal', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        but = row.add_button(20, 'Confirm Changes')
        but.set_custom_id([0])
        but.set_click_up_func(end_modal)

        but = row.add_button(20, 'Cancel Changes')
        but.set_custom_id([1])
        but.set_click_up_func(end_modal)

        box = self._export_panel.add_box()
        box.add_header(True, 'Viewport Settings', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        bool = row.add_bool(20, 'Show Only Selected Normals',
                            default=self._selected_only)
        bool.set_click_up_func(toggle_show_only_selected)

        row = box.add_row()
        bool = row.add_bool(20, 'Scale Up Selected Normals',
                            default=self._selected_scale)
        bool.set_click_up_func(toggle_selected_scale)

        row = box.add_row()
        self._xray_bool = row.add_bool(20, 'X-Ray', default=self._x_ray_mode)
        self._xray_bool.set_click_up_func(toggle_x_ray)

        row = box.add_row()
        num = row.add_number(
            20, 'Normals Length', self._normal_size, 2, .01, .01, 10.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_normal_size)

        row = box.add_row()
        num = row.add_number(
            20, 'Normals Brightness', self._line_brightness, 2, .01, .01, 2.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_line_brightness)

        row = box.add_row()
        num = row.add_number(
            20, 'Vertex Point Size', self._point_size, 1, .1, .1, 10.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_point_size)

        row = box.add_row()
        num = row.add_number(
            20, 'Loop Size', self._loop_tri_size, 2, .1, 0.0, 1.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_loop_tri_size)

        row = box.add_row()
        bool = row.add_bool(20, 'Display Wireframe',
                            default=self._use_wireframe_overlay)
        bool.set_click_up_func(toggle_wireframe)

        row = box.add_row()
        num = row.add_number(
            20, 'Gizmo Size', self._gizmo_size, 0, 10, 100, 1000)
        num.set_slide_factor(2)
        num.set_value_change_func(change_gizmo_size)

        row = box.add_row()
        num = row.add_number(
            20, 'UI Scale', self._ui_scale, 2, .1, 0.5, 3.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_ui_scale)

        row = box.add_row()
        but = row.add_button(20, 'Save Addon Preferences')
        but.set_click_up_func(save_preferences)

        box = self._export_panel.add_box()
        box.add_header(True, 'Keymap', 20, False)
        box.set_header_font_size(14)
        # box.set_collapsed(True)
        self._keymap_box = box.add_box()
        keymap_initialize(self)

    # TOOLS PANEL
    if True:
        icon = img_load('AbLogo.png', __file__)

        self._tools_panel = self._window.add_panel([25, rh-75], 275)
        self._tools_panel.set_separation(8)
        self._tools_panel.set_horizontal_alignment('LEFT')
        self._tools_panel.add_header(True, 'Abnormal', 30, False)
        self._tools_panel.set_header_font_size(20)
        self._tools_panel.set_height_min_max(
            max=self.act_reg.height*0.95)
        self._tools_panel.set_header_icon_data(
            image=icon, width=35, height=35)
        self._tools_panel.header.set_draw_box(False)

        box = self._tools_panel.add_box()
        box.add_header(True, 'Settings', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        bool = row.add_bool(20, 'Edit Individual Loop Normals',
                            default=self._individual_loops)
        bool.set_click_up_func(toggle_individual_loops)

        row = box.add_row()

        row = box.add_row()
        label = row.add_label(20, 'Mirror Axis: ')
        label.set_width_min_max(max=100)

        bool = row.add_bool(20, 'X', default=self._mirror_x)
        bool.set_custom_id([0])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_mirror_axis)

        bool = row.add_bool(20, 'Y', default=self._mirror_y)
        bool.set_custom_id([1])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_mirror_axis)

        bool = row.add_bool(20, 'Z', default=self._mirror_z)
        bool.set_custom_id([2])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_mirror_axis)

        # row = box.add_row()
        # num = row.add_number(
        #     20, 'Mirror Search Range', self._mirror_range, 2, .1, .01, 5.0)
        # num.set_slide_factor(2)
        # num.set_value_change_func(change_mirror_range)

        row = box.add_row()
        label = row.add_label(20, 'Lock Axis: ')
        label.set_width_min_max(max=100)

        bool = row.add_bool(20, 'X', default=self._lock_x)
        bool.set_custom_id([0])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_lock_axis)

        bool = row.add_bool(20, 'Y', default=self._lock_y)
        bool.set_custom_id([1])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_lock_axis)

        bool = row.add_bool(20, 'Z', default=self._lock_z)
        bool.set_custom_id([2])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_lock_axis)

        box = self._tools_panel.add_box()
        box.add_header(True, 'Axis Alignment', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        label = row.add_label(20, 'Mirror Normals: ')
        label.set_width_min_max(max=100)

        but = row.add_button(20, 'X')
        but.set_custom_id([0])
        but.set_width_min_max(max=35)
        but.set_click_up_func(mirror_selection)

        but = row.add_button(20, 'Y')
        but.set_custom_id([1])
        but.set_width_min_max(max=35)
        but.set_click_up_func(mirror_selection)

        but = row.add_button(20, 'Z')
        but.set_custom_id([2])
        but.set_width_min_max(max=35)
        but.set_click_up_func(mirror_selection)

        box.add_text_row(20, 'Flatten Normals on Axis', font_size=12)

        row = box.add_row()
        but = row.add_button(20, 'X')
        but.set_custom_id([0])
        but.set_width_min_max(max=35)
        but.set_click_up_func(flatten_axis)

        but = row.add_button(20, 'Y')
        but.set_custom_id([1])
        but.set_width_min_max(max=35)
        but.set_click_up_func(flatten_axis)

        but = row.add_button(20, 'Z')
        but.set_custom_id([2])
        but.set_width_min_max(max=35)
        but.set_click_up_func(flatten_axis)

        box.add_text_row(20, 'Align to Axis', font_size=12)

        row = box.add_row()
        but = row.add_button(20, '+X')
        but.set_custom_id([0])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)

        but = row.add_button(20, '-X')
        but.set_custom_id([1])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)

        but = row.add_button(20, '+Y')
        but.set_custom_id([2])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)

        but = row.add_button(20, '-Y')
        but.set_custom_id([3])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)

        but = row.add_button(20, '+Z')
        but.set_custom_id([4])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)

        but = row.add_button(20, '-Z')
        but.set_custom_id([5])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)

        box = self._tools_panel.add_box()
        box.add_header(True, 'Normal Direction', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        but = row.add_button(20, 'Flip Normals')
        but.set_click_up_func(flip_selection)

        row = box.add_row()
        but = row.add_button(20, 'Set Outside')
        but.set_custom_id([0])
        but.set_click_up_func(set_direction)

        but = row.add_button(20, 'Set Inside')
        but.set_custom_id([1])
        but.set_click_up_func(set_direction)

        row = box.add_row()
        but = row.add_button(20, 'Reset Vectors')
        but.set_click_up_func(reset_vectors)

        row = box.add_row()
        but = row.add_button(20, 'Set Normals From Faces')
        but.set_click_up_func(set_from_faces)

        box = self._tools_panel.add_box()
        box.add_header(True, 'Manipulate Normals', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        self._gizmo_bool = row.add_bool(20, 'Use Rotation Gizmo',
                                        default=self._use_gizmo)
        self._gizmo_bool.set_click_up_func(toggle_use_gizmo)

        row = box.add_row()
        but = row.add_button(20, 'Average Individual Vertex Normals')
        but.set_click_up_func(average_individual)

        row = box.add_row()
        but = row.add_button(20, 'Average All Selected Normals')
        but.set_click_up_func(average_selection)

        row = box.add_row()
        but = row.add_button(20, 'Smooth Selected Normals')
        but.set_click_up_func(smooth_selection)

        row = box.add_row()
        num = row.add_number(
            20, 'Smooth Strength', self._smooth_strength, 2, .1, .01, 5.0)
        num.set_slide_factor(15)
        num.set_value_change_func(change_smooth_strength)

        num = row.add_number(
            20, 'Smooth Iterations', self._smooth_iterations, 0, 1, 1, 25)
        num.set_slide_factor(15)
        num.set_value_change_func(change_smooth_iterations)

        row = box.add_row()
        but = row.add_button(20, 'Set Smooth Shading')
        but.set_custom_id([2])
        but.set_click_up_func(change_shading)

        but = row.add_button(20, 'Set Flat Shading')
        but.set_custom_id([2])
        but.set_click_up_func(change_shading)

        box = self._tools_panel.add_box()
        box.add_header(True, 'Copy/Paste Normals', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        but = row.add_button(20, 'Copy Active Normal to Selected')
        but.set_click_up_func(active_to_selection)

        row = box.add_row()
        but = row.add_button(20, 'Store Active Normal')
        but.set_click_up_func(store_active)

        row = box.add_row()
        but = row.add_button(20, 'Paste Stored Normal')
        but.set_click_up_func(paste_stored)

        box = self._tools_panel.add_box()
        box.add_header(True, 'Target Normals', 20, False)
        box.header.set_draw_box(False)
        box.set_header_font_size(14)

        row = box.add_row()
        but = row.add_button(20, 'Sphereize Normals')
        but.set_click_up_func(begin_sphereize_mode)

        row = box.add_row()
        but = row.add_button(20, 'Point Normals at Target')
        but.set_click_up_func(begin_point_mode)

    self._window.set_scale(self._ui_scale)
    self._window.create_shape_data()
    return


#
#
#


# BUTTON FUNCTIONS
def change_ui_scale(self, arguments):
    arguments[0]._ui_scale = self.value

    arguments[0]._window.set_scale(arguments[0]._ui_scale)
    arguments[0]._window.create_shape_data()
    return True


def change_gizmo_size(self, arguments):
    arguments[0]._gizmo_size = self.value
    arguments[0]._rot_gizmo.update_size(self.value)
    return


def change_point_size(self, arguments):
    arguments[0]._point_size = self.value
    arguments[0]._points_container.set_point_size(
        arguments[0]._point_size)
    arguments[0].redraw = True
    return


def change_loop_tri_size(self, arguments):
    arguments[0]._loop_tri_size = self.value
    arguments[0]._points_container.set_loop_scale(
        arguments[0]._loop_tri_size)
    arguments[0].redraw = True
    return


def change_mirror_range(self, arguments):
    arguments[0]._mirror_range = self.value
    cache_mirror_data(arguments[0])
    return


def change_line_brightness(self, arguments):
    arguments[0]._line_brightness = self.value
    arguments[0]._points_container.set_brightess(
        arguments[0]._line_brightness)
    return


def change_normal_size(self, arguments):
    arguments[0]._normal_size = self.value
    arguments[0]._points_container.set_normal_scale(
        arguments[0]._normal_size)
    arguments[0].redraw = True
    return


def change_target_strength(self, arguments):
    arguments[0].target_strength = self.value

    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        if arguments[0].sphereize_mode:
            sphereize_normals(arguments[0], sel_inds)
        elif arguments[0].point_mode:
            point_normals(arguments[0], sel_inds)
    return


def change_smooth_strength(self, arguments):
    arguments[0]._smooth_strength = self.value
    return


def change_smooth_iterations(self, arguments):
    arguments[0]._smooth_iterations = self.value
    return


def change_rotation_increment(self, arguments):
    for item in arguments[0]._rot_increment_row.items:
        if item.item_type == 'BOOLEAN':
            item.set_bool(False)

    if self.custom_id[0] == 0:
        self.set_bool(True)
        arguments[0]._rot_increment_one = True
        arguments[0]._rot_increment = 1
    if self.custom_id[0] == 1:
        self.set_bool(True)
        arguments[0]._rot_increment_five = True
        arguments[0]._rot_increment = 5
    if self.custom_id[0] == 2:
        self.set_bool(True)
        arguments[0]._rot_increment_ten = True
        arguments[0]._rot_increment = 10

    return


#


def toggle_use_gizmo(self, arguments):
    arguments[0]._use_gizmo = self.bool_val
    update_orbit_empty(arguments[0])
    gizmo_update_hide(arguments[0], arguments[0]._use_gizmo)
    return


def toggle_x_ray(self, arguments):
    arguments[0]._x_ray_mode = self.bool_val
    return


def toggle_wireframe(self, arguments):
    arguments[0]._use_wireframe_overlay = self.bool_val
    for space in arguments[0]._draw_area.spaces:
        if space.type == 'VIEW_3D':
            space.overlay.show_wireframes = self.bool_val
            space.overlay.wireframe_threshold = 1.0
    return


def toggle_selected_scale(self, arguments):
    arguments[0]._selected_scale = self.bool_val
    arguments[0]._points_container.set_scale_selection(
        arguments[0]._selected_scale)
    arguments[0].redraw = True
    return


def toggle_show_only_selected(self, arguments):
    arguments[0]._selected_only = self.bool_val
    arguments[0]._points_container.set_draw_only_selected(
        arguments[0]._selected_only)
    arguments[0].redraw = True
    return


def toggle_lock_axis(self, arguments):
    if self.custom_id[0] == 0:
        arguments[0]._lock_x = self.bool_val
    if self.custom_id[0] == 1:
        arguments[0]._lock_y = self.bool_val
    if self.custom_id[0] == 2:
        arguments[0]._lock_z = self.bool_val
    return


def toggle_mirror_axis(self, arguments):
    if self.custom_id[0] == 0:
        arguments[0]._mirror_x = self.bool_val
    if self.custom_id[0] == 1:
        arguments[0]._mirror_y = self.bool_val
    if self.custom_id[0] == 2:
        arguments[0]._mirror_z = self.bool_val
    return


def toggle_align_vectors(self, arguments):
    arguments[0].point_align = self.bool_val

    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        point_normals(arguments[0], sel_inds)
    return


def toggle_individual_loops(self, arguments):
    arguments[0]._individual_loops = self.bool_val
    arguments[0]._points_container.set_draw_tris(
        arguments[0]._individual_loops)

    arguments[0].redraw = True
    return


#


def mirror_selection(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        mirror_normals(arguments[0], sel_inds, self.custom_id[0])
    return


def flatten_axis(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        flatten_normals(arguments[0], sel_inds, self.custom_id[0])
    return


def algin_to_axis(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        if self.custom_id[0] == 0:
            align_to_axis_normals(arguments[0], sel_inds, 0, 1)
        if self.custom_id[0] == 1:
            align_to_axis_normals(arguments[0], sel_inds, 0, -1)
        if self.custom_id[0] == 2:
            align_to_axis_normals(arguments[0], sel_inds, 1, 1)
        if self.custom_id[0] == 3:
            align_to_axis_normals(arguments[0], sel_inds, 1, -1)
        if self.custom_id[0] == 4:
            align_to_axis_normals(arguments[0], sel_inds, 2, 1)
        if self.custom_id[0] == 5:
            align_to_axis_normals(arguments[0], sel_inds, 2, -1)

    return


def flip_selection(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        flip_normals(arguments[0], sel_inds)
    return


def set_direction(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        if self.custom_id[0] == 0:
            set_outside_inside(arguments[0], sel_inds, 1)
        if self.custom_id[0] == 1:
            set_outside_inside(arguments[0], sel_inds, -1)

    return


def set_from_faces(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        set_normals_from_faces(arguments[0], sel_inds)

    return


def average_individual(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        average_vertex_normals(arguments[0], sel_inds)
    return


def average_selection(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        average_selected_normals(arguments[0], sel_inds)
    return


def smooth_selection(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        smooth_normals(
            arguments[0], sel_inds, 0.5)
    return


def change_shading(self, arguments):
    if self.custom_id[0] == 0:
        for p in arguments[0]._object.data.polygons:
            p.use_smooth = True
        arguments[0]._object_smooth = True
        set_new_normals(arguments[0])

    if self.custom_id[0] == 1:
        for p in arguments[0]._object.data.polygons:
            p.use_smooth = False
        arguments[0]._object_smooth = False
        set_new_normals(arguments[0])
    return


def active_to_selection(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        copy_active_to_selected(arguments[0], sel_inds)
    return


def store_active(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        arguments[0]._copy_normals, arguments[0]._copy_normals_tangs = get_po_loop_data(
            arguments[0], arguments[0]._active_point)
    return


def paste_stored(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        paste_normal(arguments[0], sel_inds)
    return


def begin_sphereize_mode(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        start_sphereize_mode(arguments[0])
    return


def finish_sphereize_mode(self, arguments):
    if self.custom_id[0] == 0:
        end_sphereize_mode(arguments[0], True)
    else:
        end_sphereize_mode(arguments[0], False)
    return


def begin_point_mode(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        start_point_mode(arguments[0])
    return


def finish_point_mode(self, arguments):
    if self.custom_id[0] == 0:
        end_point_mode(arguments[0], True)
    else:
        end_point_mode(arguments[0], False)
    return


def end_modal(self, arguments):
    if self.custom_id[0] == 0:
        finish_modal(arguments[0], False)
        status = {'FINISHED'}
    if self.custom_id[0] == 1:
        finish_modal(arguments[0], True)
        status = {'CANCELLED'}

    return status


def reset_vectors(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) != 0:
        reset_normals(arguments[0], sel_inds)
    return


def save_preferences(self, arguments):
    arguments[0]._behavior_prefs.rotate_gizmo_use = arguments[0]._use_gizmo
    arguments[0]._display_prefs.gizmo_size = arguments[0]._gizmo_size
    arguments[0]._display_prefs.normal_size = arguments[0]._normal_size
    arguments[0]._display_prefs.line_brightness = arguments[0]._line_brightness
    arguments[0]._display_prefs.point_size = arguments[0]._point_size
    arguments[0]._display_prefs.loop_tri_size = arguments[0]._loop_tri_size
    arguments[0]._display_prefs.selected_only = arguments[0]._selected_only
    arguments[0]._display_prefs.selected_scale = arguments[0]._selected_scale
    arguments[0]._display_prefs.display_wireframe = arguments[0]._use_wireframe_overlay
    arguments[0]._display_prefs.ui_scale = arguments[0]._ui_scale

    bpy.ops.wm.save_userpref()
    return


def rotate_normals_incremental(self, arguments):
    sel_inds = arguments[0]._points_container.get_selected_loops()
    if len(sel_inds) > 0:
        incremental_rotate_vectors(
            arguments[0], sel_inds, self.custom_id[0], self.custom_id[1])
    return


def reset_ui(self, arguments):
    rw = arguments[0].act_reg.width
    rh = arguments[0].act_reg.height
    arguments[0]._export_panel.set_new_position([rw-25, rh-75])
    arguments[0]._tools_panel.set_new_position([25, rh-75])
    return
