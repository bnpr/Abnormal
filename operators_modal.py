import bpy
from bpy.props import *
from bpy.types import Operator
from mathutils import Vector
from .properties import *
from .functions_general import *
from .functions_drawing import *
from .functions_modal import *
from .functions_keymaps import *
from .functions_modal_buttons import *
from .functions_modal_keymap import *
from .functions_tools import *
from .classes import *
import time


class ABN_OT_normal_editor_modal(Operator):
    bl_idname = "abnormal.normal_editor_modal"
    bl_label = "Start Normal Editor"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def modal(self, context, event):
        self._modal_running = False
        status = {"RUNNING_MODAL"}

        if bpy.context.area == None:
            finish_modal(self, True)
            self.report({'WARNING'}, "Something went wrong. Cancelling modal")
            return {"CANCELLED"}

        if bpy.context.area.type != 'VIEW_3D':
            finish_modal(self, True)
            self.report({'WARNING'}, "Left 3D View. Cancelling modal")
            return {"CANCELLED"}

        # If event.type is blank avoid testing it agaisnt keys as it prints a lot of errors
        if event.type == '':
            self._modal_running = True
            return status

        self._mouse_abs_loc[:] = [event.mouse_x, event.mouse_y, 0.0]
        self._mouse_reg_loc[:] = [
            event.mouse_region_x, event.mouse_region_y, 0.0]

        self.act_reg, self.act_rv3d = check_area(self)
        # self._mouse_act_loc = [self._mouse_abs_loc[0]-self.act_reg.x, self._mouse_abs_loc[1]-self.act_reg.y]

        self._window.check_dimensions(context)
        # Check that mousemove is larger than a pixel to be tested
        mouse_move_check = True
        if event.type == 'MOUSEMOVE' and Vector(self._mouse_reg_loc-self._prev_mouse_loc).length < 1.0:
            mouse_move_check = False

        if mouse_move_check:
            if self.typing:
                status = typing_keymap(self, context, event)

            elif self.tool_mode and self._current_tool != None:
                if self.ui_hover:
                    status = basic_ui_hover_keymap(self, context, event)
                else:
                    status = self._current_tool.test_mode(
                        self, context, event, self.keymap, None)

            else:
                if self.ui_hover:
                    status = basic_ui_hover_keymap(self, context, event)
                else:
                    status = basic_keymap(self, context, event)
            self._prev_mouse_loc[:] = self._mouse_reg_loc

        refresh_batches(self, context)

        self._modal_running = True
        return status

    def invoke(self, context, event):
        self.act_reg, self.act_rv3d = check_area(self)
        rh = self.act_reg.height
        rw = self.act_reg.width

        if context.active_object == None:
            self.report({'WARNING'}, "No valid active object selected")
            return {'CANCELLED'}

        if context.active_object.type != 'MESH':
            self.report({'WARNING'}, "Active object is not a mesh")
            return {'CANCELLED'}

        if context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if context.space_data.type == 'VIEW_3D':
            # INITIALIZE PROPERTIES
            self._addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
                0]].preferences
            self._display_prefs = self._addon_prefs.display
            self._behavior_prefs = self._addon_prefs.behavior
            self._keymap_sel_prefs = self._addon_prefs.keymap_sel
            self._keymap_shortcut_prefs = self._addon_prefs.keymap_shortcut
            self._keymap_tool_prefs = self._addon_prefs.keymap_tool
            self._mouse_abs_loc = np.array([event.mouse_x, event.mouse_y, 0.0])
            self._mouse_reg_loc = np.array(
                [event.mouse_region_x, event.mouse_region_y, 0.0])
            self._prev_mouse_loc = np.array(
                [event.mouse_region_x, event.mouse_region_y, 0.0])

            self._mouse_init = np.array([0.0, 0.0, 0.0])
            self._active_point = None
            self._active_face = None

            self._mode_cache = []
            self._line_drawing_pos = []

            self._copy_normals = np.array([])

            self.target_strength = 1.0
            self._target_emp = None
            self.point_align = False

            self.translate_mode = 0
            self.translate_axis = 2
            self.translate_draw_line = []

            self._rot_increment_one = True
            self._rot_increment_five = False
            self._rot_increment_ten = False
            self._rot_increment = 1

            self._object_smooth = True

            self._smooth_iterations = 5
            self._smooth_strength = 0.25

            self._mirror_range = 0.1

            self._mirror_x = False
            self._mirror_y = False
            self._mirror_z = False

            self._current_filter = ''

            self._draw_area = context.area
            self._modal_running = True
            self.redraw = False
            self.redraw_active = False
            self.circle_radius = 50

            context.scene.abnormal_props.object = context.active_object.name

            # VIEWPORT DISPLAY SETTINGS
            self._x_ray_mode = False
            self._use_gizmo = self._behavior_prefs.rotate_gizmo_use
            self._gizmo_size = self._display_prefs.gizmo_size
            self._normal_size = self._display_prefs.normal_size
            self._line_brightness = self._display_prefs.line_brightness
            self._point_size = self._display_prefs.point_size
            self._loop_tri_size = self._display_prefs.loop_tri_size
            self._selected_only = self._display_prefs.selected_only
            self._selected_scale = self._display_prefs.selected_scale
            self._individual_loops = self._behavior_prefs.individual_loops
            if self._display_prefs.ui_scale == 0.0:
                self._ui_scale = context.window.width/1920
            else:
                self._ui_scale = self._display_prefs.ui_scale
            self.prev_view = context.region_data.view_matrix.copy()

            # CACHE VIEWPORT SETTINGS
            viewport_change_cache(self, context)

            # NAVIGATION KEYS LIST
            init_nav_list(self)

            # MODES
            self.rotating = False
            self.sphereize_mode = False
            self.point_mode = False
            self.gizmo_click = False
            self.waiting = False

            self.box_selecting = False
            self.lasso_selecting = False
            self.circle_selecting = False
            self.circle_resizing = False
            self.circle_removing = False

            self._current_tool = None
            self.tool_mode = False

            self.click_hold = False
            self.selection_drawing = True
            self.typing = False
            self.bezier_changing = False
            self.ui_hover = False

            # UNDO STACK STORAGE
            self._history_stack = []
            self._history_select_stack = []
            self._history_normal_stack = []
            self._history_position = 0
            self._history_select_position = 0
            self._history_normal_position = 0
            self._history_steps = 128

            # INITIALIZE OBJECTS
            self._objects_mod_status = []
            self._objects_sk_vis = []
            ob_bm, ob_kd, ob_bvh = ob_data_structures(
                self, context.active_object)

            # INITIALIZE OBJECT DATA LISTS
            self._object = context.active_object
            self._object_name = context.active_object.name
            self._object_pointer = context.active_object.as_pointer()

            self._object_bm = ob_bm
            self._object_bvh = ob_bvh
            self._object_kd = ob_kd

            if self._object.data.use_auto_smooth == False:
                self._object.data.use_auto_smooth = True
                self._object.data.auto_smooth_angle = 180

            # INITIALIZE BATCHES AND SHADERS
            self.shader_2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            self.shader_3d = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

            self._container = ABNContainer(
                self._object.matrix_world.normalized())
            self._container.set_scale_selection(self._selected_scale)
            self._container.set_brightess(self._line_brightness)
            self._container.set_normal_scale(self._normal_size)
            self._container.set_point_size(self._point_size)
            self._container.set_loop_scale(self._loop_tri_size)
            self._container.set_draw_only_selected(self._selected_only)
            self._container.set_draw_tris(self._individual_loops)

            # INITIALIZE POINT DATA
            cache_point_data(self)
            self._orbit_ob = add_orbit_empty(self._object)
            self._target_emp = add_target_empty(self._object)

            update_filter_weights(self)

            # INITIALIZE UI WINDOW
            load_keymap(self)
            init_ui_panels(self, rw, rh, self._ui_scale)

            update_orbit_empty(self)

            setup_tools(self)

            # SETUP BATCHES
            self._container.clear_batches()
            refresh_batches(self, context)

            # OPENGL DRAWING HANDLER
            args = (self, context)
            self._draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_2d, args, "WINDOW", "POST_PIXEL")
            self._draw_handle_3d = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback_3d, args, "WINDOW", "POST_VIEW")

            dns = bpy.app.driver_namespace
            dns["dh2d"] = self._draw_handle_2d
            dns["dh3d"] = self._draw_handle_3d

            add_to_undostack(self, 2)

            self._window.check_in_window()

            # SET MODAL
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(ABN_OT_normal_editor_modal)
    return


def unregister():
    bpy.utils.unregister_class(ABN_OT_normal_editor_modal)
    return
