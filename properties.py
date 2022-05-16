import bpy
from bpy.props import *
from bpy.types import PropertyGroup, AddonPreferences
from . import prefs_display, prefs_behavior, prefs_sel_keymap, prefs_shortcut_keymap, prefs_tool_keymap
from .ui import update_panel


class AbnormalAddonPreferences(AddonPreferences):
    bl_idname = __package__

    object: StringProperty()
    vertex_group: StringProperty(
        description='Vertex Group to filter normal changes with')
    vcol: StringProperty(
        description='Vertex Color to write data to/from')

    use_n_panel: BoolProperty(
        default=True, description='Use N Panel tab for addon. If False use the 3D View Header', update=update_panel)

    settings: EnumProperty(
        name='Settings', description='Settings to display',
        items=[('PREFS_DISPLAY', 'Display', ''),
               ('PREFS_BEHAVIOR', 'Behavior', ''),
               ('PREFS_SEL_KEYMAP', 'Keymap Selection', ''),
               ('PREFS_SHORTCUT_KEYMAP', 'Keymap Shortcuts', ''),
               ('PREFS_TOOL_KEYMAP', 'Keymap Tools', '')],
        default='PREFS_DISPLAY')

    behavior: PointerProperty(type=prefs_behavior.prefs)
    display: PointerProperty(type=prefs_display.prefs)
    keymap_sel: PointerProperty(type=prefs_sel_keymap.prefs)
    keymap_shortcut: PointerProperty(type=prefs_shortcut_keymap.prefs)
    keymap_tool: PointerProperty(type=prefs_tool_keymap.prefs)

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
    prefs_sel_keymap.register()
    prefs_shortcut_keymap.register()
    prefs_tool_keymap.register()
    bpy.utils.register_class(AbnormalAddonPreferences)
    return


def unregister():
    prefs_display.unregister()
    prefs_behavior.unregister()
    prefs_sel_keymap.unregister()
    prefs_shortcut_keymap.unregister()
    prefs_tool_keymap.unregister()
    bpy.utils.unregister_class(AbnormalAddonPreferences)
    return
