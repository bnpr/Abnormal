import bpy
from mathutils import Vector, Euler
from mathutils.geometry import intersect_line_plane
from .functions_modal import *
from .classes_tool import *


def setup_tools(modal):
    modal.tools = GEN_Modal_Container()
    modal.tools.set_cancel_keys(['Cancel Tool 1', 'Cancel Tool 2'])
    modal.tools.set_confirm_keys(['Confirm Tool 1', 'Confirm Tool 2'])
    modal.tools.set_pass_through_events(modal.nav_list)

    # BOX SEL
    tool = modal.tools.add_tool(inherit_confirm=False)
    tool.set_use_start(True)
    tool.add_start_argument('Box Start Selection', box_sel_start)
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
    tool.add_start_argument('Lasso Start Selection', lasso_sel_start)
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
    tool.add_start_argument('Circle Start Selection', circle_sel_start)
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
    tool = modal.tools.add_tool(inherit_confirm=False)
    tool.set_mouse_function(sphereize_mouse)
    tool.set_confirm_function(sphereize_confirm)
    tool.set_mouse_pass(True)
    tool.add_keymap_argument('Target Move Start', sphereize_start_move)
    tool.add_keymap_argument('Target Center Reset', sphereize_reset)
    tool.add_keymap_argument('Toggle X-Ray', toggle_x_ray)

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
    tool = modal.tools.add_tool(inherit_confirm=False)
    tool.set_mouse_function(point_mouse)
    tool.set_confirm_function(point_confirm)
    tool.set_mouse_pass(True)
    tool.add_keymap_argument('Target Move Start', point_start_move)
    tool.add_keymap_argument('Target Center Reset', point_reset)
    tool.add_keymap_argument('Toggle X-Ray', toggle_x_ray)

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
    return


#
# BOX SELECT FUNCS
def box_sel_start(modal, context, event, keys, func_data):
    modal._mode_cache.append(modal._mouse_reg_loc)
    modal.box_selecting = True
    return


def box_sel_mouse(modal, context, event, func_data):
    prev_loc = Vector((modal._mode_cache[-1][0], modal._mode_cache[-1][1]))
    cur_loc = Vector(modal._mouse_reg_loc)

    if event.alt:
        if modal._mouse_init == None:
            modal._mouse_init = modal._mouse_reg_loc

        else:
            offset = [modal._mouse_reg_loc[0]-modal._mouse_init[0],
                      modal._mouse_reg_loc[1]-modal._mouse_init[1]]
            for p in range(len(modal._mode_cache)):
                modal._mode_cache.append(
                    [modal._mode_cache[0][0]+offset[0], modal._mode_cache[0][1]+offset[1]])
                modal._mode_cache.pop(0)
            modal._mouse_init = modal._mouse_reg_loc

    else:
        if modal._mouse_init:
            modal._mouse_init = None

        if (cur_loc-prev_loc).length > 10.0:
            modal._mode_cache.append(modal._mouse_reg_loc)
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

    modal.tool_mode = False
    modal.box_selecting = False
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    update_orbit_empty(modal)
    keymap_refresh(modal)
    end_selection_drawing(modal)
    return


def box_sel_cancel(modal, context, event, keys, func_data):
    modal.tool_mode = False
    modal.box_selecting = False
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    keymap_refresh(modal)
    end_selection_drawing(modal)
    return


#
# LASSO SELECT FUNCS
def lasso_sel_start(modal, context, event, keys, func_data):
    modal._mode_cache.append(modal._mouse_reg_loc)
    modal.lasso_selecting = True
    return


def lasso_sel_mouse(modal, context, event, func_data):
    prev_loc = Vector((modal._mode_cache[-1][0], modal._mode_cache[-1][1]))
    cur_loc = Vector(modal._mouse_reg_loc)

    if event.alt:
        if modal._mouse_init == None:
            modal._mouse_init = modal._mouse_reg_loc

        else:
            offset = cur_loc - prev_loc
            for p in range(len(modal._mode_cache)):
                modal._mode_cache.append(
                    [modal._mode_cache[0][0]+offset[0], modal._mode_cache[0][1]+offset[1]])
                modal._mode_cache.pop(0)
            modal._mouse_init = modal._mouse_reg_loc

    else:
        if modal._mouse_init:
            modal._mouse_init = None

        if (cur_loc-prev_loc).length > 10.0:
            modal._mode_cache.append(modal._mouse_reg_loc)
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

    modal.tool_mode = False
    modal.lasso_selecting = False
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    update_orbit_empty(modal)
    keymap_refresh(modal)
    end_selection_drawing(modal)
    return


def lasso_sel_cancel(modal, context, event, keys, func_data):
    modal.tool_mode = False
    modal.lasso_selecting = False
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    keymap_refresh(modal)
    end_selection_drawing(modal)
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
        modal._mode_cache.append(
            [modal._mouse_reg_loc[0]+modal.circle_radius, modal._mouse_reg_loc[1]])
    else:
        modal._mode_cache.append(
            [modal._mouse_reg_loc[0]-modal.circle_radius, modal._mouse_reg_loc[1]])
    modal._mode_cache.append(modal.circle_radius)
    return


def circle_sel_cancel(modal, context, event, keys, func_data):
    add_to_undostack(modal, 0)
    modal.tool_mode = False
    modal.circle_selecting = False
    modal.circle_removing = False
    update_orbit_empty(modal)
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    keymap_refresh(modal)
    end_selection_drawing(modal)
    return


#
# CIRCLE SELECT RESIZE FUNCS
def circle_resize_mouse(modal, context, event, func_data):
    prev_loc = Vector((modal._mode_cache[0][0], modal._mode_cache[0][1]))
    cur_loc = Vector((modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]))

    diff = int((cur_loc-prev_loc).length)
    modal.circle_radius = diff
    return


def circle_resize_confirm(modal, context, event, keys, func_data):
    modal._mode_cache.clear()
    modal.circle_resizing = False
    modal._current_tool = modal._circle_sel_tool
    return


def circle_resize_cancel(modal, context, event, keys, func_data):
    modal.circle_radius = modal._mode_cache[1]
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
    center = view3d_utils.location_3d_to_region_2d(
        modal.act_reg, modal.act_rv3d, modal._mode_cache[2])

    start_vec = Vector(
        (modal._mode_cache[0][0]-center[0], modal._mode_cache[0][1]-center[1]))
    mouse_vec = Vector(
        (modal._mouse_reg_loc[0]-center[0], modal._mouse_reg_loc[1]-center[1]))

    ang = mouse_vec.angle_signed(start_vec)
    if event.shift:
        ang *= 0.1

    if ang != 0.0:
        modal._mode_cache[3] = modal._mode_cache[3]+ang*modal._mode_cache[4]
        rotate_vectors(
            modal, modal._mode_cache[1], modal._mode_cache[3])
        modal._mode_cache.pop(0)
        modal._mode_cache.insert(0, modal._mouse_reg_loc)

        modal.redraw_active = True
    return


def rotate_norms_confirm(modal, context, event, keys, func_data):
    modal._points_container.clear_cached_normals()

    add_to_undostack(modal, 1)
    modal._mode_cache.clear()
    modal._mouse_init = None
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()

    modal.rotating = False
    keymap_refresh(modal)
    gizmo_update_hide(modal, True)
    modal.tool_mode = False
    end_selection_drawing(modal)
    end_active_drawing(modal)
    return


def rotate_norms_cancel(modal, context, event, keys, func_data):
    modal._points_container.restore_cached_normals()

    set_new_normals(modal)
    modal._mode_cache.clear()
    modal._mouse_init = None
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()

    modal.redraw = True
    modal.rotating = False
    keymap_refresh(modal)
    gizmo_update_hide(modal, True)
    modal.tool_mode = False
    end_selection_drawing(modal)
    end_active_drawing(modal)
    return


def rotate_pre_navigate(modal, context, event, func_data):
    modal._mode_cache.pop(0)
    modal._mode_cache.insert(0, modal._mouse_reg_loc)
    modal.rotating = False
    end_selection_drawing(modal)
    bpy.context.window.cursor_modal_set('NONE')
    return


def rotate_post_navigate(modal, context, event, func_data):
    if modal.translate_mode == 0:
        rotate_vectors(
            modal, modal._mode_cache[1], modal._mode_cache[3])
        modal.redraw_active = True

    modal._mode_cache.pop(0)
    modal._mode_cache.insert(0, modal._mouse_reg_loc)
    bpy.context.window.cursor_modal_set('DEFAULT')
    modal.rotating = True
    modal.selection_drawing = True
    modal._mode_cache[4] = translate_axis_side(modal)
    return


def rotate_set_x(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'ROTATING', 0)
    modal._mode_cache[4] = translate_axis_side(modal)
    rotate_vectors(
        modal, modal._mode_cache[1], modal._mode_cache[3]*modal._mode_cache[4])
    modal.redraw_active = True
    return


def rotate_set_y(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'ROTATING', 1)
    modal._mode_cache[4] = translate_axis_side(modal)
    rotate_vectors(
        modal, modal._mode_cache[1], modal._mode_cache[3]*modal._mode_cache[4])
    modal.redraw_active = True
    return


def rotate_set_z(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'ROTATING', 2)
    modal._mode_cache[4] = translate_axis_side(modal)
    rotate_vectors(
        modal, modal._mode_cache[1], modal._mode_cache[3]*modal._mode_cache[4])
    modal.redraw_active = True
    return


#
# SPHEREIZE FUNCS
def sphereize_mouse(modal, context, event, func_data):
    hov_status = modal._window.test_hover(modal._mouse_reg_loc)
    modal.ui_hover = hov_status != None
    return


def sphereize_start_move(modal, context, event, keys, func_data):
    modal._window.set_status('VIEW TRANSLATION')

    rco = view3d_utils.location_3d_to_region_2d(
        modal.act_reg, modal.act_rv3d, modal._target_emp.location)

    modal._mode_cache.append(modal._mouse_reg_loc)
    modal._mode_cache.append(modal._target_emp.location.copy())
    modal._mode_cache.append(rco)
    keymap_target_move(modal)
    modal._current_tool = modal._sphereize_move_tool
    return


def sphereize_reset(modal, context, event, keys, func_data):
    modal._target_emp.location = modal._mode_cache[1]
    sphereize_normals(modal, modal._mode_cache[0])
    return


def sphereize_confirm(modal, context, event, keys, func_data):
    if event.value == 'PRESS':
        # Test 2d ui selection
        if modal._sphere_panel.visible:
            modal._sphere_panel.test_click_down(
                modal._mouse_reg_loc, event.shift, arguments=[event])
            modal.click_hold = True
    else:
        if modal._sphere_panel.visible:
            modal._sphere_panel.test_click_up(
                modal._mouse_reg_loc, event.shift, arguments=[event])
            modal.click_hold = False
    return


def toggle_x_ray(modal, context, event, keys, func_data):
    modal._x_ray_mode = not modal._x_ray_mode
    modal._xray_bool.toggle_bool()
    return


#
# SPHEREIZE MOVE FUNCS
def sphereize_move_mouse(modal, context, event, func_data):
    move_target(modal, event.shift)
    sphereize_normals(modal, modal._mode_cache[0])

    modal._mode_cache.pop(2)
    modal._mode_cache.insert(2, modal._mouse_reg_loc)

    modal.redraw_active = True
    return


def sphereize_move_confirm(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    keymap_target(modal)
    modal._mode_cache.pop(4)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._current_tool = modal._sphereize_tool
    end_active_drawing(modal)
    return


def sphereize_move_cancel(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    modal.redraw = True
    modal._target_emp.location = modal._mode_cache[3].copy()
    keymap_target(modal)
    sphereize_normals(modal, modal._mode_cache[0])
    modal._mode_cache.pop(4)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._current_tool = modal._sphereize_tool
    end_active_drawing(modal)
    return


def sphereize_move_set_x(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 0)
    move_target(modal, event.shift)
    sphereize_normals(modal, modal._mode_cache[0])

    modal.redraw_active = True
    return


def sphereize_move_set_y(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 1)
    move_target(modal, event.shift)
    sphereize_normals(modal, modal._mode_cache[0])

    modal.redraw_active = True
    return


def sphereize_move_set_z(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 2)
    move_target(modal, event.shift)
    sphereize_normals(modal, modal._mode_cache[0])

    modal.redraw_active = True
    return


#
# POINT FUNCS
def point_mouse(modal, context, event, func_data):
    hov_status = modal._window.test_hover(modal._mouse_reg_loc)
    modal.ui_hover = hov_status != None
    return


def point_start_move(modal, context, event, keys, func_data):
    modal._window.set_status('VIEW TRANSLATION')

    rco = view3d_utils.location_3d_to_region_2d(
        modal.act_reg, modal.act_rv3d, modal._target_emp.location)

    modal._mode_cache.append(modal._mouse_reg_loc)
    modal._mode_cache.append(modal._target_emp.location.copy())
    modal._mode_cache.append(rco)
    keymap_target_move(modal)
    modal._current_tool = modal._point_move_tool
    return


def point_reset(modal, context, event, keys, func_data):
    modal._target_emp.location = modal._mode_cache[1]
    point_normals(modal, modal._mode_cache[0])
    return


def point_confirm(modal, context, event, keys, func_data):
    if event.value == 'PRESS':
        # Test 2d ui selection
        if modal._point_panel.visible:
            modal._point_panel.test_click_down(
                modal._mouse_reg_loc, event.shift, arguments=[event])
            modal.click_hold = True
    else:
        if modal._point_panel.visible:
            modal._point_panel.test_click_up(
                modal._mouse_reg_loc, event.shift, arguments=[event])
            modal.click_hold = False
    return


#
# POINT MOVE FUNCS
def point_move_mouse(modal, context, event, func_data):
    move_target(modal, event.shift)
    point_normals(modal, modal._mode_cache[0])

    modal._mode_cache.pop(2)
    modal._mode_cache.insert(2, modal._mouse_reg_loc)

    modal.redraw_active = True
    return


def point_move_confirm(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    keymap_target(modal)
    modal._mode_cache.pop(4)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._current_tool = modal._point_tool
    end_active_drawing(modal)
    return


def point_move_cancel(modal, context, event, keys, func_data):
    modal.translate_axis = 2
    modal.translate_mode = 0
    clear_translate_axis_draw(modal)
    modal._window.clear_status()
    modal._target_emp.location = modal._mode_cache[3].copy()
    keymap_target(modal)
    point_normals(modal, modal._mode_cache[0])
    modal._mode_cache.pop(4)
    modal._mode_cache.pop(3)
    modal._mode_cache.pop(2)
    modal._current_tool = modal._point_tool
    end_active_drawing(modal)
    return


def point_move_set_x(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 0)
    move_target(modal, event.shift)
    point_normals(modal, modal._mode_cache[0])

    modal.redraw_active = True
    return


def point_move_set_y(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 1)
    move_target(modal, event.shift)
    point_normals(modal, modal._mode_cache[0])

    modal.redraw_active = True
    return


def point_move_set_z(modal, context, event, keys, func_data):
    translate_axis_change(modal, 'TRANSLATING', 2)
    move_target(modal, event.shift)
    point_normals(modal, modal._mode_cache[0])

    modal.redraw_active = True
    return


#
# GIZMO FUNCS
def gizmo_mouse(modal, context, event, func_data):
    start_vec = modal._mode_cache[0]
    view_vec = view3d_utils.region_2d_to_vector_3d(
        modal.act_reg, modal.act_rv3d, Vector((modal._mouse_reg_loc[0], modal._mouse_reg_loc[1])))
    view_orig = view3d_utils.region_2d_to_origin_3d(
        modal.act_reg, modal.act_rv3d, Vector((modal._mouse_reg_loc[0], modal._mouse_reg_loc[1])))

    line_a = view_orig
    line_b = view_orig + view_vec*10000
    # Get start vector to measure angle of mouse
    if modal.translate_axis == 0:
        giz_vec = modal._mode_cache[4] @ Vector((1, 0, 0)) - \
            modal._mode_cache[4].translation

    if modal.translate_axis == 1:
        giz_vec = modal._mode_cache[4] @ Vector((0, 1, 0)) - \
            modal._mode_cache[4].translation

    if modal.translate_axis == 2:
        giz_vec = modal._mode_cache[4] @ Vector((0, 0, 1)) - \
            modal._mode_cache[4].translation

    mouse_co_3d = intersect_line_plane(
        line_a, line_b, modal._mode_cache[4].translation, giz_vec)

    mouse_co_local = modal._mode_cache[4].inverted() @ mouse_co_3d

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
        modal._mode_cache[2] = modal._mode_cache[2]+ang
        modal._mode_cache.pop(0)
        modal._mode_cache.insert(0, mouse_loc)

        if modal._mode_cache[5]:
            rotate_vectors(
                modal, modal._mode_cache[1], modal._mode_cache[2]*ang_fac)
            modal._window.update_gizmo_rot(
                modal._mode_cache[2], modal._mode_cache[3])
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

    if modal._mode_cache[5]:
        add_to_undostack(modal, 1)

    modal.gizmo_click = False
    modal.tool_mode = False
    modal.translate_mode = 0
    modal.translate_axis = 2
    modal._mode_cache.clear()
    modal.click_hold = False
    end_active_drawing(modal)
    return


def gizmo_cancel(modal, context, event, keys, func_data):
    if modal._mode_cache[5]:
        modal._points_container.restore_cached_normals()

        set_new_normals(modal)
    else:
        modal._orbit_ob.matrix_world = modal._mode_cache[4].copy()
        modal._window.update_gizmo_orientation(
            modal._orbit_ob.matrix_world)

    for gizmo in modal._rot_gizmo.gizmos:
        gizmo.active = True
        gizmo.in_use = False

    modal.gizmo_click = False
    modal.tool_mode = False
    modal.translate_mode = 0
    modal.translate_axis = 2
    modal._mode_cache.clear()
    end_active_drawing(modal)
    modal.click_hold = False
    return


#
# MIRROR FUNCS
def mirror_x(modal, context, event, keys, func_data):
    mirror_normals(modal, modal._mode_cache[0], 0)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def mirror_y(modal, context, event, keys, func_data):
    mirror_normals(modal, modal._mode_cache[0], 1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def mirror_z(modal, context, event, keys, func_data):
    mirror_normals(modal, modal._mode_cache[0], 2)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def mirror_cancel(modal, context, event, keys, func_data):
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


#
# FLATTEN FUNCS
def flatten_x(modal, context, event, keys, func_data):
    flatten_normals(modal, modal._mode_cache[0], 0)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def flatten_y(modal, context, event, keys, func_data):
    flatten_normals(modal, modal._mode_cache[0], 1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def flatten_z(modal, context, event, keys, func_data):
    flatten_normals(modal, modal._mode_cache[0], 2)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def flatten_cancel(modal, context, event, keys, func_data):
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


#
# ALIGN FUNCS
def align_pos_x(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, modal._mode_cache[0], 0, 1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def align_pos_y(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, modal._mode_cache[0], 1, 1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def align_pos_z(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, modal._mode_cache[0], 2, 1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def align_neg_x(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, modal._mode_cache[0], 0, -1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def align_neg_y(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, modal._mode_cache[0], 1, -1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def align_neg_z(modal, context, event, keys, func_data):
    align_to_axis_normals(modal, modal._mode_cache[0], 2, -1)
    modal._mode_cache.clear()
    modal.tool_mode = False
    return


def align_cancel(modal, context, event, keys, func_data):
    modal._mode_cache.clear()
    modal.tool_mode = False
    return
