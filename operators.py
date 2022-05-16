import bpy
from bpy.props import *
from bpy.types import Operator
import numpy as np


class ABN_OT_store_norms_in_vcol(Operator):
    bl_idname = "abnormal.store_norms_in_vcol"
    bl_label = "Normals  --->  Vertex Colors"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_description = 'Convert current custom normals to the selected Vertex Colors'

    def execute(self, context):
        scn = context.scene
        aobj = context.active_object

        addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
            0]].preferences

        if addon_prefs.vcol is not None and addon_prefs.vcol in aobj.data.vertex_colors:
            aobj.data.calc_normals_split()

            loop_amnt = len(aobj.data.loops)

            norms = np.zeros(loop_amnt*3, dtype=np.float32)

            aobj.data.loops.foreach_get(
                'normal', norms)

            norms.shape = [loop_amnt, 3]

            alphas = np.ones(loop_amnt, dtype=np.float32).reshape(-1, 1)
            norms = np.hstack((norms, alphas))

            aobj.data.vertex_colors[addon_prefs.vcol].data.foreach_set(
                'color', norms.ravel())

        return {'FINISHED'}


class ABN_OT_convert_vcol_to_norms(Operator):
    bl_idname = "abnormal.convert_vcol_to_norms"
    bl_label = "Vertex Colors  --->  Normals"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_description = 'Convert selected Vertex Colors to custom normals'

    def execute(self, context):
        scn = context.scene
        aobj = context.active_object

        addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
            0]].preferences

        if addon_prefs.vcol is not None and addon_prefs.vcol in aobj.data.vertex_colors:
            aobj.data.calc_normals_split()

            loop_amnt = len(aobj.data.loops)

            cols = np.zeros(loop_amnt*4, dtype=np.float32)

            aobj.data.vertex_colors[addon_prefs.vcol].data.foreach_get(
                'color', cols)

            cols.shape = [loop_amnt, 4]

            cols = cols[:, [0, 1, 2]]

            aobj.data.normals_split_custom_set(cols)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(ABN_OT_store_norms_in_vcol)
    bpy.utils.register_class(ABN_OT_convert_vcol_to_norms)
    return


def unregister():
    bpy.utils.unregister_class(ABN_OT_store_norms_in_vcol)
    bpy.utils.unregister_class(ABN_OT_convert_vcol_to_norms)
    return
