import bpy
from bpy_extras import view3d_utils
from .functions_drawing import *
from .functions_modal import *
from .classes import *


def basic_ui_hover_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    # test hover panels
    if event.type == 'MOUSEMOVE' and self.click_hold == False:
        hov_status = self._window.test_hover(self._mouse_reg_loc.tolist())
        self.ui_hover = hov_status != None

    # click down move
    if event.type == 'MOUSEMOVE' and self.click_hold:
        self._window.click_down_move(
            self._mouse_reg_loc.tolist(), event.shift, arguments=[event])

    # Panel scrolling
    if event.type == 'WHEELDOWNMOUSE' and event.value == 'PRESS':
        scroll_status = self._window.scroll_panel(10)
        if scroll_status:
            status = {'RUNNING_MODAL'}

    if event.type == 'WHEELUPMOUSE' and event.value == 'PRESS':
        scroll_status = self._window.scroll_panel(-10)
        if scroll_status:
            status = {'RUNNING_MODAL'}

    if event.type == 'Z' and event.value == 'PRESS' and event.ctrl:
        if event.shift:
            move_undostack(self, -1)
            self._window.set_key('Undo')
        else:
            move_undostack(self, 1)
            self._window.set_key('Redo')

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and not event.ctrl:
        status = {'RUNNING_MODAL'}

        # Test 2d ui selection
        panel_status = self._window.test_click_down(
            self._mouse_reg_loc.tolist(), event.shift, arguments=[event])
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
            self._mouse_reg_loc.tolist(), event.shift, arguments=[event])
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
    key = 'Toggle Gizmo'
    if key in keys:
        self._use_gizmo = not self._use_gizmo
        self._gizmo_bool.toggle_bool()
        update_orbit_empty(self)
        if self._container.sel_status.any():
            gizmo_update_hide(self, True)
        else:
            gizmo_update_hide(self, False)
        self._window.set_key(key)
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
        hov_status = self._window.test_hover(self._mouse_reg_loc.tolist())
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
            self._window.set_key('Undo')
        else:
            move_undostack(self, 1)
            self._window.set_key('Redo')
        return status

    #
    #
    #

    keys = keys_find(self.keymap.keymap_items, event)
    if len(keys) == 0:
        nav_status = test_navigation_key(self.nav_list, event)
        if nav_status:
            self._window.set_key('Navigation')
        return {'PASS_THROUGH'}

    #
    #

    # SHORTCUT KEYS
    if True:
        # hide unselected normals
        key = 'Hide Unselected'
        if key in keys:
            if self._container.sel_status.all() == False:
                self._container.hide_status[~self._container.sel_status] = True
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # hide selected normals
        key = 'Hide Selected'
        if key in keys:
            if self._container.sel_status.any():
                self._container.hide_status[self._container.sel_status] = True
                self._container.sel_status[:] = False
                self._container.act_status[:] = False
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # unhide normals
        key = 'Unhide'
        if key in keys:
            if self._container.hide_status.any():
                self._container.sel_status[self._container.hide_status] = True
                self._container.hide_status[:] = False
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # clear rotation
        key = 'Reset Gizmo Rotation'
        if key in keys:
            if self._use_gizmo:
                loc = self._orbit_ob.location.copy()
                self._orbit_ob.matrix_world = self._object.matrix_world
                self._orbit_ob.matrix_world.translation = loc
                self._window.update_gizmo_orientation(
                    self._orbit_ob.matrix_world)
            self._window.set_key(key)
            return status

        # Rotate Normals
        key = 'Rotate Normals'
        if key in keys:
            update_filter_weights(self)

            if self._container.sel_status.any():
                avg_loc = np.mean(
                    self._container.loop_coords[self._container.sel_status], axis=0)

                self._window.set_status('VIEW ROTATION')

                self._container.cache_norms[:] = self._container.new_norms

                self._mode_cache.clear()
                self._mode_cache.append(avg_loc)
                self._mode_cache.append(0)
                self._mode_cache.append(1)
                self._mouse_init[:] = self._mouse_reg_loc

                self.rotating = True
                self._current_tool = self._rotate_norms_tool
                self.tool_mode = True
                keymap_rotating(self)
                gizmo_update_hide(self, False)
                self.selection_drawing = True
                start_active_drawing(self)
            self._window.set_key(key)
            return status

        # toggle xray
        key = 'Toggle X-Ray'
        if key in keys:
            self._x_ray_mode = not self._x_ray_mode
            self._xray_bool.toggle_bool()
            self._window.set_key(key)
            return status

        # Toggle Gizmo
        key = 'Toggle Gizmo'
        if key in keys:
            self._use_gizmo = not self._use_gizmo
            self._gizmo_bool.toggle_bool()
            update_orbit_empty(self)
            if self._container.sel_status.any():
                gizmo_update_hide(self, True)
            else:
                gizmo_update_hide(self, False)
            self._window.set_key(key)
            return status

        # Mirror Normals
        key = 'Mirror Normals Start'
        if key in keys:
            if self._container.sel_status.any():
                self.tool_mode = True
                self._current_tool = self._mirror_tool
                keymap_mirror(self)
                self._window.set_key(key)

        # Smooth Normals
        key = 'Smooth Normals'
        if key in keys:
            if self._container.sel_status.any():
                smooth_normals(self, 0.5)
                self._window.set_key(key)

        # Flatten Normals
        key = 'Flatten Normals Start'
        if key in keys:
            if self._container.sel_status.any():
                self.tool_mode = True
                self._current_tool = self._flatten_tool
                keymap_flatten(self)
                self._window.set_key(key)

        # Align Normals
        key = 'Align Normals Start'
        if key in keys:
            if self._container.sel_status.any():
                self.tool_mode = True
                self._current_tool = self._align_tool
                keymap_align(self)
                self._window.set_key(key)

        # Copy Active Normal
        key = 'Copy Active Normal'
        if key in keys:
            if self._container.act_status.any():
                store_active_normal(self)
                self._window.set_key(key)

        # Paste Stored Normal
        key = 'Paste Stored Normal'
        if key in keys:
            if self._container.sel_status.any():
                paste_normal(self)
                self._window.set_key(key)

        # Paste Active Normal to Selected
        key = 'Paste Active Normal to Selected'
        if key in keys:
            if self._container.act_status.any():
                copy_active_to_selected(self)
                self._window.set_key(key)

        # Set Normals Outside
        key = 'Set Normals Outside'
        if key in keys:
            if self._container.sel_status.any():
                set_outside_inside(self, 1)
                self._window.set_key(key)

        # Set Normals Inside
        key = 'Set Normals Inside'
        if key in keys:
            if self._container.sel_status.any():
                set_outside_inside(self, -1)
                self._window.set_key(key)

        # Flip Normals
        key = 'Flip Normals'
        if key in keys:
            if self._container.sel_status.any():
                flip_normals(self)
                self._window.set_key(key)

        # Reset Vectors
        key = 'Reset Vectors'
        if key in keys:
            if self._container.sel_status.any():
                reset_normals(self)
                self._window.set_key(key)

        # Average Individual Normals
        key = 'Average Individual Normals'
        if key in keys:
            if self._container.sel_status.any():
                average_vertex_normals(self)
                self._window.set_key(key)

        # Average Selected Normals
        key = 'Average Selected Normals'
        if key in keys:
            if self._container.sel_status.any():
                average_selected_normals(self)
                self._window.set_key(key)

        # Set Normals from Faces
        key = 'Set Normals From Faces'
        if key in keys:
            if self._container.sel_status.any():
                set_normals_from_faces(self)
                self._window.set_key(key)

    #
    #

    # SELECTION KEYS
    if True:
        # invert selection
        key = 'Invert Selection'
        if key in keys:
            if self._container.hide_status.all() == False:
                self._container.act_status[:] = False
                self._container.sel_status[~self._container.hide_status] = ~self._container.sel_status[~self._container.hide_status]
                self._active_face = None
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # box select
        key = 'Box Select Start'
        if key in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._box_sel_tool
            self.tool_mode = True
            self.selection_drawing = True
            keymap_box_selecting(self)
            gizmo_update_hide(self, False)
            self._window.set_key(key)
            return status

        # circle select
        key = 'Circle Select Start'
        if key in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._circle_sel_tool
            self.tool_mode = True
            self.selection_drawing = True
            self.circle_selecting = True
            keymap_circle_selecting(self)
            gizmo_update_hide(self, False)
            self._window.set_key(key)
            return status

        # lasso select
        key = 'Lasso Select Start'
        if key in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._lasso_sel_tool
            self.tool_mode = True
            self.selection_drawing = True
            keymap_lasso_selecting(self)
            gizmo_update_hide(self, False)
            self._window.set_key(key)
            return status

        # select all normals
        key = 'Select All'
        if key in keys:
            change = not self._container.sel_status.all()
            if change:
                self._container.sel_status[:] = True
                self._active_face = None
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # unselect all normals
        key = 'Unselect All'
        if key in keys:
            change = self._container.sel_status.any()
            if change:
                self._container.sel_status[:] = False
                self._container.act_status[:] = False

                self._active_point = None
                self._active_face = None
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # select linked normals
        key = 'Select Linked'
        if key in keys:
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
            self._window.set_key(key)
            return status

        # select linked under cursor normals
        key = 'Select Hover Linked'
        if key in keys:
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
            self._window.set_key(key)
            return status

        # New Click selection
        key = 'New Click Selection'
        if key in keys:
            sel_res = selection_test(self, False)
            if sel_res:
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # Add Click selection
        key = 'Add Click Selection'
        if key in keys:
            sel_res = selection_test(self, True)
            if sel_res:
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # New Edge loop selection
        key = 'New Loop Selection'
        if key in keys:
            sel_res = loop_selection_test(self, False)
            if sel_res:
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # Add Edge loop selection
        key = 'Add Loop Selection'
        if key in keys:
            sel_res = loop_selection_test(self, True)
            if sel_res:
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # New Vertex Path selection
        key = 'New Shortest Path Selection'
        if key in keys:
            sel_res = path_selection_test(self, False)
            if sel_res:
                add_to_undostack(self, 0)
            self._window.set_key(key)
            return status

        # Add Vertex Path selection
        key = 'Add Shortest Path Selection'
        if key in keys:
            sel_res = path_selection_test(self, True)
            if sel_res:
                add_to_undostack(self, 0)
            self._window.set_key(key)
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
        self._window.set_key('Navigation')

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
