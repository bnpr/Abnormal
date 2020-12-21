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
from .classes import *
from .ui_classes import *


from bpy.types import PropertyGroup


class ABN_OT_normal_editor_modal(Operator):
    bl_idname = "abnormal.normal_editor_modal"
    bl_label = "Start Normal Editor"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def modal(self, context, event):
        self._modal_running = False
        scn_prop = context.scene.abnormal_props

        if bpy.context.area == None:
            finish_modal(self)
            self.report({'WARNING'}, "Something went wrong. Cancelling modal")
            return {"CANCELLED"}

        if bpy.context.area.type != 'VIEW_3D':
            finish_modal(self)
            self.report({'WARNING'}, "Left 3D View. Cancelling modal")
            return {"CANCELLED"}

        status = {"RUNNING_MODAL"}

        self._mouse_loc = [event.mouse_region_x, event.mouse_region_y]
        self._window.check_border_change()

        if self.pre_moving:
            status = pre_moving_keymap(self, context, event)

        elif self.moving:
            status = moving_keymap(self, context, event)

        elif self.resizing:
            status = resizing_keymap(self, context, event)

        elif self.pre_item_click:
            status = pre_item_click_keymap(self, context, event)

        elif self.box_selecting or self.box_select_start:
            status = box_select_keymap(self, context, event)

        elif self.lasso_selecting:
            status = lasso_select_keymap(self, context, event)

        elif self.circle_selecting or self.circle_select_start:
            status = circle_select_keymap(self, context, event)

        elif self.num_sliding:
            status = num_sliding_keymap(self, context, event)

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
            status = basic_keymap(self, context, event)

        self._modal_running = True
        refresh_batches(self, context)
        return status

    def invoke(self, context, event):
        region = context.region
        rh = region.height
        rw = region.width
        data = bpy.data

        abn_props = context.scene.abnormal_props
        addon_prefs = bpy.context.preferences.addons[__package__].preferences

        if context.active_object == None:
            self.report({'WARNING'}, "No valid active object selected")
            return {'CANCELLED'}

        if context.active_object.type != 'MESH':
            self.report({'WARNING'}, "Active object is not a mesh")
            return {'CANCELLED'}

        if context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if context.area.type == 'VIEW_3D':
            for space in context.area.spaces:
                if space.type == 'VIEW_3D':
                    self._reg_header = space.show_region_toolbar
                    self._reg_ui = space.show_region_ui
                    self._cursor = space.overlay.show_cursor
                    self._wireframe = space.overlay.show_wireframes
                    self._thresh = space.overlay.wireframe_threshold
                    self._text = space.overlay.show_text

                    #space.show_region_header = False
                    space.show_region_toolbar = False
                    space.show_region_ui = False
                    space.overlay.show_cursor = False
                    space.overlay.show_wireframes = addon_prefs.display_wireframe
                    space.overlay.wireframe_threshold = 1.0
                    space.overlay.show_text = False

        if context.space_data.type == 'VIEW_3D':
            # INITIALIZE PROPERTIES
            self._mouse_loc = [event.mouse_region_x, event.mouse_region_y]
            self._prev_reg_dim = [rw, rh]
            self._active_point = None
            self._changing_po_cache = []
            self._line_drawing_pos = []
            self._copy_normals = None
            self._copy_normal_ind = None
            self._copy_normals_vecs = None
            self.circle_radius = 100.0
            self.circle_status = False
            self.target_strength = 1.0
            self.target_emp = None
            self.point_align = False
            self.translate_mode = 0
            self.translate_axis = 2
            self.translate_draw_line = []
            self.max_undo = 32
            self.undo_norm_state = 0
            self.undo_sel_state = 0
            self.rotate_gizmo_draw = False
            self._rot_increment_one = True
            self._rot_increment_five = False
            self._rot_increment_ten = False
            self._rot_increment = 1
            self._modal_running = True
            self._object_smooth = True
            self._filter_weights = None
            self._lock_x = False
            self._lock_y = False
            self._lock_z = False

            self.area = context.area

            abn_props.object = context.active_object.name
            # NAVIGATION KEYS LIST
            init_nav_list(self)

            # MODES
            self.pre_moving_no_coll = False
            self.pre_moving = False
            self.moving = False
            self.resizing = False
            self.pre_item_click = False
            self.box_select_start = False
            self.box_selecting = False
            self.lasso_selecting = False
            self.circle_selecting = False
            self.circle_select_start = False
            self.circle_resizing = False
            self.num_sliding = False
            self.rotating = False
            self.sphereize_mode = False
            self.sphereize_move = False
            self.point_mode = False
            self.point_move = False
            self.gizmo_click = False
            self.waiting = False

            # VIEWPORT DISPLAY SETTINGS
            self._x_ray_mode = False
            self.redraw = True
            self.prev_view = context.region_data.view_matrix.copy()
            # UNDO STACK STORAGE
            self.undo_sel_stack = []
            self.undo_norm_stack = []

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
            self.shader_img = gpu.shader.from_builtin('2D_IMAGE')

            self._points_container = ABNPoints(
                self.shader_3d, self._object.matrix_world)

            # INITIALIZE POINT DATA
            cache_point_data(self)
            add_orbit_empty(self)

            update_filter_weights(self)

            add_to_undostack(self, 0)
            add_to_undostack(self, 1)

            # INITIALIZE PANELS
            self._window = UIWindow(
                self.shader_2d, self.shader_3d, self.shader_img)
            self._window.add_border(
                color=(0.423, 0.144, 0.863, 1.0), thickness=2, use_header=False)

            bool_size = round(14*self._window.scale)

            r_height = bpy.context.region.height
            r_width = bpy.context.region.width
            panel = self._window.add_panel(
                header_text='Abnormal', hover_highlight=True)
            panel.subp_use_header_box = False
            panel.position = [25, r_height - 25]
            panel.alignment = 'TL'
            panel.header_icon = img_load(self, 'AbLogo.png')
            panel.icon_shader = self.shader_img

            subp = panel.add_subpanel(
                self._window.scale, header_text='Lock Axis')
            row = subp.add_row()
            row.add_bool_prop(120, 'X',
                              bool_size, self._lock_x)
            row.add_bool_prop(121, 'Y',
                              bool_size, self._lock_y)
            row.add_bool_prop(122, 'Z',
                              bool_size, self._lock_z)

            subp = panel.add_subpanel(
                self._window.scale, header_text='Mirror Normals')
            row = subp.add_row()
            row.add_button(2, 'X')
            row.add_button(3, 'Y')
            row.add_button(4, 'Z')

            subp = panel.add_subpanel(
                self._window.scale, header_text='Axis Alignment')
            subp.add_text_row('Flatten Normals', round(12*self._window.scale))
            row = subp.add_row()
            row.add_button(5, 'X')
            row.add_button(6, 'Y')
            row.add_button(7, 'Z')
            subp.add_text_row('Align to Axis', round(12*self._window.scale))
            row = subp.add_row()
            row.add_button(8, '+X')
            row.add_button(11, '-X')
            row.add_button(9, '+Y')
            row.add_button(12, '-Y')
            row.add_button(10, '+Z')
            row.add_button(13, '-Z')

            subp = panel.add_subpanel(
                self._window.scale, header_text='Normal Direction')
            row = subp.add_row()
            row.add_button(14, 'Flip Normals')
            row = subp.add_row()
            row.add_button(15, 'Set Outside')
            row.add_button(16, 'Set Inside')
            row = subp.add_row()
            row.add_button(17, 'Reset Vectors')
            subp = panel.add_subpanel(
                self._window.scale, header_text='Manipulate Normals')
            row = subp.add_row()
            row.add_bool_prop(59, 'Use Rotation Gizmo',
                              bool_size, addon_prefs.rotate_gizmo_use)
            row = subp.add_row()
            row.add_button(18, 'Average Individual Vertex Normals')
            row = subp.add_row()
            row.add_button(19, 'Average All Selected Normals')
            row = subp.add_row()
            row.add_button(20, 'Smooth Selected Normals')
            row = subp.add_row()
            row.add_num_prop(56, 'Smooth Strength', round(
                abn_props.smooth_strength, 2), 2, 0.01, 0.01, 1.0)
            row.add_num_prop(57, 'Smooth Iterations',
                             abn_props.smooth_iters, 0, 1, 1, 25)
            row = subp.add_row()
            row.add_button(40, 'Set Smooth Shading')
            row.add_button(41, 'Set Flat Shading')
            subp = panel.add_subpanel(
                self._window.scale, header_text='Copy/Paste Normals')
            row = subp.add_row()
            row.add_button(21, 'Copy Active Normal to Selected')
            row = subp.add_row()
            row.add_button(22, 'Copy Active Normal')
            row = subp.add_row()
            row.add_button(23, 'Paste Normal to Selected')
            subp = panel.add_subpanel(
                self._window.scale, header_text='Target Normals')
            row = subp.add_row()
            row.add_button(24, 'Sphereize Normals')
            row = subp.add_row()
            row.add_button(30, 'Point Normals at Target')
            panel = self._window.add_panel(
                header_text='Addon Settings', hover_highlight=True, x_size=225)
            panel.position = [r_width-25, r_height-25]
            panel.alignment = 'TR'
            subp = panel.add_subpanel(
                self._window.scale, header_text='Finish Modal')
            row = subp.add_row()
            row.add_button(0, 'Confirm Changes')
            row.add_button(1, 'Cancel Changes')

            subp = panel.add_subpanel(
                self._window.scale, header_text='Viewport Settings')
            row = subp.add_row()
            row.add_bool_prop(50, 'Show Only Selected Normals',
                              bool_size, addon_prefs.selected_only)
            row = subp.add_row()
            row.add_bool_prop(70, 'Scale Up Selected Normals',
                              bool_size, addon_prefs.selected_scale)
            row = subp.add_row()
            row.add_bool_prop(51, 'X-Ray', bool_size, self._x_ray_mode)
            row = subp.add_row()
            row.add_num_prop(52, 'Normals Length', round(
                addon_prefs.normal_size, 2), 2, 0.01, 0.01, 10.0)
            row = subp.add_row()
            row.add_num_prop(53, 'Normals Brightness', round(
                addon_prefs.line_brightness, 2), 2, 0.01, 0.01, 2.0)
            row = subp.add_row()
            row.add_num_prop(54, 'Vertex Point Size', round(
                addon_prefs.point_size, 1), 1, 0.1, 0.1, 10.0)
            row = subp.add_row()
            row.add_bool_prop(55, 'Display Wireframe',
                              bool_size, addon_prefs.display_wireframe)
            row = subp.add_row()
            row.add_num_prop(91, 'Gizmo Size', round(
                addon_prefs.gizmo_size, 0), 0, 10, 100, 1000)
            row = subp.add_row()
            row.add_bool_prop(90, 'Left Click Select',
                              bool_size, addon_prefs.left_select)
            # row = subp.add_row()
            # row.add_num_prop(101, 'UI Scale', self._window.scale, 2, .1, 0.1, 5.0)
            row = subp.add_row()
            row.add_button(34, 'Save Addon Preferences')

            subp = panel.add_subpanel(self._window.scale, header_text='Keymap')
            subp.text_align = 'Left'

            keymap_initialize(self)

            self.rot_gizmo = self._window.add_rot_gizmo(
                self._object.matrix_world, addon_prefs.gizmo_size, [True, True, True], 0.045)

            panel = self._window.add_panel(
                header_text='Incremental Rotations', hover_highlight=True)
            panel.alignment = 'TL'
            panel.visible_on_hover = False
            panel.visible = False
            panel.add_visible_oh_hov_icon(25)
            panel.reposition_offset = [
                self.rot_gizmo.size/2+25, self.rot_gizmo.size/2]
            subp = panel.add_subpanel(self._window.scale, header_text='')
            subp.use_header_box = False
            subp.use_header = False
            row = subp.add_row()
            row.add_bool_prop(80, '+/-1°', bool_size, self._rot_increment_one)
            row.add_bool_prop(81, '+/-5°', bool_size, self._rot_increment_five)
            row.add_bool_prop(82, '+/-10°', bool_size, self._rot_increment_ten)
            row = subp.add_row()
            label = row.add_label('X')
            label.icon = img_load(self, 'XAxis.png')
            row.add_button(83, '_')
            row.add_button(84, '+')
            row = subp.add_row()
            label = row.add_label('Y')
            label.icon = img_load(self, 'YAxis.png')
            row.add_button(85, '_')
            row.add_button(86, '+')
            row = subp.add_row()
            label = row.add_label('Z')
            label.icon = img_load(self, 'ZAxis.png')
            row.add_button(87, '_')
            row.add_button(88, '+')

            #panel.collapse = True
            self._window.create_all_drawing_data()

            update_orbit_empty(self,)

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
