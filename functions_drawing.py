import bpy
import bmesh
import bgl
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from .functions_general import *



def refresh_batches(self, context):
    #region outline calculation
    region = context.region
    rv3d = context.region_data
    rh = region.height
    rw = region.width
    
    center = rw/2

    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    
    
    #LASSO SELECTION LINES
    lassosel_screen_lines = []
    if self.lasso_selecting:
        for i in range(len(self._changing_po_cache)):
            lassosel_screen_lines.append(self._changing_po_cache[i-1])
            lassosel_screen_lines.append(self._changing_po_cache[i])

    #CIRCLE SELECTION LINES
    circlesel_screen_lines = []
    if self.circle_selecting or self.circle_select_start or self.circle_resizing:
        if self.circle_resizing:
            cur_loc = mathutils.Vector(( self._changing_po_cache[0][0], self._changing_po_cache[0][1] ))
        else:
            cur_loc = mathutils.Vector(( self._mouse_loc[0], self._mouse_loc[1] ))
        
        co = cur_loc.copy()
        co[1] += self.circle_radius
        angle = math.radians(360/32)

        for i in range(32):
            circlesel_screen_lines.append(co.copy())
            co = rotate_2d(cur_loc, co, angle)
            circlesel_screen_lines.append(co.copy())


    #BOX SELECTION LINES
    boxsel_screen_lines = []
    if self.box_selecting:
        
        init_loc = mathutils.Vector(( self._changing_po_cache[0][0], self._changing_po_cache[0][1] ))
        cur_loc = mathutils.Vector(( self._mouse_loc[0], self._mouse_loc[1] ))
        
        top_right = mathutils.Vector(( self._mouse_loc[0], self._changing_po_cache[0][1] ))
        bot_left = mathutils.Vector(( self._changing_po_cache[0][0], self._mouse_loc[1] ))
        
        
        vec = init_loc-top_right
        start_co = top_right
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        boxsel_screen_lines += dashed_lines
        
        vec = top_right-cur_loc
        start_co = cur_loc
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        boxsel_screen_lines += dashed_lines
        
        vec = cur_loc-bot_left
        start_co = bot_left
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        boxsel_screen_lines += dashed_lines
        
        vec = bot_left-init_loc
        start_co = init_loc
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        boxsel_screen_lines += dashed_lines
    
    rot_screen_lines = []
    if self.rotating:
        cent_loc = view3d_utils.location_3d_to_region_2d(region, rv3d, self._changing_po_cache[1])
        cur_loc = mathutils.Vector(( self._mouse_loc[0], self._mouse_loc[1] ))
        
        
        vec = cur_loc-cent_loc
        start_co = cent_loc
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        rot_screen_lines += dashed_lines

    
    #stores 2d batches
    self.batch_boxsel_screen_lines = batch_for_shader(self.shader_2d, 'LINES', {"pos": boxsel_screen_lines})
    self.batch_circlesel_screen_lines = batch_for_shader(self.shader_2d, 'LINES', {"pos": circlesel_screen_lines})
    self.batch_lassosel_screen_lines = batch_for_shader(self.shader_2d, 'LINES', {"pos": lassosel_screen_lines})
    self.batch_rotate_screen_lines = batch_for_shader(self.shader_2d, 'LINES', {"pos": rot_screen_lines})
    
    if self.redraw:
        self._points_container.update(addon_prefs.normal_size, self._active_point, addon_prefs.selected_only, addon_prefs.selected_scale)
        self.redraw = False
    
    force_scene_update()
    return



def draw_callback_3d(self, context):
    try:
        addon_prefs = bpy.context.preferences.addons[__package__].preferences

        self._points_container.draw_po(True, self._x_ray_mode, addon_prefs.line_brightness, addon_prefs.point_size)
        self._points_container.draw_sel_po(True, self._x_ray_mode, addon_prefs.line_brightness, addon_prefs.point_size)
        self._points_container.draw_act_po(True, self._x_ray_mode, addon_prefs.line_brightness, addon_prefs.point_size)
        self._points_container.draw_line(self._x_ray_mode, addon_prefs.line_brightness)
        self._points_container.draw_sel_line(self._x_ray_mode, addon_prefs.line_brightness)
        self._points_container.draw_act_line(self._x_ray_mode, addon_prefs.line_brightness)

        if len(self.translate_draw_line) > 0:
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glLineWidth(2)
            self.shader_3d.bind()
            if self.translate_axis == 0:
                self.shader_3d.uniform_float("color", (1.0,0.0,0.0,1.0))
            if self.translate_axis == 1:
                self.shader_3d.uniform_float("color", (0.0,1.0,0.0,1.0))
            if self.translate_axis == 2:
                self.shader_3d.uniform_float("color", (0.0,0.0,1.0,1.0))
            self.batch_translate_line.draw(self.shader_3d)
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glDisable(bgl.GL_DEPTH_TEST)

        if addon_prefs.rotate_gizmo_use and self.rotate_gizmo_draw:
            self._window.gizmo_draw()
    except:
        pass
    
    return



def draw_callback_2d(self, context):

    try:
        bgl.glLineWidth(2)
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", (0.05, 0.05, 0.05, 1))
        self.batch_rotate_screen_lines.draw(self.shader_2d)

        bgl.glLineWidth(1)
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1))
        self.batch_boxsel_screen_lines.draw(self.shader_2d)
        
        bgl.glLineWidth(1)
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1))
        self.batch_circlesel_screen_lines.draw(self.shader_2d)

        bgl.glLineWidth(1)
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1))
        self.batch_lassosel_screen_lines.draw(self.shader_2d)

        self._window.draw()

        bgl.glPointSize(2)
        self.batch_po = batch_for_shader(self.shader_2d, 'POINTS', { "pos": self._temp_po_draw })
        self.shader_2d.bind()
        self.shader_2d.uniform_float("color", (1.0, 0.0, 0.0, 1))
        self.batch_po.draw(self.shader_2d)
    except:
        pass
    return



def clear_drawing(self):
    context = bpy.context
    bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle_2d, "WINDOW")
    bpy.types.SpaceView3D.draw_handler_remove(self._draw_handle_3d, "WINDOW")
    
    self._draw_handle_2d = None
    self._draw_handle_3d = None
    return