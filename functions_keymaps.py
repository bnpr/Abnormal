import bpy
from bpy_extras import view3d_utils
from .functions_drawing import *
from .functions_modal import *
from .classes import *
import time


def basic_ui_hover_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    # test hover panels
    if event.type == 'MOUSEMOVE' and self.click_hold == False:
        hov_status = self._window.test_hover(self._mouse_reg_loc)
        self.ui_hover = hov_status != None

    # click down move
    if event.type == 'MOUSEMOVE' and self.click_hold:
        self._window.click_down_move(
            self._mouse_reg_loc, event.shift, arguments=[event])

    # Panel scrolling
    if event.type == 'WHEELDOWNMOUSE' and event.value == 'PRESS':
        scroll_status = self._window.scroll_panel(10)
        if scroll_status:
            status = {'RUNNING_MODAL'}

    if event.type == 'WHEELUPMOUSE' and event.value == 'PRESS':
        scroll_status = self._window.scroll_panel(-10)
        if scroll_status:
            status = {'RUNNING_MODAL'}

    # undo
    if event.type == 'Z' and event.value == 'PRESS' and event.ctrl and event.shift == False:
        move_undostack(self, 1)
    # redo
    if event.type == 'Z' and event.value == 'PRESS' and event.ctrl and event.shift:
        move_undostack(self, -1)

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and not event.ctrl:
        status = {'RUNNING_MODAL'}

        # Test 2d ui selection
        panel_status = self._window.test_click_down(
            self._mouse_reg_loc, event.shift, arguments=[event])
        self.click_hold = True
        if panel_status:
            if panel_status[0] == 'GIZMO':
                gizmo_click_init(self, event, panel_status[1])
                self.ui_hover = False

            else:
                if panel_status[0] == {'CANCELLED'}:
                    status = panel_status[0]
                if panel_status[0] == {'FINISHED'}:
                    status = panel_status[0]

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        status = {'RUNNING_MODAL'}

        panel_status = self._window.test_click_up(
            self._mouse_reg_loc, event.shift, arguments=[event])
        self.click_hold = False
        if panel_status:
            rco = view3d_utils.location_3d_to_region_2d(
                self.act_reg, self.act_rv3d, self._orbit_ob.location)
            if rco != None:
                self.gizmo_reposition_offset = [
                    self._gizmo_panel.position[0]-rco[0], self._gizmo_panel.position[1]-rco[1]]

            if panel_status[0] == 'NUMBER_BAR_TYPE':
                self.typing = True
            if panel_status[0] == {'CANCELLED'}:
                status = panel_status[0]
            if panel_status[0] == {'FINISHED'}:
                status = panel_status[0]

    keys = keys_find(self.keymap.keymap_items, event)
    if len(keys) == 0:
        keys = []
    #     return status
    # else:
    #     status = {"RUNNING_MODAL"}

    # Toggle Gizmo
    if 'Toggle Gizmo' in keys:
        self._use_gizmo = not self._use_gizmo
        self._gizmo_bool.toggle_bool()
        update_orbit_empty(self)
        if self._container.sel_status.any():
            gizmo_update_hide(self, True)
        else:
            gizmo_update_hide(self, False)
        return status

    # Cancel modal
    if 'Cancel Modal' in keys:
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, True)
        status = {'CANCELLED'}

    # Confirm modal
    if 'Confirm Modal' in keys:
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, False)
        status = {'FINISHED'}

    return status


def basic_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    # test hover ui
    if event.type == 'MOUSEMOVE' and self.click_hold == False:
        status = {'RUNNING_MODAL'}
        hov_status = self._window.test_hover(self._mouse_reg_loc)
        self.ui_hover = hov_status != None
        if self.ui_hover:
            return status

    # Gizmo stuff
    if event.type == 'MIDDLEMOUSE':
        self.waiting = True
        gizmo_update_hide(self, False)

    # view moved so update gizmo
    update_gizmo = False
    if context.region_data.view_matrix != self.prev_view:
        update_gizmo = True

    # middle mouse released so update gizmo
    if self.waiting and event.value == 'RELEASE':
        update_gizmo = True

    if update_gizmo and self._use_gizmo:
        self._window.update_gizmo_pos(self._orbit_ob.matrix_world)
        relocate_gizmo_panel(self)
        self.prev_view = context.region_data.view_matrix.copy()
        self.waiting = False

        if self._container.sel_status.any():
            gizmo_update_hide(self, True)
        else:
            gizmo_update_hide(self, False)

    # undo redo
    if event.type == 'Z' and event.value == 'PRESS' and event.ctrl:
        if event.shift:
            move_undostack(self, -1)
        else:
            move_undostack(self, 1)
        return status

    #
    #
    #

    keys = keys_find(self.keymap.keymap_items, event)
    if len(keys) == 0:
        return {'PASS_THROUGH'}

    #
    #

    # SHORTCUT KEYS
    if True:
        # hide unselected normals
        if 'Hide Unselected' in keys:
            if self._container.sel_status.all() == False:
                self._container.hide_status[~self._container.sel_status] = True
                add_to_undostack(self, 0)
            return status

        # hide selected normals
        if 'Hide Selected' in keys:
            if self._container.sel_status.any():
                self._container.hide_status[self._container.sel_status] = True
                self._container.sel_status[:] = False
                self._container.act_status[:] = False
                add_to_undostack(self, 0)
            return status

        # unhide normals
        if 'Unhide' in keys:
            if self._container.hide_status.any():
                self._container.sel_status[self._container.hide_status] = True
                self._container.hide_status[:] = False
                add_to_undostack(self, 0)
            return status

        # clear rotation
        if 'Reset Gizmo Rotation' in keys:
            if self._use_gizmo:
                loc = self._orbit_ob.location.copy()
                self._orbit_ob.matrix_world = self._object.matrix_world
                self._orbit_ob.matrix_world.translation = loc
                self._window.update_gizmo_orientation(
                    self._orbit_ob.matrix_world)
            return status

        # Rotate Normals
        if 'Rotate Normals' in keys:
            update_filter_weights(self)

            if self._container.sel_status.any():
                avg_loc = np.mean(
                    self._container.loop_coords[self._container.sel_status], axis=0)

                self._window.set_status('VIEW ROTATION')

                self._container.cache_norms = self._container.new_norms.copy()

                self._mode_cache.clear()
                self._mode_cache.append(avg_loc)
                self._mode_cache.append(0)
                self._mode_cache.append(1)
                self._mouse_init = self._mouse_reg_loc

                self.rotating = True
                self._current_tool = self._rotate_norms_tool
                self.tool_mode = True
                keymap_rotating(self)
                gizmo_update_hide(self, False)
                self.selection_drawing = True
                start_active_drawing(self)
            return status

        # toggle xray
        if 'Toggle X-Ray' in keys:
            self._x_ray_mode = not self._x_ray_mode
            self._xray_bool.toggle_bool()
            return status

        # Toggle Gizmo
        if 'Toggle Gizmo' in keys:
            self._use_gizmo = not self._use_gizmo
            self._gizmo_bool.toggle_bool()
            update_orbit_empty(self)
            if self._container.sel_status.any():
                gizmo_update_hide(self, True)
            else:
                gizmo_update_hide(self, False)
            return status

        # Mirror Normals
        if 'Mirror Normals Start' in keys:
            if self._container.sel_status.any():
                self.tool_mode = True
                self._current_tool = self._mirror_tool

        # Smooth Normals
        if 'Smooth Normals' in keys:
            if self._container.sel_status.any():
                smooth_normals(self, 0.5)

        # Flatten Normals
        if 'Flatten Normals Start' in keys:
            if self._container.sel_status.any():
                self.tool_mode = True
                self._current_tool = self._flatten_tool

        # Align Normals
        if 'Align Normals Start' in keys:
            if self._container.sel_status.any():
                self.tool_mode = True
                self._current_tool = self._align_tool

        # Copy Active Normal
        if 'Copy Active Normal' in keys:
            if self._container.sel_status.any():
                self._copy_normals, self._copy_normals_tangs = get_po_loop_data(
                    self, self._active_point)

        # Paste Stored Normal
        if 'Paste Stored Normal' in keys:
            if self._container.sel_status.any():
                paste_normal(self)

        # Paste Active Normal to Selected
        if 'Paste Active Normal to Selected' in keys:
            if self._container.sel_status.any():
                copy_active_to_selected(self)

        # Set Normals Outside
        if 'Set Normals Outside' in keys:
            if self._container.sel_status.any():
                set_outside_inside(self, 1)

        # Set Normals Inside
        if 'Set Normals Inside' in keys:
            if self._container.sel_status.any():
                set_outside_inside(self, -1)

        # Flip Normals
        if 'Flip Normals' in keys:
            if self._container.sel_status.any():
                flip_normals(self)

        # Reset Vectors
        if 'Reset Vectors' in keys:
            if self._container.sel_status.any():
                reset_normals(self)

        # Average Individual Normals
        if 'Average Individual Normals' in keys:
            if self._container.sel_status.any():
                average_vertex_normals(self)

        # Average Selected Normals
        if 'Average Selected Normals' in keys:
            if self._container.sel_status.any():
                average_selected_normals(self)

        # Set Normals from Faces
        if 'Set Normals From Faces' in keys:
            if self._container.sel_status.any():
                set_normals_from_faces(self)

    #
    #

    # SELECTION KEYS
    if True:
        # invert selection
        if 'Invert Selection' in keys:
            if self._container.hide_status.all() == False:
                self._container.act_status[:] = False
                self._container.sel_status[~self._container.hide_status] = ~self._container.sel_status[~self._container.hide_status]
                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # box select
        if 'Box Start' in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._box_sel_tool
            self.tool_mode = True
            self.selection_drawing = True
            keymap_box_selecting(self)
            gizmo_update_hide(self, False)
            return status

        # circle select
        if 'Circle Start' in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._circle_sel_tool
            self.tool_mode = True
            self.selection_drawing = True
            self.circle_selecting = True
            keymap_circle_selecting(self)
            gizmo_update_hide(self, False)
            return status

        # lasso select
        if 'Lasso Start' in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._lasso_sel_tool
            self.tool_mode = True
            self.selection_drawing = True
            keymap_lasso_selecting(self)
            gizmo_update_hide(self, False)
            return status

        # select all normals
        if 'Select All' in keys:
            change = not self._container.sel_status.all()
            if change:
                self._container.sel_status[:] = True
                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # unselect all normals
        if 'Unselect All' in keys:
            change = self._container.sel_status.any()
            if change:
                self._container.sel_status[:] = False
                self._container.act_status[:] = False

                self._active_point = None
                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # select linked normals
        if 'Select Linked' in keys:
            change = False
            if self._container.sel_status.any():
                vis_pos = get_visible_points(self)
                sel_inds = get_selected_points(self, any_selected=True)

                new_sel = get_linked_geo(
                    self._object_bm, list(sel_inds), vis=list(vis_pos))

                if len(new_sel) > 0:
                    self._container.sel_status[get_vert_ls(
                        self, new_sel)] = True
                    add_to_undostack(self, 0)
            return status

        # select linked under cursor normals
        if 'Select Hover Linked' in keys:
            # selection test
            face_res = ray_cast_to_mouse(self)
            if face_res != None:
                vis_pos = get_visible_points(self)
                hov_inds = [
                    v.index for v in self._object_bm.faces[face_res[1]].verts if v.index in vis_pos]

                new_sel = get_linked_geo(
                    self._object_bm, hov_inds, vis=list(vis_pos))

                if len(new_sel) > 0:
                    self._container.sel_status[get_vert_ls(
                        self, new_sel)] = True
                    add_to_undostack(self, 0)
            return status

        # New Click selection
        if 'New Click Selection' in keys:
            sel_res = selection_test(self, False)
            if sel_res:
                add_to_undostack(self, 0)
            return status

        # Add Click selection
        if 'Add Click Selection' in keys:
            sel_res = selection_test(self, True)
            if sel_res:
                add_to_undostack(self, 0)
            return status

        # New Edge loop selection
        if 'New Loop Selection' in keys:
            sel_res = loop_selection_test(self, False)
            if sel_res:
                add_to_undostack(self, 0)
            return status

        # Add Edge loop selection
        if 'Add Loop Selection' in keys:
            sel_res = loop_selection_test(self, True)
            if sel_res:
                add_to_undostack(self, 0)
            return status

        # New Vertex Path selection
        if 'New Shortest Path Selection' in keys:
            sel_res = path_selection_test(self, False)
            if sel_res:
                add_to_undostack(self, 0)
            return status

        # Add Vertex Path selection
        if 'Add Shortest Path Selection' in keys:
            sel_res = path_selection_test(self, True)
            if sel_res:
                add_to_undostack(self, 0)
            return status

    #
    #

    # cancel modal
    if 'Cancel Modal' in keys:
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, True)
        status = {'CANCELLED'}
        return status

    # Confirm modal
    if 'Confirm Modal' in keys:
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, False)
        status = {'FINISHED'}
        return status

    #
    #

    # allow viewport navigation
    nav_status = test_navigation_key(self.nav_list, event)
    if nav_status:
        # allow navigation
        status = {'PASS_THROUGH'}

    return status


def typing_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    # typing keys
    if event.type == 'RET' and event.value == 'PRESS':
        self._window.type_confirm(arguments=[event])
        self.typing = False
    elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        self._window.type_confirm(arguments=[event])
        self.typing = False

    elif (event.type == 'ESC' or event.type == 'RIGHTMOUSE') and event.value == 'PRESS':
        self._window.type_cancel()
        self.typing = False

    elif event.type == 'LEFT_ARROW' and event.value == 'PRESS':
        self._window.type_move_pos(-1)
    elif event.type == 'RIGHT_ARROW' and event.value == 'PRESS':
        self._window.type_move_pos(1)

    elif event.type == 'BACK_SPACE' and event.value == 'PRESS':
        self._window.type_backspace_key()
    elif event.type == 'DEL' and event.value == 'PRESS':
        self._window.type_delete_key()

    else:
        self._window.type_add_key(event.ascii)

    return status
