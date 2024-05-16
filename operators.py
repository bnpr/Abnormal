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
            if bpy.app.version[0] <= 4 and bpy.app.version[1] < 1:
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
            if bpy.app.version[0] <= 4 and bpy.app.version[1] < 1:
                aobj.data.calc_normals_split()

            loop_amnt = len(aobj.data.loops)

            cols = np.zeros(loop_amnt*4, dtype=np.float32)

            aobj.data.vertex_colors[addon_prefs.vcol].data.foreach_get(
                'color', cols)

            cols.shape = [loop_amnt, 4]

            cols = cols[:, [0, 1, 2]]

            aobj.data.normals_split_custom_set(cols)

        return {'FINISHED'}


class ABN_OT_store_norms_in_attr(Operator):
    bl_idname = "abnormal.store_norms_in_attr"
    bl_label = "Normals  --->  Face Corner Attribute"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_description = 'Convert current custom normals to the selected Vertex Colors'

    def execute(self, context):
        scn = context.scene
        aobj = context.active_object

        addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
            0]].preferences

        if addon_prefs.attribute is None or addon_prefs.attribute not in aobj.data.attributes:
            self.report({"ERROR"}, "Set attribute does not exist!")
            return {"CANCELLED"}
        if aobj.data.attributes[addon_prefs.attribute].domain != 'CORNER':
            self.report({"ERROR"}, "Set attribute is not a face corner domain!")
            return {"CANCELLED"}
        if aobj.data.attributes[addon_prefs.attribute].data_type != 'FLOAT_VECTOR':
            self.report({"ERROR"}, "Set attribute is not a vector type!")
            return {"CANCELLED"}

        if bpy.app.version[0] <= 4 and bpy.app.version[1] < 1:
            aobj.data.calc_normals_split()

        loop_amnt = len(aobj.data.loops)

        norms = np.zeros(loop_amnt*3, dtype=np.float32)

        aobj.data.loops.foreach_get(
            'normal', norms)

        norms.shape = [loop_amnt, 3]

        aobj.data.attributes[addon_prefs.attribute].data.foreach_set(
            'vector', norms.ravel())

        return {'FINISHED'}


class ABN_OT_convert_attr_to_norms(Operator):
    bl_idname = "abnormal.convert_attr_to_norms"
    bl_label = "Face Corner Attribute  --->  Normals"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}
    bl_description = 'Convert selected Vertex Colors to custom normals'

    def execute(self, context):
        scn = context.scene
        aobj = context.active_object

        addon_prefs = bpy.context.preferences.addons[__package__.split('.')[
            0]].preferences

        if addon_prefs.attribute is None or addon_prefs.attribute not in aobj.data.attributes:
            self.report({"ERROR"}, "Set attribute does not exist!")
            return {"CANCELLED"}
        if aobj.data.attributes[addon_prefs.attribute].domain != 'CORNER':
            self.report({"ERROR"}, "Set attribute is not a face corner domain!")
            return {"CANCELLED"}
        if aobj.data.attributes[addon_prefs.attribute].data_type != 'FLOAT_VECTOR':
            self.report({"ERROR"}, "Set attribute is not a vector type!")
            return {"CANCELLED"}

        if bpy.app.version[0] <= 4 and bpy.app.version[1] < 1:
            aobj.data.calc_normals_split()

        # loop_amnt = len(aobj.data.loops)

        # norms = np.zeros(loop_amnt*3, dtype=np.float32)

        # aobj.data.attributes[addon_prefs.attribute].data.foreach_get(
        #     'vector', norms)
        
        norms = []
        for vec in aobj.data.attributes[addon_prefs.attribute].data:
            norms.append(vec.vector)

        aobj.data.normals_split_custom_set(norms)

        return {'FINISHED'}


def register():
    bpy.utils.register_class(ABN_OT_store_norms_in_vcol)
    bpy.utils.register_class(ABN_OT_convert_vcol_to_norms)
    bpy.utils.register_class(ABN_OT_store_norms_in_attr)
    bpy.utils.register_class(ABN_OT_convert_attr_to_norms)
    return


def unregister():
    bpy.utils.unregister_class(ABN_OT_store_norms_in_vcol)
    bpy.utils.unregister_class(ABN_OT_convert_vcol_to_norms)
    bpy.utils.unregister_class(ABN_OT_store_norms_in_attr)
    bpy.utils.unregister_class(ABN_OT_convert_attr_to_norms)
    return
