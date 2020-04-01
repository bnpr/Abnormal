import bpy
from bpy_extras import view3d_utils
from .functions_drawing import *
from .functions_modal import *
from .classes import *



def basic_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    
    region = context.region
    rv3d = context.region_data

    if event.type in self.nav_list:
        # allow navigation
        status = {'PASS_THROUGH'}
    
    if event.type == 'MIDDLEMOUSE':
        self.waiting = True
        gizmo_hide(self)
    
    update_gizmo = False
    if context.region_data.view_matrix != self.prev_view:
        update_gizmo = True

    if self.waiting and event.value == 'RELEASE':
        update_gizmo = True

    
    if update_gizmo and addon_prefs.rotate_gizmo_use:
        self._window.update_gizmo_pos(self._orbit_ob.matrix_world)
        relocate_gizmo_panel(self)
        self.prev_view = context.region_data.view_matrix.copy()
        self.waiting = False
        if self.rotate_gizmo_draw == False:
            sel_pos = self._points_container.get_selected()
            if len(sel_pos) > 0:
                gizmo_unhide(self)



    if event.type == 'MOUSEMOVE':
        if addon_prefs.rotate_gizmo_use and self.rotate_gizmo_draw:
            giz_hover = self._window.test_gizmo_hover(self._mouse_loc)
        hov_status = self._window.test_hover(self._mouse_loc)



    #select all points
    if event.type == 'A' and event.value == 'PRESS':
        change = False
        if event.alt:
            for po in self._points_container.points:
                if po.valid and po.select == True:
                    po.select = False
                    change = True
            self._active_point = None
        else:
            for po in self._points_container.points:
                if po.valid and po.select == False:
                    po.select = True
                    change = True
        if change:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}
    
    if event.type == 'I' and event.value == 'PRESS' and event.ctrl:
        change = False
        for po in self._points_container.points:
            if po.valid and po.hide == False:
                po.select = not po.select
                change = True
        
        if change:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}
    
    if event.type == 'H':
        if event.alt:
            for po in self._points_container.points:
                if po.hide:
                    po.hide = False
                    po.select = True

        elif event.shift:
            sel_pos = self._points_container.get_unselected()
            for ind in sel_pos:
                self._points_container.points[ind].hide = True
                self._points_container.points[ind].select = False

        else:
            sel_pos = self._points_container.get_selected()
            for ind in sel_pos:
                self._points_container.points[ind].hide = True
                self._points_container.points[ind].select = False
        update_orbit_empty(self,)
        self.redraw = True
        status = {"RUNNING_MODAL"}
    

    if event.type == 'L' and event.value == 'PRESS':
        change = False
        if event.ctrl:
            sel_pos = self._points_container.get_selected()
            new_sel = get_linked_geo(self._object_bm, sel_pos)

            for ind in new_sel:
                if self._points_container.points[ind].select == False:
                    self._points_container.points[ind].select = True
                    change = True
        else:
            #selection test
            face_ind = ray_cast_to_mouse(self, context)
            if face_ind != None:
                sel_ind = self._object_bm.faces[face_ind].verts[0].index
                new_sel = get_linked_geo(self._object_bm, [sel_ind])

                for ind in new_sel:
                    if self._points_container.points[ind].select == False:
                        self._points_container.points[ind].select = True
                        change = True
        
        if change:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
            status = {"RUNNING_MODAL"}


    if event.type == 'B':
        self.box_select_start = True
        bpy.context.window.cursor_modal_set('CROSSHAIR')
        keymap_refresh_box(self)
        gizmo_hide(self)
        status = {"RUNNING_MODAL"}
    

    if event.type == 'C':
        self.circle_select_start = True
        bpy.context.window.cursor_modal_set('CROSSHAIR')
        keymap_refresh_circle(self)
        gizmo_hide(self)
        status = {"RUNNING_MODAL"}

    if event.type == 'LEFTMOUSE' and event.ctrl and event.value == 'PRESS':
        self.lasso_selecting = True
        self._changing_po_cache.append(self._mouse_loc)
        bpy.context.window.cursor_modal_set('CROSSHAIR')
        keymap_refresh_lasso(self)
        gizmo_hide(self)
        status = {"RUNNING_MODAL"}
    

    if event.type == 'R' and event.value == 'PRESS':
        if event.alt:
            if addon_prefs.rotate_gizmo_use:
                loc = self._orbit_ob.location.copy()
                self._orbit_ob.matrix_world = self._object.matrix_world
                self._orbit_ob.matrix_world.translation = loc
                self._window.update_gizmo_orientation(self._orbit_ob.matrix_world)
        else:
            sel_pos = self._points_container.get_selected()

            if len(sel_pos) > 0:
                sel_cos = self._points_container.get_selected_cos()
                avg_loc = average_vecs(sel_cos)

                cache_norms = []
                for ind in sel_pos:
                    po = self._points_container.points[ind]
                    norms = []
                    for l_norm in po.loop_normals:
                        norms.append(l_norm)
                    cache_norms.append(norms)


                self._window.set_status('VIEW ROTATION')

                self._changing_po_cache.clear()
                self._changing_po_cache.append(self._mouse_loc)
                self._changing_po_cache.append(avg_loc)
                self._changing_po_cache.append(cache_norms)
                self._changing_po_cache.append(0)
                self._changing_po_cache.append(1)
                self.rotating = True
                del(sel_cos)
                del(avg_loc)
                keymap_refresh_rotating(self)
                gizmo_hide(self)
        status = {"RUNNING_MODAL"}
    

    if event.type == 'Z' and event.value == 'PRESS':
        if event.ctrl:
            if event.shift:
                move_undostack(self, 1, -1)   
            else:
                move_undostack(self, 1, 1)
        else:
            self._x_ray_mode = not self._x_ray_mode
            self._window.boolean_toggle_id(51)
        status = {"RUNNING_MODAL"}
    
    if event.type == 'X' and event.value == 'PRESS' and event.ctrl:
        if event.shift:
            move_undostack(self, 0, -1)   
        else:
            move_undostack(self, 0, 1)
        status = {"RUNNING_MODAL"}

    #test selection of points/roots and hovering of buttons
    if event.type == 'RIGHTMOUSE' and event.value == 'PRESS' and event.ctrl != True and addon_prefs.left_select == False:
        sel_res = selection_test(self, context, event)
        if sel_res:
            self.redraw = True
            add_to_undostack(self, 0)
            update_orbit_empty(self)
            status = {'RUNNING_MODAL'}
        status = {"RUNNING_MODAL"}

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and event.ctrl != True:
        no_gizmo = gizmo_init(self, context, event)
        
        if no_gizmo:
            hov_status = self._window.test_hover(self._mouse_loc)
            if hov_status == 'EDGE':
                self.resizing = True
                self._window.start_resize(self._mouse_loc)
            elif hov_status == 'PANEL_HEADER' or hov_status == 'SUBPANEL_HEADER':
                self.pre_moving = True
                self.pre_moving_no_coll = False
                self._window.start_move(self._mouse_loc)
            elif hov_status == 'PANEL' or hov_status == 'SUBPANEL':
                self.pre_moving = True
                self.pre_moving_no_coll = True
                self._window.start_move(self._mouse_loc)
            elif hov_status != None:
                self.pre_item_click = True
                self._stored_mouse = [self._mouse_loc[0], self._mouse_loc[1]]


            if hov_status == None:
                if addon_prefs.left_select:
                    sel_res = selection_test(self, context, event)
                    if sel_res:
                        self.redraw = True
                        add_to_undostack(self, 0)
                        update_orbit_empty(self)
                        status = {'RUNNING_MODAL'}
            else:
                status = {'RUNNING_MODAL'}
    
    #cancel modal
    if event.type in {'ESC'} and event.value == 'PRESS':
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob
        
        
        #restore normals
        ob.data.normals_split_custom_set(self.og_loop_norms)
        
        finish_modal(self)
        status = {'CANCELLED'}
    
    return status



def pre_moving_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'MOUSEMOVE':
        click_res = self._window.test_click()
        if click_res != None:
            if self._window.panels[click_res[1]].moveable:
                if abs(self._mouse_loc[0] - self._window.panel_move_cache[1][0]) > 5:
                    self.moving = True
                    self.pre_moving = False
                    self.pre_moving_no_coll = False
                if abs(self._mouse_loc[1] - self._window.panel_move_cache[1][1]) > 5:
                    self.moving = True
                    self.pre_moving = False
                    self.pre_moving_no_coll = False
    
    elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        if self.pre_moving_no_coll == False:
            self._window.panel_collapse_test()
        
        self.pre_moving = False
        self.pre_moving_no_coll = False
    return status


def moving_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'MOUSEMOVE':
        self._window.move_panel( self._mouse_loc )
    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        self._window.move_panel( self._mouse_loc )
        if self._window.panel_move_cache[0][0] == 2:
            region = bpy.context.region
            rv3d = bpy.context.region_data
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, self._orbit_ob.location)

            panel = self._window.panels[2]
            panel.reposition_offset = [panel.position[0]-rco[0], panel.position[1]-rco[1]]
        self.moving = False
        self._window.confirm_move()
    return status


def resizing_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    
    if event.type == 'MOUSEMOVE':
        self._window.resize_panel( self._mouse_loc )
    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        self._window.resize_panel( self._mouse_loc )
        self.resizing = False
        self._window.confirm_resize()
    return status


def pre_item_click_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    
    if event.type == 'MOUSEMOVE':
        click_res = self._window.test_click()
        if click_res != None:
            if click_res[0] == 'NUM_BAR':
                if abs(self._mouse_loc[0] - self._stored_mouse[0]) > 5:
                    self._window.start_num_slide(self._mouse_loc)
                    self.num_sliding = True
                    self.pre_item_click = False
                    self._stored_mouse.clear()
    

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        hov_status = self._window.test_hover(self._mouse_loc)
        click_res = self._window.test_click()
        
        if click_res != None:
            status = button_pressed(self, event, click_res[0], click_res[2])

        self.pre_item_click = False
        del(click_res)
    return status





def rotating_keymap(self, context, event):
    status = {'RUNNING_MODAL'}


    if event.type == 'X' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 0)
        self._changing_po_cache[4] = translate_axis_side(self)
        rotate_vectors(self, self._changing_po_cache[3]*self._changing_po_cache[4])
        self.redraw = True
    

    if event.type == 'Y' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 1)
        self._changing_po_cache[4] = translate_axis_side(self)
        rotate_vectors(self, self._changing_po_cache[3]*self._changing_po_cache[4])
        self.redraw = True


    if event.type == 'Z' and event.value == 'PRESS':
        translate_axis_change(self, 'ROTATING', 2)
        self._changing_po_cache[4] = translate_axis_side(self)
        rotate_vectors(self, self._changing_po_cache[3]*self._changing_po_cache[4])
        self.redraw = True
        
    
    
    if event.type == 'MOUSEMOVE':
        region = bpy.context.region
        rv3d = bpy.context.region_data
        center = view3d_utils.location_3d_to_region_2d(region, rv3d, self._changing_po_cache[1])

        start_vec = mathutils.Vector((self._changing_po_cache[0][0]-center[0], self._changing_po_cache[0][1]-center[1] ))
        mouse_vec = mathutils.Vector((self._mouse_loc[0]-center[0], self._mouse_loc[1]-center[1] ))

        ang = mouse_vec.angle_signed(start_vec)
        if event.shift:
            ang *= 0.1
        
        if ang != 0.0:
            self._changing_po_cache[3] = self._changing_po_cache[3]+ang
            rotate_vectors(self, self._changing_po_cache[3]*self._changing_po_cache[4])
            self._changing_po_cache.pop(0)
            self._changing_po_cache.insert(0, self._mouse_loc)

        self.redraw = True

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        add_to_undostack(self, 1)
        self._changing_po_cache.clear()
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.rotating = False
        keymap_refresh_base(self)
        gizmo_unhide(self)

    if event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for l, l_norm in enumerate(po.loop_normals):
                po.loop_normals[l] = self._changing_po_cache[2][i][l].copy()

        set_new_normals(self)
        self._changing_po_cache.clear()
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.redraw = True
        self.rotating = False
        keymap_refresh_base(self)
        gizmo_unhide(self)


    return status


def num_sliding_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    abn_props = context.scene.abnormal_props
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    
    if event.type == 'MOUSEMOVE':
        new_value = self._window.slide_number(self._mouse_loc, event.shift)

        if self._window.num_slide_cache[3] == 52:
            addon_prefs.normal_size = new_value
            self.redraw = True
        
        if self._window.num_slide_cache[3] == 53:
            addon_prefs.line_brightness = new_value
            self.redraw = True
        
        if self._window.num_slide_cache[3] == 54:
            addon_prefs.point_size = new_value
            self.redraw = True
    
        if self._window.num_slide_cache[3] == 56:
            abn_props.smooth_strength = new_value
        
        if self._window.num_slide_cache[3] == 57:
            new_value = self._window.slide_number(self._mouse_loc, event.shift, fac=0.06)
            abn_props.smooth_iters = new_value
        
        if self._window.num_slide_cache[3] == 91:
            new_value = self._window.slide_number(self._mouse_loc, event.shift, fac=1)
            abn_props.gizmo_size = new_value
            self.rot_gizmo.update_size(new_value)
            self._window.update_gizmo_pos(self._orbit_ob.matrix_world)

    
        if self._window.num_slide_cache[3] == 58:
            self.target_strength = new_value
            sel_pos = self._points_container.get_selected()
            if len(sel_pos) != 0:
                if self.sphereize_mode:
                    sphereize_normals(self, sel_pos)
                if self.point_mode:
                    point_normals(self, sel_pos)

    #confirm slide change
    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        self._window.confirm_num_slide()
        self.num_sliding = False
    

    #cancel slide change restore original
    if event.type == 'RIGHTMOUSE':
        og_value = self._window.cancel_num_slide()

        if self._window.num_slide_cache[3] == 52:
            addon_prefs.normal_size = og_value
            self.redraw = True
        
        if self._window.num_slide_cache[3] == 53:
            addon_prefs.line_brightness = og_value
            self.redraw = True
        
        if self._window.num_slide_cache[3] == 54:
            addon_prefs.point_size = og_value
            self.redraw = True
        
        if self._window.num_slide_cache[3] == 56:
            abn_props.smooth_strength = og_value

        if self._window.num_slide_cache[3] == 57:
            abn_props.smooth_iters = og_value

        if self._window.num_slide_cache[3] == 91:
            abn_props.gizmo_size = og_value
            self.rot_gizmo.update_size(og_value)
            self._window.update_gizmo_pos(self._orbit_ob.matrix_world)
    
        if self._window.num_slide_cache[3] == 58:
            self.target_strength = og_value
            sel_pos = self._points_container.get_selected()
            if len(sel_pos) != 0:
                if self.sphereize_mode:
                    sphereize_normals(self, sel_pos)
                if self.point_mode:
                    point_normals(self, sel_pos)
        
        self.num_sliding = False
    
    return status



def sphereize_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    
    region = context.region
    rv3d = context.region_data
    
    if event.type in self.nav_list:
        # allow navigation
        status = {'PASS_THROUGH'}
    
        


    if event.type == 'MOUSEMOVE':
        hov_status = self._window.test_hover(self._mouse_loc)


    if event.type == 'N':
        status = {'PASS_THROUGH'}
    
    if event.type == 'G' and event.value == 'PRESS':
        sel_pos = self._points_container.get_selected()
        if event.alt:
            if len(sel_pos) > 0:
                sel_cos = self._points_container.get_selected_cos()
                avg_loc = average_vecs(sel_cos)

                self.target_emp.location = avg_loc
                sphereize_normals(self, sel_pos)

        else:
            if len(sel_pos) > 0:
                sel_cos = self._points_container.get_selected_cos()
                avg_loc = average_vecs(sel_cos)

                cache_norms = []
                for ind in sel_pos:
                    po = self._points_container.points[ind]
                    norms = []
                    for l_norm in po.loop_normals:
                        norms.append(l_norm)
                    cache_norms.append(norms)

                sphereize_normals(self, sel_pos)
                self._window.set_status('VIEW TRANSLATION')

                region = bpy.context.region
                rv3d = bpy.context.region_data
                rco = view3d_utils.location_3d_to_region_2d(region, rv3d, avg_loc)

                self._changing_po_cache.insert(0, self._mouse_loc)
                self._changing_po_cache.insert(1, self.target_emp.location.copy())
                self._changing_po_cache.insert(2, cache_norms)
                self._changing_po_cache.insert(3, rco)

                self.sphereize_mode = False
                self.sphereize_move = True
                keymap_refresh_target_move(self)



    if event.type == 'Z' and event.value == 'PRESS':
        self._x_ray_mode = not self._x_ray_mode
        self._window.boolean_toggle_id(51)
    

    #test selection of points/roots and hovering of buttons
    if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and event.ctrl != True:
        hov_status = self._window.test_hover(self._mouse_loc)
        if hov_status == 'EDGE':
            self.resizing = True
            self._window.start_resize(self._mouse_loc)
        elif hov_status == 'PANEL_HEADER' or hov_status == 'SUBPANEL_HEADER':
            self.pre_moving = True
            self.pre_moving_no_coll = False
            self._window.start_move(self._mouse_loc)
        elif hov_status == 'PANEL' or hov_status == 'SUBPANEL':
            self.pre_moving = True
            self.pre_moving_no_coll = True
            self._window.start_move(self._mouse_loc)
        elif hov_status != None:
            self.pre_item_click = True
            self._stored_mouse = [self._mouse_loc[0], self._mouse_loc[1]]

        if hov_status == None:
            status = {'PASS_THROUGH'}

    return status

def sphereize_move_keymap(self, context, event):
    status = {'RUNNING_MODAL'}


    if event.type == 'X' and event.value == 'PRESS':
        translate_axis_change(self, 'TRANSLATING', 0)
        move_target(self, event.shift)
        self.redraw = True
    

    if event.type == 'Y' and event.value == 'PRESS':
        translate_axis_change(self, 'TRANSLATING', 1)
        move_target(self, event.shift)
        self.redraw = True


    if event.type == 'Z' and event.value == 'PRESS':
        translate_axis_change(self, 'TRANSLATING', 2)
        move_target(self, event.shift)
        self.redraw = True




    if event.type == 'MOUSEMOVE':
        sel_pos = self._points_container.get_selected()
        
        move_target(self, event.shift)
        sphereize_normals(self, sel_pos)

        self._changing_po_cache.pop(0)
        self._changing_po_cache.insert(0, self._mouse_loc)

        self.redraw = True
    

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.sphereize_mode = True
        self.sphereize_move = False
        keymap_refresh_target(self)
        while len(self._changing_po_cache) > 1:
            self._changing_po_cache.pop(0)

    if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for l, l_norm in enumerate(po.loop_normals):
                po.loop_normals[l] = self._changing_po_cache[2][i][l].copy()

        set_new_normals(self)
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.redraw = True
        self.sphereize_mode = True
        self.sphereize_move = False
        self.target_emp.location = self._changing_po_cache[1].copy()
        keymap_refresh_target(self)
        while len(self._changing_po_cache) > 1:
            self._changing_po_cache.pop(0)


    return status




def point_keymap(self, context, event):
    status = {'RUNNING_MODAL'}
    
    region = context.region
    rv3d = context.region_data
    
    if event.type in self.nav_list:
        # allow navigation
        status = {'PASS_THROUGH'}
    


    if event.type == 'MOUSEMOVE':
        hov_status = self._window.test_hover(self._mouse_loc)

    if event.type == 'N':
        status = {'PASS_THROUGH'}
    
    if event.type == 'G' and event.value == 'PRESS':
        sel_pos = self._points_container.get_selected()
        if event.alt:
            if len(sel_pos) > 0:
                sel_cos = self._points_container.get_selected_cos()
                avg_loc = average_vecs(sel_cos)

                self.target_emp.location = avg_loc
                point_normals(self, sel_pos)

        else:
            if len(sel_pos) > 0:
                sel_cos = self._points_container.get_selected_cos()
                avg_loc = average_vecs(sel_cos)
                
                cache_norms = []
                for ind in sel_pos:
                    po = self._points_container.points[ind]
                    norms = []
                    for l_norm in po.loop_normals:
                        norms.append(l_norm)
                    cache_norms.append(norms)

                point_normals(self, sel_pos)
                self._window.set_status('VIEW TRANSLATION')

                region = bpy.context.region
                rv3d = bpy.context.region_data
                rco = view3d_utils.location_3d_to_region_2d(region, rv3d, avg_loc)

                self._changing_po_cache.insert(0, self._mouse_loc)
                self._changing_po_cache.insert(1, self.target_emp.location.copy())
                self._changing_po_cache.insert(2, cache_norms)
                self._changing_po_cache.insert(3, rco)

                self.point_mode = False
                self.point_move = True
                keymap_refresh_target_move(self)



    if event.type == 'Z' and event.value == 'PRESS':
        self._x_ray_mode = not self._x_ray_mode
        self._window.boolean_toggle_id(51)
    

    #test selection of points/roots and hovering of buttons
    if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and event.ctrl != True:
        hov_status = self._window.test_hover(self._mouse_loc)
        if hov_status == 'EDGE':
            self.resizing = True
            self._window.start_resize(self._mouse_loc)
        elif hov_status == 'PANEL_HEADER' or hov_status == 'SUBPANEL_HEADER':
            self.pre_moving = True
            self.pre_moving_no_coll = False
            self._window.start_move(self._mouse_loc)
        elif hov_status == 'PANEL' or hov_status == 'SUBPANEL':
            self.pre_moving = True
            self.pre_moving_no_coll = True
            self._window.start_move(self._mouse_loc)
        elif hov_status != None:
            self.pre_item_click = True
            self._stored_mouse = [self._mouse_loc[0], self._mouse_loc[1]]

        status = {'RUNNING_MODAL'}

    return status

def point_move_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    


    if event.type == 'X' and event.value == 'PRESS':
        translate_axis_change(self, 'TRANSLATING', 0)
        move_target(self, event.shift)
        self.redraw = True
    

    if event.type == 'Y' and event.value == 'PRESS':
        translate_axis_change(self, 'TRANSLATING', 1)
        move_target(self, event.shift)
        self.redraw = True


    if event.type == 'Z' and event.value == 'PRESS':
        translate_axis_change(self, 'TRANSLATING', 2)
        move_target(self, event.shift)
        self.redraw = True




    if event.type == 'MOUSEMOVE':
        sel_pos = self._points_container.get_selected()
        
        move_target(self, event.shift)
        point_normals(self, sel_pos)

        self._changing_po_cache.pop(0)
        self._changing_po_cache.insert(0, self._mouse_loc)

        self.redraw = True
    

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.point_mode = True
        self.point_move = False
        keymap_refresh_target(self)
        while len(self._changing_po_cache) > 1:
            self._changing_po_cache.pop(0)

    if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for l, l_norm in enumerate(po.loop_normals):
                po.loop_normals[l] = self._changing_po_cache[2][i][l].copy()

        set_new_normals(self)
        self.translate_axis = 2
        self.translate_mode = 0
        clear_translate_axis_draw(self)
        self._window.clear_status()
        self.redraw = True
        self.point_mode = True
        self.point_move = False
        self.target_emp.location = self._changing_po_cache[1].copy()
        keymap_refresh_target(self)
        while len(self._changing_po_cache) > 1:
            self._changing_po_cache.pop(0)


    return status



def gizmo_click_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'MOUSEMOVE':
        region = bpy.context.region
        rv3d = bpy.context.region_data



        start_vec = self._changing_po_cache[0]
        view_vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1])))
        view_orig = view3d_utils.region_2d_to_origin_3d(region, rv3d, mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1])))
        line_a = view_orig
        line_b = view_orig + view_vec*10000
        if self._changing_po_cache[1][0] == 'ROT_X':
            x_vec = self._changing_po_cache[5] @ mathutils.Vector((1,0,0)) - self._changing_po_cache[5].translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(line_a, line_b, self._changing_po_cache[5].translation, x_vec)
        if self._changing_po_cache[1][0] == 'ROT_Y':
            y_vec = self._changing_po_cache[5] @ mathutils.Vector((0,1,0)) - self._changing_po_cache[5].translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(line_a, line_b, self._changing_po_cache[5].translation, y_vec)
        if self._changing_po_cache[1][0] == 'ROT_Z':
            z_vec = self._changing_po_cache[5] @ mathutils.Vector((0,0,1)) - self._changing_po_cache[5].translation
            mouse_co_3d = mathutils.geometry.intersect_line_plane(line_a, line_b, self._changing_po_cache[5].translation, z_vec)

        mouse_co_local = self._changing_po_cache[5].inverted() @ mouse_co_3d

        self.translate_mode = 2
        if self._changing_po_cache[1][0] == 'ROT_X':
            mouse_loc = mouse_co_local.yz
            ang = start_vec.angle_signed(mouse_co_local.yz)*-1
            self.translate_axis = 0
        if self._changing_po_cache[1][0] == 'ROT_Y':
            mouse_loc = mouse_co_local.xz
            ang = start_vec.angle_signed(mouse_co_local.xz)*-1
            self.translate_axis = 1
        if self._changing_po_cache[1][0] == 'ROT_Z':
            mouse_loc = mouse_co_local.xy
            ang = start_vec.angle_signed(mouse_co_local.xy)*-1
            self.translate_axis = 2

        if event.shift:
            ang *= 0.1
        
        if ang != 0.0:
            self._changing_po_cache[3] = self._changing_po_cache[3]+ang
            self._changing_po_cache.pop(0)
            self._changing_po_cache.insert(0, mouse_loc)

            if self._changing_po_cache[6]:
                rotate_vectors(self, self._changing_po_cache[3])
                self._window.update_gizmo_rot(self._changing_po_cache[3], self._changing_po_cache[4])
                self.redraw = True
            else:
                if self.translate_axis == 0:
                    rot_mat = mathutils.Euler([ang,0,0]).to_matrix().to_4x4()
                if self.translate_axis == 1:
                    rot_mat = mathutils.Euler([0,-ang,0]).to_matrix().to_4x4()
                if self.translate_axis == 2:
                    rot_mat = mathutils.Euler([0,0,ang]).to_matrix().to_4x4()

                self._orbit_ob.matrix_world = self._orbit_ob.matrix_world @ rot_mat
                self._window.update_gizmo_orientation(self._orbit_ob.matrix_world)
                


    

    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        for gizmo in self._window.gizmo_sets[self._changing_po_cache[1][1][0]].gizmos:
            gizmo.active = True
            gizmo.in_use = False
        
        if self._changing_po_cache[6]:
            add_to_undostack(self, 1)

        self.gizmo_click = False
        self.translate_mode = 0
        self.translate_axis = 2
        self._changing_po_cache.clear()
        

    if event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
        if self._changing_po_cache[6]:
            sel_pos = self._points_container.get_selected()
            for i, ind in enumerate(sel_pos):
                po = self._points_container.points[ind]

                for l, l_norm in enumerate(po.loop_normals):
                    po.loop_normals[l] = self._changing_po_cache[2][i][l].copy()

            set_new_normals(self)
        else:
            self._orbit_ob.matrix_world = self._changing_po_cache[5].copy()
            self._window.update_gizmo_orientation(self._orbit_ob.matrix_world)
        
        for gizmo in self._window.gizmo_sets[self._changing_po_cache[1][1][0]].gizmos:
            gizmo.active = True
            gizmo.in_use = False
        
        self.gizmo_click = False
        self.translate_mode = 0
        self.translate_axis = 2
        self._changing_po_cache.clear()
        self.redraw = True


    return status




def box_select_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
        self._changing_po_cache.append(self._mouse_loc)
        self.box_select_start = False
        self.box_selecting = True
    

    if event.type == 'MOUSEMOVE' and self.box_selecting:
        if event.alt:
            if len(self._changing_po_cache) == 1:
                self._changing_po_cache.append(self._mouse_loc)
            else:
                prev_loc = mathutils.Vector(( self._changing_po_cache[1][0], self._changing_po_cache[1][1] ))
                cur_loc = mathutils.Vector(( self._mouse_loc[0], self._mouse_loc[1] ))

                new_loc = cur_loc - prev_loc
                new_loc[0] += self._changing_po_cache[0][0]
                new_loc[1] += self._changing_po_cache[0][1]

                self._changing_po_cache.clear()

                self._changing_po_cache.append([ new_loc[0], new_loc[1] ])
                self._changing_po_cache.append(self._mouse_loc)
            
        else:
            if len(self._changing_po_cache) == 2:
                self._changing_po_cache.pop(1)


    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        sel_res = box_selection_test(self, context, event)
        
        if sel_res:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
        
        if self._active_point != None:
            if self._points_container.points[self._active_point].select == False:
                self._active_point = None
            

        self.box_select_start = False
        self.box_selecting = False
        self._changing_po_cache.clear()
        self.redraw = True
        bpy.context.window.cursor_modal_set('DEFAULT')
        update_orbit_empty(self)
        keymap_refresh_base(self)
        gizmo_unhide(self)
    
    
    if event.type == 'RIGHTMOUSE':
        
        self.box_select_start = False
        self.box_selecting = False
        bpy.context.window.cursor_modal_set('DEFAULT')
        self._changing_po_cache.clear()
        keymap_refresh_base(self)
        gizmo_unhide(self)

    
    
    return status


def lasso_select_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type == 'MOUSEMOVE':
        if len(self._changing_po_cache) > 0:
            prev_loc = mathutils.Vector(( self._changing_po_cache[-1][0], self._changing_po_cache[-1][1] ))
            cur_loc = mathutils.Vector(( self._mouse_loc[0], self._mouse_loc[1] ))

            if (cur_loc-prev_loc).length > 10.0:
                self._changing_po_cache.append(self._mouse_loc)


    if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
        sel_res = lasso_selection_test(self, context, event)

        self.lasso_selecting = False
        self._changing_po_cache.clear()
        if sel_res:
            add_to_undostack(self, 0)
            self.redraw = True
            update_orbit_empty(self)
        
        if self._active_point != None:
            if self._points_container.points[self._active_point].select == False:
                self._active_point = None
        keymap_refresh_base(self)
        gizmo_unhide(self)
    
    
    if event.type == 'RIGHTMOUSE':
        self.lasso_selecting = False
        self._changing_po_cache.clear()
        keymap_refresh_base(self)
        gizmo_unhide(self)
    
    
    return status


def circle_select_keymap(self, context, event):
    status = {'RUNNING_MODAL'}

    if event.type in self.nav_list:
        status = {'PASS_THROUGH'}
    
    if event.type == 'F':
        if event.value == 'PRESS':
            self.circle_resizing = True
            if self._mouse_loc[0]-self.circle_radius < 0:
                self._changing_po_cache.append([ self._mouse_loc[0]+self.circle_radius, self._mouse_loc[1]  ])
            else:
                self._changing_po_cache.append([ self._mouse_loc[0]-self.circle_radius, self._mouse_loc[1]  ])
            self._changing_po_cache.append(self.circle_radius)
        
        elif event.value == 'RELEASE':
            self.circle_resizing = False
            self._changing_po_cache.clear()
    
    if self.circle_resizing:
        prev_loc = mathutils.Vector(( self._changing_po_cache[0][0], self._changing_po_cache[0][1] ))
        cur_loc = mathutils.Vector(( self._mouse_loc[0], self._mouse_loc[1] ))

        diff = int((cur_loc-prev_loc).length)
        self.circle_radius = diff

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            self.circle_resizing = False
            self.circle_radius = self._changing_po_cache[1]
            self._changing_po_cache.clear()
    
    else:
        if event.type == 'LEFT_BRACKET' and event.value == 'PRESS':
            self.circle_radius -= 10
        
        if event.type == 'RIGHT_BRACKET' and event.value == 'PRESS':
            self.circle_radius += 10
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.circle_status = event.ctrl
            sel_res = circle_selection_test(self, context, event, self.circle_radius, self.circle_status)
            if self._active_point != None:
                if self._points_container.points[self._active_point].select == False:
                    self._active_point = None
            if sel_res:
                self.redraw = True
            
            self.circle_select_start = False
            self.circle_selecting = True

        if event.type == 'MOUSEMOVE' and self.circle_selecting:
            sel_res = circle_selection_test(self, context, event, self.circle_radius, self.circle_status)
            if self._active_point != None:
                if self._points_container.points[self._active_point].select == False:
                    self._active_point = None
            if sel_res:
                self.redraw = True

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.circle_select_start = True
            self.circle_selecting = False
            update_orbit_empty(self)
        
        
        if event.type == 'RIGHTMOUSE':
            add_to_undostack(self, 0)
            self.circle_select_start = False
            self.circle_selecting = False
            keymap_refresh_base(self)
            gizmo_unhide(self)
    
    
    return status

