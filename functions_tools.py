import bpy
from mathutils import Vector, Euler
from mathutils.geometry import intersect_line_plane
from bpy_extras import view3d_utils
from .functions_modal import *
from .classes_tool import *


def setup_tools(modal):
    modal.tools = GEN_Modal_Container()
    modal.tools.set_cancel_keys(['Cancel Tool 1', 'Cancel Tool 2'])
    modal.tools.set_confirm_keys(['Confirm Tool 1', 'Confirm Tool 2'])
    modal.tools.set_pass_through_events(modal.nav_list)

    # BASIC TOOL
    if True:
        tool = modal.tools.add_tool(
            inherit_cancel=False, inherit_confirm=False)
        tool.set_mouse_function(mouse)
        tool.add_cancel_key('Cancel Modal')
        tool.set_cancel_function(cancel_modal)
        tool.add_confirm_key('Confirm Modal')
        tool.set_confirm_function(confirm_modal)
        tool.add_keymap_argument('History Undo', hist_undo)
        tool.add_keymap_argument('History Redo', hist_redo)
        tool.set_always_function(click_hold_release)

        # tool.set_pre_pass_through_function(gizmo_pre_navigate)
        # tool.set_post_pass_through_function(gizmo_post_navigate)

        tool.add_keymap_argument(
            'Box Select Start', box_select_start)
        tool.add_keymap_argument(
            'Circle Select Start', circle_select_start)
        tool.add_keymap_argument(
            'Lasso Select Start', lasso_select_start)

        tool.add_keymap_argument('Toggle Gizmo', toggle_gizmo)

        tool.add_keymap_argument('Hide Selected', hide_selected)
        tool.add_keymap_argument('Hide Unselected', hide_unselected)
        tool.add_keymap_argument('Unhide', unhide)

        tool.add_keymap_argument('Reset Gizmo Rotation', reset_gizmo)
        tool.add_keymap_argument('Rotate Normals', rotate_start)
        tool.add_keymap_argument('Toggle X-Ray', toggle_xray)
        tool.add_keymap_argument('Mirror Normals Start', mirror_start)
        tool.add_keymap_argument('Smooth Normals', smooth_norms)
        tool.add_keymap_argument('Flatten Normals Start', flatten_norms)
        tool.add_keymap_argument('Align Normals Start', align_norms)
        tool.add_keymap_argument('Copy Active Normal', copy_active)

        tool.add_keymap_argument('Paste Stored Normal', paste_stored)
        tool.add_keymap_argument(
            'Paste Active Normal to Selected', paste_active_to_selected)
        tool.add_keymap_argument('Set Normals Outside', set_outside)
        tool.add_keymap_argument('Set Normals Inside', set_inside)
        tool.add_keymap_argument('Flip Normals', flip_norms)
        tool.add_keymap_argument('Reset Vectors', reset_vectors)
        tool.add_keymap_argument(
            'Average Individual Normals', average_individual)
        tool.add_keymap_argument('Average Selected Normals', average_selected)
        tool.add_keymap_argument('Set Normals From Faces', normals_from_faces)

        #

        tool.add_keymap_argument('Select All', select_all)
        tool.add_keymap_argument('Deselect All', deselect_all)
        tool.add_keymap_argument('Select Linked', select_linked)
        tool.add_keymap_argument('Select Hover Linked', select_hover_linked)
        tool.add_keymap_argument('Invert Selection', invert_selection)
        tool.add_keymap_argument('New Click Selection', new_click_select)
        tool.add_keymap_argument('Add Click Selection', add_click_select)
        tool.add_keymap_argument('New Loop Selection', new_loop_select)
        tool.add_keymap_argument('Add Loop Selection', add_loop_select)
        tool.add_keymap_argument(
            'New Shortest Path Selection', new_shortest_select)
        tool.add_keymap_argument(
            'Add Shortest Path Selection', add_shortest_select)

        tool.add_keymap_argument(
            'Filter Mask From Selected', filter_from_sel)
        tool.add_keymap_argument(
            'Clear Filter Mask', filter_clear)

        modal._basic_tool = tool
        modal._current_tool = modal._basic_tool

    #
    #
    #

    # SELECTION TOOLS
    if True:
        # BOX SEL
        tool = modal.tools.add_tool(inherit_confirm=False)
        tool.set_use_start(True)
        tool.add_start_argument('Box Select Start Selection', box_sel_start)
        tool.set_mouse_function(box_sel_mouse)
        tool.set_cancel_function(box_sel_cancel)
        tool.set_confirm_function(box_sel_confirm)
        tool.add_confirm_key('Box New Selection')
        tool.add_confirm_key('Box Add Selection')
        tool.add_confirm_key('Box Remove Selection')
        # tool.set_pre_pass_through_function(clear_draw_pre_navigate)
        # tool.set_post_pass_through_function(clear_draw_post_navigate)

        modal._box_sel_tool = tool

        # LASSO SEL
        tool = modal.tools.add_tool(inherit_confirm=False)
        tool.set_use_start(True)
        tool.add_start_argument(
            'Lasso Select Start Selection', lasso_sel_start)
        tool.set_mouse_function(lasso_sel_mouse)
        tool.set_cancel_function(lasso_sel_cancel)
        tool.set_confirm_function(lasso_sel_confirm)
        tool.add_confirm_key('Lasso New Selection')
        tool.add_confirm_key('Lasso Add Selection')
        tool.add_confirm_key('Lasso Remove Selection')
        # tool.set_pre_pass_through_function(clear_draw_pre_navigate)
        # tool.set_post_pass_through_function(clear_draw_post_navigate)

        modal._lasso_sel_tool = tool

        # CIRCLE SEL
        tool = modal.tools.add_tool(inherit_confirm=False)
        tool.set_use_start(True)
        tool.add_start_argument(
            'Circle Select Start Selection', circle_sel_start)
        tool.add_keymap_argument('Circle Increase Size 1',
                                 circle_sel_inc, pre_start=True)
        tool.add_keymap_argument('Circle Increase Size 2',
                                 circle_sel_inc, pre_start=True)
        tool.add_keymap_argument('Circle Decrease Size 1',
                                 circle_sel_dec, pre_start=True)
        tool.add_keymap_argument('Circle Decrease Size 2',
                                 circle_sel_dec, pre_start=True)
        tool.add_keymap_argument('Circle Resize Mode Start',
                                 circle_sel_start_resize, pre_start=True)
        tool.set_mouse_function(circle_sel_mouse)
        tool.set_cancel_function(circle_sel_cancel)
        tool.set_confirm_function(circle_sel_confirm)
        tool.add_confirm_key('Circle End Selection')
        tool.add_confirm_key('Circle Add Selection')
        tool.add_confirm_key('Circle Remove Selection')
        # tool.set_pre_pass_through_function(clear_draw_pre_navigate)
        # tool.set_post_pass_through_function(clear_draw_post_navigate)

        modal._circle_sel_tool = tool

        # CIRCLE SEL RESIZE
        tool = modal.tools.add_tool()
        tool.set_mouse_function(circle_resize_mouse)
        tool.set_cancel_function(circle_resize_cancel)
        tool.set_confirm_function(circle_resize_confirm)
        tool.add_confirm_key('Circle Resize Confirm')

        modal._circle_resize_tool = tool

    # NORMAL TOOLS
    if True:
        # ROTATE NORMALS
        tool = modal.tools.add_tool()
        tool.set_mouse_function(rotate_norms_mouse)
        tool.set_cancel_function(rotate_norms_cancel)
        tool.set_confirm_function(rotate_norms_confirm)
        tool.add_keymap_argument('Rotate X Axis', rotate_set_x)
        tool.add_keymap_argument('Rotate Y Axis', rotate_set_y)
        tool.add_keymap_argument('Rotate Z Axis', rotate_set_z)

        tool.set_pre_pass_through_function(rotate_pre_navigate)
        tool.set_post_pass_through_function(rotate_post_navigate)

        modal._rotate_norms_tool = tool

        # SPHEREIZE
        tool = modal.tools.add_tool(
            inherit_confirm=False, inherit_cancel=False)
        tool.set_mouse_function(sphereize_mouse)
        tool.set_mouse_pass(True)
        tool.add_keymap_argument('Target Move Start', sphereize_start_move)
        tool.add_keymap_argument('Target Center Reset', sphereize_reset)
        tool.add_keymap_argument('Toggle X-Ray', toggle_x_ray)
        tool.add_cancel_key('Cancel Tool 1')

        modal._sphereize_tool = tool

        # SPHEREIZE MOVE
        tool = modal.tools.add_tool()
        tool.set_mouse_function(sphereize_move_mouse)
        tool.set_cancel_function(sphereize_move_cancel)
        tool.set_confirm_function(sphereize_move_confirm)
        tool.add_keymap_argument('Target Move X Axis', sphereize_move_set_x)
        tool.add_keymap_argument('Target Move Y Axis', sphereize_move_set_y)
        tool.add_keymap_argument('Target Move Z Axis', sphereize_move_set_z)
        tool.add_keymap_argument('Toggle X-Ray', toggle_x_ray)

        modal._sphereize_move_tool = tool

        # POINT
        tool = modal.tools.add_tool(
            inherit_confirm=False, inherit_cancel=False)
        tool.set_mouse_function(point_mouse)
        tool.set_mouse_pass(True)
        tool.add_keymap_argument('Target Move Start', point_start_move)
        tool.add_keymap_argument('Target Center Reset', point_reset)
        tool.add_keymap_argument('Toggle X-Ray', toggle_x_ray)
        tool.add_cancel_key('Cancel Tool 1')

        modal._point_tool = tool

        # POINT MOVE
        tool = modal.tools.add_tool()
        tool.set_mouse_function(point_move_mouse)
        tool.set_cancel_function(point_move_cancel)
        tool.set_confirm_function(point_move_confirm)
        tool.add_keymap_argument('Target Move X Axis', point_move_set_x)
        tool.add_keymap_argument('Target Move Y Axis', point_move_set_y)
        tool.add_keymap_argument('Target Move Z Axis', point_move_set_z)
        tool.add_keymap_argument('Toggle X-Ray', toggle_x_ray)

        modal._point_move_tool = tool

        # GIZMO CLICK
        tool = modal.tools.add_tool()
        tool.set_mouse_function(gizmo_mouse)
        tool.set_confirm_function(gizmo_confirm)
        tool.set_cancel_function(gizmo_cancel)
        tool.add_confirm_key('Confirm Tool 3')

        modal._gizmo_tool = tool

        # MIRROR
        tool = modal.tools.add_tool(inherit_confirm=False)
        tool.set_cancel_function(mirror_cancel)
        tool.add_keymap_argument('Mirror Normals X', mirror_x)
        tool.add_keymap_argument('Mirror Normals Y', mirror_y)
        tool.add_keymap_argument('Mirror Normals Z', mirror_z)

        modal._mirror_tool = tool

        # FLATTEN
        tool = modal.tools.add_tool(inherit_confirm=False)
        tool.set_cancel_function(flatten_cancel)
        tool.add_keymap_argument('Flatten Normals X', flatten_x)
        tool.add_keymap_argument('Flatten Normals Y', flatten_y)
        tool.add_keymap_argument('Flatten Normals Z', flatten_z)

        modal._flatten_tool = tool

        # ALIGN
        tool = modal.tools.add_tool(inherit_confirm=False)
        tool.set_cancel_function(align_cancel)
        tool.add_keymap_argument('Align Normals Pos X', align_pos_x)
        tool.add_keymap_argument('Align Normals Pos Y', align_pos_y)
        tool.add_keymap_argument('Align Normals Pos Z', align_pos_z)
        tool.add_keymap_argument('Align Normals Neg X', align_neg_x)
        tool.add_keymap_argument('Align Normals Neg Y', align_neg_y)
        tool.add_keymap_argument('Align Normals Neg Z', align_neg_z)

        modal._align_tool = tool

    # UI TOOLS
    if True:
        tool = modal.tools.add_tool(
            inherit_cancel=False, inherit_confirm=False, inherit_pass_thru=False)

        tool.add_cancel_key('Cancel Modal')
        tool.set_cancel_function(cancel_modal)
        tool.add_confirm_key('Confirm Modal')
        tool.set_confirm_function(confirm_modal)

        tool.add_keymap_argument('Select All', ui_select_all)
        tool.add_keymap_argument('Deselect All', ui_deselect_all)

        # tool.add_keymap_argument('Invert Selection', ui_invert_selection)

        tool.add_keymap_argument('Toggle Cyclic Status', ui_toggle_cyclic)

        tool.add_keymap_argument('Reset Point Rotate', ui_reset_rot)
        tool.add_keymap_argument('Point Rotate Start', ui_rot_start)

        tool.add_keymap_argument('Reset Point Sharpness', ui_reset_sharp)
        tool.add_keymap_argument('Point Sharpness Start', ui_sharp_start)

        tool.add_keymap_argument('Delete Selected Points', ui_delete_selected)

        tool.add_keymap_argument('Toggle Gizmo', toggle_gizmo)

        tool.add_keymap_argument('UI Panel Scroll Up 1', ui_scroll_up)
        tool.add_keymap_argument('UI Panel Scroll Up 2', ui_scroll_up)
        tool.add_keymap_argument('UI Panel Scroll Down 1', ui_scroll_down)
        tool.add_keymap_argument('UI Panel Scroll Down 2', ui_scroll_down)
        tool.add_keymap_argument('UI Click', ui_click)

        tool.set_timer_function(ui_timer)

        tool.add_cancel_key('Cancel Modal')
        tool.add_keymap_argument('History Undo', hist_undo)
        tool.add_keymap_argument('History Redo', hist_redo)
        tool.set_mouse_function(ui_tool)

        modal._ui_tool = tool

        #

        tool = modal.tools.add_tool(
            inherit_cancel=False, inherit_confirm=False, inherit_pass_thru=False)

        tool.add_keymap_argument('Select All', ui_select_all)
        tool.add_keymap_argument('Deselect All', ui_deselect_all)

        # tool.add_keymap_argument('Invert Selection', ui_invert_selection)

        tool.add_keymap_argument('Toggle Cyclic Status', ui_toggle_cyclic)

        tool.add_keymap_argument('Reset Point Rotate', ui_reset_rot)
        tool.add_keymap_argument('Point Rotate Start', ui_rot_start)

        tool.add_keymap_argument('Reset Point Sharpness', ui_reset_sharp)
        tool.add_keymap_argument('Point Sharpness Start', ui_sharp_start)

        tool.add_keymap_argument('Delete Selected Points', ui_delete_selected)

        tool.add_keymap_argument('Toggle Gizmo', toggle_gizmo)

        tool.add_keymap_argument('UI Panel Scroll Up 1', ui_scroll_up)
        tool.add_keymap_argument('UI Panel Scroll Up 2', ui_scroll_up)
        tool.add_keymap_argument('UI Panel Scroll Down 1', ui_scroll_down)
        tool.add_keymap_argument('UI Panel Scroll Down 2', ui_scroll_down)
        tool.add_keymap_argument('UI Click', ui_click)

        tool.set_timer_function(ui_timer)

        tool.set_mouse_function(popup_tool)

        modal._popup_tool = tool

        #

        tool = modal.tools.add_tool(
            inherit_cancel=False, inherit_confirm=False, inherit_pass_thru=False)
        tool.set_always_function(typing_tool)

        modal._typing_tool = tool

    return


def tool_end(modal):
    modal._mouse_init = None
    modal._mode_cache.clear()
    keymap_refresh(modal)
    modal._current_tool = modal._basic_tool
    return


def sel_tool_end(modal):
    bpy.context.window.cursor_modal_set('DEFAULT')
    update_orbit_empty(modal)
    end_selection_drawing(modal)
    tool_end(modal)
    return


#


def ui_tool(modal, context, event, func_data):
    ended = ui_mouse(modal, context, event, func_data)
    if ended:
        if modal._point_panel.visible:
            modal._current_tool = modal._point_tool
        elif modal._sphere_panel.visible:
            modal._current_tool = modal._sphereize_tool
        else:
            modal._current_tool = modal._basic_tool

        return {'RUNNING_MODAL'}
    return


def popup_tool(modal, context, event, func_data):
    ended = popup_mouse(modal, context, event, func_data)
    if ended:
        modal._current_tool = modal._basic_tool

        return {'RUNNING_MODAL'}
    return


def typing_tool(modal, context, event, func_data):
    ended = typing_keys(modal, context, event, func_data)
    if ended:
        if modal._window.popup_mode:
            modal._current_tool = modal._popup_tool
        else:
            modal._current_tool = modal._ui_tool
        return {'RUNNING_MODAL'}
    return


#


def ui_mouse(modal, context, event, func_data):
    if modal.click_hold == False:
        hov_status = modal._window.test_hover(modal._mouse_reg_loc)
        modal.ui_hover = hov_status is not None
        if modal.ui_hover == False:
            ui_hover_timer_end(modal)
            return True

    else:
        modal._window.click_down_move(
            modal._mouse_reg_loc, event.shift, arguments=[event])

    return False


def popup_mouse(modal, context, event, func_data):
    if modal.click_hold == False:
        hov_status = modal._window.test_hover(modal._mouse_reg_loc)
        modal.ui_hover = hov_status is not None
        if hov_status == 'CLOSED':
            modal._window.set_popup_mode(False)
            modal._popup_panel = None
            modal._current_tool = modal._ui_tool
            if modal.ui_hover == False:
                ui_hover_timer_end(modal)
                return True

    # if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
    #     modal.click_hold = False

    else:
        modal._window.click_down_move(
            modal._mouse_reg_loc, event.shift, arguments=[event])

    return False


def ui_select_all(modal, context, event, keys, func_data):
    modal._window.curve_box_select_points(True)
    return


def ui_deselect_all(modal, context, event, keys, func_data):
    modal._window.curve_box_select_points(False)
    return


def ui_invert_selection(modal, context, event, keys, func_data):
    return


def ui_toggle_cyclic(modal, context, event, keys, func_data):
    bezier_hover = modal._window.curve_box_toggle_cyclic()
    return


def ui_reset_rot(modal, context, event, keys, func_data):
    bezier_hover = modal._window.curve_box_clear_rotation(arguments=[
        modal, event])
    return


def ui_rot_start(modal, context, event, keys, func_data):
    bezier_hover, bezier_id, changing, mid_co = modal._window.curve_box_rotate_points(
        0.0, arguments=[event])

    if changing:
        modal._mode_cache.append(np.array([mid_co[0], mid_co[1], 0.0]))
        modal._mouse_init = modal._mouse_reg_loc.copy()
        modal.rotating = True
        modal.active_drawing = True
        modal._window.curve_box_store_data(rotations=True)
        modal._current_tool = modal._bez_rotate_tool
        keymap_rotating(modal)
    return


def ui_reset_sharp(modal, context, event, keys, func_data):
    bezier_hover = modal._window.curve_box_clear_sharpness(arguments=[
        modal, event])
    return


def ui_sharp_start(modal, context, event, keys, func_data):
    bezier_hover, bezier_id, changing = modal._window.curve_box_sharpen_points(
        0.0, arguments=[event])

    if changing:
        modal._mouse_init = modal._mouse_reg_loc.copy()
        modal._window.curve_box_store_data(sharpness=True)
        modal._current_tool = modal._bez_sharpness_tool
        # keymap_sharpness_changing(modal)
    return


def ui_delete_selected(modal, context, event, keys, func_data):
    bez_hover = modal._window.curve_box_delete_points(
        arguments=[event])
    return


def ui_scroll_up(modal, context, event, keys, func_data):
    modal._window.scroll_panel(10)
    return


def ui_scroll_down(modal, context, event, keys, func_data):
    modal._window.scroll_panel(-10)
    return


def ui_click(modal, context, event, keys, func_data):
    status = {'RUNNING_MODAL'}

    if event.value == 'PRESS':
        panel_status = modal._window.test_click_down(
            modal._mouse_reg_loc, event.shift, arguments=[event])
        modal.click_hold = True
        if panel_status:
            if panel_status[0] == 'GIZMO':
                gizmo_click_init(modal, event, panel_status[1])
                modal.ui_hover = False

            else:
                if panel_status[0] == {'CANCELLED'}:
                    status = panel_status[0]
                if panel_status[0] == {'FINISHED'}:
                    status = panel_status[0]

    elif event.value == 'RELEASE':
        panel_status = modal._window.test_click_up(
            modal._mouse_reg_loc, event.shift, arguments=[event])
        modal.click_hold = False
        if panel_status:
            rco = view3d_utils.location_3d_to_region_2d(
                modal.act_reg, modal.act_rv3d, modal._orbit_ob.location)
            if rco != None:
                modal.gizmo_reposition_offset = [
                    modal._gizmo_panel.position[0]-rco[0], modal._gizmo_panel.position[1]-rco[1]]

            if panel_status[0] == 'NUMBER_BAR_TYPE':
                modal._current_tool = modal._typing_tool
            if panel_status[0] == {'CANCELLED'}:
                status = panel_status[0]
            if panel_status[0] == {'FINISHED'}:
                status = panel_status[0]
    return status


def ui_timer(modal, context, event, func_data):
    if event.type != 'TIMER':
        modal._hover_stop_time = modal._hover_timer.time_duration
        if modal._hover_delay_passed:
            modal._window.tooltip_hide()

        modal._hover_delay_passed = False

    else:
        if modal._hover_delay_passed == False and (modal._hover_timer.time_duration-modal._hover_stop_time) > modal._hover_delay:
            modal._window.tooltip_show(modal._mouse_reg_loc)
            modal._hover_delay_passed = True

    return


def ui_hover_timer_start(modal):
    if modal._hover_timer is None:
        modal._hover_timer = bpy.context.window_manager.event_timer_add(
            0.25, window=bpy.context.window)
    return


def ui_hover_timer_end(modal):
    if modal._hover_timer is not None:
        bpy.context.window_manager.event_timer_remove(
            modal._hover_timer)
        modal._hover_timer = None
    return


def click_hold_release(modal, context, event, func_data):
    if event.value == 'RELEASE':
        modal.click_hold = False
    return


def typing_keys(modal, context, event, func_data):
    # typing keys
    if event.type == 'RET' and event.value == 'PRESS':
        modal._window.type_confirm(arguments=[event])
        return True
    elif event.type == 'NUMPAD_ENTER' and event.value == 'RELEASE':
        modal._window.type_confirm(arguments=[event])
        return True
    elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        modal._window.type_confirm(arguments=[event])
        return True

    elif event.type == 'ESC' and event.value == 'PRESS':
        modal._window.type_cancel()
        return True
    elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
        modal._window.type_cancel()
        return True

    elif event.type == 'LEFT_ARROW' and event.value == 'PRESS':
        modal._window.type_move_pos(-1)
        return False
    elif event.type == 'RIGHT_ARROW' and event.value == 'PRESS':
        modal._window.type_move_pos(1)
        return False

    elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
        modal._window.type_backspace_key()
        return False
    elif event.type == 'DEL' and event.value == 'PRESS':
        modal._window.type_delete_key()
        return False

    else:
        modal._window.type_add_key(event.ascii)
        return False

    return


#


#
# BASIC FUNCS
def mouse(modal, context, event, func_data):
    if modal.click_hold == False:
        hov_status = modal._window.test_hover(modal._mouse_reg_loc)
        modal.ui_hover = hov_status is not None
        if modal.ui_hover:
            ui_hover_timer_start(modal)
            modal._current_tool = modal._ui_tool
            return {'RUNNING_MODAL'}

    # view moved so update gizmo
    if modal._use_gizmo and context.region_data.view_matrix != modal.prev_view:
        modal._window.update_gizmo_pos(modal._orbit_ob.matrix_world)
        relocate_gizmo_panel(modal)
        modal.prev_view = context.region_data.view_matrix.copy()

        if modal._container.sel_status.any():
            gizmo_update_hide(modal, True)
        else:
            gizmo_update_hide(modal, False)

    #
    #
    #

    return


def gizmo_pre_navigate(modal, context, event, func_data):
    gizmo_update_hide(modal, False)
    modal._window.set_key('Navigation')
    return


def gizmo_post_navigate(modal, context, event, func_data):
    gizmo_update_hide(modal, True)
    return


def toggle_gizmo(modal, context, event, keys, func_data):
    modal._use_gizmo = not modal._use_gizmo
    modal._gizmo_bool.toggle_bool()
    update_orbit_empty(modal)
    if modal._container.sel_status.any():
        gizmo_update_hide(modal, True)
    else:
        gizmo_update_hide(modal, False)

    modal._window.set_key('Toggle Gizmo')
    return


def cancel_modal(modal, context, event, keys, func_data):
    finish_modal(modal, True)
    return {'CANCELLED'}


def confirm_modal(modal, context, event, keys, func_data):
    finish_modal(modal, False)
    return {'FINISHED'}


def hist_undo(modal, context, event, keys, func_data):
    move_undostack(modal, 1)
    modal._window.set_key('Undo')
    return


def hist_redo(modal, context, event, keys, func_data):
    move_undostack(modal, -1)
    modal._window.set_key('Redo')
    return


def hide_unselected(modal, context, event, keys, func_data):
    if modal._container.sel_status.all() == False:
        modal._container.hide_status[~modal._container.sel_status] = True

        modal._window.set_key('Hide Unselected')
        add_to_undostack(modal, 0)
    return


def hide_selected(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        modal._container.hide_status[modal._container.sel_status] = True
        modal._container.sel_status[:] = False
        modal._container.act_status[:] = False

        modal._window.set_key('Hide Selected')
        add_to_undostack(modal, 0)
    return


def unhide(modal, context, event, keys, func_data):
    if modal._container.hide_status.any():
        modal._container.sel_status[modal._container.hide_status] = True
        modal._container.hide_status[:] = False

        modal._window.set_key('Unhide')
        add_to_undostack(modal, 0)
    return


def reset_gizmo(modal, context, event, keys, func_data):
    if modal._use_gizmo:
        loc = modal._orbit_ob.location.copy()
        modal._orbit_ob.matrix_world = modal._object.matrix_world
        modal._orbit_ob.matrix_world.translation = loc
        modal._window.update_gizmo_orientation(
            modal._orbit_ob.matrix_world)

        modal._window.set_key('Reset Gizmo')
    return


def rotate_start(modal, context, event, keys, func_data):

    if modal._container.sel_status.any():
        avg_loc = np.mean(
            modal._container.loop_coords[modal._container.sel_status], axis=0)

        modal._window.set_status('VIEW ROTATION')

        modal._container.cache_norms[:] = modal._container.new_norms

        modal._mode_cache.append(avg_loc)
        modal._mode_cache.append(0)
        modal._mode_cache.append(1)
        modal._mouse_init = modal._mouse_reg_loc.copy()

        modal.rotating = True
        modal._current_tool = modal._rotate_norms_tool
        keymap_rotating(modal)
        gizmo_update_hide(modal, False)
        modal.selection_drawing = True
        start_active_drawing(modal)

        modal._window.set_key('Rotation')
    return


def toggle_xray(modal, context, event, keys, func_data):
    modal._x_ray_mode = not modal._x_ray_mode
    modal._xray_bool.toggle_bool()

    modal._window.set_key('Toggle X-Ray')
    return


def mirror_start(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        modal._current_tool = modal._mirror_tool
        keymap_mirror(modal)

        modal._window.set_key('Mirror Normals')
    return


def smooth_norms(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        smooth_normals(modal, 0.5)

        modal._window.set_key('Smooth Normals')
        add_to_undostack(modal, 0)
    return


def flatten_norms(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        modal._current_tool = modal._flatten_tool
        keymap_flatten(modal)

        modal._window.set_key('Flatten Normals')
    return


def align_norms(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        modal._current_tool = modal._align_tool
        keymap_align(modal)

        modal._window.set_key('Align Normals')
    return


def copy_active(modal, context, event, keys, func_data):
    if modal._container.act_status.any():
        store_active_normal(modal)

        modal._window.set_key('Copy Active Normal')
    return


def paste_stored(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        paste_normal(modal)

        modal._window.set_key('Paste Stored Normal')
        add_to_undostack(modal, 0)
    return


def paste_active_to_selected(modal, context, event, keys, func_data):
    if modal._container.act_status.any():
        copy_active_to_selected(modal)

        modal._window.set_key('Paste Active Normal to Selected')
        add_to_undostack(modal, 0)
    return


def set_outside(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        set_outside_inside(modal, 1)

        modal._window.set_key('Set Normals Outside')
        add_to_undostack(modal, 0)
    return


def set_inside(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        set_outside_inside(modal, -1)

        modal._window.set_key('Set Normals Inside')
        add_to_undostack(modal, 0)
    return


def flip_norms(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        flip_normals(modal)

        modal._window.set_key('Flip Normals')
        add_to_undostack(modal, 0)
    return


def reset_vectors(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        reset_normals(modal)

        modal._window.set_key('Reset Vectors')
        add_to_undostack(modal, 0)
    return


def average_individual(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        average_vertex_normals(modal)

        modal._window.set_key('Average Individual Normals')
        add_to_undostack(modal, 0)
    return


def average_selected(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        average_selected_normals(modal)

        modal._window.set_key('Average Selected Normals')
        add_to_undostack(modal, 0)
    return


def normals_from_faces(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        set_normals_from_faces(modal)

        modal._window.set_key('Normals From Faces')
        add_to_undostack(modal, 0)
    return


#


def invert_selection(modal, context, event, keys, func_data):
    if modal._container.hide_status.all() == False:
        modal._container.act_status[:] = False
        modal._container.sel_status[~modal._container.hide_status] = ~modal._container.sel_status[~modal._container.hide_status]
        modal._active_face = None

        modal._window.set_key('Invert Selection')
        add_to_undostack(modal, 0)
    return


def box_select_start(modal, context, event, keys, func_data):
    bpy.context.window.cursor_modal_set('CROSSHAIR')
    modal._current_tool = modal._box_sel_tool
    modal.selection_drawing = True
    keymap_box_selecting(modal)
    gizmo_update_hide(modal, False)

    modal._window.set_key('Box Select Start')
    return


def circle_select_start(modal, context, event, keys, func_data):
    bpy.context.window.cursor_modal_set('CROSSHAIR')
    modal._current_tool = modal._circle_sel_tool
    modal.selection_drawing = True
    modal.circle_selecting = True
    keymap_circle_selecting(modal)

    modal._window.set_key('Circle Select Start')
    return


def lasso_select_start(modal, context, event, keys, func_data):
    bpy.context.window.cursor_modal_set('CROSSHAIR')
    modal._current_tool = modal._lasso_sel_tool
    modal.selection_drawing = True
    keymap_lasso_selecting(modal)
    gizmo_update_hide(modal, False)

    modal._window.set_key('Lasso Select Start')
    return


def select_all(modal, context, event, keys, func_data):
    change = not modal._container.sel_status.all()
    if change:
        modal._container.sel_status[:] = True
        modal._active_face = None

        modal._window.set_key('Select All')
        add_to_undostack(modal, 0)
    return


def deselect_all(modal, context, event, keys, func_data):
    change = modal._container.sel_status.any()
    if change:
        modal._container.sel_status[:] = False
        modal._container.act_status[:] = False

        modal._active_point = None
        modal._active_face = None

        modal._window.set_key('Deselect All')
        add_to_undostack(modal, 0)
    return


def select_linked(modal, context, event, keys, func_data):
    if modal._container.sel_status.any():
        vis_pos = get_visible_points(modal)
        sel_inds = get_selected_points(modal, any_selected=True)

        new_sel = get_linked_geo(
            modal._object_bm, list(sel_inds), vis=list(vis_pos))

        if len(new_sel) > 0:
            modal._container.sel_status[get_vert_ls(
                modal, new_sel)] = True

        modal._window.set_key('Select Linked')
        add_to_undostack(modal, 0)
    return


def select_hover_linked(modal, context, event, keys, func_data):
    face_res = ray_cast_to_mouse(modal)
    if face_res != None:
        vis_pos = get_visible_points(modal)
        hov_inds = [
            v.index for v in modal._object_bm.faces[face_res[1]].verts if v.index in vis_pos]

        new_sel = get_linked_geo(
            modal._object_bm, hov_inds, vis=list(vis_pos))

        if len(new_sel) > 0:
            modal._container.sel_status[get_vert_ls(
                modal, new_sel)] = True

        modal._window.set_key('Select Hover Linked')
        add_to_undostack(modal, 0)
    return


def new_click_select(modal, context, event, keys, func_data):
    sel_res = selection_test(modal, False)
    if sel_res:

        modal._window.set_key('New Click Select')
        add_to_undostack(modal, 0)
    return


def add_click_select(modal, context, event, keys, func_data):
    sel_res = selection_test(modal, True)
    if sel_res:
        modal._window.set_key('Add Click Select')
        add_to_undostack(modal, 0)
    return


def new_loop_select(modal, context, event, keys, func_data):
    sel_res = loop_selection_test(modal, False)
    if sel_res:
        modal._window.set_key('New Loop Select')
        add_to_undostack(modal, 0)
    return


def add_loop_select(modal, context, event, keys, func_data):
    sel_res = loop_selection_test(modal, True)
    if sel_res:
        modal._window.set_key('Add Loop Select')
        add_to_undostack(modal, 0)
    return


def new_shortest_select(modal, context, event, keys, func_data):
    sel_res = path_selection_test(modal, False)
    if sel_res:
        modal._window.set_key('New Shortest Path Select')
        add_to_undostack(modal, 0)
    return


def add_shortest_select(modal, context, event, keys, func_data):
    sel_res = path_selection_test(modal, True)
    if sel_res:
        modal._window.set_key('Add Shortest Path Select')
        add_to_undostack(modal, 0)
    return


def filter_from_sel(modal, context, event, keys, func_data):
    selection_to_filer_mask(modal)
    return


def filter_clear(modal, context, event, keys, func_data):
    clear_filter_mask(modal)
    return


#
# BOX SELECT FUNCS
def box_sel_start(modal, context, event, keys, func_data):
    modal._mode_cache.append(
        [modal._mouse_reg_loc.copy(), modal._mouse_reg_loc.copy()])
    modal.box_selecting = True
    return


def box_sel_mouse(modal, context, event, func_data):
    if event.alt:
        if modal._mouse_init is None:
            modal._mouse_init = modal._mouse_reg_loc.copy()
        else:
            offset = modal._mouse_reg_loc-modal._mouse_init

            for p in range(len(modal._mode_cache[0])):
                modal._mode_cache[0][p][0] += offset[0]
                modal._mode_cache[0][p][1] += offset[1]

            modal._mouse_init = modal._mouse_reg_loc.copy()
    else:
        modal._mouse_init = None

        modal._mode_cache[0].pop(-1)
        modal._mode_cache[0].append(modal._mouse_reg_loc.copy())
    return


def box_sel_confirm(modal, context, event, keys, func_data):
    if 'Box Add Selection' in keys:
        change = box_selection_test(modal, True, False)
        if change:
            add_to_undostack(modal, 0)

    elif 'Box Remove Selection' in keys:
        change = box_selection_test(modal, False, True)
        if change:
            add_to_undostack(modal, 0)

    elif 'Box New Selection' in keys:
        change = box_selection_test(modal, False, False)
        if change:
            add_to_undostack(modal, 0)

    modal.box_selecting = False
    sel_tool_end(modal)
    return


def box_sel_cancel(modal, context, event, keys, func_data):
    modal.box_selecting = False
    sel_tool_end(modal)
    return


#
# LASSO SELECT FUNCS
def lasso_sel_start(modal, context, event, keys, func_data):
    modal._mode_cache.append([modal._mouse_reg_loc.copy()])
    modal.lasso_selecting = True
    return


def lasso_sel_mouse(modal, context, event, func_data):
    if event.alt:
        if modal._mouse_init is None:
            modal._mouse_init = modal._mouse_reg_loc.copy()
        else:
            offset = modal._mouse_reg_loc-modal._mouse_init

            for p in range(len(modal._mode_cache[0])):
                modal._mode_cache[0][p][0] += offset[0]
                modal._mode_cache[0][p][1] += offset[1]

            modal._mouse_init = modal._mouse_reg_loc.copy()

    else:
        modal._mouse_init = None

        prev_loc = Vector(modal._mode_cache[0][-1])
        cur_loc = Vector(modal._mouse_reg_loc)
        offset = cur_loc.xy - prev_loc.xy

        if offset.length > 5.0:
            modal._mode_cache[0].append(modal._mouse_reg_loc.copy())
    return


def lasso_sel_confirm(modal, context, event, keys, func_data):
    if 'Lasso Add Selection' in keys:
        change = lasso_selection_test(modal, True, False)
        if change:
            add_to_undostack(modal, 0)

    elif 'Lasso Remove Selection' in keys:
        change = lasso_selection_test(modal, False, True)
        if change:
            add_to_undostack(modal, 0)

    elif 'Lasso New Selection' in keys:
        change = lasso_selection_test(modal, False, False)
        if change:
            add_to_undostack(modal, 0)

    modal.lasso_selecting = False
    sel_tool_end(modal)
    return


def lasso_sel_cancel(modal, context, event, keys, func_data):
    modal.lasso_selecting = False
    sel_tool_end(modal)
    return


#
# CIRCLE SELECT FUNCS
def circle_sel_start(modal, context, event, keys, func_data):
    if 'Circle Add Selection' in keys:
        change = circle_selection_test(modal, True, False, modal.circle_radius)
    elif 'Circle Remove Selection' in keys:
        change = circle_selection_test(modal, False, True, modal.circle_radius)
        modal.circle_removing = True
    else:
        change = circle_selection_test(
            modal, False, False, modal.circle_radius)

    if change:
        modal.redraw = True
    return


def circle_sel_mouse(modal, context, event, func_data):
    if modal.circle_removing == False:
        change = circle_selection_test(modal, True, False, modal.circle_radius)
    else:
        change = circle_selection_test(modal, False, True, modal.circle_radius)

    if change:
        modal.redraw = True
    return


def circle_sel_confirm(modal, context, event, keys, func_data):
    modal.circle_removing = False
    modal._circle_sel_tool.restart()
    modal._mode_cache.clear()
    return


def circle_sel_inc(modal, context, event, keys, func_data):
    modal.circle_radius += 10
    return


def circle_sel_dec(modal, context, event, keys, func_data):
    modal.circle_radius -= 10
    if modal.circle_radius < 10:
        modal.circle_radius = 10
    return


def circle_sel_start_resize(modal, context, event, keys, func_data):
    modal.circle_resizing = True
    modal._current_tool = modal._circle_resize_tool

    if modal._mouse_reg_loc[0]-modal.circle_radius < 0:
        modal._mouse_init = modal._mouse_reg_loc.copy()
        modal._mouse_init[0] += modal.circle_radius
    else:
        modal._mouse_init = modal._mouse_reg_loc.copy()
        modal._mouse_init[0] -= modal.circle_radius

    modal._mode_cache.append(modal.circle_radius)
    return


def circle_sel_cancel(modal, context, event, keys, func_data):
    add_to_undostack(modal, 0)
    modal.circle_selecting = False
    modal.circle_removing = False
    sel_tool_end(modal)
    return


#
# CIRCLE SELECT RESIZE FUNCS
def circle_resize_mouse(modal, context, event, func_data):
    prev_loc = Vector(modal._mouse_init)
    cur_loc = Vector(modal._mouse_reg_loc)

    diff = int((cur_loc-prev_loc).length)
    modal.circle_radius = diff
    return


def circle_resize_confirm(modal, context, event, keys, func_data):
    modal._mode_cache.clear()
    modal.circle_resizing = False
    modal._current_tool = modal._circle_sel_tool
    return


def circle_resize_cancel(modal, context, event, keys, func_data):
    modal.circle_radius = modal._mode_cache[0]
    modal._mode_cache.clear()
    modal.circle_resizing = False
    modal._current_tool = modal._circle_sel_tool
    return


#
# NAVIGATE CLEAR DRAWING
def clear_draw_pre_navigate(modal, context, event, func_data):
    modal.selection_drawing = False
    empty_selection_drawing_lists(modal)
    return


def clear_draw_post_navigate(modal, context, event, func_data):
    modal.selection_drawing = True
    return


#
# ROTATE NORMALS FUNCS
def rotate_norms_mouse(modal, context, event, func_data):
    center = np.array(view3d_utils.location_3d_to_region_2d(
        modal.act_reg, modal.act_rv3d, modal._mode_cache[0]).to_3d())

    start_vec = Vector(modal._mouse_init-center).xy
    mouse_vec = Vector(modal._mouse_reg_loc-center).xy

    ang = mouse_vec.angle_signed(start_vec)
    if event.shift:
        ang *= 0.1

    if ang != 0.0:
        modal._mode_cache[1] = modal._mode_cache[1]+ang*modal._mode_cache[2]
        rotate_vectors(modal, modal._mode_cache[1])
        modal._mouse_init = modal._mouse_reg_loc.copy()

        modal.redraw_active = True
    return


def rotate_norms_confirm(modal, context, event, keys, func_data):

    add_to_undostack(modal, 1)

    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()

    modal.rotating = False
    tool_end(modal)
    gizmo_update_hide(modal, True)
    end_selection_drawing(modal)
    end_active_drawing(modal)
    return


def rotate_norms_cancel(modal, context, event, keys, func_data):
    modal._container.new_norms[:] = modal._container.cache_norms

    set_new_normals(modal)

    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()

    modal.redraw = True
    modal.rotating = False
    tool_end(modal)
    gizmo_update_hide(modal, True)
    end_selection_drawing(modal)
    end_active_drawing(modal)
    return


def rotate_pre_navigate(modal, context, event, func_data):
    modal.rotating = False
    end_selection_drawing(modal)
    bpy.context.window.cursor_modal_set('NONE')
    return


def rotate_post_navigate(modal, context, event, func_data):
    if modal.translate_mode == 0:
        rotate_vectors(modal, modal._mode_cache[1])
        modal.redraw_active = True

    modal._mouse_init = modal._mouse_reg_loc.copy()
    bpy.context.window.cursor_modal_set('DEFAULT')
    modal.rotating = True
    modal.selection_drawing = True
    modal._mode_cache[2] = translate_axis_side(modal)
    return


def rotate_set_x(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'ROTATING', 0)
    modal._mode_cache[2] = translate_axis_side(modal)
    rotate_vectors(modal, modal._mode_cache[1]*modal._mode_cache[2])
    modal.redraw_active = True
    return


def rotate_set_y(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'ROTATING', 1)
    modal._mode_cache[2] = translate_axis_side(modal)
    rotate_vectors(modal, modal._mode_cache[1]*modal._mode_cache[2])
    modal.redraw_active = True
    return


def rotate_set_z(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'ROTATING', 2)
    modal._mode_cache[2] = translate_axis_side(modal)
    rotate_vectors(modal, modal._mode_cache[1]*modal._mode_cache[2])
    modal.redraw_active = True
    return


#
# SPHEREIZE FUNCS
def sphereize_mouse(modal, context, event, func_data):
    hov_status = modal._window.test_hover(modal._mouse_reg_loc)
    modal.ui_hover = hov_status is not None
    if modal.ui_hover:
        ui_hover_timer_start(modal)
        modal._current_tool = modal._ui_tool
        return {'RUNNING_MODAL'}
    return


def sphereize_start_move(modal, context, event, keys, func_data):
    modal._window.set_status('VIEW TRANSLATION')

    rco = view3d_utils.location_3d_to_region_2d(
        modal.act_reg, modal.act_rv3d, modal._target_emp.location)

    modal._mode_cache.append(modal._mouse_reg_loc.copy())
    modal._mode_cache.append(modal._target_emp.location.copy())
    modal._mode_cache.append(rco)
    keymap_target_move(modal)
    modal._current_tool = modal._sphereize_move_tool
    return


def sphereize_reset(modal, context, event, keys, func_data):
    modal._target_emp.location = modal._mode_cache[0]
    sphereize_normals(modal)
    return


def toggle_x_ray(modal, context, event, keys, func_data):
    modal._x_ray_mode = not modal._x_ray_mode
    modal._xray_bool.toggle_bool()
    return


#
# SPHEREIZE MOVE FUNCS
def sphereize_move_mouse(modal, context, event, func_data):
    move_target(modal, event.shift)
    sphereize_normals(modal)

    modal._mode_cache.pop(1)
    modal._mode_cache.insert(1, modal._mouse_reg_loc.copy())

    modal.redraw_active = True
    return


def sphereize_move_confirm(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    keymap_target(modal)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._mode_cache.pop(1)
    modal._current_tool = modal._sphereize_tool
    end_active_drawing(modal)
    return


def sphereize_move_cancel(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    modal.redraw = True
    modal._target_emp.location = modal._mode_cache[2].copy()
    keymap_target(modal)
    sphereize_normals(modal)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._mode_cache.pop(1)
    modal._current_tool = modal._sphereize_tool
    end_active_drawing(modal)
    return


def sphereize_move_set_x(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 0)
    move_target(modal, event.shift)
    sphereize_normals(modal)

    modal.redraw_active = True
    return


def sphereize_move_set_y(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 1)
    move_target(modal, event.shift)
    sphereize_normals(modal)

    modal.redraw_active = True
    return


def sphereize_move_set_z(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 2)
    move_target(modal, event.shift)
    sphereize_normals(modal)

    modal.redraw_active = True
    return


#
# POINT FUNCS
def point_mouse(modal, context, event, func_data):
    hov_status = modal._window.test_hover(modal._mouse_reg_loc)
    modal.ui_hover = hov_status is not None
    if modal.ui_hover:
        ui_hover_timer_start(modal)
        modal._current_tool = modal._ui_tool
        return {'RUNNING_MODAL'}
    return


def point_start_move(modal, context, event, keys, func_data):
    modal._window.set_status('VIEW TRANSLATION')

    rco = view3d_utils.location_3d_to_region_2d(
        modal.act_reg, modal.act_rv3d, modal._target_emp.location)

    modal._mode_cache.append(modal._mouse_reg_loc.copy())
    modal._mode_cache.append(modal._target_emp.location.copy())
    modal._mode_cache.append(rco)
    keymap_target_move(modal)
    modal._current_tool = modal._point_move_tool
    return


def point_reset(modal, context, event, keys, func_data):
    modal._target_emp.location = modal._mode_cache[0]
    point_normals(modal)
    return


#
# POINT MOVE FUNCS
def point_move_mouse(modal, context, event, func_data):
    move_target(modal, event.shift)
    point_normals(modal)

    modal._mode_cache.pop(1)
    modal._mode_cache.insert(1, modal._mouse_reg_loc.copy())

    modal.redraw_active = True
    return


def point_move_confirm(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    keymap_target(modal)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._mode_cache.pop(1)
    modal._current_tool = modal._point_tool
    end_active_drawing(modal)
    return


def point_move_cancel(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    modal._target_emp.location = modal._mode_cache[2].copy()
    keymap_target(modal)
    point_normals(modal)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._mode_cache.pop(1)
    modal._current_tool = modal._point_tool
    end_active_drawing(modal)
    return


def point_move_set_x(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 0)
    move_target(modal, event.shift)
    point_normals(modal)

    modal.redraw_active = True
    return


def point_move_set_y(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 1)
    move_target(modal, event.shift)
    point_normals(modal)

    modal.redraw_active = True
    return


def point_move_set_z(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 2)
    move_target(modal, event.shift)
    point_normals(modal)

    modal.redraw_active = True
    return


#
# GIZMO FUNCS
def gizmo_mouse(modal, context, event, func_data):
    start_vec = modal._mode_cache[0]
    view_vec = view3d_utils.region_2d_to_vector_3d(
        modal.act_reg, modal.act_rv3d, modal._mouse_reg_loc)
    view_orig = view3d_utils.region_2d_to_origin_3d(
        modal.act_reg, modal.act_rv3d, modal._mouse_reg_loc)

    line_a = view_orig
    line_b = view_orig + view_vec*10000
    # Get start vector to measure angle of mouse
    if modal.translate_axis == 0:
        giz_vec = modal._mode_cache[3] @ Vector((1, 0, 0)) - \
            modal._mode_cache[3].translation

    if modal.translate_axis == 1:
        giz_vec = modal._mode_cache[3] @ Vector((0, 1, 0)) - \
            modal._mode_cache[3].translation

    if modal.translate_axis == 2:
        giz_vec = modal._mode_cache[3] @ Vector((0, 0, 1)) - \
            modal._mode_cache[3].translation

    mouse_co_3d = intersect_line_plane(
        line_a, line_b, modal._mode_cache[3].translation, giz_vec)

    mouse_co_local = modal._mode_cache[3].inverted() @ mouse_co_3d

    # Get angle of current rotation
    ang_fac = 1.0
    if modal.translate_axis == 0:
        mouse_loc = mouse_co_local.yz

    elif modal.translate_axis == 1:
        mouse_loc = mouse_co_local.xz
        ang_fac = -1.0

    elif modal.translate_axis == 2:
        mouse_loc = mouse_co_local.xy

    ang = start_vec.angle_signed(mouse_loc)*-1
    if event.shift:
        ang *= 0.1

    # Apply angle to normals or gizmo
    if ang != 0.0:
        modal._mode_cache[1] = modal._mode_cache[1]+ang
        modal._mode_cache.pop(0)
        modal._mode_cache.insert(0, mouse_loc)

        if modal._mode_cache[4]:
            rotate_vectors(modal, modal._mode_cache[1]*ang_fac)
            modal._window.update_gizmo_rot(
                modal._mode_cache[1], modal._mode_cache[2])
            modal.redraw_active = True
        else:
            if modal.translate_axis == 0:
                rot_mat = Euler([ang, 0, 0]).to_matrix().to_4x4()
            if modal.translate_axis == 1:
                rot_mat = Euler([0, -ang, 0]).to_matrix().to_4x4()
            if modal.translate_axis == 2:
                rot_mat = Euler([0, 0, ang]).to_matrix().to_4x4()

            modal._orbit_ob.matrix_world = modal._orbit_ob.matrix_world @ rot_mat
            modal._window.update_gizmo_orientation(
                modal._orbit_ob.matrix_world)
    return


def gizmo_confirm(modal, context, event, keys, func_data):
    for gizmo in modal._rot_gizmo.gizmos:
        gizmo.active = True
        gizmo.in_use = False

    if modal._mode_cache[4]:
        add_to_undostack(modal, 1)

    modal.gizmo_click = False
    modal.translate_mode = 0
    modal.translate_axis = 2
    modal.click_hold = False
    end_active_drawing(modal)
    tool_end(modal)
    return


def gizmo_cancel(modal, context, event, keys, func_data):
    if modal._mode_cache[4]:
        modal._container.new_norms[:] = modal._container.cache_norms
        set_new_normals(modal)
    else:
        modal._orbit_ob.matrix_world = modal._mode_cache[3].copy()
        modal._window.update_gizmo_orientation(
            modal._orbit_ob.matrix_world)

    for gizmo in modal._rot_gizmo.gizmos:
        gizmo.active = True
        gizmo.in_use = False

    modal.gizmo_click = False
    modal.translate_mode = 0
    modal.translate_axis = 2
    end_active_drawing(modal)
    tool_end(modal)
    modal.click_hold = False
    return


#
# MIRROR FUNCS
def mirror_x(modal, context, event, keys, func_data):
    mirror_normals(modal, 0)
    tool_end(modal)
    return


def mirror_y(modal, context, event, keys, func_data):
    mirror_normals(modal, 1)
    tool_end(modal)
    return


def mirror_z(modal, context, event, keys, func_data):
    mirror_normals(modal, 2)
    tool_end(modal)
    return


def mirror_cancel(modal, context, event, keys, func_data):
    tool_end(modal)
    return


#
# FLATTEN FUNCS
def flatten_x(modal, context, event, keys, func_data):
    flatten_normals(modal, 0)
    tool_end(modal)
    return


def flatten_y(modal, context, event, keys, func_data):
    flatten_normals(modal, 1)
    tool_end(modal)
    return


def flatten_z(modal, context, event, keys, func_data):
    flatten_normals(modal, 2)
    tool_end(modal)
    return


def flatten_cancel(modal, context, event, keys, func_data):
    tool_end(modal)
    return


#
# ALIGN FUNCS
def align_pos_x(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, 0, 1)
    tool_end(modal)
    return


def align_pos_y(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, 1, 1)
    tool_end(modal)
    return


def align_pos_z(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, 2, 1)
    tool_end(modal)
    return


def align_neg_x(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, 0, -1)
    tool_end(modal)
    return


def align_neg_y(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, 1, -1)
    tool_end(modal)
    return


def align_neg_z(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, 2, -1)
    tool_end(modal)
    return


def align_cancel(modal, context, event, keys, func_data):
    tool_end(modal)
    return
