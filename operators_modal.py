import bpy
import math
import mathutils
import bmesh
import time
from bpy.props import *
from bpy.types import Operator
from bpy_extras import view3d_utils
from .properties import *
from .functions_general import *
from .functions_drawing import *
from .functions_modal import *
from .functions_keymaps import *
from .functions_modal_buttons import *
from .functions_modal_keymap import *
from .classes import *

from bpy.types import PropertyGroup


class ABN_OT_normal_editor_modal(Operator):
    bl_idname = "abnormal.normal_editor_modal"
    bl_label = "Start Normal Editor"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def modal(self, context, event):
        self._modal_running = False
        if bpy.context.area == None:
            finish_modal(self, True)
            self.report({'WARNING'}, "Something went wrong. Cancelling modal")
            return {"CANCELLED"}

        if bpy.context.area.type != 'VIEW_3D':
            finish_modal(self, True)
            self.report({'WARNING'}, "Left 3D View. Cancelling modal")
            return {"CANCELLED"}

        self._mouse_abs_loc = [event.mouse_x, event.mouse_y]
        self._mouse_reg_loc = [event.mouse_region_x, event.mouse_region_y]

        self.act_reg, self.act_rv3d = check_area(self)
        self._mouse_act_loc = [self._mouse_abs_loc[0] -
                               self.act_reg.x, self._mouse_abs_loc[1]-self.act_reg.y]

        self._window.check_dimensions(context)
        status = {"RUNNING_MODAL"}
        if self.typing:
            status = typing_keymap(self, context, event)
        elif self.box_selecting or self.box_select_start:
            status = box_select_keymap(self, context, event)
        elif self.lasso_select_start or self.lasso_selecting:
            status = lasso_select_keymap(self, context, event)
        elif self.circle_selecting or self.circle_select_start:
            status = circle_select_keymap(self, context, event)
        elif self.rotating:
            status = rotating_keymap(self, context, event)
        elif self.sphereize_mode:
            status = sphereize_keymap(self, context, event)
        elif self.sphereize_move:
            status = sphereize_move_keymap(self, context, event)
        elif self.point_mode:
            status = point_keymap(self, context, event)
        elif self.point_move:
            status = point_move_keymap(self, context, event)
        elif self.gizmo_click:
            status = gizmo_click_keymap(self, context, event)
        else:
            if self.ui_hover:
                status = basic_ui_hover_keymap(self, context, event)
            else:
                status = basic_keymap(self, context, event)

        refresh_batches(self, context)
        self._modal_running = True
        return status

    def invoke(self, context, event):
        self.act_reg, self.act_rv3d = check_area(self)
        rh = self.act_reg.height
        rw = self.act_reg.width
        data = bpy.data

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
            self._addon_prefs = bpy.context.preferences.addons[__package__].preferences
            self._mouse_abs_loc = [event.mouse_x, event.mouse_y]
            self._mouse_reg_loc = [event.mouse_region_x, event.mouse_region_y]

            self._mouse_init = None
            self._active_point = None

            self._mode_cache = []
            self._line_drawing_pos = []

            self._copy_normals = None
            self._copy_normals_tangs = None

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
            self._filter_weights = None

            self._smooth_iterations = 5
            self._smooth_strength = 0.25

            self._mirror_range = 0.1

            self._lock_x = False
            self._lock_y = False
            self._lock_z = False

            self._mirror_x = False
            self._mirror_y = False
            self._mirror_z = False

            self._draw_area = context.area
            self._modal_running = True
            self.redraw = True
            self.circle_radius = 50
            self.circle_status = False

            context.scene.abnormal_props.object = context.active_object.name

            # VIEWPORT DISPLAY SETTINGS
            self._x_ray_mode = False
            self._use_gizmo = self._addon_prefs.rotate_gizmo_use
            self._gizmo_size = self._addon_prefs.gizmo_size
            self._left_select = self._addon_prefs.left_select
            self._normal_size = self._addon_prefs.normal_size
            self._line_brightness = self._addon_prefs.line_brightness
            self._point_size = self._addon_prefs.point_size
            self._selected_only = self._addon_prefs.selected_only
            self._selected_scale = self._addon_prefs.selected_scale
            self._individual_loops = self._addon_prefs.individual_loops
            if self._addon_prefs.ui_scale == 0.0:
                self._ui_scale = context.window.width/1920
            else:
                self._ui_scale = self._addon_prefs.ui_scale
            self.prev_view = context.region_data.view_matrix.copy()

            # CACHE VIEWPORT SETTINGS
            viewport_change_cache(self, context)

            # NAVIGATION KEYS LIST
            init_nav_list(self)

            # MODES
            self.rotating = False
            self.sphereize_mode = False
            self.sphereize_move = False
            self.point_mode = False
            self.point_move = False
            self.gizmo_click = False
            self.waiting = False

            self.box_select_start = False
            self.box_selecting = False
            self.lasso_select_start = False
            self.lasso_selecting = False
            self.circle_selecting = False
            self.circle_select_start = False
            self.circle_resizing = False

            self.click_hold = False
            self.active_drawing = True
            self.typing = False
            self.bezier_changing = False
            self.ui_hover = False

            # UNDO STACK STORAGE
            self._history_stack = []
            self._history_position = 0
            self._history_steps = 128

            self._temp_po_draw = []

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

            self._points_container = ABNPoints(self._object.matrix_world)
            self._points_container.set_scale_selection(self._selected_scale)
            self._points_container.set_brightess(self._line_brightness)
            self._points_container.set_normal_scale(self._normal_size)
            self._points_container.set_point_size(self._point_size)
            self._points_container.set_draw_only_selected(self._selected_only)
            self._points_container.set_draw_tris(self._individual_loops)

            # INITIALIZE POINT DATA
            cache_point_data(self)
            self._orbit_ob = add_orbit_empty(self._object)
            self._target_emp = add_target_empty(self._object)

            update_filter_weights(self)

            add_to_undostack(self, 0)
            add_to_undostack(self, 1)

            # INITIALIZE UI WINDOW
            init_ui_panels(self, rw, rh, self._ui_scale)

            # SETUP BATCHES
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
