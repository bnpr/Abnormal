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

    keymap_row(keymap_items, 'New Click Selection',
               layout.row(), 'New Click Selection Key')
    keymap_row(keymap_items, 'Add Click Selection',
               layout.row(), 'Add Click Selection Key')
    keymap_row(keymap_items, 'New Loop Selection',
               layout.row(), 'New Loop Selection Key')
    keymap_row(keymap_items, 'Add Loop Selection',
               layout.row(), 'Add Loop Selection Key')
    keymap_row(keymap_items, 'New Shortest Path Selection',
               layout.row(), 'New Shortest Path Selection Key')
    keymap_row(keymap_items, 'Add Shortest Path Selection',
               layout.row(), 'Add Shortest Path Selection Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Invert Selection',
               layout.row(), 'Invert Selection Key')
    keymap_row(keymap_items, 'Select Linked',
               layout.row(), 'Select Linked Key')
    keymap_row(keymap_items, 'Select Hover Linked',
               layout.row(), 'Select Hover Linked Key')
    keymap_row(keymap_items, 'Select All',
               layout.row(), 'Select All Key')
    keymap_row(keymap_items, 'Deselect All',
               layout.row(), 'Deselect All Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Box Select Start',
               layout.row(), 'Box Select Start Key')
    keymap_row(keymap_items, 'Box Select Start Selection',
               layout.row(), 'Box Select Start Selection Key')
    keymap_row(keymap_items, 'Box New Selection',
               layout.row(), 'Box New Selection Key')
    keymap_row(keymap_items, 'Box Add Selection',
               layout.row(), 'Box Add Selection Key')
    keymap_row(keymap_items, 'Box Remove Selection',
               layout.row(), 'Box Remove Selection Key')

    #
    layout.separator()
    #

    keymap_row(keymap_items, 'Circle Select Start',
               layout.row(), 'Circle Select Start Key')
    keymap_row(keymap_items, 'Circle Select Start Selection',
               layout.row(), 'Circle Select Start Selection Key')
    keymap_row(keymap_items, 'Circle End Selection',
               layout.row(), 'Circle End Selection Key')
    keymap_row(keymap_items, 'Circle Add Selection',
               layout.row(), 'Circle Add Selection Key')
    keymap_row(keymap_items, 'Circle Remove Selection',
               layout.row(), 'Circle Remove Selection Key')

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

    keymap_row(keymap_items, 'Lasso Select Start',
               layout.row(), 'Lasso Select Start Key')
    keymap_row(keymap_items, 'Lasso Select Start Selection',
               layout.row(), 'Lasso Select Start Selection Key')
    keymap_row(keymap_items, 'Lasso New Selection',
               layout.row(), 'Lasso New Selection Key')
    keymap_row(keymap_items, 'Lasso Add Selection',
               layout.row(), 'Lasso Add Selection Key')
    keymap_row(keymap_items, 'Lasso Remove Selection',
               layout.row(), 'Lasso Remove Selection Key')


def register():
    bpy.utils.register_class(prefs)
    return


def unregister():
    bpy.utils.unregister_class(prefs)
    return
