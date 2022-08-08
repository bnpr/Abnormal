import bpy
from .functions_modal import *
from .cui_classes.cui_window import *


def init_ui_panels(modal, rw, rh, scale):
    modal._window = CUIWindowContainer(modal, bpy.context, scale)
    modal._window.set_style_color(color_panel=(0.0, 0.0, 0.1, 0.2), color_box=(0.0, 0.0, 0.1, 0.8), color_row=(
        0.0, 0.0, 0.2, 1.0), color_item=(0.0, 0.0, 0.2, 1.0), color_hover=(0.0, 0.0, 0.37, 1.0), color_click=(0.0, 0.0, 0.5, 1.0))

    modal._window.set_status_offset([25, 10])
    modal._window.set_key_offset([25, 10])

    modal._rot_gizmo = modal._window.add_rot_gizmo(
        modal._object.matrix_world, modal._display_prefs.gizmo_size, [True, True, True], 0.045)

    modal._window.add_tooltip_box()
    modal._window.tooltip_box.set_color(
        color=(0.0, 0.1, 0.1, 1.0))

    # INITIALIZE BORDER
    if True:
        modal._border = modal._window.add_border()
        modal._border.set_use_header(False)
        modal._border.set_color(color=(0.72, 0.77, 0.70, 0.75))
        modal._border.thickness = 2

    # RESET UI PANEL
    if True:
        modal._reset_panel = modal._window.add_panel([rw-10, 50], 150)
        modal._reset_panel.set_movable(False)
        modal._reset_panel.set_resizable(False)
        modal._reset_panel.set_horizontal_alignment('RIGHT')
        modal._reset_panel.set_vertical_alignment('BOTTOM')

        box = modal._reset_panel.add_box()
        box.set_margins(0, 0)

        row = box.add_row()
        but = row.add_button(20, 'Reset UI')
        but.set_click_up_func(reset_ui)

    # GIZMO PANEL
    if True:
        modal._gizmo_panel = modal._window.add_minimizable_panel(
            [int(rw/2), int(rh/2)], 250)
        modal._gizmo_panel.set_separation(8)
        modal._gizmo_panel.set_horizontal_alignment('LEFT')
        modal._gizmo_panel.add_header(
            False, 'Incremental Rotations', 30, False)
        modal._gizmo_panel.set_header_font_size(20)
        modal._gizmo_panel.set_height_min_max(
            max=modal.act_reg.height*0.95)
        modal._gizmo_panel.header.set_draw_box(False)
        modal._gizmo_panel.set_open_on_hover(True)
        modal.gizmo_reposition_offset = [
            modal._rot_gizmo.size/2+25, modal._rot_gizmo.size/2]
        modal._gizmo_panel.set_visibility(False)

        box = modal._gizmo_panel.add_box()

        modal._rot_increment_row = box.add_row()
        bool = modal._rot_increment_row.add_bool(
            20, '+/-1°', default=modal._rot_increment_one)
        bool.set_custom_id([0])
        bool.set_click_up_func(change_rotation_increment)
        bool = modal._rot_increment_row.add_bool(
            20, '+/-5°', default=modal._rot_increment_five)
        bool.set_custom_id([1])
        bool.set_click_up_func(change_rotation_increment)
        bool = modal._rot_increment_row.add_bool(
            20, '+/-10°', default=modal._rot_increment_ten)
        bool.set_custom_id([2])
        bool.set_click_up_func(change_rotation_increment)

        row = box.add_row()
        label = row.add_label(20, 'X ')
        label.set_icon_image('XAxis.png', __file__)
        label.set_icon_data(width=15, height=15)

        but = row.add_button(20, '-')
        but.set_custom_id([0, -1])
        but.set_click_up_func(rotate_normals_incremental)
        but = row.add_button(20, '+')
        but.set_custom_id([0, 1])
        but.set_click_up_func(rotate_normals_incremental)

        row = box.add_row()
        label = row.add_label(20, 'Y ')
        label.set_icon_image('YAxis.png', __file__)
        label.set_icon_data(width=15, height=15)

        but = row.add_button(20, '-')
        but.set_custom_id([1, -1])
        but.set_click_up_func(rotate_normals_incremental)
        but = row.add_button(20, '+')
        but.set_custom_id([1, 1])
        but.set_click_up_func(rotate_normals_incremental)

        row = box.add_row()
        label = row.add_label(20, 'Z ')
        label.set_icon_image('ZAxis.png', __file__)
        label.set_icon_data(width=15, height=15)

        but = row.add_button(20, '-')
        but.set_custom_id([2, -1])
        but.set_click_up_func(rotate_normals_incremental)
        but = row.add_button(20, '+')
        but.set_custom_id([2, 1])
        but.set_click_up_func(rotate_normals_incremental)

    # POINT AT PANEL
    if True:
        modal._point_panel = modal._window.add_panel(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._point_panel.set_separation(8)
        modal._point_panel.set_horizontal_alignment('LEFT')
        modal._point_panel.add_header(
            False, 'Point Normals at Target', 30, False)
        modal._point_panel.set_header_font_size(20)
        modal._point_panel.set_height_min_max(
            max=modal.act_reg.height*0.95)
        modal._point_panel.header.set_draw_box(False)
        modal._point_panel.set_visibility(False)

        box = modal._point_panel.add_box()
        row = box.add_row()

        but = row.add_button(20, 'Confirm Point')
        but.set_custom_id([0])
        but.set_click_up_func(finish_point_mode)
        but = row.add_button(20, 'Cancel Point')
        but.set_custom_id([1])
        but.set_click_up_func(finish_point_mode)

        row = box.add_row()
        modal.point_strength = row.add_number(
            20, 'Point Strength', modal.target_strength, 2, .01, .01, 1.0)
        modal.point_strength.set_slide_factor(2)
        modal.point_strength.set_value_change_func(change_point_strength)

        row = box.add_row()
        bool = row.add_bool(20, 'Align Vectors', default=modal.point_align)
        bool.set_click_up_func(toggle_align_vectors)

    # SPHEREIZE PANEL
    if True:
        modal._sphere_panel = modal._window.add_panel(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._sphere_panel.set_separation(8)
        modal._sphere_panel.set_horizontal_alignment('LEFT')
        modal._sphere_panel.add_header(
            False, 'Sphereize Normals', 30, False)
        modal._sphere_panel.set_header_font_size(20)
        modal._sphere_panel.set_height_min_max(
            max=modal.act_reg.height*0.95)
        modal._sphere_panel.header.set_draw_box(False)
        modal._sphere_panel.set_visibility(False)

        box = modal._sphere_panel.add_box()
        row = box.add_row()

        but = row.add_button(20, 'Confirm Sphereize')
        but.set_custom_id([0])
        but.set_click_up_func(finish_sphereize_mode)
        but = row.add_button(20, 'Cancel Sphereize')
        but.set_custom_id([1])
        but.set_click_up_func(finish_sphereize_mode)

        row = box.add_row()
        modal.sphere_strength = row.add_number(
            20, 'Sphereize Strength', modal.target_strength, 2, .01, .01, 1.0)
        modal.sphere_strength.set_slide_factor(2)
        modal.sphere_strength.set_value_change_func(change_sphereize_strength)

    #
    #
    #

    # DISPLAY SETTINGS SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._display_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._display_panel.add_box()

        row = box.add_row()
        bool = row.add_bool(20, 'Show Only Selected Normals',
                            default=modal._selected_only)
        bool.set_click_up_func(toggle_show_only_selected)

        row = box.add_row()
        bool = row.add_bool(20, 'Scale Up Selected Normals',
                            default=modal._selected_scale)
        bool.set_click_up_func(toggle_selected_scale)

        row = box.add_row()
        bool = row.add_bool(20, 'Draw Filter Weights',
                            default=modal._draw_weights)
        bool.set_click_up_func(toggle_draw_weights)

        row = box.add_row()
        modal._xray_bool = row.add_bool(
            20, 'X-Ray', default=modal._x_ray_mode)
        modal._xray_bool.set_click_up_func(toggle_x_ray)

        row = box.add_row()
        num = row.add_number(
            20, 'Normals Length', modal._normal_size, 2, .01, .01, 10.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_normal_size)

        row = box.add_row()
        num = row.add_number(
            20, 'Normals Brightness', modal._line_brightness, 2, .01, .01, 2.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_line_brightness)

        row = box.add_row()
        num = row.add_number(
            20, 'Vertex Point Size', modal._point_size, 1, .1, .1, 10.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_point_size)

        row = box.add_row()
        num = row.add_number(
            20, 'Loop Size', modal._loop_tri_size, 2, .1, 0.0, 1.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_loop_tri_size)

        row = box.add_row()
        bool = row.add_bool(20, 'Display Wireframe',
                            default=modal._use_wireframe_overlay)
        bool.set_click_up_func(toggle_wireframe)

        row = box.add_row()
        num = row.add_number(
            20, 'Gizmo Size', modal._gizmo_size, 0, 10, 100, 1000)
        num.set_slide_factor(2)
        num.set_value_change_func(change_gizmo_size)

        row = box.add_row()
        num = row.add_number(
            20, 'UI Scale', modal._ui_scale, 2, .1, 0.5, 3.0)
        num.set_slide_factor(2)
        num.set_value_change_func(change_ui_scale)

        row = box.add_row()
        but = row.add_button(20, 'Save Addon Preferences')
        but.set_click_up_func(save_preferences)

    # SYMMETRY SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._symmetry_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._symmetry_panel.add_box()

        box.add_text_row(20, 'Mirror Selected Normals:', font_size=12)

        row = box.add_row()
        but = row.add_button(20, 'X')
        but.set_custom_id([0])
        but.set_width_min_max(max=35)
        but.set_click_up_func(mirror_selection)
        but.add_tooltip_text_line(
            'Mirror selected normals on the X axis')

        but = row.add_button(20, 'Y')
        but.set_custom_id([1])
        but.set_width_min_max(max=35)
        but.set_click_up_func(mirror_selection)
        but.add_tooltip_text_line(
            'Mirror selected normals on the Y axis')

        but = row.add_button(20, 'Z')
        but.set_custom_id([2])
        but.set_width_min_max(max=35)
        but.set_click_up_func(mirror_selection)
        but.add_tooltip_text_line(
            'Mirror selected normals on the Z axis')

        box.add_text_row(20, 'Auto Mirror Axis:', font_size=12)

        row = box.add_row()
        bool = row.add_bool(20, 'X', default=modal._mirror_x)
        bool.set_custom_id([0])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_mirror_axis)
        bool.add_tooltip_text_line(
            'Auto mirror normals as you edit on the X axis')

        bool = row.add_bool(20, 'Y', default=modal._mirror_y)
        bool.set_custom_id([1])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_mirror_axis)
        bool.add_tooltip_text_line(
            'Auto mirror normals as you edit on the Y axis')

        bool = row.add_bool(20, 'Z', default=modal._mirror_z)
        bool.set_custom_id([2])
        bool.set_width_min_max(max=50)
        bool.set_click_up_func(toggle_mirror_axis)
        bool.add_tooltip_text_line(
            'Auto mirror normals as you edit on the Z axis')

        # row = box.add_row()
        # num = row.add_number(
        #     20, 'Mirror Search Range', modal._mirror_range, 2, .1, .01, 5.0)
        # num.set_slide_factor(2)
        # num.set_value_change_func(change_mirror_range)

    # ALIGNMENT SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._alignment_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._alignment_panel.add_box()

        box.add_text_row(20, 'Flatten Normals on Axis', font_size=12)

        row = box.add_row()
        but = row.add_button(20, 'X')
        but.set_custom_id([0])
        but.set_width_min_max(max=35)
        but.set_click_up_func(flatten_axis)
        but.add_tooltip_text_line(
            'Set selected normals to 0 on the X axis')

        but = row.add_button(20, 'Y')
        but.set_custom_id([1])
        but.set_width_min_max(max=35)
        but.set_click_up_func(flatten_axis)
        but.add_tooltip_text_line(
            'Set selected normals to 0 on the Y axis')

        but = row.add_button(20, 'Z')
        but.set_custom_id([2])
        but.set_width_min_max(max=35)
        but.set_click_up_func(flatten_axis)
        but.add_tooltip_text_line(
            'Set selected normals to 0 on the Z axis')

        box.add_text_row(20, 'Align to Axis', font_size=12)

        row = box.add_row()
        but = row.add_button(20, '+X')
        but.set_custom_id([0])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)
        but.add_tooltip_text_line(
            'Set selected normals to the local positive X axis')

        but = row.add_button(20, '-X')
        but.set_custom_id([1])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)
        but.add_tooltip_text_line(
            'Set selected normals to the local negative X axis')

        but = row.add_button(20, '+Y')
        but.set_custom_id([2])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)
        but.add_tooltip_text_line(
            'Set selected normals to the local positive Y axis')

        but = row.add_button(20, '-Y')
        but.set_custom_id([3])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)
        but.add_tooltip_text_line(
            'Set selected normals to the local negative Y axis')

        but = row.add_button(20, '+Z')
        but.set_custom_id([4])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)
        but.add_tooltip_text_line(
            'Set selected normals to the local positive Z axis')

        but = row.add_button(20, '-Z')
        but.set_custom_id([5])
        but.set_width_min_max(max=35)
        but.set_click_up_func(algin_to_axis)
        but.add_tooltip_text_line(
            'Set selected normals to the local negative Z axis')

    # NORMAL DIRECTION SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._direction_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._direction_panel.add_box()

        row = box.add_row()
        but = row.add_button(20, 'Flip Normals')
        but.set_click_up_func(flip_selection)
        but.add_tooltip_text_line(
            'Set selected normals to the opposite direction')

        row = box.add_row()
        but = row.add_button(20, 'Set Outside')
        but.set_custom_id([0])
        but.set_click_up_func(set_direction)
        but.add_tooltip_text_line(
            'Set selected normals to pointing towards the outside face direction')

        but = row.add_button(20, 'Set Inside')
        but.set_custom_id([1])
        but.set_click_up_func(set_direction)
        but.add_tooltip_text_line(
            'Set selected normals to pointing towards the inside face direction')

        row = box.add_row()
        but = row.add_button(20, 'Reset Vectors')
        but.set_click_up_func(reset_vectors)
        but.add_tooltip_text_line(
            'Reset selected normals to their original direction when you started Abnormal')

        row = box.add_row()
        but = row.add_button(20, 'Set Normals From Faces')
        but.set_click_up_func(set_from_faces)
        but.add_tooltip_text_line(
            'Set normals for all selected normals based on what faces are selected')
        but.add_tooltip_text_line(
            'Useful for creating hard edges based on which faces are selected')

    # MODIFY NORMALS SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._modify_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._modify_panel.add_box()

        row = box.add_row()
        modal._gizmo_bool = row.add_bool(20, 'Use Rotation Gizmo',
                                         default=modal._use_gizmo)
        modal._gizmo_bool.set_click_up_func(toggle_use_gizmo)

        row = box.add_row()
        but = row.add_button(20, 'Average Individual Vertex Normals')
        but.set_click_up_func(average_individual)
        but.add_tooltip_text_line(
            'Average the individual face corner normals of each selected vertex')

        row = box.add_row()
        but = row.add_button(20, 'Average All Selected Normals')
        but.set_click_up_func(average_selection)
        but.add_tooltip_text_line(
            'Average the normals of all selected normals into 1 direction')

        row = box.add_row()
        but = row.add_button(20, 'Smooth Selected Normals')
        but.set_click_up_func(smooth_selection)
        but.add_tooltip_text_line(
            'Smooth selected normals with their connected points')

        row = box.add_row()
        num = row.add_number(
            20, 'Smooth Strength', modal._smooth_strength, 2, .1, .01, 5.0)
        num.set_slide_factor(15)
        num.set_value_change_func(change_smooth_strength)
        num.add_tooltip_text_line(
            'Strength of each smooth iteration')

        num = row.add_number(
            20, 'Smooth Iterations', modal._smooth_iterations, 0, 1, 1, 25)
        num.set_slide_factor(15)
        num.set_value_change_func(change_smooth_iterations)
        num.add_tooltip_text_line(
            'Number of times to smooth the selected normals')

        row = box.add_row()
        but = row.add_button(20, 'Set Smooth Shading')
        but.set_custom_id([0])
        but.set_click_up_func(change_shading)
        but.add_tooltip_text_line(
            'Set the object to Smooth Shading while preserving the current normals')

        but = row.add_button(20, 'Set Flat Shading')
        but.set_custom_id([1])
        but.set_click_up_func(change_shading)
        but.add_tooltip_text_line(
            'Set the object to Flat Shading while preserving the current normals')

    # FILTER SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._filter_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._filter_panel.add_box()

        row = box.add_row()
        but = row.add_button(20, 'Create Filter Mask From Vgroup')
        but.set_click_up_func(filter_mask_from_vg)
        but.add_tooltip_text_line(
            'Convert the vertex group set in the addon panel into a vertex mask with gradient weights')

        row = box.add_row()
        but = row.add_button(20, 'Create Filter Mask From Selected')
        but.set_click_up_func(filter_mask_from_sel)
        but.add_tooltip_text_line(
            'Convert the current selection to a filter mask with full weight on all selected loops')

        row = box.add_row()
        but = row.add_button(20, 'Clear Filter Mask')
        but.set_click_up_func(filter_mask_clear)
        but.add_tooltip_text_line(
            'Clear filter mask and gradient weights')

    # COPY/PASTE SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._copy_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._copy_panel.add_box()

        row = box.add_row()
        but = row.add_button(20, 'Copy Active Normal to Selected')
        but.set_click_up_func(active_to_selection)
        but.add_tooltip_text_line(
            'Copy the active loop/vertex normal onto selected points')

        row = box.add_row()
        but = row.add_button(20, 'Store Active Normal')
        but.set_click_up_func(store_active)
        but.add_tooltip_text_line(
            'Stores the active loop/vertex normal for pasting')
        but = row.add_button(20, 'Paste Stored Normal')
        but.set_click_up_func(paste_stored)
        but.add_tooltip_text_line(
            'Paste the stored loop/vertex normal onto selected points')

    # TARGET MODES SUBPANEL
    if True:
        panel = modal._window.add_subpanel_popup(
            [modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]], 250)
        modal._modes_panel = panel
        panel.set_separation(8)
        panel.set_horizontal_alignment('LEFT')
        panel.set_visibility(False)
        panel.set_close_on_click(False)
        panel.set_close_margin(2)
        panel.set_height_min_max(
            max=bpy.context.region.height*0.9)

        box = modal._modes_panel.add_box()

        row = box.add_row()
        but = row.add_button(20, 'Sphereize Normals')
        but.set_click_up_func(begin_sphereize_mode)
        but.add_tooltip_text_line(
            'Start the Sphereize Normals mode')
        row = box.add_row()
        but = row.add_button(20, 'Point Normals at Target')
        but.set_click_up_func(begin_point_mode)
        but.add_tooltip_text_line(
            'Start the Point Normals at Target mode')

    #
    #
    #

    # EXPORT PANEL
    if True:
        modal._export_panel = modal._window.add_panel(
            [rw-25, rh-75], 250)
        modal._export_panel.set_separation(8)
        modal._export_panel.set_horizontal_alignment('RIGHT')
        modal._export_panel.add_header(
            True, 'Addon Settings', 30, False)
        modal._export_panel.set_header_font_size(20)
        modal._export_panel.set_height_min_max(
            max=modal.act_reg.height*0.95)
        modal._export_panel.header.set_draw_box(False)

        box = modal._export_panel.add_box()
        row = box.add_row()
        but = row.add_button(20, 'Confirm Changes')
        but.set_custom_id([0])
        but.set_click_up_func(end_modal)

        but = row.add_button(20, 'Cancel Changes')
        but.set_custom_id([1])
        but.set_click_up_func(end_modal)

        box = modal._export_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Viewport Settings')
        hbut.set_click_up_func(toggle_display_button)
        hbut.set_hover_down_func(display_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.display_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._display_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.display_collapsed)

            row = boxx.add_row()
            bool = row.add_bool(20, 'Show Only Selected Normals',
                                default=modal._selected_only)
            bool.set_click_up_func(toggle_show_only_selected)

            row = boxx.add_row()
            bool = row.add_bool(20, 'Scale Up Selected Normals',
                                default=modal._selected_scale)
            bool.set_click_up_func(toggle_selected_scale)

            row = boxx.add_row()
            bool = row.add_bool(20, 'Draw Filter Weights',
                                default=modal._draw_weights)
            bool.set_click_up_func(toggle_draw_weights)

            row = boxx.add_row()
            modal._xray_bool = row.add_bool(
                20, 'X-Ray', default=modal._x_ray_mode)
            modal._xray_bool.set_click_up_func(toggle_x_ray)

            row = boxx.add_row()
            num = row.add_number(
                20, 'Normals Length', modal._normal_size, 2, .01, .01, 10.0)
            num.set_slide_factor(2)
            num.set_value_change_func(change_normal_size)

            row = boxx.add_row()
            num = row.add_number(
                20, 'Normals Brightness', modal._line_brightness, 2, .01, .01, 2.0)
            num.set_slide_factor(2)
            num.set_value_change_func(change_line_brightness)

            row = boxx.add_row()
            num = row.add_number(
                20, 'Vertex Point Size', modal._point_size, 1, .1, .1, 10.0)
            num.set_slide_factor(2)
            num.set_value_change_func(change_point_size)

            row = boxx.add_row()
            num = row.add_number(
                20, 'Loop Size', modal._loop_tri_size, 2, .1, 0.0, 1.0)
            num.set_slide_factor(2)
            num.set_value_change_func(change_loop_tri_size)

            row = boxx.add_row()
            bool = row.add_bool(20, 'Display Wireframe',
                                default=modal._use_wireframe_overlay)
            bool.set_click_up_func(toggle_wireframe)

            row = boxx.add_row()
            num = row.add_number(
                20, 'Gizmo Size', modal._gizmo_size, 0, 10, 100, 1000)
            num.set_slide_factor(2)
            num.set_value_change_func(change_gizmo_size)

            row = boxx.add_row()
            num = row.add_number(
                20, 'UI Scale', modal._ui_scale, 2, .1, 0.5, 3.0)
            num.set_slide_factor(2)
            num.set_value_change_func(change_ui_scale)

            row = boxx.add_row()
            but = row.add_button(20, 'Save Addon Preferences')
            but.set_click_up_func(save_preferences)

            modal._display_box = boxx

        box = modal._export_panel.add_box()
        box.add_header(True, 'Keymap', 20, False)
        box.set_header_font_size(14)
        box.set_collapsed(True)
        modal._keymap_box = box.add_box()
        keymap_initialize(modal)

    # TOOLS PANEL
    if True:
        modal._tools_panel = modal._window.add_panel([25, rh-75], 275)
        modal._tools_panel.set_separation(8)
        modal._tools_panel.set_horizontal_alignment('LEFT')
        modal._tools_panel.add_header(True, 'Abnormal', 30, False)
        modal._tools_panel.set_header_font_size(20)
        modal._tools_panel.set_height_min_max(
            max=modal.act_reg.height*0.95)
        modal._tools_panel.set_header_icon_image(
            'AbLogo.png', __file__)
        modal._tools_panel.set_header_icon_data(
            width=35, height=35)
        modal._tools_panel.header.set_draw_box(False)

        #
        #
        #

        box = modal._tools_panel.add_box()

        row = box.add_row()
        bool = row.add_bool(20, 'Edit Individual Loop Normals',
                            default=modal._individual_loops)
        bool.set_click_up_func(toggle_individual_loops)
        bool.add_tooltip_text_line(
            'Allows enabling each separate face corner normal')
        bool.add_tooltip_text_line(
            'instead of every face normal connected to a vertex')

        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Symmetry')
        hbut.set_click_up_func(toggle_symmetry_button)
        hbut.set_hover_down_func(symmetry_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.symmetry_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._symmetry_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.symmetry_collapsed)

            boxx.add_text_row(20, 'Mirror Selected Normals:', font_size=12)

            row = boxx.add_row()
            but = row.add_button(20, 'X')
            but.set_custom_id([0])
            but.set_width_min_max(max=35)
            but.set_click_up_func(mirror_selection)
            but.add_tooltip_text_line(
                'Mirror selected normals on the X axis')

            but = row.add_button(20, 'Y')
            but.set_custom_id([1])
            but.set_width_min_max(max=35)
            but.set_click_up_func(mirror_selection)
            but.add_tooltip_text_line(
                'Mirror selected normals on the Y axis')

            but = row.add_button(20, 'Z')
            but.set_custom_id([2])
            but.set_width_min_max(max=35)
            but.set_click_up_func(mirror_selection)
            but.add_tooltip_text_line(
                'Mirror selected normals on the Z axis')

            boxx.add_text_row(20, 'Auto Mirror Axis:', font_size=12)

            row = boxx.add_row()
            bool = row.add_bool(20, 'X', default=modal._mirror_x)
            bool.set_custom_id([0])
            bool.set_width_min_max(max=50)
            bool.set_click_up_func(toggle_mirror_axis)
            bool.add_tooltip_text_line(
                'Auto mirror normals as you edit on the X axis')

            bool = row.add_bool(20, 'Y', default=modal._mirror_y)
            bool.set_custom_id([1])
            bool.set_width_min_max(max=50)
            bool.set_click_up_func(toggle_mirror_axis)
            bool.add_tooltip_text_line(
                'Auto mirror normals as you edit on the Y axis')

            bool = row.add_bool(20, 'Z', default=modal._mirror_z)
            bool.set_custom_id([2])
            bool.set_width_min_max(max=50)
            bool.set_click_up_func(toggle_mirror_axis)
            bool.add_tooltip_text_line(
                'Auto mirror normals as you edit on the Z axis')

            # row = boxx.add_row()
            # num = row.add_number(
            #     20, 'Mirror Search Range', modal._mirror_range, 2, .1, .01, 5.0)
            # num.set_slide_factor(2)
            # num.set_value_change_func(change_mirror_range)

            modal._symmetry_box = boxx

        #
        #
        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Axis Alignment')
        hbut.set_click_up_func(toggle_alignment_button)
        hbut.set_hover_down_func(alignment_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.alignment_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._alignment_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.alignment_collapsed)

            boxx.add_text_row(20, 'Flatten Normals on Axis', font_size=12)

            row = boxx.add_row()
            but = row.add_button(20, 'X')
            but.set_custom_id([0])
            but.set_width_min_max(max=35)
            but.set_click_up_func(flatten_axis)
            but.add_tooltip_text_line(
                'Set selected normals to 0 on the X axis')

            but = row.add_button(20, 'Y')
            but.set_custom_id([1])
            but.set_width_min_max(max=35)
            but.set_click_up_func(flatten_axis)
            but.add_tooltip_text_line(
                'Set selected normals to 0 on the Y axis')

            but = row.add_button(20, 'Z')
            but.set_custom_id([2])
            but.set_width_min_max(max=35)
            but.set_click_up_func(flatten_axis)
            but.add_tooltip_text_line(
                'Set selected normals to 0 on the Z axis')

            boxx.add_text_row(20, 'Align to Axis', font_size=12)

            row = boxx.add_row()
            but = row.add_button(20, '+X')
            but.set_custom_id([0])
            but.set_width_min_max(max=35)
            but.set_click_up_func(algin_to_axis)
            but.add_tooltip_text_line(
                'Set selected normals to the local positive X axis')

            but = row.add_button(20, '-X')
            but.set_custom_id([1])
            but.set_width_min_max(max=35)
            but.set_click_up_func(algin_to_axis)
            but.add_tooltip_text_line(
                'Set selected normals to the local negative X axis')

            but = row.add_button(20, '+Y')
            but.set_custom_id([2])
            but.set_width_min_max(max=35)
            but.set_click_up_func(algin_to_axis)
            but.add_tooltip_text_line(
                'Set selected normals to the local positive Y axis')

            but = row.add_button(20, '-Y')
            but.set_custom_id([3])
            but.set_width_min_max(max=35)
            but.set_click_up_func(algin_to_axis)
            but.add_tooltip_text_line(
                'Set selected normals to the local negative Y axis')

            but = row.add_button(20, '+Z')
            but.set_custom_id([4])
            but.set_width_min_max(max=35)
            but.set_click_up_func(algin_to_axis)
            but.add_tooltip_text_line(
                'Set selected normals to the local positive Z axis')

            but = row.add_button(20, '-Z')
            but.set_custom_id([5])
            but.set_width_min_max(max=35)
            but.set_click_up_func(algin_to_axis)
            but.add_tooltip_text_line(
                'Set selected normals to the local negative Z axis')

            modal._alignment_box = boxx

        #
        #
        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Normal Direction')
        hbut.set_click_up_func(toggle_direction_button)
        hbut.set_hover_down_func(direction_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.direction_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._direction_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.direction_collapsed)

            row = boxx.add_row()
            but = row.add_button(20, 'Flip Normals')
            but.set_click_up_func(flip_selection)
            but.add_tooltip_text_line(
                'Set selected normals to the opposite direction')

            row = boxx.add_row()
            but = row.add_button(20, 'Set Outside')
            but.set_custom_id([0])
            but.set_click_up_func(set_direction)
            but.add_tooltip_text_line(
                'Set selected normals to pointing towards the outside face direction')

            but = row.add_button(20, 'Set Inside')
            but.set_custom_id([1])
            but.set_click_up_func(set_direction)
            but.add_tooltip_text_line(
                'Set selected normals to pointing towards the inside face direction')

            row = boxx.add_row()
            but = row.add_button(20, 'Reset Vectors')
            but.set_click_up_func(reset_vectors)
            but.add_tooltip_text_line(
                'Reset selected normals to their original direction when you started Abnormal')

            row = boxx.add_row()
            but = row.add_button(20, 'Set Normals From Faces')
            but.set_click_up_func(set_from_faces)
            but.add_tooltip_text_line(
                'Set normals for all selected normals based on what faces are selected')
            but.add_tooltip_text_line(
                'Useful for creating hard edges based on which faces are selected')

            modal._direction_box = boxx

        #
        #
        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Modify Normals')
        hbut.set_click_up_func(toggle_modify_button)
        hbut.set_hover_down_func(modify_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.modify_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._modify_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.modify_collapsed)

            row = boxx.add_row()
            modal._gizmo_bool = row.add_bool(20, 'Use Rotation Gizmo',
                                             default=modal._use_gizmo)
            modal._gizmo_bool.set_click_up_func(toggle_use_gizmo)

            row = boxx.add_row()
            but = row.add_button(20, 'Average Individual Vertex Normals')
            but.set_click_up_func(average_individual)
            but.add_tooltip_text_line(
                'Average the individual face corner normals of each selected vertex')

            row = boxx.add_row()
            but = row.add_button(20, 'Average All Selected Normals')
            but.set_click_up_func(average_selection)
            but.add_tooltip_text_line(
                'Average the normals of all selected normals into 1 direction')

            row = boxx.add_row()
            but = row.add_button(20, 'Smooth Selected Normals')
            but.set_click_up_func(smooth_selection)
            but.add_tooltip_text_line(
                'Smooth selected normals with their connected points')

            row = boxx.add_row()
            num = row.add_number(
                20, 'Smooth Strength', modal._smooth_strength, 2, .1, .01, 5.0)
            num.set_slide_factor(15)
            num.set_value_change_func(change_smooth_strength)
            num.add_tooltip_text_line(
                'Strength of each smooth iteration')

            num = row.add_number(
                20, 'Smooth Iterations', modal._smooth_iterations, 0, 1, 1, 25)
            num.set_slide_factor(15)
            num.set_value_change_func(change_smooth_iterations)
            num.add_tooltip_text_line(
                'Number of times to smooth the selected normals')

            row = boxx.add_row()
            but = row.add_button(20, 'Set Smooth Shading')
            but.set_custom_id([0])
            but.set_click_up_func(change_shading)
            but.add_tooltip_text_line(
                'Set the object to Smooth Shading while preserving the current normals')

            but = row.add_button(20, 'Set Flat Shading')
            but.set_custom_id([1])
            but.set_click_up_func(change_shading)
            but.add_tooltip_text_line(
                'Set the object to Flat Shading while preserving the current normals')

            modal._modify_box = boxx

        #
        #
        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Filter Settings')
        hbut.set_click_up_func(toggle_filter_button)
        hbut.set_hover_down_func(filter_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.filter_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._filter_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.filter_collapsed)

            row = boxx.add_row()
            but = row.add_button(20, 'Create Filter Mask From Vgroup')
            but.set_click_up_func(filter_mask_from_vg)
            but.add_tooltip_text_line(
                'Convert the vertex group set in the addon panel into a vertex mask with gradient weights')

            row = boxx.add_row()
            but = row.add_button(20, 'Create Filter Mask From Selected')
            but.set_click_up_func(filter_mask_from_sel)
            but.add_tooltip_text_line(
                'Convert the current selection to a filter mask with full weight on all selected loops')

            row = boxx.add_row()
            but = row.add_button(20, 'Clear Filter Mask')
            but.set_click_up_func(filter_mask_clear)
            but.add_tooltip_text_line(
                'Clear filter mask and gradient weights')

            modal._filter_box = boxx

        #
        #
        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Copy/Paste Normals')
        hbut.set_click_up_func(toggle_copy_button)
        hbut.set_hover_down_func(copy_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.copy_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._copy_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.copy_collapsed)

            row = boxx.add_row()
            but = row.add_button(20, 'Copy Active Normal to Selected')
            but.set_click_up_func(active_to_selection)
            but.add_tooltip_text_line(
                'Copy the active loop/vertex normal onto selected points')

            row = boxx.add_row()
            but = row.add_button(20, 'Store Active Normal')
            but.set_click_up_func(store_active)
            but.add_tooltip_text_line(
                'Stores the active loop/vertex normal for pasting')
            but = row.add_button(20, 'Paste Stored Normal')
            but.set_click_up_func(paste_stored)
            but.add_tooltip_text_line(
                'Paste the stored loop/vertex normal onto selected points')

            modal._copy_box = boxx

        #
        #
        #

        box = modal._tools_panel.add_box()
        row = box.add_row()
        hbut = row.add_hover_button(30,
                                    'Normal Target Modes')
        hbut.set_click_up_func(toggle_modes_button)
        hbut.set_hover_down_func(modes_panel_show)
        hbut.set_font_size(16)
        hbut.set_bool(not modal._display_prefs.modes_collapsed)
        hbut.set_draw_box(not hbut.bool)

        modal._modes_panel.set_hover_ref(row)

        if True:
            boxx = box.add_box()
            boxx.set_visibility(not modal._display_prefs.modes_collapsed)

            row = boxx.add_row()
            but = row.add_button(20, 'Sphereize Normals')
            but.set_click_up_func(begin_sphereize_mode)
            but.add_tooltip_text_line(
                'Start the Sphereize Normals mode')
            row = boxx.add_row()
            but = row.add_button(20, 'Point Normals at Target')
            but.set_click_up_func(begin_point_mode)
            but.add_tooltip_text_line(
                'Start the Point Normals at Target mode')

            modal._modes_box = boxx

    modal._window.set_scale(modal._ui_scale)
    modal._window.create_shape_data()
    return


#
#
#


# BUTTON FUNCTIONS
def change_ui_scale(ui_item, arguments):
    arguments[0]._ui_scale = ui_item.value

    arguments[0]._window.set_scale(arguments[0]._ui_scale)
    arguments[0]._window.create_shape_data()
    return True


def change_gizmo_size(ui_item, arguments):
    arguments[0]._gizmo_size = ui_item.value
    arguments[0]._rot_gizmo.update_size(ui_item.value)
    return


def change_point_size(ui_item, arguments):
    arguments[0]._point_size = ui_item.value
    arguments[0]._container.set_point_size(
        arguments[0]._point_size)
    arguments[0].redraw = True
    return


def change_loop_tri_size(ui_item, arguments):
    arguments[0]._loop_tri_size = ui_item.value
    arguments[0]._container.set_loop_scale(
        arguments[0]._loop_tri_size)
    arguments[0].redraw = True
    return


def change_mirror_range(ui_item, arguments):
    arguments[0]._mirror_range = ui_item.value
    cache_mirror_data(arguments[0])
    return


def change_line_brightness(ui_item, arguments):
    arguments[0]._line_brightness = ui_item.value
    arguments[0]._container.set_brightess(
        arguments[0]._line_brightness)

    if arguments[0]._container.alt_shader:
        arguments[0].redraw = True
    return


def change_normal_size(ui_item, arguments):
    arguments[0]._normal_size = ui_item.value
    arguments[0]._container.set_normal_scale(
        arguments[0]._normal_size)
    arguments[0].redraw = True
    return


def change_sphereize_strength(ui_item, arguments):
    arguments[0].target_strength = ui_item.value

    if arguments[0]._container.sel_status.any():
        sphereize_normals(arguments[0])
    return


def change_point_strength(ui_item, arguments):
    arguments[0].target_strength = ui_item.value

    if arguments[0]._container.sel_status.any():
        point_normals(arguments[0])
    return


def change_smooth_strength(ui_item, arguments):
    arguments[0]._smooth_strength = ui_item.value
    return


def change_smooth_iterations(ui_item, arguments):
    arguments[0]._smooth_iterations = ui_item.value
    return


def change_rotation_increment(ui_item, arguments):
    for item in arguments[0]._rot_increment_row.items:
        if item.item_type == 'BOOLEAN':
            item.set_bool(False)

    if ui_item.custom_id[0] == 0:
        ui_item.set_bool(True)
        arguments[0]._rot_increment_one = True
        arguments[0]._rot_increment = 1
    if ui_item.custom_id[0] == 1:
        ui_item.set_bool(True)
        arguments[0]._rot_increment_five = True
        arguments[0]._rot_increment = 5
    if ui_item.custom_id[0] == 2:
        ui_item.set_bool(True)
        arguments[0]._rot_increment_ten = True
        arguments[0]._rot_increment = 10

    return


#


def toggle_use_gizmo(ui_item, arguments):
    arguments[0]._use_gizmo = ui_item.bool_val
    update_orbit_empty(arguments[0])
    gizmo_update_hide(arguments[0], arguments[0]._use_gizmo)
    return


def toggle_x_ray(ui_item, arguments):
    arguments[0]._x_ray_mode = ui_item.bool_val
    return


def toggle_wireframe(ui_item, arguments):
    arguments[0]._use_wireframe_overlay = ui_item.bool_val
    for space in arguments[0]._draw_area.spaces:
        if space.type == 'VIEW_3D':
            space.overlay.show_wireframes = ui_item.bool_val
            space.overlay.wireframe_threshold = 1.0
    return


def toggle_selected_scale(ui_item, arguments):
    arguments[0]._selected_scale = ui_item.bool_val
    arguments[0]._container.set_scale_selection(
        arguments[0]._selected_scale)
    arguments[0].redraw = True
    return


def toggle_show_only_selected(ui_item, arguments):
    arguments[0]._selected_only = ui_item.bool_val
    arguments[0]._container.set_draw_only_selected(
        arguments[0]._selected_only)
    arguments[0].redraw = True
    return


def toggle_draw_weights(ui_item, arguments):
    arguments[0]._draw_weights = ui_item.bool_val
    arguments[0]._container.set_draw_weights(
        arguments[0]._draw_weights)
    arguments[0].redraw = True
    return


def toggle_mirror_axis(ui_item, arguments):
    if ui_item.custom_id[0] == 0:
        arguments[0]._mirror_x = ui_item.bool_val
    if ui_item.custom_id[0] == 1:
        arguments[0]._mirror_y = ui_item.bool_val
    if ui_item.custom_id[0] == 2:
        arguments[0]._mirror_z = ui_item.bool_val
    return


def toggle_align_vectors(ui_item, arguments):
    arguments[0].point_align = ui_item.bool_val

    if arguments[0]._container.sel_status.any():
        point_normals(arguments[0])
    return


def toggle_individual_loops(ui_item, arguments):
    arguments[0]._individual_loops = ui_item.bool_val
    arguments[0]._container.set_draw_tris(
        arguments[0]._individual_loops)

    if ui_item.bool_val == False:
        sel_pos = get_selected_points(arguments[0], any_selected=True)
        arguments[0]._container.sel_status[arguments[0]._container.vert_link_ls[sel_pos]] = True

        if arguments[0]._container.act_status.any():
            act_verts = arguments[0]._container.loop_verts[arguments[0]._container.act_status]
            arguments[0]._container.act_status[arguments[0]
                                               ._container.vert_link_ls[act_verts]] = True

    arguments[0].redraw = True
    return


#


def repos_subpanel(panel, button, modal):
    ref_item = panel.hover_ref

    pos = [ref_item.final_pos[0]+button.scale_width, ref_item.final_pos[1]]

    if pos[0] + panel.scale_width > modal._window.dimensions[0]:
        pos = [ref_item.final_pos[0] -
               panel.scale_width, ref_item.final_pos[1]]

    panel.set_new_position(
        pos, modal._window.dimensions)

    panel.set_visibility(True)
    return


def toggle_display_button(ui_item, arguments):
    arguments[0]._display_box.set_visibility(
        not arguments[0]._display_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._display_box.visible == False:
        repos_subpanel(arguments[0]._display_panel, ui_item, arguments[0])
    else:
        arguments[0]._display_panel.set_visibility(False)

    arguments[0]._export_panel.create_shape_data()
    return


def display_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._display_panel, ui_item, arguments[0])

    else:
        arguments[0]._display_panel.set_visibility(False)

    return


def toggle_symmetry_button(ui_item, arguments):
    arguments[0]._symmetry_box.set_visibility(
        not arguments[0]._symmetry_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._symmetry_box.visible == False:
        repos_subpanel(arguments[0]._symmetry_panel, ui_item, arguments[0])
    else:
        arguments[0]._symmetry_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def symmetry_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._symmetry_panel, ui_item, arguments[0])

    else:
        arguments[0]._symmetry_panel.set_visibility(False)

    return


def toggle_alignment_button(ui_item, arguments):
    arguments[0]._alignment_box.set_visibility(
        not arguments[0]._alignment_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._alignment_box.visible == False:
        repos_subpanel(arguments[0]._alignment_panel, ui_item, arguments[0])
    else:
        arguments[0]._alignment_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def alignment_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._alignment_panel, ui_item, arguments[0])

    else:
        arguments[0]._alignment_panel.set_visibility(False)

    return


def toggle_direction_button(ui_item, arguments):
    arguments[0]._direction_box.set_visibility(
        not arguments[0]._direction_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._direction_box.visible == False:
        repos_subpanel(arguments[0]._direction_panel, ui_item, arguments[0])
    else:
        arguments[0]._direction_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def direction_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._direction_panel, ui_item, arguments[0])

    else:
        arguments[0]._direction_panel.set_visibility(False)

    return


def toggle_modify_button(ui_item, arguments):
    arguments[0]._modify_box.set_visibility(
        not arguments[0]._modify_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._modify_box.visible == False:
        repos_subpanel(arguments[0]._modify_panel, ui_item, arguments[0])
    else:
        arguments[0]._modify_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def modify_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._modify_panel, ui_item, arguments[0])

    else:
        arguments[0]._modify_panel.set_visibility(False)

    return


def toggle_filter_button(ui_item, arguments):
    arguments[0]._filter_box.set_visibility(
        not arguments[0]._filter_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._filter_box.visible == False:
        repos_subpanel(arguments[0]._filter_panel, ui_item, arguments[0])
    else:
        arguments[0]._filter_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def filter_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._filter_panel, ui_item, arguments[0])

    else:
        arguments[0]._filter_panel.set_visibility(False)

    return


def toggle_copy_button(ui_item, arguments):
    arguments[0]._copy_box.set_visibility(
        not arguments[0]._copy_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._copy_box.visible == False:
        repos_subpanel(arguments[0]._copy_panel, ui_item, arguments[0])
    else:
        arguments[0]._copy_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def copy_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._copy_panel, ui_item, arguments[0])

    else:
        arguments[0]._copy_panel.set_visibility(False)

    return


def toggle_modes_button(ui_item, arguments):
    arguments[0]._modes_box.set_visibility(
        not arguments[0]._modes_box.visible)

    ui_item.set_bool(not ui_item.bool)
    ui_item.set_draw_box(not ui_item.bool)
    if arguments[0]._modes_box.visible == False:
        repos_subpanel(arguments[0]._modes_panel, ui_item, arguments[0])
    else:
        arguments[0]._modes_panel.set_visibility(False)

    arguments[0]._tools_panel.create_shape_data()
    return


def modes_panel_show(ui_item, arguments):
    if ui_item.bool == False:
        repos_subpanel(arguments[0]._modes_panel, ui_item, arguments[0])

    else:
        arguments[0]._modes_panel.set_visibility(False)

    return


#


def filter_mask_from_vg(ui_item, arguments):
    update_filter_from_vg(arguments[0])
    add_to_undostack(arguments[0], 2)
    return


def filter_mask_from_sel(ui_item, arguments):
    selection_to_filer_mask(arguments[0])
    add_to_undostack(arguments[0], 2)
    return


def filter_mask_clear(ui_item, arguments):
    clear_filter_mask(arguments[0])
    add_to_undostack(arguments[0], 2)
    return


#


def mirror_selection(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        mirror_normals(arguments[0], ui_item.custom_id[0])
    return


def flatten_axis(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        flatten_normals(arguments[0], ui_item.custom_id[0])
    return


def algin_to_axis(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        if ui_item.custom_id[0] == 0:
            align_to_axis_normals(arguments[0], 0, 1)
        if ui_item.custom_id[0] == 1:
            align_to_axis_normals(arguments[0], 0, -1)
        if ui_item.custom_id[0] == 2:
            align_to_axis_normals(arguments[0], 1, 1)
        if ui_item.custom_id[0] == 3:
            align_to_axis_normals(arguments[0], 1, -1)
        if ui_item.custom_id[0] == 4:
            align_to_axis_normals(arguments[0], 2, 1)
        if ui_item.custom_id[0] == 5:
            align_to_axis_normals(arguments[0], 2, -1)

    return


def flip_selection(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        flip_normals(arguments[0])
    return


def set_direction(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        if ui_item.custom_id[0] == 0:
            set_outside_inside(arguments[0], 1)
        if ui_item.custom_id[0] == 1:
            set_outside_inside(arguments[0], -1)

    return


def set_from_faces(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        set_normals_from_faces(arguments[0])

    return


def average_individual(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        average_vertex_normals(arguments[0])
    return


def average_selection(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        average_selected_normals(arguments[0])
    return


def smooth_selection(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        smooth_normals(arguments[0], 0.5)
    return


def change_shading(ui_item, arguments):
    if ui_item.custom_id[0] == 0:
        for p in arguments[0]._object.data.polygons:
            p.use_smooth = True
        arguments[0]._object_smooth = True
        set_new_normals(arguments[0])

    if ui_item.custom_id[0] == 1:
        for p in arguments[0]._object.data.polygons:
            p.use_smooth = False
        arguments[0]._object_smooth = False
        set_new_normals(arguments[0])
    return


def active_to_selection(ui_item, arguments):
    if arguments[0]._container.act_status.any():
        copy_active_to_selected(arguments[0])
    return


def store_active(ui_item, arguments):
    if arguments[0]._container.act_status.any():
        store_active_normal(arguments[0])
    return


def paste_stored(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        paste_normal(arguments[0])
    return


def begin_sphereize_mode(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        start_sphereize_mode(arguments[0])
    return


def finish_sphereize_mode(ui_item, arguments):
    if ui_item.custom_id[0] == 0:
        end_sphereize_mode(arguments[0], True)
    else:
        end_sphereize_mode(arguments[0], False)
    return


def begin_point_mode(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        start_point_mode(arguments[0])
    return


def finish_point_mode(ui_item, arguments):
    if ui_item.custom_id[0] == 0:
        end_point_mode(arguments[0], True)
    else:
        end_point_mode(arguments[0], False)
    return


def end_modal(ui_item, arguments):
    if ui_item.custom_id[0] == 0:
        arguments[0]._confirm_modal = True
    if ui_item.custom_id[0] == 1:
        arguments[0]._cancel_modal = True

    return


def reset_vectors(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        reset_normals(arguments[0])
    return


def save_preferences(ui_item, arguments):
    arguments[0]._behavior_prefs.individual_loops = arguments[0]._individual_loops
    arguments[0]._behavior_prefs.rotate_gizmo_use = arguments[0]._use_gizmo

    arguments[0]._display_prefs.gizmo_size = arguments[0]._gizmo_size
    arguments[0]._display_prefs.normal_size = arguments[0]._normal_size
    arguments[0]._display_prefs.line_brightness = arguments[0]._line_brightness
    arguments[0]._display_prefs.point_size = arguments[0]._point_size
    arguments[0]._display_prefs.loop_tri_size = arguments[0]._loop_tri_size
    arguments[0]._display_prefs.selected_only = arguments[0]._selected_only
    arguments[0]._display_prefs.draw_weights = arguments[0]._draw_weights
    arguments[0]._display_prefs.selected_scale = arguments[0]._selected_scale
    arguments[0]._display_prefs.display_wireframe = arguments[0]._use_wireframe_overlay
    arguments[0]._display_prefs.ui_scale = arguments[0]._ui_scale

    arguments[0]._display_prefs.display_collapsed = not arguments[0]._display_box.visible
    arguments[0]._display_prefs.symmetry_collapsed = not arguments[0]._symmetry_box.visible
    arguments[0]._display_prefs.alignment_collapsed = not arguments[0]._alignment_box.visible
    arguments[0]._display_prefs.direction_collapsed = not arguments[0]._direction_box.visible
    arguments[0]._display_prefs.modify_collapsed = not arguments[0]._modify_box.visible
    arguments[0]._display_prefs.copy_collapsed = not arguments[0]._copy_box.visible
    arguments[0]._display_prefs.modes_collapsed = not arguments[0]._modes_box.visible

    bpy.ops.wm.save_userpref()
    return


def rotate_normals_incremental(ui_item, arguments):
    if arguments[0]._container.sel_status.any():
        incremental_rotate_vectors(
            arguments[0], ui_item.custom_id[0], ui_item.custom_id[1])
    return


def reset_ui(ui_item, arguments):
    rw = arguments[0].act_reg.width
    rh = arguments[0].act_reg.height
    arguments[0]._export_panel.set_new_position([rw-25, rh-75])
    arguments[0]._tools_panel.set_new_position([25, rh-75])
    return
