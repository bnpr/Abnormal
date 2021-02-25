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

    # cancel modal
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

        sel_inds = self._points_container.get_selected_loops()
        if len(sel_inds) > 0:
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

    if event.type == 'P' and event.value == 'PRESS':
        update_filter_weights(self)
        sel_inds = self._points_container.get_selected_loops()

        if len(sel_inds) > 0:
            sel_cos = self._points_container.get_selected_loop_cos()
            avg_loc = average_vecs(sel_cos)

            self._points_container.cache_current_normals()
            self.translate_axis = 2
            self.translate_mode = 0

            self._mode_cache.clear()
            self._mode_cache.append(self._mouse_reg_loc)
            self._mode_cache.append(sel_inds)
            self._mode_cache.append(avg_loc)
            self._mode_cache.append(0)
            self._mode_cache.append(1)

            iters = 200
            start = time.time()
            for i in range(iters):
                old_rotate_vectors(self, sel_inds, 0.25)
            old_time = (time.time()-start)/iters
            print(old_time)

            start = time.time()
            for i in range(iters):
                rotate_vectors(self, sel_inds, 0.25)
            new_time = (time.time()-start)/iters
            print(new_time)
            print(old_time/new_time)

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
            sel_inds = self._points_container.get_unselected_loops()
            if sel_inds:
                for ind in sel_inds:
                    self._points_container.points[ind[0]
                                                  ].loops[ind[1]].set_hide(True)
                    self._points_container.points[ind[0]
                                                  ].loops[ind[1]].set_select(False)
                    self._points_container.points[ind[0]
                                                  ].set_selection_from_loops()
                    self._points_container.points[ind[0]
                                                  ].set_hidden_from_loops()

                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # hide selected normals
        if 'Hide Selected' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if sel_inds:
                for ind_set in sel_inds:
                    self._points_container.points[ind_set[0]
                                                  ].loops[ind_set[1]].set_hide(True)
                    self._points_container.points[ind_set[0]
                                                  ].loops[ind_set[1]].set_select(False)
                    self._points_container.points[ind_set[0]
                                                  ].set_selection_from_loops()
                    self._points_container.points[ind_set[0]
                                                  ].set_hidden_from_loops()

                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # unhide normals
        if 'Unhide' in keys:
            change = False
            for po in self._points_container.points:
                if po.hide:
                    change = True
                    po.set_hide(False)
                    po.set_select(True)
                else:
                    for loop in po.loops:
                        if loop.hide:
                            change = True
                            loop.set_hide(False)
                            loop.set_select(True)
            if change:
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
            sel_inds = self._points_container.get_selected_loops()

            if len(sel_inds) > 0:
                sel_cos = self._points_container.get_selected_loop_cos()
                avg_loc = average_vecs(sel_cos)

                self._points_container.cache_current_normals()

                self._window.set_status('VIEW ROTATION')

                self._mode_cache.clear()
                self._mode_cache.append(self._mouse_reg_loc)
                self._mode_cache.append(sel_inds)
                self._mode_cache.append(avg_loc)
                self._mode_cache.append(0)
                self._mode_cache.append(1)
                self.rotating = True
                self._current_tool = self._rotate_norms_tool
                self.tool_mode = True
                keymap_rotating(self)
                gizmo_update_hide(self, False)
                self.active_drawing = True
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
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) > 0:
                gizmo_update_hide(self, True)
            else:
                gizmo_update_hide(self, False)
            return status

        # Mirror Normals
        if 'Mirror Normals Start' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                self._mode_cache.append(sel_inds)
                self.tool_mode = True
                self._current_tool = self._mirror_tool

        # Smooth Normals
        if 'Smooth Normals' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                smooth_normals(self, sel_inds, 0.5)

        # Flatten Normals
        if 'Flatten Normals Start' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                self._mode_cache.append(sel_inds)
                self.tool_mode = True
                self._current_tool = self._flatten_tool

        # Align Normals
        if 'Align Normals Start' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                self._mode_cache.append(sel_inds)
                self.tool_mode = True
                self._current_tool = self._align_tool

        # Copy Active Normal
        if 'Copy Active Normal' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                self._copy_normals, self._copy_normals_tangs = get_po_loop_data(
                    self, self._active_point)

        # Paste Stored Normal
        if 'Paste Stored Normal' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                paste_normal(self, sel_inds)

        # Paste Active Normal to Selected
        if 'Paste Active Normal to Selected' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                copy_active_to_selected(self, sel_inds)

        # Set Normals Outside
        if 'Set Normals Outside' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                set_outside_inside(self, sel_inds, 1)

        # Set Normals Inside
        if 'Set Normals Inside' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                set_outside_inside(self, sel_inds, -1)

        # Flip Normals
        if 'Flip Normals' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                flip_normals(self, sel_inds)

        # Reset Vectors
        if 'Reset Vectors' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                reset_normals(self, sel_inds)

        # Average Individual Normals
        if 'Average Individual Normals' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                average_vertex_normals(self, sel_inds)

        # Average Selected Normals
        if 'Average Selected Normals' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                average_selected_normals(self, sel_inds)

        # Set Normals from Faces
        if 'Set Normals From Faces' in keys:
            sel_inds = self._points_container.get_selected_loops()
            if len(sel_inds) != 0:
                set_normals_from_faces(self, sel_inds)

    #
    #

    # SELECTION KEYS
    if True:
        # invert selection
        if 'Invert Selection' in keys:
            change = False
            for po in self._points_container.points:
                if po.hide == False:
                    for loop in po.loops:
                        if loop.hide == False:
                            loop.set_select(not loop.select)
                            change = True

                    po.set_selection_from_loops()

            if change:
                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # box select
        if 'Box Start' in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._box_sel_tool
            self.tool_mode = True
            self.active_drawing = True
            keymap_box_selecting(self)
            gizmo_update_hide(self, False)
            return status

        # circle select
        if 'Circle Start' in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._circle_sel_tool
            self.tool_mode = True
            self.active_drawing = True
            self.circle_selecting = True
            keymap_circle_selecting(self)
            gizmo_update_hide(self, False)
            return status

        # lasso select
        if 'Lasso Start' in keys:
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self._current_tool = self._lasso_sel_tool
            self.tool_mode = True
            self.active_drawing = True
            keymap_lasso_selecting(self)
            gizmo_update_hide(self, False)
            return status

        # select all normals
        if 'Select All' in keys:
            for po in self._points_container.points:
                if po.select == False:
                    po.set_select(True)
                    change = True
                else:
                    for loop in po.loops:
                        if loop.select:
                            loop.set_select(True)
                            change = True

            if change:
                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # unselect all normals
        if 'Unselect All' in keys:
            change = False
            for po in self._points_container.points:
                if po.select:
                    po.set_select(False)
                    change = True
                else:
                    for loop in po.loops:
                        if loop.select:
                            loop.set_select(False)
                            change = True

            self._points_container.clear_active()
            self._active_point = None

            if change:
                self._active_face = None
                add_to_undostack(self, 0)
            return status

        # select linked normals
        if 'Select Linked' in keys:
            change = False
            sel_inds = self._points_container.get_selected_loops()
            if sel_inds:
                po_inds = []
                for ind_set in sel_inds:
                    if ind_set[0] not in po_inds:
                        po_inds.append(ind_set[0])

                vis_pos = self._points_container.get_visible()
                new_sel = get_linked_geo(self._object_bm, po_inds, vis=vis_pos)

                for ind in new_sel:
                    if self._points_container.points[ind].select == False:
                        self._points_container.points[ind].set_select(True)
                        change = True

                if change:
                    self._active_face = None
                    add_to_undostack(self, 0)
            return status

        # select linked under cursor normals
        if 'Select Hover Linked' in keys:
            # selection test
            face_res = ray_cast_to_mouse(self)
            if face_res != None:
                sel_ind = self._object_bm.faces[face_res[1]].verts[0].index

                vis_pos = self._points_container.get_visible()
                new_sel = get_linked_geo(
                    self._object_bm, [sel_ind], vis=vis_pos)

                for ind in new_sel:
                    if self._points_container.points[ind].select == False:
                        self._points_container.points[ind].set_select(True)
                        change = True

                if change:
                    self._active_face = None
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
            if self._active_point != None or self._active_face != None:
                sel_res = path_selection_test(self, False)
                if sel_res:
                    add_to_undostack(self, 0)
            return status

        # Add Vertex Path selection
        if 'Add Shortest Path Selection' in keys:
            if self._active_point != None or self._active_face != None:
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
