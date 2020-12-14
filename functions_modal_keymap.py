import bpy


def keymap_initialize(self):
    kt = self._keymap_box
    kt.clear_rows()

    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'ESC - Cancel Normal Editing')
    kt.add_text_row(text_height, 'Tab - End and Confirm Normal Editing')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'R - Rotate Selected Normals')
    kt.add_text_row(text_height, 'R + Alt - Reset Gizmo Axis')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'L-Click - Select Vertex/Gizmo Axis')
    kt.add_text_row(text_height, 'L-Click + Alt - Reorient Gizmo')
    kt.add_text_row(text_height, 'C - Start Circle Selection')
    kt.add_text_row(text_height, 'V - Start Lasso Selection')
    kt.add_text_row(text_height, 'B - Start Box Selection')
    kt.add_text_row(text_height, 'A - Select All')
    kt.add_text_row(text_height, 'A + Alt - Unselect All')
    kt.add_text_row(text_height, 'L - Select Linked Under Mouse')
    kt.add_text_row(text_height, 'L + Ctrl - Select Linked from Selected')
    kt.add_text_row(text_height, 'I + Ctrl - Invert Selection')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'H - Hide Selected Vertices')
    kt.add_text_row(text_height, 'H + Alt - Unhide Vertices')
    kt.add_text_row(text_height, 'Z - Toggle X-Ray')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'Ctrl + Z - Undo')
    kt.add_text_row(text_height, 'Ctrl + Shift + Z - Redo')

    return


#
#


def keymap_refresh(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'ESC - Cancel Normal Editing')
    kt.add_text_row(text_height, 'Tab - End and Confirm Normal Editing')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'R - Rotate Selected Normals')

    if self._use_gizmo:
        kt.add_text_row(text_height, 'R + Alt - Reset Gizmo Axis')
        kt.add_text_row(text_height, 'L-Click - Select Vertex/Gizmo Axis')
        kt.add_text_row(text_height, 'L-Click + Alt - Reorient Gizmo')
        kt.add_text_row(text_height, 'L-Click + Ctrl - Align Gizmo to Surface')
    else:
        kt.add_text_row(text_height, 'L-Click - Select Vertex')

    kt.add_text_row(text_height, 'C - Start Circle Selection')
    kt.add_text_row(text_height, 'V - Start Lasso Selection')
    kt.add_text_row(text_height, 'B - Start Box Selection')
    kt.add_text_row(text_height, 'A - Select All')
    kt.add_text_row(text_height, 'A + Alt - Unselect All')
    kt.add_text_row(text_height, 'L - Select Linked Under Mouse')
    kt.add_text_row(text_height, 'L + Ctrl - Select Linked from Selected')
    kt.add_text_row(text_height, 'I + Ctrl - Invert Selection')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'H - Hide Selected Vertices')
    kt.add_text_row(text_height, 'H + Alt - Unhide Vertices')
    kt.add_text_row(text_height, 'Z - Toggle X-Ray')
    kt.add_text_row(sep_height, '')
    kt.add_text_row(text_height, 'Ctrl + Z - Undo')
    kt.add_text_row(text_height, 'Ctrl + Shift + Z - Redo')

    self._export_panel.create_shape_data()
    return


#
#


def keymap_gizmo(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'Hold Shift - Precise Rotation')
    kt.add_text_row(text_height, 'L-Click - Confirm Rotation')
    kt.add_text_row(text_height, 'R-Click - Cancel Rotation')
    self._export_panel.create_shape_data()
    return


def keymap_target(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'G - Moved Target Center')
    kt.add_text_row(text_height, 'G + Alt - Reset Target Center')
    kt.add_text_row(text_height, 'Z - Toggle X-Ray')
    self._export_panel.create_shape_data()
    return


def keymap_target_move(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'X - Translate on X axis')
    kt.add_text_row(text_height, 'Y - Translate on Y axis')
    kt.add_text_row(text_height, 'Z - Translate on Z axis')
    kt.add_text_row(text_height, 'L-Click - Confirm Move')
    kt.add_text_row(text_height, 'R-Click - Cancel Move')
    self._export_panel.create_shape_data()
    return


def keymap_rotating(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'X - Rotate on X axis')
    kt.add_text_row(text_height, 'Y - Rotate on Y axis')
    kt.add_text_row(text_height, 'Z - Rotate on Z axis')
    kt.add_text_row(text_height, 'Hold Shift - Precise Rotation')
    kt.add_text_row(text_height, 'L-Click - Confirm Rotation')
    kt.add_text_row(text_height, 'R-Click - Cancel Rotation')
    self._export_panel.create_shape_data()
    return


def keymap_box_selecting(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'L-Click - Start New Selection')
    kt.add_text_row(text_height, 'L-Click + Shift Release- Add to Selection')
    kt.add_text_row(
        text_height, 'L-Click + Ctrl Relase - Remove from Selection')
    kt.add_text_row(text_height, 'Hold Alt - Move Box')
    kt.add_text_row(text_height, 'R-Click - Cancel Selection')
    self._export_panel.create_shape_data()
    return


def keymap_circle_selecting(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'L-Click - Add to Selection')
    kt.add_text_row(text_height, 'L-Click + Ctrl - Remove from Selection')
    kt.add_text_row(text_height, 'F - Enter Circle Resize Mode')
    kt.add_text_row(text_height, 'Alt + Scrollwheel - Change Circle Size')
    kt.add_text_row(text_height, '[ - Decrease Circle Size')
    kt.add_text_row(text_height, '] - Increase Circle Size')
    kt.add_text_row(text_height, 'R-Click - Cancel Selection Mode')
    self._export_panel.create_shape_data()
    return


def keymap_lasso_selecting(self):
    kt = self._keymap_box
    kt.clear_rows()
    text_height = 8
    sep_height = 4

    kt.add_text_row(text_height, 'L-Click Release - Start New Selection')
    kt.add_text_row(text_height, 'L-Click + Shift Release - Add to Selection')
    kt.add_text_row(
        text_height, 'L-Click + Ctrl Release - Remove from Selection')
    kt.add_text_row(text_height, 'Hold Alt - Move Lasso')
    kt.add_text_row(text_height, 'R-Click - Cancel Selection Mode')
    self._export_panel.create_shape_data()
    return
