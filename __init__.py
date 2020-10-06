from . import operators_modal
from . import properties
from . import ui
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
    import importlib
    if "__init__" in locals():
        importlib.reload(__init__)
    if "ui" in locals():
        importlib.reload(ui)
    if "properties" in locals():
        importlib.reload(properties)
    if "classes" in locals():
        importlib.reload(classes)
    if "operators_modal" in locals():
        importlib.reload(operators_modal)


def register():
    ui.register()
    properties.register()
    operators_modal.register()


def unregister():
    ui.unregister()
    properties.unregister()
    operators_modal.unregister()


if __name__ == "__main__":
    register()
