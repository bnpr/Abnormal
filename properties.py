import bpy
from bpy.props import *
from bpy.types import PropertyGroup, AddonPreferences


class ABNScnProperties(PropertyGroup):
    smooth_strength: FloatProperty(default=0.25)
    smooth_iters: IntProperty(default=5)


class AbnormalAddonPreferences(AddonPreferences):
    bl_idname = __package__

    left_select: BoolProperty(default=True)
    selected_only: BoolProperty(default=False)
    selected_scale: BoolProperty(default=True)
    rotate_gizmo_use: BoolProperty(default=True)
    display_wireframe: BoolProperty(default=True)
    normal_size: FloatProperty(default=0.5)
    point_size: FloatProperty(default=1.0)
    line_brightness: FloatProperty(default=1.0)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "left_select", text='Default Left Click Select Status')
        col.prop(self, "selected_only", text='Default Selected Only Status')
        col.prop(self, "selected_scale", text='Default Selected Scale Status')
        col.prop(self, "rotate_gizmo_use", text='Default Rotate Gizmo Status')
        col.prop(self, "display_wireframe", text='Default Wireframe Display Status')
        col.prop(self, "normal_size", text='Default Normal Length')
        col.prop(self, "point_size", text='Default Point Size')
        col.prop(self, "line_brightness", text='Default Line Brightness')