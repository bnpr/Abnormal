import bpy
import bgl
import traceback
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from .functions_general import *


def refresh_batches(self, context):
    # ACTIVELY DRAWING DATA LISTS
    if self.active_drawing:
        create_selection_drawing_lists(self)

    if self.redraw:
        self._points_container.update()

    self.redraw = False
    force_scene_update()
    return


def draw_callback_3d(self, context):
    clear_draw = False

    try:
        if self._modal_running == False:
            clear_draw = True

        bgl.glEnable(bgl.GL_BLEND)
        if self._x_ray_mode == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)

        self._points_container.draw()

        if len(self.translate_draw_line) > 0:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glLineWidth(2)
            self.shader_3d.bind()
            if self.translate_axis == 0:
                self.shader_3d.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
            if self.translate_axis == 1:
                self.shader_3d.uniform_float("color", (0.0, 1.0, 0.0, 1.0))
            if self.translate_axis == 2:
                self.shader_3d.uniform_float("color", (0.0, 0.0, 1.0, 1.0))
            self.batch_translate_line.draw(self.shader_3d)
            bgl.glDisable(bgl.GL_DEPTH_TEST)

        if self._x_ray_mode == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)

        if self._use_gizmo:
            self._window.gizmo_draw()

        bgl.glDisable(bgl.GL_BLEND)

    except Exception:
        print()
        print()
        print()
        print('######')
        print('ABNORMAL DRAW 3D ERROR! INCLUDE THE NEXT ERROR MESSAGE WITH ANY BUG REPORT')
        print('######')
        print()
        print()
        traceback.print_exc()
        print()
        print()
        print()
        clear_draw = True

    if clear_draw:
        print('Something is wrong, clear out 3D Draw Handler')
        dns = bpy.app.driver_namespace
        dc = dns.get("dh3d")
        try:
            bpy.types.SpaceView3D.draw_handler_remove(dc, 'WINDOW')
        except:
            pass
    return


def draw_callback_2d(self, context):
    clear_draw = False

    try:
        if self._modal_running == False:
            clear_draw = True

        if context.area == self._draw_area:
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
            self.batch_po = batch_for_shader(self.shader_2d, 'POINTS', {
                "pos": self._temp_po_draw})
            self.shader_2d.bind()
            self.shader_2d.uniform_float("color", (1.0, 0.0, 0.0, 1))
            self.batch_po.draw(self.shader_2d)

    except Exception:
        print()
        print()
        print()
        print('######')
        print('ABNORMAL DRAW 2D ERROR! INCLUDE THE NEXT ERROR MESSAGE WITH ANY BUG REPORT')
        print('######')
        print()
        print()
        traceback.print_exc()
        print()
        print()
        print()
        clear_draw = True

    if clear_draw:
        print('Something is wrong, clear out 2D Draw Handler')
        dns = bpy.app.driver_namespace
        dc = dns.get("dh2d")
        try:
            bpy.types.SpaceView3D.draw_handler_remove(dc, 'WINDOW')
        except:
            pass
    return


def clear_drawing(self):
    try:
        bpy.types.SpaceView3D.draw_handler_remove(
            self._draw_handle_2d, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(
            self._draw_handle_3d, "WINDOW")
    except:
        pass

    self._draw_handle_2d = None
    self._draw_handle_3d = None
    return


def viewport_change_cache(self, context):
    if context.area.type == 'VIEW_3D':
        for space in context.area.spaces:
            if space.type == 'VIEW_3D':
                self._reg_header = space.show_region_toolbar
                self._reg_ui = space.show_region_ui
                self._cursor = space.overlay.show_cursor
                self._wireframe = space.overlay.show_wireframes
                self._thresh = space.overlay.wireframe_threshold
                self._text = space.overlay.show_text

                self._use_wireframe_overlay = self._display_prefs.display_wireframe
                space.overlay.show_wireframes = self._use_wireframe_overlay
                space.overlay.wireframe_threshold = 1.0

                space.show_region_toolbar = False
                space.show_region_ui = False
                space.overlay.show_cursor = False
                space.overlay.show_text = False
    return


#
#


def end_active_drawing(self):
    self.active_drawing = False
    create_selection_drawing_lists(self)
    return


def create_selection_drawing_lists(self):
    # region outline calculation
    rh = self.act_reg.height
    rw = self.act_reg.width

    center = rw/2

    # CIRCLE SELECTION LINES
    circlesel_screen_lines = []
    if self.circle_selecting or self.circle_resizing:
        if self.circle_resizing:
            cur_loc = mathutils.Vector(
                (self._mode_cache[0][0], self._mode_cache[0][1]))
        else:
            cur_loc = mathutils.Vector(
                (self._mouse_reg_loc[0], self._mouse_reg_loc[1]))

        co = cur_loc.copy()
        co[1] += self.circle_radius
        angle = math.radians(360/32)

        for i in range(32):
            circlesel_screen_lines.append(co.copy())
            co = rotate_2d(cur_loc, co, angle)
            circlesel_screen_lines.append(co.copy())

    # LASSO SELECTION LINES
    lassosel_screen_lines = []
    if self.lasso_selecting:
        for i in range(len(self._mode_cache)):
            lassosel_screen_lines.append(self._mode_cache[i-1])
            lassosel_screen_lines.append(self._mode_cache[i])

    # BOX SELECTION LINES
    boxsel_screen_lines = []
    if self.box_selecting:

        init_loc = mathutils.Vector(
            (self._mode_cache[0][0], self._mode_cache[0][1]))
        cur_loc = mathutils.Vector(
            (self._mouse_reg_loc[0], self._mouse_reg_loc[1]))

        top_right = mathutils.Vector(
            (self._mouse_reg_loc[0], self._mode_cache[0][1]))
        bot_left = mathutils.Vector(
            (self._mode_cache[0][0], self._mouse_reg_loc[1]))

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

    # ROTATION CENTER LINE
    rot_screen_lines = []
    if self.rotating:
        cent_loc = view3d_utils.location_3d_to_region_2d(
            self.act_reg, self.act_rv3d, self._mode_cache[2])
        cur_loc = mathutils.Vector(
            (self._mouse_reg_loc[0], self._mouse_reg_loc[1]))

        vec = cur_loc-cent_loc
        start_co = cent_loc
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        rot_screen_lines += dashed_lines

    # STORE 2D BATCHES
    self.batch_boxsel_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": boxsel_screen_lines})
    self.batch_lassosel_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": lassosel_screen_lines})
    self.batch_circlesel_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": circlesel_screen_lines})
    self.batch_rotate_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": rot_screen_lines})

    return


def empty_selection_drawing_lists(self):
    # STORE 2D BATCHES
    self.batch_boxsel_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": []})
    self.batch_lassosel_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": []})
    self.batch_circlesel_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": []})
    self.batch_rotate_screen_lines = batch_for_shader(
        self.shader_2d, 'LINES', {"pos": []})

    return
