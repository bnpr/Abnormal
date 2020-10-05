from .classes import *
from .ui_classes import *
from .operators_modal import *
from .properties import *
from .ui import *
from bpy.props import *
import bpy
bl_info = {
    "name": "Abnormal",
    "author": "Cody Winchester (codywinch)",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "3D View > Object and Properties > Object tab",
    "description": "BNPR Normal Editing Tools",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
}

if "bpy" in locals():
    import imp
    if "__init__" in locals():
        imp.reload(__init__)
    if "ui" in locals():
        imp.reload(ui)
    if "properties" in locals():
        imp.reload(properties)
    if "classes" in locals():
        imp.reload(classes)
    if "ui_classes" in locals():
        imp.reload(ui_classes)
    if "operators_modal" in locals():
        imp.reload(operators_modal)


classes = [
    ABN_OT_normal_editor_modal,
    AbnormalAddonPreferences,
    ABNScnProperties,
    ABN_PT_abnormal_panel,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.abnormal_props = PointerProperty(type=ABNScnProperties)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.abnormal_props


if __name__ == "__main__":
    register()
