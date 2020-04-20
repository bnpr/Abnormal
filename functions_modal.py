import bpy
import mathutils
import os
from bpy_extras import view3d_utils
from .functions_general import *
from .functions_drawing import *
from .classes import *
from .ui_classes import *


def average_vecs(vecs):
    if len(vecs) > 0:
        vec = mathutils.Vector((0,0,0))
        for v in vecs:
            vec += v
        
        vec = vec/len(vecs)

        return vec
    return None

def set_new_normals(self,):
    for ed in self._object.data.edges:
        ed.use_edge_sharp = self.og_sharp_edges[ed.index]

    new_l_norms = self.og_loop_norms.copy()
    for po in self._points_container.points:
        for l, l_ind in enumerate(po.loop_inds):
            new_l_norms[l_ind] = po.loop_normals[l].normalized()

    self._object.data.normals_split_custom_set(new_l_norms)

    del(new_l_norms)
    return

def match_point_loops_vecs(self, po_ind, o_vecs, flip_axis=None):
    po = self._points_container.points[po_ind]

    match_inds = []
    for loop in self._object_bm.verts[po.index].link_loops:
        vec = loop.edge.other_vert(self._object_bm.verts[po_ind]).co - po.co

        small = 0
        small_ind = None
        for o, o_vec in enumerate(o_vecs):
            t_vec = o_vec.copy()
            if flip_axis != None:
                t_vec[flip_axis] *= -1
            
            ang = vec.angle(t_vec)
            if ang < small or small_ind == None:
                small_ind = o
                small = ang
        
        match_inds.append(small_ind)
    
    return match_inds

def match_point_loops_index(self, po_ind, o_ind, flip_axis=None):
    po = self._points_container.points[po_ind]
    o_po = self._points_container.points[o_ind]

    match_inds = []
    for loop in self._object_bm.verts[po_ind].link_loops:
        vec = loop.edge.other_vert(self._object_bm.verts[po_ind]).co - po.co

        small = 0
        small_ind = None
        for o, o_loop in enumerate(self._object_bm.verts[o_po.index].link_loops):
            o_vec = o_loop.edge.other_vert(self._object_bm.verts[o_ind]).co - o_po.co
            if flip_axis != None:
                vec[flip_axis] *= -1

            if vec.angle(o_vec) < small or small_ind == None:
                small_ind = o
                small = vec.angle(o_vec)
        
        match_inds.append(small_ind)
    return match_inds



def mirror_normals(self, po_inds, axis):
    for ind in po_inds:
        po = self._points_container.points[ind]
        co = po.co.copy()
        co[axis] *= -1
        
        result = self._object_kd.find(co)
        if result != None :
            if result[1] != po.index:
                o_po = self._points_container.points[result[1]]
                if o_po.valid:
                    inds = match_point_loops_index(self, result[1], po.index, flip_axis=axis)

                    for l in range(len(o_po.loop_normals)):
                        o_po.loop_normals[l] = po.loop_normals[inds[l]].copy()
                        o_po.loop_normals[l][axis] *= -1
                self.redraw = True
    
    set_new_normals(self)
    add_to_undostack(self, 1)
    return

def flatten_normals(self, po_inds, axis):
    update_filter_weights(self)
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for l in range(len(po.loop_normals)):
                vec = po.loop_normals[l].copy()
                vec[axis] = 0.0

                if vec.length > 0.0:
                    loop_norm_set(self, po, l, po.loop_normals[l], vec)
                del(vec)
            self.redraw = True
    
    set_new_normals(self)
    add_to_undostack(self, 1)
    return

def align_to_axis_normals(self, po_inds, axis, dir):
    update_filter_weights(self)
    vec = mathutils.Vector((0,0,0))

    vec[axis] = 1.0*dir
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for l in range(len(po.loop_normals)):
                loop_norm_set(self, po, l, po.loop_normals[l], vec.copy())
            self.redraw = True
    
    del(vec)

    set_new_normals(self)
    add_to_undostack(self, 1)
    return


                    

def average_vertex_normals(self, po_inds):
    update_filter_weights(self)
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            vec = average_vecs(po.loop_normals)

            for l in range(len(po.loop_normals)):
                loop_norm_set(self, po, l, po.loop_normals[l], vec.copy())
            self.redraw = True
            
            del(vec)
    
    set_new_normals(self)
    add_to_undostack(self, 1)
    return

def average_selected_normals(self, po_inds):
    update_filter_weights(self)
    avg_vec = mathutils.Vector((0,0,0))
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            vec = average_vecs(po.loop_normals)
            avg_vec += vec

            self.redraw = True
            
            del(vec)
    
    avg_vec = (avg_vec/len(po_inds)).normalized()

    if avg_vec.length > 0.0:
        for ind in po_inds:
            po = self._points_container.points[ind]
            if po.valid:
                for l in range(len(po.loop_normals)):
                    loop_norm_set(self, po, l, po.loop_normals[l], avg_vec.copy())
        set_new_normals(self)
        add_to_undostack(self, 1)

    del(avg_vec)

    return

def smooth_selected_normals(self, po_inds, iterations, fac):
    update_filter_weights(self)
    abn_props = bpy.context.scene.abnormal_props
    calc_norms = None
    for i in range(iterations):
        calc_norms = []
        for po in self._points_container.points:
            if len(po.loop_normals) > 0 and po.valid:
                loop_norms = po.loop_normals
                
                vec = mathutils.Vector((0,0,0))
                for l in loop_norms:
                    vec += l
                
                vec = vec/len(loop_norms)
                
                calc_norms.append(vec)

                del(vec)
            else:
                calc_norms.append(None)
        
        
        for ind in po_inds:
            po = self._points_container.points[ind]
            loop_norms = po.loop_normals
            loop_inds = po.loop_inds

            l_vs = [ed.other_vert(self._object_bm.verts[ind]) for ed in self._object_bm.verts[ind].link_edges]
            
            for l, l_norm in enumerate(loop_norms):
                smooth_vec = mathutils.Vector((0,0,0))

                cnt = 0
                for ov in l_vs:
                    if calc_norms[ov.index] != None:
                        smooth_vec += l_norm.lerp(calc_norms[ov.index], fac)
                        cnt += 1
                
                if cnt > 0:
                    smooth_vec = smooth_vec/cnt
                    loop_norm_set(self, po, l, po.loop_normals[l], po.loop_normals[l].lerp(smooth_vec, abn_props.smooth_strength))
                    del(smooth_vec)

            self.redraw = True
            del(po)
    
    del(calc_norms)
    set_new_normals(self)
    add_to_undostack(self, 1)
    return




def flip_normals(self, po_inds):
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for l_norm in po.loop_normals:
                l_norm *= -1
            self.redraw = True
    
    set_new_normals(self)
    add_to_undostack(self, 1)
    return

def set_outside_inside(self, po_inds, direction):
    update_filter_weights(self)
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            if self._object_smooth:
                poly_norm = mathutils.Vector((0,0,0))
                for l_ind in po.loop_inds:
                    for loop in self._object_bm.verts[po.index].link_loops:
                        poly_norm += self._object.data.polygons[loop.face.index].normal * direction
                    
                if poly_norm.length > 0.0:
                    for l, l_ind in enumerate(po.loop_inds):
                        loop_norm_set(self, po, l, po.loop_normals[l], poly_norm/len(po.loop_inds))

            else:
                for i, l_ind in enumerate(po.loop_inds):
                    for loop in self._object_bm.verts[po.index].link_loops:
                        if loop.index == l_ind:
                            po.loop_normals[i] = self._object.data.polygons[loop.face.index].normal.copy() * direction

            self.redraw = True

    
    set_new_normals(self)
    add_to_undostack(self, 1)
    return

def reset_normals(self, po_inds):
    for ind in po_inds:
        po = self._points_container.points[ind]
        if po.valid:
            for i, ind in enumerate(po.loop_inds):
                po.loop_normals[i] = self.og_loop_norms[ind].copy()
            self.redraw = True
    set_new_normals(self)
    add_to_undostack(self, 1)
    return



def copy_active_to_selected(self, po_inds):
    update_filter_weights(self)
    if self._active_point != None:
        for ind in po_inds:
            if ind != self._active_point:
                po = self._points_container.points[ind]
                if po.valid:
                    inds = match_point_loops_index(self, po.index, self._active_point)
                    for l in range(len(po.loop_normals)):
                        loop_norm_set(self, po, l, po.loop_normals[l], self._points_container.points[self._active_point].loop_normals[inds[l]].copy())

        self.redraw = True

    set_new_normals(self)
    add_to_undostack(self, 1)
    return

def copy_active_normal(self):
    if self._active_point != None:
        po = self._points_container.points[self._active_point]
        if po.valid:
            self._copy_normals = [l_norm for l_norm in po.loop_normals]
            self._copy_normals_vecs = []
            self._copy_normal_ind = po.index

            for o_loop in self._object_bm.verts[po.index].link_loops:
                o_vec = o_loop.edge.other_vert(self._object_bm.verts[po.index]).co - po.co
                self._copy_normals_vecs.append(o_vec)


    return

def paste_normal(self, po_inds):
    update_filter_weights(self)
    if self._copy_normals != None and self._copy_normals_vecs != None and self._copy_normal_ind != None:
        for ind in po_inds:
            po = self._points_container.points[ind]
            if po.valid:
                inds = match_point_loops_vecs(self, po.index, self._copy_normals_vecs)
                for l in range(len(po.loop_normals)):
                    loop_norm_set(self, po, l, po.loop_normals[l], self._copy_normals[inds[l]].copy())

                self.redraw = True
    set_new_normals(self)
    add_to_undostack(self, 1)
    return




def rotate_vectors(self, angle):
    sel_pos = self._points_container.get_selected()

    for p, p_ind in enumerate(sel_pos):
        po = self._points_container.points[p_ind]
        if self.translate_mode == 0:
            region = bpy.context.region
            rv3d = bpy.context.region_data
            mouse_co = mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1]))
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, po.co)

            co1 = view3d_utils.region_2d_to_location_3d(region, rv3d, rco, po.co)
            rco[0] += 10
            co2 = view3d_utils.region_2d_to_location_3d(region, rv3d, rco, po.co)
            rco[0] -= 10
            rco[1] -= 10
            co3 = view3d_utils.region_2d_to_location_3d(region, rv3d, rco, po.co)

            co4 = co1 + (co3-co1).cross(co2-co1)

            mat = generate_matrix(co1,co4,co2, True, True)
            mat.translation = po.co
            del(rco)
            del(co1)
            del(co2)
            del(co3)
        
        elif self.translate_mode == 1:
            mat = generate_matrix(mathutils.Vector((0,0,0)),mathutils.Vector((0,0,1)),mathutils.Vector((0,1,0)), False, True)
            mat.translation = po.co
        
        elif self.translate_mode == 2:
            if self.gizmo_click:
                mat = self._orbit_ob.matrix_world.normalized()
                mat.translation = po.co
            else:
                mat = self._object.matrix_world.normalized()
                mat.translation = po.co
        
        for l, l_norm in enumerate(po.loop_normals):
            og_norm = self._changing_po_cache[2][p][l]
            vec_local = mat.inverted() @ (self._object.matrix_world @ (self._object.data.vertices[po.index].co+og_norm))

            if self.translate_axis == 0:
                rot_vec = rotate_2d([0,0], vec_local.yz, angle)

                vec_local[1] = rot_vec[0]
                vec_local[2] = rot_vec[1]

            if self.translate_axis == 1:
                rot_vec = rotate_2d([0,0], vec_local.xz, angle)

                vec_local[0] = rot_vec[0]
                vec_local[2] = rot_vec[1]

            if self.translate_axis == 2:
                rot_vec = rotate_2d([0,0], vec_local.xy, angle)

                vec_local[0] = rot_vec[0]
                vec_local[1] = rot_vec[1]
            

            loop_norm_set(self, po, l, og_norm, ( (self._object.matrix_world.inverted() @ (mat @ vec_local)) - self._object.data.vertices[po.index].co ).normalized())
        
            del(rot_vec)
            del(og_norm)
            del(vec_local)
        
        del(mat)
    set_new_normals(self)
    return




def translate_axis_draw(self):
    mat = None
    if self.translate_mode == 0:
        self.translate_draw_line.clear()
    
    elif self.translate_mode == 1:
        mat = generate_matrix(mathutils.Vector((0,0,0)),mathutils.Vector((0,0,1)),mathutils.Vector((0,1,0)), False, True)
        mat.translation = self._changing_po_cache[1]
    
    elif self.translate_mode == 2:
        mat = self._object.matrix_world.normalized()
        mat.translation = self._changing_po_cache[1]

    if mat != None:
        self.translate_draw_line.clear()
        if self.translate_axis == 0:
            self.translate_draw_line.append(mat @ mathutils.Vector((1000,0,0)))
            self.translate_draw_line.append(mat @ mathutils.Vector((-1000,0,0)))
        if self.translate_axis == 1:
            self.translate_draw_line.append(mat @ mathutils.Vector((0,1000,0)))
            self.translate_draw_line.append(mat @ mathutils.Vector((0,-1000,0)))
        if self.translate_axis == 2:
            self.translate_draw_line.append(mat @ mathutils.Vector((0,0,1000)))
            self.translate_draw_line.append(mat @ mathutils.Vector((0,0,-1000)))
        del(mat)
    
    self.batch_translate_line = batch_for_shader(self.shader_3d, 'LINES', {"pos": self.translate_draw_line}) 
    return

def clear_translate_axis_draw(self):
    self.batch_translate_line = batch_for_shader(self.shader_3d, 'LINES', {"pos": []}) 
    return

def translate_axis_change(self, text, axis):
    if self.translate_axis != axis:
        self.translate_axis = axis
        self.translate_mode = 1
    
    else:
        self.translate_mode += 1
        if self.translate_mode == 3:
            self.translate_mode = 0
            self.translate_axis = 2

    if self.translate_mode == 0:
        self._window.set_status('VIEW '+ text)
    elif self.translate_mode == 1:
        self._window.set_status('GLOBAL ' + text)
    else:
        self._window.set_status('LOCAL ' + text)
    
    translate_axis_draw(self)

    sel_pos = self._points_container.get_selected()
    for i, ind in enumerate(sel_pos):
        po = self._points_container.points[ind]

        for l, l_norm in enumerate(po.loop_normals):
            po.loop_normals[l] = self._changing_po_cache[2][i][l].copy()
            
    return

def translate_axis_side(self):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    view_vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1])))

    
    if self.translate_mode == 1:
        mat = generate_matrix(mathutils.Vector((0,0,0)),mathutils.Vector((0,0,1)),mathutils.Vector((0,1,0)), False, True)
    else:
        mat = self._object.matrix_world.normalized()
    
    pos_vec = mathutils.Vector((0,0,0))
    neg_vec = mathutils.Vector((0,0,0))
    pos_vec[self.translate_axis] = 1.0
    neg_vec[self.translate_axis] = -1.0

    pos_vec = (mat @ pos_vec) - mat.translation
    neg_vec = (mat @ neg_vec) - mat.translation

    if pos_vec.angle(view_vec) < neg_vec.angle(view_vec):
        side = -1
    else:
        side = 1
    
    if self.translate_axis == 1:
        side *= -1
    return side



def loop_norm_set(self, po, l, og_vec, to_vec):
    weight = None
    if self._filter_weights != None:
        weight = self._filter_weights[po.index]
    if weight == None:
        po.loop_normals[l] = to_vec.normalized()
    else:
        if weight > 0.0:
            po.loop_normals[l] = og_vec.lerp(to_vec.normalized(), weight)
    return

def update_filter_weights(self):
    abn_props = bpy.context.scene.abnormal_props
    weights = None
    if abn_props.vertex_group != '':
        if abn_props.vertex_group in self._object.vertex_groups:
            weights = []

            for ind in range(len(self._points_container.points)):
                vg = self._object.vertex_groups[abn_props.vertex_group]

                try:
                    weights.append(vg.weight(ind))

                except:
                    weights.append(0.0)
        
        else:
            abn_props.vertex_group = ''

    self._filter_weights = weights
    return



def start_sphereize_mode(self):
    update_filter_weights(self)
    self._window.panels[0].visible = False
    panel = self._window.add_panel(header_text='Sphereize Normals', hover_highlight=True)
    panel.width = 225
    panel.position = [self._mouse_loc[0], self._mouse_loc[1]]
    panel.alignment = 'TL'
    subp = panel.add_subpanel(header_text='')
    subp.use_header = False
    row = subp.add_row()
    row.add_button(25, 'Confirm Sphereize')
    row.add_button(26, 'Cancel Sphereize')
    row = subp.add_row()
    row.add_num_prop(58, 'Sphereize Strength', self.target_strength, 2, 0.01, 0.01, 1.0)

    keymap_refresh_target(self)
    panel.create_shape_data()

    self.sphereize_mode = True

    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)


    self.target_emp = bpy.data.objects.new('ABN_Target Empty', None)
    self.target_emp.empty_display_size = 0.5
    self.target_emp.show_in_front = True
    self.target_emp.matrix_world = self._object.matrix_world.copy()
    self.target_emp.empty_display_type = 'SPHERE'
    bpy.context.collection.objects.link(self.target_emp)
    self.target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self.target_emp
    self.target_emp.location = avg_loc


    sel_pos = self._points_container.get_selected()
    cache_norms = []
    for ind in sel_pos:
        po = self._points_container.points[ind]
        norms = []
        for l_norm in po.loop_normals:
            norms.append(l_norm)
        cache_norms.append(norms)

    self._changing_po_cache.append(cache_norms)
    gizmo_hide(self)

    sphereize_normals(self, sel_pos)
    return

def end_sphereize_mode(self, keep_normals):
    if keep_normals == False:
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for l, l_norm in enumerate(po.loop_normals):
                po.loop_normals[l] = self._changing_po_cache[-1][i][l].copy()
        
        set_new_normals(self)
    


    self._window.panels[0].visible = True
    self._window.panels.pop(-1)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
    self._window.clear_status()
    self.redraw = True
    self.sphereize_mode = False
    self.sphereize_move = False
    bpy.data.objects.remove(self.target_emp)
    self.target_emp = None
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    gizmo_unhide(self)
    
    self._changing_po_cache.clear()
    keymap_refresh_base(self)
    return

def sphereize_normals(self, po_inds):
    for i, ind in enumerate(po_inds):
        po = self._points_container.points[ind]
        if po.valid:
            vec = (self._object.matrix_world.inverted() @ po.co) - (self._object.matrix_world.inverted() @ self.target_emp.location)
            for l, l_ind in enumerate(po.loop_inds):
                loop_norm_set(self, po, l, self._changing_po_cache[-1][i][l], self._changing_po_cache[-1][i][l].lerp(vec, self.target_strength))
            
            self.redraw = True
    
    set_new_normals(self)
    return




def start_point_mode(self):
    update_filter_weights(self)
    self._window.panels[0].visible = False
    panel = self._window.add_panel(header_text='Point Normals at Target', hover_highlight=True)
    panel.width = 225
    panel.position = [self._mouse_loc[0], self._mouse_loc[1]]
    panel.alignment = 'TL'
    subp = panel.add_subpanel(header_text='')
    subp.use_header = False
    row = subp.add_row()
    row.add_button(31, 'Confirm Point')
    row.add_button(32, 'Cancel Point')
    row = subp.add_row()
    row.add_num_prop(58, 'Point Strength', self.target_strength, 2, 0.01, 0.01, 1.0)
    row.add_bool_prop(33, 'Align Vectors', 14, self.point_align)

    keymap_refresh_target(self)
    panel.create_shape_data()

    self.point_mode = True

    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)

    self.target_emp = bpy.data.objects.new('ABN_Target Empty', None)
    self.target_emp.empty_display_size = 0.5
    self.target_emp.show_in_front = True
    self.target_emp.matrix_world = self._object.matrix_world.copy()
    self.target_emp.empty_display_type = 'SPHERE'
    bpy.context.collection.objects.link(self.target_emp)
    self.target_emp.select_set(True)
    bpy.context.view_layer.objects.active = self.target_emp
    self.target_emp.location = avg_loc


    sel_pos = self._points_container.get_selected()
    cache_norms = []
    for ind in sel_pos:
        po = self._points_container.points[ind]
        norms = []
        for l_norm in po.loop_normals:
            norms.append(l_norm)
        cache_norms.append(norms)

    self._changing_po_cache.append(cache_norms)
    gizmo_hide(self)

    point_normals(self, sel_pos)
    return

def end_point_mode(self, keep_normals):
    if keep_normals == False:
        sel_pos = self._points_container.get_selected()
        for i, ind in enumerate(sel_pos):
            po = self._points_container.points[ind]

            for l, l_norm in enumerate(po.loop_normals):
                po.loop_normals[l] = self._changing_po_cache[-1][i][l].copy()
        
        set_new_normals(self)
    


    self._window.panels[0].visible = True
    self._window.panels.pop(-1)

    add_to_undostack(self, 1)
    self.translate_axis = 2
    self.translate_mode = 0
    clear_translate_axis_draw(self)
    self._window.clear_status()
    self.redraw = True
    self.point_mode = False
    self.point_move = False
    bpy.data.objects.remove(self.target_emp)
    self.target_emp = None
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob
    self.point_align = False
    
    gizmo_unhide(self)
    
    self._changing_po_cache.clear()
    keymap_refresh_base(self)
    return

def point_normals(self, po_inds):
    if self.point_align:
        sel_cos = self._points_container.get_selected_cos()
        avg_loc = average_vecs(sel_cos)
        vec = (self._object.matrix_world.inverted() @ self.target_emp.location) - (self._object.matrix_world.inverted() @ avg_loc)
    
    for i, ind in enumerate(po_inds):
        po = self._points_container.points[ind]
        if po.valid:
            if self.point_align == False:
                vec = (self._object.matrix_world.inverted() @ self.target_emp.location) - (self._object.matrix_world.inverted() @ po.co)
            for l, l_ind in enumerate(po.loop_inds):

                loop_norm_set(self, po, l, self._changing_po_cache[-1][i][l], self._changing_po_cache[-1][i][l].lerp(vec, self.target_strength))
            
            self.redraw = True
    
    set_new_normals(self)
    return


def move_target(self, shift):
    offset = [self._mouse_loc[0] - self._changing_po_cache[0][0], self._mouse_loc[1] - self._changing_po_cache[0][1]]

    if shift:
        offset[0] = offset[0]*.1
        offset[1] = offset[1]*.1

    region = bpy.context.region
    rv3d = bpy.context.region_data

    self._changing_po_cache[3][0] = self._changing_po_cache[3][0] + offset[0]
    self._changing_po_cache[3][1] = self._changing_po_cache[3][1] + offset[1]

    new_co = view3d_utils.region_2d_to_location_3d(region, rv3d, self._changing_po_cache[3], self._changing_po_cache[1])
    if self.translate_mode == 0:
        self.target_emp.location = new_co

    elif self.translate_mode == 1:
        self.target_emp.location = self._changing_po_cache[1].copy()
        self.target_emp.location[self.translate_axis] = new_co[self.translate_axis]
    
    elif self.translate_mode == 2:
        loc_co = self._object.matrix_world.inverted() @ new_co
        def_dist = loc_co[self.translate_axis]

        def_vec = mathutils.Vector((0,0,0))
        def_vec[self.translate_axis] = def_dist

        def_vec = (self._object.matrix_world @ def_vec) - self._object.matrix_world.translation

        self.target_emp.location = self._changing_po_cache[1].copy()
        self.target_emp.location += def_vec
    

    return






def gizmo_init(self, context, event):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    region = bpy.context.region
    rv3d = bpy.context.region_data
    

    if addon_prefs.rotate_gizmo_use and self.rotate_gizmo_draw:
        giz_hover = self._window.test_gizmo_hover(self._mouse_loc)
        if giz_hover:
            giz_status = self._window.test_gizmo_click()
            if giz_status != None:
                if event.alt == False:
                    sel_pos = self._points_container.get_selected()
                    if len(sel_pos) == 0:
                        return True
                
                self._changing_po_cache.clear()

                if event.alt == False:
                    cache_norms = []
                    for ind in sel_pos:
                        po = self._points_container.points[ind]
                        norms = []
                        for l_norm in po.loop_normals:
                            norms.append(l_norm)
                        cache_norms.append(norms)

                    for gizmo in self._window.gizmo_sets[giz_status[1][0]].gizmos:
                        if gizmo.index != giz_status[1][1]:
                            gizmo.active = False
                        else:
                            gizmo.in_use = True
                

                view_vec = view3d_utils.region_2d_to_vector_3d(region, rv3d, mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1])))
                view_orig = view3d_utils.region_2d_to_origin_3d(region, rv3d, mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1])))
                line_a = view_orig
                line_b = view_orig + view_vec*10000
                if giz_status[0] == 'ROT_X':
                    x_vec = self._orbit_ob.matrix_world @ mathutils.Vector((1,0,0)) - self._orbit_ob.matrix_world.translation
                    mouse_co_3d = mathutils.geometry.intersect_line_plane(line_a, line_b, self._orbit_ob.matrix_world.translation, x_vec)
                if giz_status[0] == 'ROT_Y':
                    y_vec = self._orbit_ob.matrix_world @ mathutils.Vector((0,1,0)) - self._orbit_ob.matrix_world.translation
                    mouse_co_3d = mathutils.geometry.intersect_line_plane(line_a, line_b, self._orbit_ob.matrix_world.translation, y_vec)
                if giz_status[0] == 'ROT_Z':
                    z_vec = self._orbit_ob.matrix_world @ mathutils.Vector((0,0,1)) - self._orbit_ob.matrix_world.translation
                    mouse_co_3d = mathutils.geometry.intersect_line_plane(line_a, line_b, self._orbit_ob.matrix_world.translation, z_vec)
                mouse_co_local = self._orbit_ob.matrix_world.inverted() @ mouse_co_3d

                if giz_status[0] == 'ROT_X':
                    test_vec = mouse_co_local.yz
                    ang_offset = mathutils.Vector((0,1)).angle_signed(test_vec)
                    self._changing_po_cache.append(mouse_co_local.yz)
                if giz_status[0] == 'ROT_Y':
                    test_vec = mouse_co_local.xz
                    ang_offset = mathutils.Vector((0,1)).angle_signed(test_vec)
                    self._changing_po_cache.append(mouse_co_local.xz)
                if giz_status[0] == 'ROT_Z':
                    test_vec = mouse_co_local.xy
                    ang_offset = mathutils.Vector((0,1)).angle_signed(test_vec)
                    self._changing_po_cache.append(mouse_co_local.xy)

                if event.alt == False:
                    self._window.update_gizmo_rot(0, -ang_offset)
                    self._changing_po_cache.append(giz_status)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)
                    self._changing_po_cache.append(-ang_offset)
                    self._changing_po_cache.append(self._orbit_ob.matrix_world.copy())
                    self._changing_po_cache.append(True)
                else:
                    self._changing_po_cache.append(giz_status)
                    self._changing_po_cache.append([])
                    self._changing_po_cache.append(0)
                    self._changing_po_cache.append(-ang_offset)
                    self._changing_po_cache.append(self._orbit_ob.matrix_world.copy())
                    self._changing_po_cache.append(False)
                
                self.gizmo_click = True

                return False
    return True

def relocate_gizmo_panel(self):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    rco = view3d_utils.location_3d_to_region_2d(region, rv3d, self._orbit_ob.location)

    panel = self._window.panels[2]
    if rco != None:
        self._window.reposition_panel(2, [rco[0]+panel.reposition_offset[0], rco[1]+panel.reposition_offset[1]])
    return

def gizmo_hide(self):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    if addon_prefs.rotate_gizmo_use:
        self.rotate_gizmo_draw = False
        self._window.panels[2].visible = False
        self._window.panels[2].visible_on_hover = False
    return

def gizmo_unhide(self):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    if addon_prefs.rotate_gizmo_use:
        self.rotate_gizmo_draw = True
        self._window.panels[2].visible_on_hover = True
    return


def init_nav_list(self):
    self.nav_list = ['LEFTMOUSE', 'MOUSEMOVE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'N']

    names = ['Zoom View', 'Rotate View', 'Pan View', 'Dolly View', 
    'View Selected', 'View Camera Center', 'View All', 'View Axis', 
    'View Orbit', 'View Roll', 'View Persp/Ortho',]

    for item in bpy.context.window_manager.keyconfigs[0].keymaps['3D View'].keymap_items:
        if item.name in names:
            if item.type not in self.nav_list:
                self.nav_list.append(item.type)
    for item in bpy.context.window_manager.keyconfigs[2].keymaps['3D View'].keymap_items:
        if item.name in names:
            if item.type not in self.nav_list:
                self.nav_list.append(item.type)
    
    return



def add_to_undostack(self, stack_type):
    if stack_type == 0:
        sel_status = self._points_container.get_selected()

        if self.undo_sel_state > 0:
            while self.undo_sel_state > 0:
                self.undo_sel_stack.pop(0)
                self.undo_sel_state -= 1
        
        if len(self.undo_sel_stack)+1 > self.max_undo:
            self.undo_sel_stack.pop(-1)
        self.undo_sel_stack.insert(0, sel_status)
    
    else:
        cur_normals = self._points_container.get_current_normals()
        if self.undo_norm_state > 0:
            while self.undo_norm_state > 0:
                self.undo_norm_stack.pop(0)
                self.undo_norm_state -= 1
        
        if len(self.undo_norm_stack)+1 > self.max_undo:
            self.undo_norm_stack.pop(-1)
        self.undo_norm_stack.insert(0, cur_normals)

    return

def move_undostack(self, stack_type, dir):
    if stack_type == 0:
        if dir > 0 and len(self.undo_sel_stack)-1 > self.undo_sel_state or dir < 0 and self.undo_sel_state > 0:
            self.undo_sel_state += dir
            for po in self._points_container.points:
                if po.index in self.undo_sel_stack[self.undo_sel_state]:
                    po.select = True
                else:
                    po.select = False
            if self._active_point != None:
                if self._points_container.points[self._active_point].select == False:
                    self._active_point = None
            update_orbit_empty(self)
            self.redraw = True
    
    else:
        if dir > 0 and len(self.undo_norm_stack)-1 > self.undo_norm_state or dir < 0 and self.undo_norm_state > 0:
            self.undo_norm_state += dir
            norms_state = self.undo_norm_stack[self.undo_norm_state]
            for p, po in enumerate(self._points_container.points):
                for l in range(len(po.loop_normals)):
                    po.loop_normals[l] = norms_state[p][l].copy()
            self.redraw = True
            set_new_normals(self)
    
    return





def button_pressed(self, event, but_type, but_id):
    region = bpy.context.region
    rh = region.height
    rw = region.width
    status = {'RUNNING_MODAL'}

    abn_props = bpy.context.scene.abnormal_props
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    
    ####
    ##ENDING MODAL
    ####
    #CONFIRM NORMAL CHANGES
    if but_id == 0:
        finish_modal(self)
        status = {'FINISHED'}
    
    #CANCEL NORMAL CHANGES
    elif but_id == 1:
        ob = self._object
        if self._object.as_pointer() != self._object_pointer:
            for o_ob in bpy.data.objects:
                if o_ob.as_pointer() == self._object_pointer:
                    ob = o_ob
        
        #restore normals
        ob.data.normals_split_custom_set(self.og_loop_norms)

        for ed in self._object.data.edges:
            ed.use_edge_sharp = self.og_sharp_edges[ed.index]

        finish_modal(self)
        status = {'CANCELLED'}
    

    else:
        sel_pos = self._points_container.get_selected()
        
        if len(sel_pos) != 0:
            ####
            ##MIRRORING NORMALS
            ####
            if but_id == 2:
                mirror_normals(self, sel_pos, 0)

            if but_id == 3:
                mirror_normals(self, sel_pos, 1)

            if but_id == 4:
                mirror_normals(self, sel_pos, 2)


            ####
            ##FLATTENING NORMALS
            ####
            if but_id == 5:
                flatten_normals(self, sel_pos, 0)

            if but_id == 6:
                flatten_normals(self, sel_pos, 1)

            if but_id == 7:
                flatten_normals(self, sel_pos, 2)
        

            ####
            ##AXIS ALIGNMENT
            ####
            if but_id == 8:
                align_to_axis_normals(self, sel_pos, 0, 1)

            if but_id == 9:
                align_to_axis_normals(self, sel_pos, 1, 1)

            if but_id == 10:
                align_to_axis_normals(self, sel_pos, 2, 1)
            
            if but_id == 11:
                align_to_axis_normals(self, sel_pos, 0, -1)

            if but_id == 12:
                align_to_axis_normals(self, sel_pos, 1, -1)

            if but_id == 13:
                align_to_axis_normals(self, sel_pos, 2, -1)
            

            ####
            ##NORMAL DIRECTION
            ####
            if but_id == 14:
                flip_normals(self, sel_pos)

            if but_id == 15:
                set_outside_inside(self, sel_pos, 1)

            if but_id == 16:
                set_outside_inside(self, sel_pos, -1)
                
            if but_id == 17:
                reset_normals(self, sel_pos)


            if but_id == 18:
                average_vertex_normals(self, sel_pos)
            
            if but_id == 19:
                average_selected_normals(self, sel_pos)

            if but_id == 20:
                smooth_selected_normals(self, sel_pos, abn_props.smooth_iters, 0.5)



            ####
            ##NORMAL DIRECTION
            ####
            if but_id == 21:
                copy_active_to_selected(self, sel_pos)
            if but_id == 22:
                copy_active_normal(self)
            if but_id == 23:
                paste_normal(self, sel_pos)
        

            ####
            ##SPHEREIZE NORMALS
            ####
            if but_id == 24:
                start_sphereize_mode(self)
            if but_id == 25:
                end_sphereize_mode(self, True)
            if but_id == 26:
                end_sphereize_mode(self, False)
            
            if but_id == 58:
                if but_type == 'NUM_LEFT_ARROW':
                    new_val = self._window.num_change(event.shift)
                    self.target_strength = new_val
                    if self.sphereize_mode:
                        sphereize_normals(self, sel_pos)
                    if self.point_mode:
                        point_normals(self, sel_pos)
                if but_type == 'NUM_RIGHT_ARROW':
                    new_val = self._window.num_change(event.shift)
                    self.target_strength = new_val
                    if self.sphereize_mode:
                        sphereize_normals(self, sel_pos)
                    if self.point_mode:
                        point_normals(self, sel_pos)


            ####
            ##POINT NORMALS
            ####
            if but_id == 30:
                start_point_mode(self)
            if but_id == 31:
                end_point_mode(self, True)
            if but_id == 32:
                end_point_mode(self, False)
            
            if but_id == 33:
                self.point_align = not self.point_align
                self._window.boolean_toggle_hover()
                self.redraw = True
                point_normals(self, sel_pos)

            
            if but_id == 40:
                for p in self._object.data.polygons:
                    p.use_smooth = True
                self._object_smooth = True
                set_new_normals(self)
            
            if but_id == 41:
                for p in self._object.data.polygons:
                    p.use_smooth = False
                self._object_smooth = False
                set_new_normals(self)
            


            ####
            ##INCREMENT ROTATE NORMALS
            ####
            if but_id == 83:
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
                    
                    self._changing_po_cache.clear()
                    self._changing_po_cache.append(self._mouse_loc)
                    self._changing_po_cache.append(avg_loc)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)

                    self.translate_mode = 2
                    self.translate_axis = 0
                    rotate_vectors(self, math.radians(-self._rot_increment))
                    self.translate_mode = 0
                    self.translate_axis = 2
                    self._changing_po_cache.clear()
                    self.redraw = True
            
            if but_id == 84:
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
                    
                    self._changing_po_cache.clear()
                    self._changing_po_cache.append(self._mouse_loc)
                    self._changing_po_cache.append(avg_loc)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)

                    self.translate_mode = 2
                    self.translate_axis = 0
                    rotate_vectors(self, math.radians(self._rot_increment))
                    self.translate_mode = 0
                    self.translate_axis = 2
                    self._changing_po_cache.clear()
                    self.redraw = True

            if but_id == 85:
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
                    
                    self._changing_po_cache.clear()
                    self._changing_po_cache.append(self._mouse_loc)
                    self._changing_po_cache.append(avg_loc)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)

                    self.translate_mode = 2
                    self.translate_axis = 1
                    rotate_vectors(self, math.radians(-self._rot_increment))
                    self.translate_mode = 0
                    self.translate_axis = 2
                    self._changing_po_cache.clear()
                    self.redraw = True
            
            if but_id == 86:
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
                    
                    self._changing_po_cache.clear()
                    self._changing_po_cache.append(self._mouse_loc)
                    self._changing_po_cache.append(avg_loc)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)

                    self.translate_mode = 2
                    self.translate_axis = 1
                    rotate_vectors(self, math.radians(self._rot_increment))
                    self.translate_mode = 0
                    self.translate_axis = 2
                    self._changing_po_cache.clear()
                    self.redraw = True
            
            if but_id == 87:
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
                    
                    self._changing_po_cache.clear()
                    self._changing_po_cache.append(self._mouse_loc)
                    self._changing_po_cache.append(avg_loc)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)

                    self.translate_mode = 2
                    self.translate_axis = 2
                    rotate_vectors(self, math.radians(-self._rot_increment))
                    self.translate_mode = 0
                    self.translate_axis = 2
                    self._changing_po_cache.clear()
                    self.redraw = True
            
            if but_id == 88:
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
                    
                    self._changing_po_cache.clear()
                    self._changing_po_cache.append(self._mouse_loc)
                    self._changing_po_cache.append(avg_loc)
                    self._changing_po_cache.append(cache_norms)
                    self._changing_po_cache.append(0)

                    self.translate_mode = 2
                    self.translate_axis = 2
                    rotate_vectors(self, math.radians(self._rot_increment))
                    self.translate_mode = 0
                    self.translate_axis = 2
                    self._changing_po_cache.clear()
                    self.redraw = True

        if but_id == 34:
            print(__package__, 'Saving user preferences')
            bpy.ops.wm.save_userpref()
        
        ####
        ##Property buttons
        ####
        if but_id == 50:
            addon_prefs.selected_only = not addon_prefs.selected_only
            self._window.boolean_toggle_hover()
            self.redraw = True
        
        if but_id == 70:
            addon_prefs.selected_scale = not addon_prefs.selected_scale
            self._window.boolean_toggle_hover()
            self.redraw = True
        
        if but_id == 51:
            self._x_ray_mode = not self._x_ray_mode
            self._window.boolean_toggle_hover()
        
        if but_id == 52:
            if but_type == 'NUM_LEFT_ARROW':
                new_val = self._window.num_change(event.shift)
                addon_prefs.normal_size = new_val
                self.redraw = True
            if but_type == 'NUM_RIGHT_ARROW':
                new_val = self._window.num_change(event.shift)
                addon_prefs.normal_size = new_val
                self.redraw = True
            
        if but_id == 53:
            if but_type == 'NUM_LEFT_ARROW':
                new_val = self._window.num_change(event.shift)
                addon_prefs.line_brightness = new_val
            if but_type == 'NUM_RIGHT_ARROW':
                new_val = self._window.num_change(event.shift)
                addon_prefs.line_brightness = new_val
        
        if but_id == 54:
            if but_type == 'NUM_LEFT_ARROW':
                new_val = self._window.num_change(event.shift)
                addon_prefs.point_size = new_val
            if but_type == 'NUM_RIGHT_ARROW':
                new_val = self._window.num_change(event.shift)
                addon_prefs.point_size = new_val


        if but_id == 55:
            for space in bpy.context.area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_wireframes = not space.overlay.show_wireframes
                    addon_prefs.display_wireframe = space.overlay.show_wireframes
                    self._window.boolean_toggle_hover()
        
        if but_id == 56:
            if but_type == 'NUM_LEFT_ARROW':
                new_val = self._window.num_change(event.shift)
                abn_props.smooth_strength = new_val
            if but_type == 'NUM_RIGHT_ARROW':
                new_val = self._window.num_change(event.shift)
                abn_props.smooth_strength = new_val

        if but_id == 57:
            if but_type == 'NUM_LEFT_ARROW':
                new_val = self._window.num_change(event.shift)
                abn_props.smooth_iters = new_val
            if but_type == 'NUM_RIGHT_ARROW':
                new_val = self._window.num_change(event.shift)
                abn_props.smooth_iters = new_val
        
        if but_id == 59:
            addon_prefs.rotate_gizmo_use = not addon_prefs.rotate_gizmo_use
            self._window.boolean_toggle_hover()
            self.redraw = True
            self._window.panels[2].visible_on_hover = addon_prefs.rotate_gizmo_use
            keymap_refresh_base(self)
            if addon_prefs.rotate_gizmo_use:
                gizmo_unhide(self)
            else:
                gizmo_hide(self)

        
        if but_id == 90:
            addon_prefs.left_select = not addon_prefs.left_select
            self._window.boolean_toggle_hover()

        if but_id == 91:
            if but_type == 'NUM_LEFT_ARROW':
                new_val = self._window.num_change(event.shift)
                abn_props.gizmo_size = new_val
                self.rot_gizmo.update_size(new_val)
                self._window.update_gizmo_pos(self._orbit_ob.matrix_world)
            if but_type == 'NUM_RIGHT_ARROW':
                new_val = self._window.num_change(event.shift)
                abn_props.gizmo_size = new_val
                self.rot_gizmo.update_size(new_val)
                self._window.update_gizmo_pos(self._orbit_ob.matrix_world)

        if but_id == 80:
            if self._rot_increment_one == False:
                self._rot_increment_one = True
                self._rot_increment_five = False
                self._rot_increment_ten = False
                self._window.panels[2].subpanels[0].rows[0].items[0].bool = self._rot_increment_one
                self._window.panels[2].subpanels[0].rows[0].items[1].bool = self._rot_increment_five
                self._window.panels[2].subpanels[0].rows[0].items[2].bool = self._rot_increment_ten
                self._rot_increment = 1
        
        if but_id == 81:
            if self._rot_increment_five == False:
                self._rot_increment_one = False
                self._rot_increment_five = True
                self._rot_increment_ten = False
                self._window.panels[2].subpanels[0].rows[0].items[0].bool = self._rot_increment_one
                self._window.panels[2].subpanels[0].rows[0].items[1].bool = self._rot_increment_five
                self._window.panels[2].subpanels[0].rows[0].items[2].bool = self._rot_increment_ten
                self._rot_increment = 5
        
        if but_id == 82:
            if self._rot_increment_ten == False:
                self._rot_increment_one = False
                self._rot_increment_five = False
                self._rot_increment_ten = True
                self._window.panels[2].subpanels[0].rows[0].items[0].bool = self._rot_increment_one
                self._window.panels[2].subpanels[0].rows[0].items[1].bool = self._rot_increment_five
                self._window.panels[2].subpanels[0].rows[0].items[2].bool = self._rot_increment_ten
                self._rot_increment = 10
        

    
    return status





def ob_data_structures(self, ob):
    if ob.data.shape_keys != None:
        for sk in ob.data.shape_keys.key_blocks:
            self._objects_sk_vis.append(sk.mute)
            sk.mute = True
    
    bm = create_simple_bm(self, ob)
    
    bvh = mathutils.bvhtree.BVHTree.FromBMesh(bm)
    
    kd = create_kd(bm)
    
    
    return bm, kd, bvh


def cache_point_data(self):
    self._object.data.calc_normals_split()
    self.og_loop_norms = [loop.normal.copy() for loop in self._object.data.loops]
    self.og_sharp_edges = [ed.use_edge_sharp for ed in self._object.data.edges]
    
    for v in self._object_bm.verts:
        if len(v.link_loops) > 0:
            loop_inds = [l.index for l in v.link_loops]
            loop_norms = [self._object.data.loops[l.index].normal for l in v.link_loops]
            
        
            self._points_container.add_point(v.co, v.normal, loop_norms, loop_inds)
        else:
            self._points_container.add_empty_point(v.co, mathutils.Vector((0,0,1)))
    
    return






def selection_test(self, context, event, radius=8.0):
    region = context.region
    rv3d = context.region_data
    mouse_co = mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1]))
    
    
    if self._x_ray_mode == False:
        bvh = self._object_bvh
    else:
        bvh = None
    
    

    
    
    nearest_dist = -1
    nearest_point = None
    nearest_sel_point = None
    for p, point in enumerate(self._points_container.points):
        if point.valid and point.hide == False:
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, point.co)
            if rco != None:
                dist = (rco - mouse_co).length
                if nearest_point == None or dist < nearest_dist:
                    #if point is in range of selection radius
                    if dist < radius:
                        #make sure point is valid. test occlusion if it is enabled
                        valid_po = False
                        if bvh != None:
                            hit = ray_cast_view_occlude_test(point.co, mouse_co, bvh)
                            
                            if hit == False:
                                valid_po = True
                        else:
                            valid_po = True
                        
                        if valid_po:
                            if point.select == False:
                                nearest_dist = dist
                                nearest_point = p
                            else:
                                nearest_sel_point = p
    
    if nearest_point == None and nearest_sel_point != None:
        nearest_point = nearest_sel_point
    
    
    if nearest_point != None:
        #unselect all and clear active point if shift not held
        if event.shift == False:
            self._active_point = None
            for p, point in enumerate(self._points_container.points):
                point.select = False
        
        if self._active_point == nearest_point:
            self._active_point = None
            self._points_container.points[nearest_point].select = False
        else:
            self._active_point = nearest_point
            self._points_container.points[nearest_point].select = True

        return True
    
    else:
        return False


def box_selection_test(self, context, event):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    mouse_co = mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1]))

    bvh = None
    
    if self._x_ray_mode == False:
        bvh = self._object_bvh

    low_x = self._changing_po_cache[0][0]
    hi_x = self._mouse_loc[0]
    low_y = self._changing_po_cache[0][1]
    hi_y = self._mouse_loc[1]
    
    if self._changing_po_cache[0][0] > self._mouse_loc[0]:
        low_x = self._mouse_loc[0]
        hi_x = self._changing_po_cache[0][0]
        
    if self._changing_po_cache[0][1] > self._mouse_loc[1]:
        low_y = self._mouse_loc[1]
        hi_y = self._changing_po_cache[0][1]
    

    if event.ctrl:
        add_rem_status = 2
    else:
        if event.shift:
            add_rem_status = 1
        else:
            add_rem_status = 0
    
    change = False
    for po in self._points_container.points:
        if po.valid and po.hide == False:
            co = po.co
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            
            if rco != None:
                if rco[0] > low_x and rco[0] < hi_x and rco[1] > low_y and rco[1] < hi_y:
                    if bvh != None:
                        occluded = False
                        hit = ray_cast_view_occlude_test(co, mouse_co, bvh)
                        #INSIDE BOX AND IN VIEW
                        if hit == False:
                            if add_rem_status == 2:
                                if po.select != False:
                                    po.select = False
                                    change = True
                            else:
                                if po.select != True:
                                    po.select = True
                                    change = True
                        #INSIDE BOX BUT NOT IN VIEW
                        else:
                            if add_rem_status == 0:
                                if po.select != False:
                                    po.select = False
                                    change = True
                    
                    #INSIDE BOX NO BVH TEST
                    else:
                        if add_rem_status == 2:
                            if po.select != False:
                                po.select = False
                                change = True
                        else:
                            if po.select != True:
                                po.select = True
                                change = True
                #OUTSIDE BOX
                else:
                    if add_rem_status == 0:
                        if po.select != False:
                            po.select = False
                            change = True
                        

    return change


def circle_selection_test(self, context, event, radius, remove):
    region = context.region
    rv3d = context.region_data
    mouse_co = mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1]))
    
    
    if self._x_ray_mode == False:
        bvh = self._object_bvh
    else:
        bvh = None
    
    change = False
    for p, point in enumerate(self._points_container.points):
        if point.valid and point.hide == False:
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, point.co)
            if rco != None:
                dist = (rco - mouse_co).length
                if dist < radius:
                    if bvh != None:
                        hit = ray_cast_view_occlude_test(point.co, mouse_co, bvh)
                        
                        if hit == False:
                            if point.select == remove:
                                point.select = not remove
                                change = True
                    else:
                        if point.select == remove:
                            point.select = not remove
                            change = True
    
    return change


def lasso_selection_test(self, context, event):
    region = context.region
    rv3d = context.region_data
    mouse_co = mathutils.Vector((self._mouse_loc[0], self._mouse_loc[1]))

    if self._x_ray_mode == False:
        bvh = self._object_bvh
    else:
        bvh = None
    
    remove = False

    if event.shift:
        remove = True
    
    in_range_inds = bounding_box_filter(self._changing_po_cache, [ view3d_utils.location_3d_to_region_2d(region, rv3d, po.co) for po in self._points_container.points])
    
    change = False
    for p in in_range_inds:
        point = self._points_container.points[p]
        if point.valid and point.hide == False:
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, point.co)
            if rco != None:
                if bvh != None:
                    hit = ray_cast_view_occlude_test(point.co, mouse_co, bvh)
                    if hit == False:
                        sel_res = test_point_in_shape(self._changing_po_cache, rco)
                        if sel_res and point.select == remove:
                            point.select = not remove
                            change = True
                else:
                    sel_res =  test_point_in_shape(self._changing_po_cache, rco)
                    if sel_res and point.select == remove:
                        point.select = not remove
                        change = True
    
    return change




def add_orbit_empty(self,):
    for i in range(len(bpy.context.selected_objects)):
        bpy.context.selected_objects[0].select_set(False)

    self._orbit_ob = bpy.data.objects.new('ABN_Orbit Empty', None)
    self._orbit_ob.empty_display_size = 0.0
    self._orbit_ob.matrix_world = self._object.matrix_world.copy()
    bpy.context.collection.objects.link(self._orbit_ob)
    bpy.context.view_layer.objects.active = self._orbit_ob
    return


def update_orbit_empty(self,):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    sel_cos = self._points_container.get_selected_cos()
    avg_loc = average_vecs(sel_cos)

    if avg_loc != None:
        gizmo_unhide(self)
        self._orbit_ob.matrix_world.translation = avg_loc
    else:
        gizmo_hide(self)
        self._orbit_ob.matrix_world.translation = self._object.location
    
    self._orbit_ob.select_set(True)
    bpy.context.view_layer.objects.active = self._orbit_ob

    if addon_prefs.rotate_gizmo_use:
        self.update_gizmos = True
        self._window.update_gizmo_pos(self._orbit_ob.matrix_world)
        relocate_gizmo_panel(self)

    del(avg_loc)
    del(sel_cos)
    return


def delete_orbit_empty(self,):
    if self._orbit_ob != None:
        try:
            bpy.data.objects.remove(self._orbit_ob)
        except:
            self._orbit_ob = None

    return



def img_load(self, img_name):
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    img_fp = directory.replace('/', '\\') + '\\' + img_name

    not_there = True
    for img in bpy.data.images:
        if img.filepath == img_fp:
            not_there = False
            break
    
    if not_there:
        img = bpy.data.images.load(img_fp)
    img.colorspace_settings.name = 'Raw'

    if img.gl_load():
        raise Exception()

    return img




def keymap_initialize(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()
    row = subp.add_text_row('ESC - Cancel Normal Editing', 10)
    row = subp.add_text_row('Tab - End and Confirm Normal Editing', 10)
    row = subp.add_text_row('R - Rotate Selected Normals', 10)
    row = subp.add_text_row('R + Alt - Reset Gizmo Axis', 10)
    row = subp.add_text_row('L-Click - Select Vertex/Gizmo Axis', 10)
    row = subp.add_text_row('L-Click + Alt - Reorient Gizmo', 10)
    row = subp.add_text_row('L-Click + Ctrl - Start Lasso Selection', 10)
    row = subp.add_text_row('C - Start Circle Selection', 10)
    row = subp.add_text_row('B - Start Box Selection', 10)
    row = subp.add_text_row('A - Select All', 10)
    row = subp.add_text_row('A + Alt - Unselect All', 10)
    row = subp.add_text_row('L - Select Linked Under Mouse', 10)
    row = subp.add_text_row('L + Ctrl - Select Linked from Selected', 10)
    row = subp.add_text_row('I + Ctrl - Invert Selection', 10)
    row = subp.add_text_row('H - Hide Selected Vertices', 10)
    row = subp.add_text_row('H + Alt - Unhide Vertices', 10)
    row = subp.add_text_row('Z - Toggle X-Ray', 10)
    row = subp.add_text_row('Ctrl + Z - Undo Normals Change', 10)
    row = subp.add_text_row('Ctrl + Shift + Z - Redo Normals Change', 10)
    row = subp.add_text_row('Ctrl + X - Undo Selection Change', 10)
    row = subp.add_text_row('Ctrl + Shift + X - Redo Selection Change', 10)
    return

def keymap_refresh_base(self):
    addon_prefs = bpy.context.preferences.addons[__package__].preferences

    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('ESC - Cancel Normal Editing', 10)
    row = subp.add_text_row('Tab - End and Confirm Normal Editing', 10)
    row = subp.add_text_row('R - Rotate Selected Normals', 10)
    if addon_prefs.rotate_gizmo_use:
        row = subp.add_text_row('R + Alt - Reset Gizmo Axis', 10)
        row = subp.add_text_row('L-Click - Select Vertex/Gizmo Axis', 10)
        row = subp.add_text_row('L-Click + Alt - Reorient Gizmo', 10)
    else:
        row = subp.add_text_row('L-Click - Select Vertex', 10)
    row = subp.add_text_row('L-Click + Ctrl - Start Lasso Selection', 10)
    row = subp.add_text_row('C - Start Circle Selection', 10)
    row = subp.add_text_row('B - Start Box Selection', 10)
    row = subp.add_text_row('A - Select All', 10)
    row = subp.add_text_row('A + Alt - Unselect All', 10)
    row = subp.add_text_row('L - Select Linked Under Mouse', 10)
    row = subp.add_text_row('L + Ctrl - Select Linked from Selected', 10)
    row = subp.add_text_row('I + Ctrl - Invert Selection', 10)
    row = subp.add_text_row('H - Hide Selected Vertices', 10)
    row = subp.add_text_row('H + Alt - Unhide Vertices', 10)
    row = subp.add_text_row('Z - Toggle X-Ray', 10)
    row = subp.add_text_row('Ctrl + Z - Undo Normals Change', 10)
    row = subp.add_text_row('Ctrl + Shift + Z - Redo Normals Change', 10)
    row = subp.add_text_row('Ctrl + X - Undo Selection Change', 10)
    row = subp.add_text_row('Ctrl + Shift + X - Redo Selection Change', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_rotating(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('X - Rotate on X axis', 10)
    row = subp.add_text_row('Y - Rotate on Y axis', 10)
    row = subp.add_text_row('Z - Rotate on Z axis', 10)
    row = subp.add_text_row('Hold Shift - Rotate 10x Smaller', 10)
    row = subp.add_text_row('L-Click - Confirm Rotation', 10)
    row = subp.add_text_row('R-Click - Cancel Rotation', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_gizmo(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('Hold Shift - Rotate 10x Smaller', 10)
    row = subp.add_text_row('L-Click - Confirm Rotation', 10)
    row = subp.add_text_row('R-Click - Cancel Rotation', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_lasso(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('L-Click Release - Finish Selection', 10)
    row = subp.add_text_row('L-Ctrl + Shift Release - Remove from Selection', 10)
    row = subp.add_text_row('R-Click - Cancel Selection Mode', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_circle(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('L-Click - Add to Selection', 10)
    row = subp.add_text_row('L-Click + Ctrl - Remove from Selection', 10)
    row = subp.add_text_row('Hold F - Change Cricle Size', 10)
    row = subp.add_text_row('[ - Decrease Circle Size', 10)
    row = subp.add_text_row('] - Increase Circle Size', 10)
    row = subp.add_text_row('R-Click - Cancel Selection Mode', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_box(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('L-Click - Start New Selection', 10)
    row = subp.add_text_row('L-Click + Shift - Add to Selection', 10)
    row = subp.add_text_row('L-Click + Ctrl - Remove from Selection', 10)
    row = subp.add_text_row('R-Click - Cancel Selection Mode', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_target(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('G - Moved Target Center', 10)
    row = subp.add_text_row('G + Alt - Reset Target Center', 10)
    row = subp.add_text_row('Z - Toggle X-Ray', 10)
    self._window.panels[1].create_shape_data()
    return

def keymap_refresh_target_move(self):
    subp = self._window.panels[1].subpanels[2]
    subp.clear_rows()

    row = subp.add_text_row('X - Translate on X axis', 10)
    row = subp.add_text_row('Y - Translate on Y axis', 10)
    row = subp.add_text_row('Z - Translate on Z axis', 10)
    row = subp.add_text_row('L-Click - Confirm Move', 10)
    row = subp.add_text_row('R-Click - Cancel Move', 10)
    self._window.panels[1].create_shape_data()
    return





def finish_modal(self):
    if bpy.context.area != None:
        if bpy.context.area.type == 'VIEW_3D':
            for space in bpy.context.area.spaces:
                if space.type == 'VIEW_3D':
                    space.show_region_toolbar = self._reg_header
                    space.show_region_ui = self._reg_ui
                    space.overlay.show_cursor = self._cursor
                    space.overlay.show_wireframes = self._wireframe
                    space.overlay.wireframe_threshold = self._thresh
                    space.overlay.show_text = self._text
    bpy.context.window.cursor_modal_set('DEFAULT')


    clear_drawing(self)
    restore_modifiers(self)
    delete_orbit_empty(self)
    
    if self.target_emp != None:
        try:
            bpy.data.objects.remove(self.target_emp)
        except:
            self.target_emp = None

    abn_props = bpy.context.scene.abnormal_props
    abn_props.object = ''

    self._object.select_set(True)
    bpy.context.view_layer.objects.active = self._object
    return


def restore_modifiers(self):
    if self._object.data.shape_keys != None:
        for s in range(len(self._object.data.shape_keys.key_blocks)):
            self._object.data.shape_keys.key_blocks[s].mute = self._objects_sk_vis[s]
    
    #restore modifier status
    for m, mod in enumerate(self._object.modifiers):
        mod.show_viewport = self._objects_mod_status[m][0]
        mod.show_render = self._objects_mod_status[m][1]
    
    return

