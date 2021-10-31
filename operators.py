import bpy
from bpy.props import *
from bpy.types import Operator
import numpy as np


class ABN_OT_store_norms_in_vcol(Operator):
    bl_idname = "abnormal.store_norms_in_vcol"
    bl_label = "Store Current Normals in Vertex Colors"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        scn = context.scene
        aobj = context.active_object
        abn_props = context.scene.abnormal_props

        if abn_props.vcol is not None and abn_props.vcol in aobj.data.vertex_colors:
            aobj.data.calc_normals_split()

            loop_amnt = len(aobj.data.loops)

            norms = np.zeros(loop_amnt*3, dtype=np.float32)

            aobj.data.loops.foreach_get(
                'normal', norms)

            norms.shape = [loop_amnt, 3]

            alphas = np.ones(loop_amnt, dtype=np.float32).reshape(-1, 1)
            norms = np.hstack((norms, alphas))

            aobj.data.vertex_colors[abn_props.vcol].data.foreach_set(
                'color', norms.ravel())

        return {'FINISHED'}


class ABN_OT_convert_vcol_to_norms(Operator):
    bl_idname = "abnormal.convert_vcol_to_norms"
    bl_label = "Convert Vertex Colors to Normals"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context):
        scn = context.scene
        aobj = context.active_object
        abn_props = context.scene.abnormal_props

        if abn_props.vcol is not None and abn_props.vcol in aobj.data.vertex_colors:
            aobj.data.calc_normals_split()

            loop_amnt = len(aobj.data.loops)

            cols = np.zeros(loop_amnt*4, dtype=np.float32)

            aobj.data.vertex_colors[abn_props.vcol].data.foreach_get(
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
