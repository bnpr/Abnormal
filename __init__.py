bl_info = {
    "name": "Abnormal",
    "author": "Cody Winchester (codywinch)",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D View > Object and Properties > Object tab",
    "description": "BNPR Normal Editing Tools",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
    }



import bpy
from bpy.props import *
from .ui import *
from .properties import *
from .operators_modal import *
from .classes import *



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
