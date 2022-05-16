

def keymap_string_find(keymap_items, key_name, name_replace=None):
    scroll_up = ['WHEELINMOUSE', 'WHEELUPMOUSE']
    scroll_down = ['WHEELOUTMOUSE', 'WHEELDOWNMOUSE']

    key_string = ''
    for key in keymap_items:
        if key.name == key_name:
            key_mods = ''
            if key.any == False:
                if key.ctrl:
                    key_mods += 'CTRL+'
                if key.alt:
                    key_mods += 'ALT+'
                if key.shift:
                    key_mods += 'SHIFT+'

            if key.type == 'LEFTMOUSE':
                key_type = 'L-CLICK'
            elif key.type == 'RIGHTMOUSE':
                key_type = 'R-CLICK'
            else:
                key_type = key.type

            if name_replace == None:
                key_string = key_mods + key_type + ' - ' + key.name
            else:
                key_string = key_mods + key_type + ' - ' + name_replace

    return key_string


#
#


def keymap_initialize(modal):
    kt = modal._keymap_box
    kt.clear_rows()

    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Modal', name_replace='Cancel Normal Editing'))
    kt.add_text_row(text_height, keymap_string_find(modal.keymap.keymap_items,
                    'Confirm Modal', name_replace='End and Confirm Normal Editing'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'New Click Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Add Click Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'New Loop Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Add Loop Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'New Shortest Path Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Add Shortest Path Selection'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Select Start'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Box Select Start'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Lasso Select Start'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Select All'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Deselect All'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Select Hover Linked'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Select Linked'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Invert Selection'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Hide Selected'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Hide Unselected'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Unhide'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Toggle X-Ray'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, 'CTRL+Z - Undo')
    kt.add_text_row(text_height, 'CTRL+SHIFT+Z - Redo')

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Rotate Normals'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Toggle Gizmo'))

    if modal._use_gizmo:
        kt.add_text_row(text_height, keymap_string_find(
            modal.keymap.keymap_items, 'Reset Gizmo Rotation'))
        kt.add_text_row(text_height, 'LEFTMOUSE+ALT - Reorient Gizmo')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Mirror Normals Start'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Flatten Normals Start'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Start'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Copy Active Normal'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Paste Stored Normal'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Paste Active Normal to Selected'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Set Normals Outside'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Set Normals Inside'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Flip Normals'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Reset Vectors'))

    kt.add_text_row(sep_height, '')

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Smooth Normals'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Set Normals From Faces'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Average Individual Normals'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Average Selected Normals'))

    return


def keymap_refresh(modal):
    keymap_initialize(modal)
    modal._export_panel.create_shape_data()
    return


#
#


def keymap_gizmo(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, 'HOLD SHIFT - Precise Rotation')
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Confirm Tool 1', name_replace='Confirm Rotation'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Rotation'))
    modal._export_panel.create_shape_data()
    return


def keymap_target(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Target Move Start'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Target Center Reset'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Toggle X-Ray'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 1', name_replace='Cancel'))
    modal._export_panel.create_shape_data()
    return


def keymap_mirror(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Mirror Normals X'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Mirror Normals Y'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Mirror Normals Z'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Mirror'))
    modal._export_panel.create_shape_data()
    return


def keymap_flatten(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Flatten Normals X'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Flatten Normals Y'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Flatten Normals Z'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Flatten'))
    modal._export_panel.create_shape_data()
    return


def keymap_align(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Pos X'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Pos Y'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Pos Z'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Neg X'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Neg Y'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Align Normals Neg Z'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Align'))
    modal._export_panel.create_shape_data()
    return


def keymap_target_move(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Target Move X Axis'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Target Move Y Axis'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Target Move Z Axis'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Confirm Tool 1', name_replace='Confirm Move'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Move'))
    modal._export_panel.create_shape_data()
    return


def keymap_rotating(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Rotate X Axis'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Rotate Y Axis'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Rotate Z Axis'))
    kt.add_text_row(text_height, 'HOLD SHIFT - Precise Rotation')
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Confirm Tool 1', name_replace='Confirm Rotation'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Rotation'))
    modal._export_panel.create_shape_data()
    return


def keymap_box_selecting(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Box New Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Box Add Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Box Remove Selection'))
    kt.add_text_row(text_height, 'HOLD ALT - Move Box')
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Selection'))
    modal._export_panel.create_shape_data()
    return


def keymap_circle_selecting(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Add Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Remove Selection'))

    kt.add_text_row(text_height, ''
                    )
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Resize Mode Start'))

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Increase Size 1'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Increase Size 2'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Decrease Size 1'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Circle Decrease Size 2'))

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Selection'))
    modal._export_panel.create_shape_data()
    return


def keymap_lasso_selecting(modal):
    kt = modal._keymap_box
    kt.clear_rows()
    text_height = 8

    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Lasso New Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Lasso Add Selection'))
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Lasso Remove Selection'))
    kt.add_text_row(text_height, 'HOLD ALT - Move Lasso')
    kt.add_text_row(text_height, keymap_string_find(
        modal.keymap.keymap_items, 'Cancel Tool 2', name_replace='Cancel Selection'))
    modal._export_panel.create_shape_data()
    return
