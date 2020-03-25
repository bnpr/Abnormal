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
        objs = data.objects
        aobj = context.active_object
        scn_prop = scn.abnormal_props
        
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.operator("abnormal.normal_editor_modal")
        row.alignment = 'CENTER'
        row.scale_y = 2