import bpy
from bpy_extras import view3d_utils
from .functions_drawing import *
from .functions_modal import *
from .classes import *


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

    # select all bezier points
    if event.type == 'A' and event.value == 'PRESS':
        self._window.bezier_box_select_points(not event.alt)
    # toggle cyclic of bezier lines
    if event.type == 'F' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}
        bezier_hover = self._window.bezier_box_toggle_cyclic()

    # rotate select bezier points
    if event.type == 'R' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}
        if event.alt:
            bezier_hover = self._window.bezier_box_clear_rotation(arguments=[
                                                                  self, event])

        else:
            bezier_hover, bezier_id, self.bezier_changing, mid_co = self._window.bezier_box_rotate_points(
                0.0, arguments=[event])

            if self.bezier_changing:
                self._mode_cache.append(mid_co)
                self._mouse_init = self._mouse_reg_loc
                self.rotating = True
                keymap_rotating(self)

    # change sharpness of selected points
    if event.type == 'S' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}
        if event.alt:
            bezier_hover = self._window.bezier_box_clear_sharpness(arguments=[
                                                                   self, event])

        else:
            bezier_hover, bezier_id, self.bezier_changing = self._window.bezier_box_sharpen_points(
                0.0, arguments=[event])

            if self.bezier_changing:
                self.sharpness_changing = True
                self._mouse_init = self._mouse_reg_loc
                keymap_sharpness_changing(self)

    # deleted selected points and roots
    if event.type == 'X' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}
        bez_hover = self._window.bezier_box_delete_points(
            arguments=[event])

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and not event.ctrl:
        status = {'RUNNING_MODAL'}

        # Test 2d ui selection
        panel_status = self._window.test_click_down(
            self._mouse_reg_loc, event.shift, arguments=[event])
        self.click_hold = True
        if panel_status:
            if panel_status[0] == 'GIZMO':
                gizmo_click_init(self, event, panel_status[1])

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

    # cancel modal
    if event.type in {'ESC'} and event.value == 'PRESS':
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, True)
        status = {'CANCELLED'}

    if event.type in {'TAB'} and event.value == 'PRESS':
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

    # allow viewport navigation
    if event.type in self.nav_list:
        # allow navigation
        status = {'PASS_THROUGH'}

    # test hover ui
    if event.type == 'MOUSEMOVE' and self.click_hold == False:
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

    # select all normals
    if event.type == 'A' and event.value == 'PRESS':
        change = False
        if event.alt:
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
        else:
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
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}

    # invert selection
    if event.type == 'I' and event.value == 'PRESS' and event.ctrl:
        change = False
        for po in self._points_container.points:
            if po.hide == False:
                for loop in po.loops:
                    if loop.hide == False:
                        loop.set_select(not loop.select)
                        change = True

                po.set_selection_from_loops()

        if change:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}

    # hide normals
    if event.type == 'H' and event.value == 'PRESS':
        if event.alt:
            for po in self._points_container.points:
                if po.hide:
                    po.set_hide(False)
                    po.set_select(True)
                else:
                    for loop in po.loops:
                        if loop.hide:
                            loop.set_hide(False)
                            loop.set_select(True)

        elif event.shift:
            sel_inds = self._points_container.get_unselected_loops()
            for ind in sel_inds:
                self._points_container.points[ind[0]
                                              ].loops[ind[1]].set_hide(True)
                self._points_container.points[ind[0]
                                              ].loops[ind[1]].set_select(False)
                self._points_container.points[ind[0]
                                              ].set_selection_from_loops()
                self._points_container.points[ind[0]].set_hidden_from_loops()

        else:
            sel_inds = self._points_container.get_selected_loops()
            for ind in sel_inds:
                self._points_container.points[ind[0]
                                              ].loops[ind[1]].set_hide(True)
                self._points_container.points[ind[0]
                                              ].loops[ind[1]].set_select(False)
                self._points_container.points[ind[0]
                                              ].set_selection_from_loops()
                self._points_container.points[ind[0]].set_hidden_from_loops()

        update_orbit_empty(self)
        self.redraw = True
        status = {"RUNNING_MODAL"}

    # select linked normals
    if event.type == 'L' and event.value == 'PRESS':
        change = False
        if event.ctrl:
            sel_inds = self._points_container.get_selected_loops()
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
        else:
            # selection test
            face_ind = ray_cast_to_mouse(self)
            if face_ind != None:
                sel_ind = self._object_bm.faces[face_ind].verts[0].index

                vis_pos = self._points_container.get_visible()
                new_sel = get_linked_geo(
                    self._object_bm, [sel_ind], vis=vis_pos)

                for ind in new_sel:
                    if self._points_container.points[ind].select == False:
                        self._points_container.points[ind].set_select(True)
                        change = True

        if change:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}

    # box select
    if event.type == 'B' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}
        self.box_select_start = True
        bpy.context.window.cursor_modal_set('CROSSHAIR')
        keymap_box_selecting(self)
        gizmo_update_hide(self, False)

    # circle select
    if event.type == 'C' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}
        self.circle_select_start = True
        bpy.context.window.cursor_modal_set('CROSSHAIR')
        keymap_circle_selecting(self)
        gizmo_update_hide(self, False)

    # lasso select
    if event.type == 'V' and event.value == 'PRESS':
        status = {"RUNNING_MODAL"}
        self.lasso_select_start = True
        bpy.context.window.cursor_modal_set('CROSSHAIR')
        keymap_lasso_selecting(self)
        gizmo_update_hide(self, False)

    # rotation
    if event.type == 'R' and event.value == 'PRESS':
        if event.alt:
            if self._use_gizmo:
                loc = self._orbit_ob.location.copy()
                self._orbit_ob.matrix_world = self._object.matrix_world
                self._orbit_ob.matrix_world.translation = loc
                self._window.update_gizmo_orientation(
                    self._orbit_ob.matrix_world)
        else:
            update_filter_weights(self)
            sel_inds = self._points_container.get_selected_loops()

            if len(sel_inds) > 0:
                sel_cos = self._points_container.get_selected_loop_cos()
                avg_loc = average_vecs(sel_cos)

                self._points_container.cache_current_normals()

                self._window.set_status('VIEW ROTATION')

                self._mode_cache.clear()
                self._mode_cache.append(self._mouse_reg_loc)
                self._mode_cache.append(avg_loc)
                self._mode_cache.append(0)
                self._mode_cache.append(1)
                self.rotating = True
                keymap_rotating(self)
                gizmo_update_hide(self, False)
        status = {"RUNNING_MODAL"}

    if event.type == 'Z' and event.value == 'PRESS':
        if event.ctrl:
            if event.shift:
                move_undostack(self, -1)
            else:
                move_undostack(self, 1)
        else:
            self._x_ray_mode = not self._x_ray_mode
            self._xray_bool.toggle_bool()
        status = {"RUNNING_MODAL"}

    click = (event.type == 'RIGHTMOUSE' and self._left_select == False) or (
        event.type == 'LEFTMOUSE' and self._left_select)
    if click and event.value == 'PRESS' and event.ctrl != True and event.alt != True:
        sel_res = selection_test(self, event)
        if sel_res:
            self.redraw = True
            add_to_undostack(self, 0)
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}

    # cancel modal
    if event.type in {'ESC'} and event.value == 'PRESS':
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, True)
        status = {'CANCELLED'}

    if event.type in {'TAB'} and event.value == 'PRESS':
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob

        finish_modal(self, False)
        status = {'FINISHED'}

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

    elif event.type == 'ESC' and event.value == 'PRESS':
        self._window.type_cancel()
        self.typing = False
    elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
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


def rotating_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    self.active_drawing = True

    if event.type == 'X' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 0)
        self._mode_cache[3] = translate_axis_side(self)
        rotate_vectors(
            self, self._mode_cache[2]*self._mode_cache[3])
        self.redraw = True

    if event.type == 'Y' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 1)
        self._mode_cache[3] = translate_axis_side(self)
        rotate_vectors(
            self, self._mode_cache[2]*self._mode_cache[3])
        self.redraw = True

    if event.type == 'Z' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 2)
        self._mode_cache[3] = translate_axis_side(self)
        rotate_vectors(
            self, self._mode_cache[2]*self._mode_cache[3])
        self.redraw = True

    if event.type == 'R' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 2)
        self._mode_cache[3] = translate_axis_side(self)
        rotate_vectors(
            self, self._mode_cache[2]*self._mode_cache[3])
        self.redraw = True

    if event.type == 'MOUSEMOVE':
        center = view3d_utils.location_3d_to_region_2d(
            self.act_reg, self.act_rv3d, self._mode_cache[1])

        start_vec = mathutils.Vector(
            (self._mode_cache[0][0]-center[0], self._mode_cache[0][1]-center[1]))
        mouse_vec = mathutils.Vector(
            (self._mouse_reg_loc[0]-center[0], self._mouse_reg_loc[1]-center[1]))

        ang = mouse_vec.angle_signed(start_vec)
        if event.shift:
            ang *= 0.1

        if ang != 0.0:
            self._mode_cache[2] = self._mode_cache[2]+ang
            rotate_vectors(
                self, self._mode_cache[2]*self._mode_cache[3])
            self._mode_cache.pop(0)
            self._mode_cache.insert(0, self._mouse_reg_loc)

            self.redraw = True

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        self._points_container.clear_cached_normals()

        add_to_undostack(self, 1)
        self._mode_cache.clear()
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.rotating = False
        keymap_refresh(self)
        gizmo_update_hide(self, True)

    if event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
        self._points_container.restore_cached_normals()

        set_new_normals(self)
        self._mode_cache.clear()
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.redraw = True
        self.rotating = False
        keymap_refresh(self)
        gizmo_update_hide(self, True)

    return status


def gizmo_click_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'MOUSEMOVE':
        start_vec = self._mode_cache[0]
        view_vec = view3d_utils.region_2d_to_vector_3d(
            self.act_reg, self.act_rv3d, mathutils.Vector((self._mouse_reg_loc[0], self._mouse_reg_loc[1])))
        view_orig = view3d_utils.region_2d_to_origin_3d(
            self.act_reg, self.act_rv3d, mathutils.Vector((self._mouse_reg_loc[0], self._mouse_reg_loc[1])))
        line_a = view_orig
        line_b = view_orig + view_vec*10000
        if self._mode_cache[1][0] == 'ROT_X':
            x_vec = self._mode_cache[4] @ mathutils.Vector(
                (1, 0, 0)) - self._mode_cache[4].translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(
                line_a, line_b, self._mode_cache[4].translation, x_vec)
        if self._mode_cache[1][0] == 'ROT_Y':
            y_vec = self._mode_cache[4] @ mathutils.Vector(
                (0, 1, 0)) - self._mode_cache[4].translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(
                line_a, line_b, self._mode_cache[4].translation, y_vec)
        if self._mode_cache[1][0] == 'ROT_Z':
            z_vec = self._mode_cache[4] @ mathutils.Vector(
                (0, 0, 1)) - self._mode_cache[4].translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(
                line_a, line_b, self._mode_cache[4].translation, z_vec)

        mouse_co_local = self._mode_cache[4].inverted() @ mouse_co_3d

        self.translate_mode = 2
        if self._mode_cache[1][0] == 'ROT_X':
            mouse_loc = mouse_co_local.yz
            ang = start_vec.angle_signed(mouse_co_local.yz)*-1
            self.translate_axis = 0
        if self._mode_cache[1][0] == 'ROT_Y':
            mouse_loc = mouse_co_local.xz
            ang = start_vec.angle_signed(mouse_co_local.xz)*-1
            self.translate_axis = 1
        if self._mode_cache[1][0] == 'ROT_Z':
            mouse_loc = mouse_co_local.xy
            ang = start_vec.angle_signed(mouse_co_local.xy)*-1
            self.translate_axis = 2

        if event.shift:
            ang *= 0.1

        if ang != 0.0:
            self._mode_cache[2] = self._mode_cache[2]+ang
            self._mode_cache.pop(0)
            self._mode_cache.insert(0, mouse_loc)

            if self._mode_cache[5]:
                rotate_vectors(self, self._mode_cache[2])
                self._window.update_gizmo_rot(
                    self._mode_cache[2], self._mode_cache[3])
                self.redraw = True
            else:
                if self.translate_axis == 0:
                    rot_mat = mathutils.Euler([ang, 0, 0]).to_matrix().to_4x4()
                if self.translate_axis == 1:
                    rot_mat = mathutils.Euler(
                        [0, -ang, 0]).to_matrix().to_4x4()
                if self.translate_axis == 2:
                    rot_mat = mathutils.Euler([0, 0, ang]).to_matrix().to_4x4()

                self._orbit_ob.matrix_world = self._orbit_ob.matrix_world @ rot_mat
                self._window.update_gizmo_orientation(
                    self._orbit_ob.matrix_world)

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        for gizmo in self._rot_gizmo.gizmos:
            gizmo.active = True
            gizmo.in_use = False

        if self._mode_cache[5]:
            add_to_undostack(self, 1)

        self.gizmo_click = False
        self.translate_mode = 0
        self.translate_axis = 2
        self._mode_cache.clear()
        self.click_hold = False

    if event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
        if self._mode_cache[5]:
            self._points_container.restore_cached_normals()

            set_new_normals(self)
        else:
            self._orbit_ob.matrix_world = self._mode_cache[4].copy()
            self._window.update_gizmo_orientation(self._orbit_ob.matrix_world)

        for gizmo in self._rot_gizmo.gizmos:
            gizmo.active = True
            gizmo.in_use = False

        self.gizmo_click = False
        self.translate_mode = 0
        self.translate_axis = 2
        self._mode_cache.clear()
        self.redraw = True
        self.click_hold = False
    return status


#
#


def sphereize_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type in self.nav_list:
        # allow navigation
        status = {'PASS_THROUGH'}

    # test hover panels
    if event.type == 'MOUSEMOVE' and self.click_hold == False:
        hov_status = self._window.test_hover(self._mouse_reg_loc)
        self.ui_hover = hov_status != None

    # click down move
    if event.type == 'MOUSEMOVE' and self.click_hold:
        self._window.click_down_move(
            self._mouse_reg_loc, event.shift, arguments=[event])

    if event.type == 'N':
        status = {'PASS_THROUGH'}

    if event.type == 'G' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()
        if event.alt:
            if len(sel_inds) > 0:
                sel_cos = self._points_container.get_selected_loop_cos()
                avg_loc = average_vecs(sel_cos)

                self._target_emp.location = avg_loc
                sphereize_normals(self, sel_inds)

        else:
            if len(sel_inds) > 0:
                sel_cos = self._points_container.get_selected_loop_cos()

                self._points_container.cache_current_normals()

                sphereize_normals(self, sel_inds)
                self._window.set_status('VIEW TRANSLATION')

                rco = view3d_utils.location_3d_to_region_2d(
                    self.act_reg, self.act_rv3d, self._target_emp.location)

                self._mode_cache.insert(0, self._mouse_reg_loc)
                self._mode_cache.insert(
                    1, self._target_emp.location.copy())
                self._mode_cache.insert(2, rco)

                self.sphereize_mode = False
                self.sphereize_move = True
                keymap_target_move(self)

    if event.type == 'Z' and event.value == 'PRESS':
        self._x_ray_mode = not self._x_ray_mode
        self._xray_bool.toggle_bool()

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}

        panel_status = False
        # Test 2d ui selection
        if self._sphere_panel.visible:
            panel_status = self._sphere_panel.test_click_down(
                self._mouse_reg_loc, event.shift, arguments=[event])
            self.click_hold = True

        if panel_status:
            if panel_status[0] == {'CANCELLED'}:
                status = panel_status[0]
            if panel_status[0] == {'FINISHED'}:
                status = panel_status[0]

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        status = {'RUNNING_MODAL'}
        panel_status = None

        if self._sphere_panel.visible:
            panel_status = self._sphere_panel.test_click_up(
                self._mouse_reg_loc, event.shift, arguments=[event])
            self.click_hold = False

        if panel_status:
            if panel_status[0] == 'NUMBER_BAR_TYPE':
                self.typing = True
            if panel_status[0] == {'CANCELLED'}:
                status = panel_status[0]
            if panel_status[0] == {'FINISHED'}:
                status = panel_status[0]

    return status


def sphereize_move_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'X' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()

        translate_axis_change(self, 'TRANSLATING', 0)
        move_target(self, event.shift)
        sphereize_normals(self, sel_inds)

        self.redraw = True

    if event.type == 'Y' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()

        translate_axis_change(self, 'TRANSLATING', 1)
        move_target(self, event.shift)
        sphereize_normals(self, sel_inds)

        self.redraw = True

    if event.type == 'Z' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()

        translate_axis_change(self, 'TRANSLATING', 2)
        move_target(self, event.shift)
        sphereize_normals(self, sel_inds)

        self.redraw = True

    if event.type == 'MOUSEMOVE':
        sel_inds = self._points_container.get_selected_loops()

        move_target(self, event.shift)
        sphereize_normals(self, sel_inds)

        self._mode_cache.pop(0)
        self._mode_cache.insert(0, self._mouse_reg_loc)

        self.redraw = True

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.sphereize_mode = True
        self.sphereize_move = False
        keymap_target(self)
        while len(self._mode_cache) > 1:
            self._mode_cache.pop(0)

    if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()
        for i, ind in enumerate(sel_inds):
            po = self._points_container.points[ind]

            for loop in po.loops:
                loop.normal = self._mode_cache[2][i][l].copy()

        set_new_normals(self)
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.redraw = True
        self.sphereize_mode = True
        self.sphereize_move = False
        self._target_emp.location = self._mode_cache[1].copy()
        keymap_target(self)
        while len(self._mode_cache) > 1:
            self._mode_cache.pop(0)
    return status


def point_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type in self.nav_list:
        # allow navigation
        status = {'PASS_THROUGH'}

    # test hover panels
    if event.type == 'MOUSEMOVE' and self.click_hold == False:
        hov_status = self._window.test_hover(self._mouse_reg_loc)
        self.ui_hover = hov_status != None

    # click down move
    if event.type == 'MOUSEMOVE' and self.click_hold:
        self._window.click_down_move(
            self._mouse_reg_loc, event.shift, arguments=[event])

    if event.type == 'N':
        status = {'PASS_THROUGH'}

    if event.type == 'G' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()
        if event.alt:
            if len(sel_inds) > 0:
                sel_cos = self._points_container.get_selected_loop_cos()
                avg_loc = average_vecs(sel_cos)

                self._target_emp.location = avg_loc
                point_normals(self, sel_inds)

        else:
            if len(sel_inds) > 0:
                sel_cos = self._points_container.get_selected_loop_cos()

                self._points_container.cache_current_normals()

                point_normals(self, sel_inds)
                self._window.set_status('VIEW TRANSLATION')

                rco = view3d_utils.location_3d_to_region_2d(
                    self.act_reg, self.act_rv3d, self._target_emp.location)

                self._mode_cache.insert(0, self._mouse_reg_loc)
                self._mode_cache.insert(
                    1, self._target_emp.location.copy())
                self._mode_cache.insert(2, rco)

                self.point_mode = False
                self.point_move = True
                keymap_target_move(self)

    if event.type == 'Z' and event.value == 'PRESS':
        self._x_ray_mode = not self._x_ray_mode
        self._xray_bool.toggle_bool()

        status = {'RUNNING_MODAL'}

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        status = {'RUNNING_MODAL'}

        panel_status = False
        # Test 2d ui selection
        if self._point_panel.visible:
            panel_status = self._point_panel.test_click_down(
                self._mouse_reg_loc, event.shift, arguments=[event])
            self.click_hold = True

        if panel_status:
            if panel_status[0] == {'CANCELLED'}:
                status = panel_status[0]
            if panel_status[0] == {'FINISHED'}:
                status = panel_status[0]

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        status = {'RUNNING_MODAL'}
        panel_status = None

        if self._point_panel.visible:
            panel_status = self._point_panel.test_click_up(
                self._mouse_reg_loc, event.shift, arguments=[event])
            self.click_hold = False

        if panel_status:
            if panel_status[0] == 'NUMBER_BAR_TYPE':
                self.typing = True
            if panel_status[0] == {'CANCELLED'}:
                status = panel_status[0]
            if panel_status[0] == {'FINISHED'}:
                status = panel_status[0]

    return status


def point_move_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'X' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()

        translate_axis_change(self, 'TRANSLATING', 0)
        move_target(self, event.shift)
        point_normals(self, sel_inds)

        self.redraw = True

    if event.type == 'Y' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()

        translate_axis_change(self, 'TRANSLATING', 1)
        move_target(self, event.shift)
        point_normals(self, sel_inds)

        self.redraw = True

    if event.type == 'Z' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()

        translate_axis_change(self, 'TRANSLATING', 2)
        move_target(self, event.shift)
        point_normals(self, sel_inds)

        self.redraw = True

    if event.type == 'MOUSEMOVE':
        sel_inds = self._points_container.get_selected_loops()

        move_target(self, event.shift)
        point_normals(self, sel_inds)

        self._mode_cache.pop(0)
        self._mode_cache.insert(0, self._mouse_reg_loc)

        self.redraw = True

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.point_mode = True
        self.point_move = False
        keymap_target(self)
        while len(self._mode_cache) > 1:
            self._mode_cache.pop(0)

    if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
        sel_inds = self._points_container.get_selected_loops()
        for i, ind in enumerate(sel_inds):
            po = self._points_container.points[ind]

            for loop in po.loops:
                loop.normal = self._mode_cache[2][i][l].copy()

        set_new_normals(self)
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.redraw = True
        self.point_mode = True
        self.point_move = False
        self._target_emp.location = self._mode_cache[1].copy()
        keymap_target(self)
        while len(self._mode_cache) > 1:
            self._mode_cache.pop(0)
    return status


#
#


def box_select_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    self.active_drawing = True

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self._mode_cache.append(self._mouse_reg_loc)
        self.box_select_start = False
        self.box_selecting = True

    if event.type == 'MOUSEMOVE' and self.box_selecting:
        prev_loc = mathutils.Vector(
            (self._mode_cache[-1][0], self._mode_cache[-1][1]))
        cur_loc = mathutils.Vector(self._mouse_reg_loc)

        if event.alt:
            if self._mouse_init == None:
                self._mouse_init = self._mouse_reg_loc

            else:
                offset = [self._mouse_reg_loc[0]-self._mouse_init[0],
                          self._mouse_reg_loc[1]-self._mouse_init[1]]
                for p in range(len(self._mode_cache)):
                    self._mode_cache.append(
                        [self._mode_cache[0][0]+offset[0], self._mode_cache[0][1]+offset[1]])
                    self._mode_cache.pop(0)
                self._mouse_init = self._mouse_reg_loc

        else:
            if self._mouse_init:
                self._mouse_init = None

            if (cur_loc-prev_loc).length > 10.0:
                self._mode_cache.append(self._mouse_reg_loc)

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        change = box_selection_test(self, event)
        if change:
            add_to_undostack(self, 0)
            self.redraw = True

        self.box_select_start = False
        self.box_selecting = False
        self._mode_cache.clear()
        bpy.context.window.cursor_modal_set('DEFAULT')
        update_orbit_empty(self)
        keymap_refresh(self)

    if event.type == 'RIGHTMOUSE':
        self.box_select_start = False
        self.box_selecting = False
        bpy.context.window.cursor_modal_set('DEFAULT')
        gizmo_update_hide(self, True)
        self._mode_cache.clear()
        keymap_refresh(self)

    return status


def lasso_select_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    self.active_drawing = True

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self._mode_cache.append(self._mouse_reg_loc)
        self.lasso_select_start = False
        self.lasso_selecting = True

    if event.type == 'MOUSEMOVE' and self.lasso_selecting:
        prev_loc = mathutils.Vector(
            (self._mode_cache[-1][0], self._mode_cache[-1][1]))
        cur_loc = mathutils.Vector(self._mouse_reg_loc)

        if event.alt:
            if self._mouse_init == None:
                self._mouse_init = self._mouse_reg_loc

            else:
                offset = cur_loc - prev_loc
                for p in range(len(self._mode_cache)):
                    self._mode_cache.append(
                        [self._mode_cache[0][0]+offset[0], self._mode_cache[0][1]+offset[1]])
                    self._mode_cache.pop(0)
                self._mouse_init = self._mouse_reg_loc

        else:
            if self._mouse_init:
                self._mouse_init = None

            if (cur_loc-prev_loc).length > 10.0:
                self._mode_cache.append(self._mouse_reg_loc)

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        change = lasso_selection_test(self, event)
        if change:
            add_to_undostack(self, 0)
            self.redraw = True

        self.lasso_selecting = False
        self._mode_cache.clear()
        bpy.context.window.cursor_modal_set('DEFAULT')
        keymap_refresh(self)
        update_orbit_empty(self)

    if event.type == 'RIGHTMOUSE':
        self.lasso_selecting = False
        self._mode_cache.clear()
        bpy.context.window.cursor_modal_set('DEFAULT')
        keymap_refresh(self)
        gizmo_update_hide(self, True)

    return status


def circle_select_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    self.active_drawing = True

    if event.type in self.nav_list:
        status = {'PASS_THROUGH'}
        self.navigating = True

    if event.type == 'F':
        if event.value == 'PRESS':
            self.circle_resizing = True
            if self._mouse_reg_loc[0]-self.circle_radius < 0:
                self._mode_cache.append(
                    [self._mouse_reg_loc[0]+self.circle_radius, self._mouse_reg_loc[1]])
            else:
                self._mode_cache.append(
                    [self._mouse_reg_loc[0]-self.circle_radius, self._mouse_reg_loc[1]])
            self._mode_cache.append(self.circle_radius)

        elif event.value == 'RELEASE':
            self.circle_resizing = False
            self._mode_cache.clear()

    if self.circle_resizing:
        prev_loc = mathutils.Vector(
            (self._mode_cache[0][0], self._mode_cache[0][1]))
        cur_loc = mathutils.Vector(self._mouse_reg_loc)

        diff = int((cur_loc-prev_loc).length)
        self.circle_radius = diff

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.circle_resizing = False
            self.circle_radius = self._mode_cache[1]
            self._mode_cache.clear()

    else:
        if event.type == 'LEFT_BRACKET' and event.value == 'PRESS':
            self.circle_radius -= 10

        if event.type == 'RIGHT_BRACKET' and event.value == 'PRESS':
            self.circle_radius += 10

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            circle_selection_test(self, event, self.circle_radius)
            self.redraw = True

            self.circle_select_start = False
            self.circle_selecting = True

        if event.type == 'MOUSEMOVE' and self.circle_selecting:
            circle_selection_test(self, event, self.circle_radius)
            self.redraw = True

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.circle_select_start = True
            self.circle_selecting = False

        if event.type == 'RIGHTMOUSE':
            add_to_undostack(self, 0)

            self.circle_select_start = False
            self.circle_selecting = False
            bpy.context.window.cursor_modal_set('DEFAULT')
            keymap_refresh(self)
            update_orbit_empty(self)

    return status
