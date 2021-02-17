import bpy
from bpy.props import *
from bpy.types import PropertyGroup, AddonPreferences
from . import prefs_display, prefs_behavior, prefs_keymap


class ABNScnProperties(PropertyGroup):
    object: StringProperty()
    vertex_group: StringProperty(
        description='Vertex Group to filter normal changes with')


class AbnormalAddonPreferences(AddonPreferences):
    bl_idname = __package__

    settings: EnumProperty(
        name='Settings', description='Settings to display',
        items=[('PREFS_DISPLAY', 'Display', ''), ('PREFS_BEHAVIOR', 'Behavior', ''), ('PREFS_KEYMAP', 'Keymap', '')], default='PREFS_DISPLAY')

    behavior: PointerProperty(type=prefs_behavior.prefs)
    display: PointerProperty(type=prefs_display.prefs)
    keymap: PointerProperty(type=prefs_keymap.prefs)

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        row = column.row(align=True)
        row.prop(self, 'settings', expand=True)

        box = column.box()
        globals()[self.settings.lower()].draw(self, context, box)


def register():
    prefs_display.register()
    prefs_behavior.register()
    prefs_keymap.register()
    bpy.utils.register_class(ABNScnProperties)
    bpy.utils.register_class(AbnormalAddonPreferences)

    bpy.types.Scene.abnormal_props = PointerProperty(type=ABNScnProperties)
    return


def unregister():
    prefs_display.unregister()
    prefs_behavior.unregister()
    prefs_keymap.unregister()
    bpy.utils.unregister_class(ABNScnProperties)
    bpy.utils.unregister_class(AbnormalAddonPreferences)

    del bpy.types.Scene.abnormal_props
    return
