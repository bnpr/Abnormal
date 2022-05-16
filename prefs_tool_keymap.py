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
    keymap_row(keymap_items, 'Rotate X Axis',
               layout.row(), 'Rotate X Axis Key')
    keymap_row(keymap_items, 'Rotate Y Axis',
               layout.row(), 'Rotate Y Axis Key')
    keymap_row(keymap_items, 'Rotate Z Axis',
               layout.row(), 'Rotate Z Axis Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Target Move Start',
               layout.row(), 'Target Move Start Key')
    keymap_row(keymap_items, 'Target Center Reset',
               layout.row(), 'Target Center Reset Key')
    keymap_row(keymap_items, 'Target Move X Axis',
               layout.row(), 'Target Move X Axis Key')
    keymap_row(keymap_items, 'Target Move Y Axis',
               layout.row(), 'Target Move Y Axis Key')
    keymap_row(keymap_items, 'Target Move Z Axis',
               layout.row(), 'Target Move Z Axis Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Filter Mask From Selected',
               layout.row(), 'Create Filter Mask From Selected Key')
    keymap_row(keymap_items, 'Clear Filter Mask',
               layout.row(), 'Clear Filter Mask Key')

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


def register():
    bpy.utils.register_class(prefs)
    return


def unregister():
    bpy.utils.unregister_class(prefs)
    return
