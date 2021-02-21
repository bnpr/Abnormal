import bpy
from .functions_modal import *
from .classes_tool import *


def setup_tools(modal):
    modal.tools = GEN_Modal_Container()
    modal.tools.set_cancel_keys(['Cancel Tool 1', 'Cancel Tool 2'])
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
    tool.add_keymap_argument('Circle Select Increase 1',
                             circle_sel_inc, pre_start=True)
    tool.add_keymap_argument('Circle Select Increase 2',
                             circle_sel_inc, pre_start=True)
    tool.add_keymap_argument('Circle Select Decrease 1',
                             circle_sel_dec, pre_start=True)
    tool.add_keymap_argument('Circle Select Decrease 2',
                             circle_sel_dec, pre_start=True)
    tool.add_keymap_argument('Circle Select Resize Start',
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
    tool.add_confirm_key('Circle Select Resize Confirm')

    modal._circle_resize_tool = tool

    # # ROTATE POINTS
    # tool = modal.tools.add_tool()
    # tool.set_mouse_function(rotate_pos_mouse)
    # tool.set_cancel_function(rotate_pos_cancel)
    # tool.set_confirm_function(rotate_pos_confirm)
    # tool.set_pre_pass_through_function(rotate_pre_navigate)
    # tool.set_post_pass_through_function(rotate_post_navigate)

    # modal._rotate_pos_tool = tool
    return


# ROTATE
# GIZMO CLICK
# SPHEREIZE
# SPHEREIZE MOVE
# POINT
# POINT MOVE


#
# BOX SELECT FUNCS
def box_sel_start(modal, context, event, keys, func_data):
    modal._mode_cache.append(modal._mouse_reg_loc)
    modal.box_selecting = True
    return


def box_sel_mouse(modal, context, event, func_data):
    prev_loc = mathutils.Vector(
        (modal._mode_cache[-1][0], modal._mode_cache[-1][1]))
    cur_loc = mathutils.Vector(modal._mouse_reg_loc)

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
    end_active_drawing(modal)
    return


def box_sel_cancel(modal, context, event, keys, func_data):
    modal.tool_mode = False
    modal.box_selecting = False
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    keymap_refresh(modal)
    end_active_drawing(modal)
    return


#
# LASSO SELECT FUNCS
def lasso_sel_start(modal, context, event, keys, func_data):
    modal._mode_cache.append(modal._mouse_reg_loc)
    modal.lasso_selecting = True
    return


def lasso_sel_mouse(modal, context, event, func_data):
    prev_loc = mathutils.Vector(
        (modal._mode_cache[-1][0], modal._mode_cache[-1][1]))
    cur_loc = mathutils.Vector(modal._mouse_reg_loc)

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
    end_active_drawing(modal)
    return


def lasso_sel_cancel(modal, context, event, keys, func_data):
    modal.tool_mode = False
    modal.lasso_selecting = False
    modal._mode_cache.clear()
    bpy.context.window.cursor_modal_set('DEFAULT')
    keymap_refresh(modal)
    end_active_drawing(modal)
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
    end_active_drawing(modal)
    return


#
# CIRCLE SELECT RESIZE FUNCS
def circle_resize_mouse(modal, context, event, func_data):
    prev_loc = mathutils.Vector(
        (modal._mode_cache[0][0], modal._mode_cache[0][1]))
    cur_loc = mathutils.Vector(
        (modal._mouse_reg_loc[0], modal._mouse_reg_loc[1]))

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
    modal.active_drawing = False
    empty_selection_drawing_lists(modal)
    return


def clear_draw_post_navigate(modal, context, event, func_data):
    modal.active_drawing = True
    return
