import bpy
from bpy.props import *
from bpy.types import PropertyGroup, AddonPreferences


class ABNScnProperties(PropertyGroup):
    object: StringProperty()
    vertex_group: StringProperty(
        description='Vertex Group to filter normal changes with')


class AbnormalAddonPreferences(AddonPreferences):
    bl_idname = __package__

    individual_loops: BoolProperty(default=False)
    left_select: BoolProperty(default=True)
    selected_only: BoolProperty(default=False)
    selected_scale: BoolProperty(default=True)
    rotate_gizmo_use: BoolProperty(default=True)
    display_wireframe: BoolProperty(default=True)
    normal_size: FloatProperty(default=0.5)
    point_size: FloatProperty(default=1.0)
    line_brightness: FloatProperty(default=1.0)
    gizmo_size: IntProperty(default=200)
    ui_scale: FloatProperty(default=0.0, min=0.25)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "left_select", text='Default Left Click Select Status')
        col.prop(self, "selected_only", text='Default Selected Only Status')
        col.prop(self, "selected_scale", text='Default Selected Scale Status')
        col.prop(self, "rotate_gizmo_use", text='Default Rotate Gizmo Status')
        col.prop(self, "display_wireframe",
                 text='Default Wireframe Display Status')
        col.prop(self, "normal_size", text='Default Normal Length')
        col.prop(self, "point_size", text='Default Point Size')
        col.prop(self, "line_brightness", text='Default Line Brightness')
        col.prop(self, "gizmo_size", text='Default Gizmo Size')
        col.prop(self, "ui_scale", text='Default UI Size')
        col.prop(self, "individual_loops",
                 text='Default Edit Individual Loops')


def register():
    bpy.utils.register_class(ABNScnProperties)
    bpy.utils.register_class(AbnormalAddonPreferences)

    bpy.types.Scene.abnormal_props = PointerProperty(type=ABNScnProperties)
    return


def unregister():
    bpy.utils.unregister_class(ABNScnProperties)
    bpy.utils.unregister_class(AbnormalAddonPreferences)

    del bpy.types.Scene.abnormal_props
    return
