import bpy
from bpy.props import *
from bpy.types import Panel
from .operators_modal import *
from bpy.app.handlers import persistent


@persistent
def load_handler(dummy):
    addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
        0]].preferences

    addon_prefs.use_n_panel = addon_prefs.use_n_panel

    return


def update_panel(self, context):

    addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
        0]].preferences

    if addon_prefs.use_n_panel:
        ABN_PT_abnormal_panel.bl_category = 'BNPR Abnormal'
        ABN_PT_abnormal_panel.bl_region_type = 'UI'
        ABN_PT_abnormal_panel.menu_remove()

    else:
        ABN_PT_abnormal_panel.bl_category = ''
        ABN_PT_abnormal_panel.bl_region_type = 'HEADER'
        ABN_PT_abnormal_panel.menu_add()

    try:
        bpy.utils.unregister_class(ABN_PT_abnormal_panel)
    except:
        pass

    bpy.utils.register_class(ABN_PT_abnormal_panel)

    return


class ABN_OT_switch_panel_loc(Operator):
    bl_idname = "abnormal.switch_panel_loc"
    bl_label = ""
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_description = 'Switch location of Abnormal panel'

    val: BoolProperty(default=True)

    def execute(self, context):

        addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
            0]].preferences

        addon_prefs.use_n_panel = self.val

        return {'FINISHED'}


class ABN_PT_abnormal_panel(Panel):
    """Creates a Panel in the scene context of the properties editor"""
    # bl_label = "Tools"
    bl_label = "BNPR Abnormal"
    bl_space_type = 'VIEW_3D'
    # bl_region_type = 'UI'
    bl_region_type = 'HEADER'
    # bl_category = 'BNPR Abnormal'

    def draw(self, context):
        layout = self.layout
        data = bpy.data

        addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
            0]].preferences

        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.operator("abnormal.normal_editor_modal")
        row.alignment = 'CENTER'
        row.scale_y = 2

        ob = context.active_object
        if addon_prefs.object != '':
            if addon_prefs.object in data.objects:
                ob = data.objects[addon_prefs.object]

        if ob != None:
            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.prop_search(addon_prefs, 'vertex_group', ob,
                            'vertex_groups', text='Filter Vertex Group')
            row.alignment = 'CENTER'

            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.prop_search(addon_prefs, 'vcol', ob.data,
                            'vertex_colors', text='Vertex Color')
            row.alignment = 'CENTER'

        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.operator("abnormal.convert_vcol_to_norms")
        row.alignment = 'CENTER'
        row.scale_y = 2

        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.operator("abnormal.store_norms_in_vcol")
        row.alignment = 'CENTER'
        row.scale_y = 2

        row = layout.row(align=True)
        row.alignment = 'CENTER'

        if addon_prefs.use_n_panel:
            row.operator("abnormal.switch_panel_loc",
                         text='Move to Header Tab').val = False
        else:
            row.operator("abnormal.switch_panel_loc",
                         text='Move to N Panel Tab').val = True

        row.alignment = 'CENTER'
        row.scale_y = 1.5

    #############################################################################
    # the following two methods add/remove RF to/from the main 3D View menu
    # NOTE: this is a total hack: hijacked the draw function!
    @staticmethod
    def menu_add():
        # for more icon options, see:
        #     https://docs.blender.org/api/current/bpy.types.UILayout.html#bpy.types.UILayout.operator
        ABN_PT_abnormal_panel.menu_remove()
        ABN_PT_abnormal_panel._menu_original = bpy.types.VIEW3D_MT_editor_menus.draw_collapsible

        def hijacked(context, layout):
            obj = context.active_object
            # mode_string = context.mode
            # edit_object = context.edit_object
            # gp_edit = obj and obj.mode in {'EDIT_GPENCIL', 'PAINT_GPENCIL', 'SCULPT_GPENCIL', 'WEIGHT_GPENCIL'}

            ABN_PT_abnormal_panel._menu_original(context, layout)

            # if context.mode in {'EDIT_MESH', 'OBJECT'}:
            if context.mode in 'OBJECT':
                row = layout.row(align=True)
                # row.menu("ABN_PT_abnormal_panel", text="BNPR Abnormal")
                row.popover(panel="ABN_PT_abnormal_panel",
                            text=ABN_PT_abnormal_panel.bl_label)

        bpy.types.VIEW3D_MT_editor_menus.draw_collapsible = hijacked

    @staticmethod
    def menu_remove():
        if not hasattr(ABN_PT_abnormal_panel, '_menu_original'):
            return
        bpy.types.VIEW3D_MT_editor_menus.draw_collapsible = ABN_PT_abnormal_panel._menu_original
        del ABN_PT_abnormal_panel._menu_original


def register():
    bpy.utils.register_class(ABN_OT_switch_panel_loc)
    ABN_PT_abnormal_panel.bl_category = 'BNPR Abnormal'
    ABN_PT_abnormal_panel.bl_region_type = 'UI'
    ABN_PT_abnormal_panel.menu_remove()
    bpy.utils.register_class(ABN_PT_abnormal_panel)
    bpy.app.handlers.load_post.append(load_handler)
    return


def unregister():
    bpy.utils.unregister_class(ABN_OT_switch_panel_loc)
    ABN_PT_abnormal_panel.menu_remove()
    bpy.utils.unregister_class(ABN_PT_abnormal_panel)
    bpy.app.handlers.load_post.remove(load_handler)
    return
