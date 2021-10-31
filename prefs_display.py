import bpy

from bpy.types import PropertyGroup
from bpy.props import *


class prefs(PropertyGroup):
    selected_only: BoolProperty(default=False)
    selected_scale: BoolProperty(default=True)
    draw_weights: BoolProperty(default=True)
    display_wireframe: BoolProperty(default=True)
    normal_size: FloatProperty(default=0.5, min=0.01, max=10.0)
    point_size: FloatProperty(default=1.0, min=.1, max=10.0)
    loop_tri_size: FloatProperty(default=0.75, min=0.0, max=1.0)
    line_brightness: FloatProperty(default=1.0, min=.01, max=2.0)
    gizmo_size: IntProperty(default=200, min=10, max=1000)
    ui_scale: FloatProperty(default=0.0, min=0.25, max=3.0)

    display_collapsed: BoolProperty(default=True)
    symmetry_collapsed: BoolProperty(default=True)
    alignment_collapsed: BoolProperty(default=True)
    direction_collapsed: BoolProperty(default=True)
    modify_collapsed: BoolProperty(default=True)
    filter_collapsed: BoolProperty(default=True)
    copy_collapsed: BoolProperty(default=True)
    modes_collapsed: BoolProperty(default=True)


def label_row(path, prop, row, label):
    row.label(text=label)
    row.prop(path, prop, text='')


def draw(preference, context, layout):
    label_row(preference.display, 'selected_only',
              layout.row(), 'Display Selected Normals Only')
    label_row(preference.display, 'selected_scale',
              layout.row(), 'Scale Selected Nomrals')
    label_row(preference.display, 'draw_weights',
              layout.row(), 'Draw Filter Weights')
    label_row(preference.display, 'display_wireframe',
              layout.row(), 'Display Wireframe')
    label_row(preference.display, 'normal_size',
              layout.row(), 'Normal Length')
    label_row(preference.display, 'point_size',
              layout.row(), 'Point Size')
    label_row(preference.display, 'line_brightness',
              layout.row(), 'Normal Brightness')
    label_row(preference.display, 'gizmo_size',
              layout.row(), 'Gizmo Pixel Size')
    label_row(preference.display, 'ui_scale',
              layout.row(), 'UI Scale')

    label_row(preference.display, 'display_collapsed',
              layout.row(), 'Viewport Settings menu collapsed')
    label_row(preference.display, 'symmetry_collapsed',
              layout.row(), 'Symmetry menu collapsed')
    label_row(preference.display, 'alignment_collapsed',
              layout.row(), 'Axis Alignment menu collapsed')
    label_row(preference.display, 'direction_collapsed',
              layout.row(), 'Normal Direction menu collapsed')
    label_row(preference.display, 'modify_collapsed',
              layout.row(), 'Modify Normals menu collapsed')
    label_row(preference.display, 'filter_collapsed',
              layout.row(), 'Filter menu collapsed')
    label_row(preference.display, 'copy_collapsed',
              layout.row(), 'Copy/Paster menu collapsed')
    label_row(preference.display, 'modes_collapsed',
              layout.row(), 'Normal Target Modes menu collapsed')


def register():
    bpy.utils.register_class(prefs)
    return


def unregister():
    bpy.utils.unregister_class(prefs)
    return
