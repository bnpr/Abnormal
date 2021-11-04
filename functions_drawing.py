import bpy
import bgl
import traceback
from mathutils import Vector
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from .functions_general import *


def refresh_batches(modal, context):
    # ACTIVELY DRAWING DATA LISTS
    if modal.selection_drawing:
        create_selection_drawing_lists(modal)

    if modal.redraw:
        modal._container.update_static()

    if modal.redraw_active:
        modal._container.update_active()

    modal.redraw = False
    modal.redraw_active = False
    force_scene_update()
    return


def draw_callback_3d(modal, context):
    clear_draw = False

    try:
        if modal._modal_running == False:
            clear_draw = True

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_VERTEX_PROGRAM_POINT_SIZE)
        if modal._x_ray_mode == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)

        modal._container.draw()

        if len(modal.translate_draw_line) > 0:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
            bgl.glLineWidth(2)
            modal.shader_3d.bind()
            if modal.translate_axis == 0:
                modal.shader_3d.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
            if modal.translate_axis == 1:
                modal.shader_3d.uniform_float("color", (0.0, 1.0, 0.0, 1.0))
            if modal.translate_axis == 2:
                modal.shader_3d.uniform_float("color", (0.0, 0.0, 1.0, 1.0))
            modal.batch_translate_line.draw(modal.shader_3d)
            bgl.glDisable(bgl.GL_DEPTH_TEST)

        if modal._x_ray_mode == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)

        if modal._use_gizmo:
            modal._window.gizmo_draw()

        bgl.glDisable(bgl.GL_BLEND)
        bgl.glDisable(bgl.GL_VERTEX_PROGRAM_POINT_SIZE)

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


def draw_callback_2d(modal, context):
    clear_draw = False

    try:
        if modal._modal_running == False:
            clear_draw = True

        if context.area == modal._draw_area:
            start_col = (1.0, 0.0, 0.0, 1)
            end_col = (0.0, 0.0, 1.0, 1)
            if modal.gradient_drawing:
                if modal._mode_cache[0][0]:
                    start_col = (1.0, 0.7, 0.7, 1)
                if modal._mode_cache[0][1]:
                    end_col = (0.7, 0.7, 1.0, 1)

            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", start_col)
            modal.batch_gradient_start_screen_points.draw(modal.shader_2d)

            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", end_col)
            modal.batch_gradient_end_screen_points.draw(modal.shader_2d)

            bgl.glLineWidth(2)
            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", (0.05, 0.05, 0.05, 1))
            modal.batch_rotate_screen_lines.draw(modal.shader_2d)

            bgl.glLineWidth(2)
            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", (0.05, 0.05, 0.05, 1))
            modal.batch_gradient_screen_lines.draw(modal.shader_2d)

            bgl.glLineWidth(1)
            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1))
            modal.batch_boxsel_screen_lines.draw(modal.shader_2d)

            bgl.glLineWidth(1)
            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1))
            modal.batch_circlesel_screen_lines.draw(modal.shader_2d)

            bgl.glLineWidth(1)
            modal.shader_2d.bind()
            modal.shader_2d.uniform_float("color", (1.0, 1.0, 1.0, 1))
            modal.batch_lassosel_screen_lines.draw(modal.shader_2d)

            modal._window.draw()

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


def clear_drawing(modal):
    try:
        bpy.types.SpaceView3D.draw_handler_remove(
            modal._draw_handle_2d, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(
            modal._draw_handle_3d, "WINDOW")
    except:
        pass

    modal._draw_handle_2d = None
    modal._draw_handle_3d = None
    return


def viewport_change_cache(modal, context):
    if context.area.type == 'VIEW_3D':
        for space in context.area.spaces:
            if space.type == 'VIEW_3D':
                modal._reg_header = space.show_region_toolbar
                modal._reg_ui = space.show_region_ui
                modal._cursor = space.overlay.show_cursor
                modal._wireframe = space.overlay.show_wireframes
                modal._thresh = space.overlay.wireframe_threshold
                modal._text = space.overlay.show_text

                modal._use_wireframe_overlay = modal._display_prefs.display_wireframe
                space.overlay.show_wireframes = modal._use_wireframe_overlay
                space.overlay.wireframe_threshold = 1.0

                space.show_region_toolbar = False
                space.show_region_ui = False
                space.overlay.show_cursor = False
                space.overlay.show_text = False
    return


#
#


def start_active_drawing(modal):
    modal._container.update_active()
    modal._container.update_static(exclude_active=True)
    return


def end_active_drawing(modal):
    modal._container.clear_active_batches()
    modal._container.update_static()
    return


def end_selection_drawing(modal):
    modal.selection_drawing = False
    empty_selection_drawing_lists(modal)
    return


def create_selection_drawing_lists(modal):
    # region outline calculation
    rh = modal.act_reg.height
    rw = modal.act_reg.width

    center = rw/2

    # CIRCLE SELECTION LINES
    circlesel_screen_lines = []
    if modal.circle_selecting or modal.circle_resizing:
        if modal.circle_resizing:
            cur_loc = modal._mouse_init[:2]
        else:
            cur_loc = modal._mouse_reg_loc[:2]

        circlesel_screen_lines = get_circle_cos(
            cur_loc, 32, modal.circle_radius, close_end=True).tolist()

    # LASSO SELECTION LINES
    lassosel_screen_lines = []
    if modal.lasso_selecting:
        lassosel_screen_lines = np.vstack(
            (np.array(modal._mode_cache[0]), modal._mode_cache[0][0]))[:, [0, 1]].tolist()

    # BOX SELECTION LINES
    boxsel_screen_lines = []
    if modal.box_selecting:

        init_loc = Vector(modal._mode_cache[0][0]).xy
        cur_loc = Vector(modal._mode_cache[0][1]).xy

        top_right = Vector(
            (modal._mode_cache[0][1][0], modal._mode_cache[0][0][1]))
        bot_left = Vector(
            (modal._mode_cache[0][0][0], modal._mode_cache[0][1][1]))

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
    if modal.rotating:
        cent_loc = view3d_utils.location_3d_to_region_2d(
            modal.act_reg, modal.act_rv3d, modal._mode_cache[0])
        cur_loc = Vector(modal._mouse_reg_loc[:2])

        vec = cur_loc-cent_loc
        start_co = cent_loc
        dashed_lines = vec_to_dashed(start_co, vec, int(vec.length/10))
        rot_screen_lines += dashed_lines

    gradient_screen_lines = []
    gradient_start_screen_points = []
    gradient_end_screen_points = []
    # GRADIENT LINE
    if modal.gradient_drawing:
        start_co = modal._mode_cache[3][2]
        end_co = modal._mode_cache[3][3]

        vec = end_co-start_co
        dashed_lines = vec_to_dashed(
            start_co, vec, int(get_np_vec_lengths(vec.reshape(1, -1))[0]/10))
        gradient_screen_lines += dashed_lines

        gradient_start_screen_points = get_circle_cos(
            start_co, 16, 5).tolist()
        gradient_end_screen_points = get_circle_cos(
            end_co, 16, 5).tolist()

    # STORE 2D BATCHES
    modal.batch_boxsel_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINES', {"pos": boxsel_screen_lines})
    modal.batch_lassosel_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINE_STRIP', {"pos": lassosel_screen_lines})
    modal.batch_circlesel_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINE_STRIP', {"pos": circlesel_screen_lines})
    modal.batch_rotate_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINES', {"pos": rot_screen_lines})

    modal.batch_gradient_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINES', {"pos": gradient_screen_lines})
    modal.batch_gradient_start_screen_points = batch_for_shader(
        modal.shader_2d, 'TRI_FAN', {"pos": gradient_start_screen_points})
    modal.batch_gradient_end_screen_points = batch_for_shader(
        modal.shader_2d, 'TRI_FAN', {"pos": gradient_end_screen_points})

    return


def empty_selection_drawing_lists(modal):
    # STORE 2D BATCHES
    modal.batch_boxsel_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINES', {"pos": []})
    modal.batch_lassosel_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINE_STRIP', {"pos": []})
    modal.batch_circlesel_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINE_STRIP', {"pos": []})
    modal.batch_rotate_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINES', {"pos": []})

    modal.batch_gradient_screen_lines = batch_for_shader(
        modal.shader_2d, 'LINES', {"pos": []})
    modal.batch_gradient_start_screen_points = batch_for_shader(
        modal.shader_2d, 'TRI_FAN', {"pos": []})
    modal.batch_gradient_end_screen_points = batch_for_shader(
        modal.shader_2d, 'TRI_FAN', {"pos": []})

    return
