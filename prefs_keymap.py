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

    keymap_row(keymap_items, 'Rotate Normals',
               layout.row(), 'Rotate Normals Key')
    keymap_row(keymap_items, 'Toggle X-Ray', layout.row(), 'Toggle X-Ray Key')
    keymap_row(keymap_items, 'Toggle Gizmo', layout.row(), 'Toggle Gizmo Key')
    keymap_row(keymap_items, 'Reset Gizmo Rotation',
               layout.row(), 'Reset Gizmo Rotation Key')
    keymap_row(keymap_items, 'Unhide', layout.row(), 'Unhide Normals Key')
    keymap_row(keymap_items, 'Hide Selected',
               layout.row(), 'Hide Selected Normals Key')
    keymap_row(keymap_items, 'Hide Unselected',
               layout.row(), 'Hide Unselected Normals Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Circle Start',
               layout.row(), 'Circle Select Start Key')
    keymap_row(keymap_items, 'Box Start', layout.row(), 'Box Select Start Key')
    keymap_row(keymap_items, 'Lasso Start',
               layout.row(), 'Lasso Select Start Key')
    keymap_row(keymap_items, 'Invert Selection',
               layout.row(), 'Invert Selection Key')
    keymap_row(keymap_items, 'New Click Selection',
               layout.row(), 'New Click Selection Key')
    keymap_row(keymap_items, 'Add Click Selection',
               layout.row(), 'Add Click Selection Key')
    keymap_row(keymap_items, 'New Loop Selection',
               layout.row(), 'New Loop Selection Key')
    keymap_row(keymap_items, 'Add Loop Selection',
               layout.row(), 'Add Loop Selection Key')
    keymap_row(keymap_items, 'Select Linked',
               layout.row(), 'Select Linked Key')
    keymap_row(keymap_items, 'Select Hover Linked',
               layout.row(), 'Select Hover Linked Key')
    keymap_row(keymap_items, 'Select All', layout.row(), 'Select All Key')
    keymap_row(keymap_items, 'Unselect All', layout.row(), 'Unselect All Key')

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

    keymap_row(keymap_items, 'Smooth Normals',
               layout.row(), 'Smooth Normals Key')

    keymap_row(keymap_items, 'Flatten Normals Start',
               layout.row(), 'Flatten Normals Start Key')
    keymap_row(keymap_items, 'Flatten Normals X',
               layout.row(), 'Flatten Normals X Key')
    keymap_row(keymap_items, 'Flatten Normals Y',
               layout.row(), 'Flatten Normals Y Key')
    keymap_row(keymap_items, 'Flatten Normals Z',
               layout.row(), 'Flatten Normals Z Key')

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

    keymap_row(keymap_items, 'Copy Active Normal',
               layout.row(), 'Copy Active Normal Key')
    keymap_row(keymap_items, 'Paste Stored Normal',
               layout.row(), 'Paste Stored Normal Key')
    keymap_row(keymap_items, 'Paste Active Normal to Selected',
               layout.row(), 'Paste Active Normal to Selected Key')

    keymap_row(keymap_items, 'Set Normals Outside',
               layout.row(), 'Set Normals Outside Key')
    keymap_row(keymap_items, 'Set Normals Inside',
               layout.row(), 'Set Normals Inside Key')

    keymap_row(keymap_items, 'Flip Normals', layout.row(), 'Flip Normals Key')
    keymap_row(keymap_items, 'Reset Vectors',
               layout.row(), 'Reset Vectors Key')

    keymap_row(keymap_items, 'Average Individual Normals',
               layout.row(), 'Average Individual Normals Key')
    keymap_row(keymap_items, 'Average Selected Normals',
               layout.row(), 'Average Selected Normals Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Cancel Modal', layout.row(), 'Cancel Modal Key')
    keymap_row(keymap_items, 'Confirm Modal',
               layout.row(), 'Confirm Modal Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Cancel Tool 1',
               layout.row(), 'Cancel Tool Key 1')
    keymap_row(keymap_items, 'Cancel Tool 2',
               layout.row(), 'Cancel Tool Key 2')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Box Start Selection',
               layout.row(), 'Box Start Selection Key')
    keymap_row(keymap_items, 'Box New Selection',
               layout.row(), 'Box New Selection Key')
    keymap_row(keymap_items, 'Box Add Selection',
               layout.row(), 'Box Add Selection Key')
    keymap_row(keymap_items, 'Box Remove Selection',
               layout.row(), 'Box Remove Selection Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Circle Start Selection',
               layout.row(), 'Circle Start Selection Key')
    keymap_row(keymap_items, 'Circle End Selection',
               layout.row(), 'Circle End Selection Key')
    keymap_row(keymap_items, 'Circle Add Selection',
               layout.row(), 'Circle Add Selection Key')
    keymap_row(keymap_items, 'Circle Remove Selection',
               layout.row(), 'Circle Remove Selection Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Circle Resize Mode Start',
               layout.row(), 'Circle Resize Mode Start Key')
    keymap_row(keymap_items, 'Circle Resize Confirm',
               layout.row(), 'Circle Resize Confirm Key')

    keymap_row(keymap_items, 'Circle Increase Size 1',
               layout.row(), 'Circle Increase Size Key 1')
    keymap_row(keymap_items, 'Circle Increase Size 2',
               layout.row(), 'Circle Increase Size Key 2')
    keymap_row(keymap_items, 'Circle Decrease Size 1',
               layout.row(), 'Circle Decrease Size Key 1')
    keymap_row(keymap_items, 'Circle Decrease Size 2',
               layout.row(), 'Circle Decrease Size Key 2')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Lasso Start Selection',
               layout.row(), 'Lasso Start Selection Key')
    keymap_row(keymap_items, 'Lasso New Selection',
               layout.row(), 'Lasso New Selection Key')
    keymap_row(keymap_items, 'Lasso Add Selection',
               layout.row(), 'Lasso Add Selection Key')
    keymap_row(keymap_items, 'Lasso Remove Selection',
               layout.row(), 'Lasso Remove Selection Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Rotate X Axis',
               layout.row(), 'Rotate X Axis Key')
    keymap_row(keymap_items, 'Rotate Y Axis',
               layout.row(), 'Rotate Y Axis Key')
    keymap_row(keymap_items, 'Rotate Z Axis',
               layout.row(), 'Rotate Z Axis Key')


def register():
    bpy.utils.register_class(prefs)
    return


def unregister():
    bpy.utils.unregister_class(prefs)
    return
