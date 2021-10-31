import bpy
from bpy.props import *
from bpy.types import UIList, Panel, Operator
from .properties import *
from .operators_modal import *


class ABN_PT_abnormal_panel(Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BNPR Abnormal'

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        data = bpy.data
        scn_prop = scn.abnormal_props

        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.operator("abnormal.normal_editor_modal")
        row.alignment = 'CENTER'
        row.scale_y = 2

        ob = context.active_object
        if scn_prop.object != '':
            if scn_prop.object in data.objects:
                ob = data.objects[scn_prop.object]

        if ob != None:
            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.prop_search(scn_prop, 'vertex_group', ob,
                            'vertex_groups', text='Filter Vertex Group')
            row.alignment = 'CENTER'

            row = layout.row(align=True)
            row.alignment = 'CENTER'
            row.prop_search(scn_prop, 'vcol', ob.data,
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


def register():
    bpy.utils.register_class(ABN_PT_abnormal_panel)
    return


def unregister():
    bpy.utils.unregister_class(ABN_PT_abnormal_panel)
    return
