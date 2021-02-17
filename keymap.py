import bpy


addon_keymaps = []


def register():
    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # BASIC KEYMAP
        km = wm.keyconfigs.addon.keymaps.new(
            name='Abnormal', space_type='EMPTY')

        km.keymap_items.new('Rotate Normals', 'R', 'PRESS')
        km.keymap_items.new('Toggle X-Ray', 'Z', 'PRESS')
        km.keymap_items.new('Hide Unselected', 'H', 'PRESS', alt=True)
        km.keymap_items.new('Hide Selected', 'H', 'PRESS', shift=True)
        km.keymap_items.new('Unhide', 'H', 'PRESS')
        km.keymap_items.new('Reset Gizmo Rotation', 'R', 'PRESS', alt=True)
        km.keymap_items.new('Toggle Gizmo', 'G', 'PRESS')

        km.keymap_items.new('Invert Selection', 'I', 'PRESS')
        km.keymap_items.new('New Click Selection', 'RIGHTMOUSE', 'PRESS')
        km.keymap_items.new('Add Click Selection',
                            'RIGHTMOUSE', 'PRESS', shift=True)
        km.keymap_items.new('New Loop Selection',
                            'RIGHTMOUSE', 'PRESS', alt=True)
        km.keymap_items.new('Add Loop Selection', 'RIGHTMOUSE',
                            'PRESS', alt=True, shift=True)
        km.keymap_items.new('Select Linked', 'L', 'PRESS', ctrl=True)
        km.keymap_items.new('Select Hover Linked', 'L', 'PRESS')
        km.keymap_items.new('Circle Start', 'C', 'PRESS')
        km.keymap_items.new('Box Start', 'B', 'PRESS')
        km.keymap_items.new('Lasso Start', 'V', 'PRESS')
        km.keymap_items.new('Select All', 'A', 'PRESS')
        km.keymap_items.new('Unselect All', 'A', 'PRESS', alt=True)

        km.keymap_items.new('Cancel Modal', 'ESC', 'PRESS')
        km.keymap_items.new('Confirm Modal', 'TAB', 'PRESS')
        addon_keymaps.append(km)

        # TOOLS KEYMAP
        km.keymap_items.new('Box Start Selection',
                            'LEFTMOUSE', 'PRESS', any=True)
        km.keymap_items.new('Box New Selection',
                            'LEFTMOUSE', 'RELEASE', any=True)
        km.keymap_items.new('Box Add Selection',
                            'LEFTMOUSE', 'RELEASE', shift=True)
        km.keymap_items.new('Box Remove Selection',
                            'LEFTMOUSE', 'RELEASE', ctrl=True)

        km.keymap_items.new('Lasso Start Selection',
                            'LEFTMOUSE', 'PRESS', any=True)
        km.keymap_items.new('Lasso New Selection',
                            'LEFTMOUSE', 'RELEASE', any=True)
        km.keymap_items.new('Lasso Add Selection',
                            'LEFTMOUSE', 'RELEASE', shift=True)
        km.keymap_items.new('Lasso Remove Selection',
                            'LEFTMOUSE', 'RELEASE', ctrl=True)

        km.keymap_items.new('Circle Start Selection',
                            'LEFTMOUSE', 'PRESS', any=True)
        km.keymap_items.new('Circle End Selection',
                            'LEFTMOUSE', 'RELEASE', any=True)
        km.keymap_items.new('Circle Add Selection',
                            'LEFTMOUSE', 'PRESS', shift=True)
        km.keymap_items.new('Circle Remove Selection',
                            'LEFTMOUSE', 'PRESS', ctrl=True)

        km.keymap_items.new('Circle Resize Mode Start',
                            'F', 'PRESS')
        km.keymap_items.new('Circle Confirm Resize',
                            'LEFTMOUSE', 'PRESS')

        km.keymap_items.new('Circle Increase Size 1',
                            'WHEELUPMOUSE', 'PRESS', alt=True)
        km.keymap_items.new('Circle Increase Size 2',
                            'RIGHT_BRACKET', 'PRESS')
        km.keymap_items.new('Circle Decrease Size 1',
                            'WHEELDOWNMOUSE', 'PRESS', alt=True)
        km.keymap_items.new('Circle Decrease Size 2',
                            'LEFT_BRACKET', 'PRESS')

        km.keymap_items.new('Cancel Tool 1', 'ESC', 'PRESS')
        km.keymap_items.new('Cancel Tool 2', 'RIGHTMOUSE', 'PRESS')

        addon_keymaps.append(km)


def unregister():
    for km in addon_keymaps:
        for i in range(len(km.keymap_items)):
            km.keymap_items.remove(km.keymap_items[0])
    addon_keymaps.clear()
