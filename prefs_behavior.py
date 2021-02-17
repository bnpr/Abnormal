import bpy

from bpy.types import PropertyGroup
from bpy.props import *


class prefs(PropertyGroup):
    individual_loops: BoolProperty(default=False)
    rotate_gizmo_use: BoolProperty(default=True)


def label_row(path, prop, row, label):
    row.label(text=label)
    row.prop(path, prop, text='')


def draw(preference, context, layout):
    label_row(preference.behavior, 'rotate_gizmo_use',
              layout.row(), 'Use Rotation Gizmo')
    label_row(preference.behavior, 'individual_loops',
              layout.row(), 'Edit Split Individual Loops')


def register():
    bpy.utils.register_class(prefs)
    return


def unregister():
    bpy.utils.unregister_class(prefs)
    return
