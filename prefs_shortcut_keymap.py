import bpy

from bpy.types import PropertyGroup
from bpy.props import *
from .keymap import addon_keymaps


class prefs(PropertyGroup):
    brush_circle_select: BoolProperty(default=False)


def label_row(path, prop, row, label):
    row.label(text=label)
    row.prop(path, prop, text='')


def keymap_row(items, key, row, label):
    row.label(text=label)
    row.prop(items[key], 'type', text='', full_event=True)
    row.prop(items[key], 'value', text='')


def draw(preference, context, layout):
    # label_row(preference.keymap, 'brush_circle_select',
    #           layout.row(), 'Circle Select - Blender Brush Behavior')

    # layout.separator()

    keymap = addon_keymaps[0]
    keymap_items = keymap.keymap_items

    keymap_row(keymap_items, 'Toggle X-Ray', layout.row(), 'Toggle X-Ray Key')
    keymap_row(keymap_items, 'Toggle Gizmo', layout.row(), 'Toggle Gizmo Key')
    keymap_row(keymap_items, 'Reset Gizmo Rotation',
               layout.row(), 'Reset Gizmo Rotation Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Unhide', layout.row(), 'Unhide Normals Key')
    keymap_row(keymap_items, 'Hide Selected',
               layout.row(), 'Hide Selected Normals Key')
    keymap_row(keymap_items, 'Hide Unselected',
               layout.row(), 'Hide Unselected Normals Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Mirror Normals Start',
               layout.row(), 'Mirror Normals Start Key')
    keymap_row(keymap_items, 'Mirror Normals X',
               layout.row(), 'Mirror Normals X Key')
    keymap_row(keymap_items, 'Mirror Normals Y',
               layout.row(), 'Mirror Normals Y Key')
    keymap_row(keymap_items, 'Mirror Normals Z',
               layout.row(), 'Mirror Normals Z Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Flatten Normals Start',
               layout.row(), 'Flatten Normals Start Key')
    keymap_row(keymap_items, 'Flatten Normals X',
               layout.row(), 'Flatten Normals X Key')
    keymap_row(keymap_items, 'Flatten Normals Y',
               layout.row(), 'Flatten Normals Y Key')
    keymap_row(keymap_items, 'Flatten Normals Z',
               layout.row(), 'Flatten Normals Z Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Align Normals Start',
               layout.row(), 'Align Normals Start Key')
    keymap_row(keymap_items, 'Align Normals Pos X',
               layout.row(), 'Align Normals Pos X Key')
    keymap_row(keymap_items, 'Align Normals Pos Y',
               layout.row(), 'Align Normals Pos Y Key')
    keymap_row(keymap_items, 'Align Normals Pos Z',
               layout.row(), 'Align Normals Pos Z Key')
    keymap_row(keymap_items, 'Align Normals Neg X',
               layout.row(), 'Align Normals Neg X Key')
    keymap_row(keymap_items, 'Align Normals Neg Y',
               layout.row(), 'Align Normals Neg Y Key')
    keymap_row(keymap_items, 'Align Normals Neg Z',
               layout.row(), 'Align Normals Neg Z Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Smooth Normals',
               layout.row(), 'Smooth Normals Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Copy Active Normal',
               layout.row(), 'Copy Active Normal Key')
    keymap_row(keymap_items, 'Paste Stored Normal',
               layout.row(), 'Paste Stored Normal Key')
    keymap_row(keymap_items, 'Paste Active Normal to Selected',
               layout.row(), 'Paste Active Normal to Selected Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Set Normals Outside',
               layout.row(), 'Set Normals Outside Key')
    keymap_row(keymap_items, 'Set Normals Inside',
               layout.row(), 'Set Normals Inside Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Flip Normals', layout.row(), 'Flip Normals Key')
    keymap_row(keymap_items, 'Reset Vectors',
               layout.row(), 'Reset Vectors Key')
    keymap_row(keymap_items, 'Set Normals From Faces',
               layout.row(), 'Set Normals From Faces Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Average Individual Normals',
               layout.row(), 'Average Individual Normals Key')
    keymap_row(keymap_items, 'Average Selected Normals',
               layout.row(), 'Average Selected Normals Key')


def register():
    bpy.utils.register_class(prefs)
    return


def unregister():
    bpy.utils.unregister_class(prefs)
    return
