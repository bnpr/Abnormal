import bpy
import bmesh
import math
import mathutils
import bpy_extras
import time
from bpy_extras import view3d_utils
from mathutils.bvhtree import BVHTree

gen_mods = ['ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE', 
            'EDGE_SPLIT', 'MASK', 'MIRROR', 'MULTIRES', 'REMESH',
            'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE', 'WIREFRAME'
            ]




def rotate_2d(origin, point, angle):
    x = origin[0] + math.cos(angle) * (point[0] - origin[0]) - math.sin(angle) * (point[1] - origin[1])
    y = origin[1] + math.sin(angle) * (point[0] - origin[0]) + math.cos(angle) * (point[1] - origin[1])
    
    vec = mathutils.Vector((x, y))
    return vec


def refresh_bm(bm):
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return


def create_kd(bm):
    size = len(bm.verts)
    kd = mathutils.kdtree.KDTree(size)
    
    for i, v in enumerate(bm.verts):
        kd.insert(v.co, i)
    
    kd.balance()
    
    return kd




def ob_to_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    refresh_bm(bm)
    
    bm.normal_update()
    
    return bm


def ob_to_bm_world(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    refresh_bm(bm)
    
    
    #bm in world space
    for v in bm.verts:
        v.co = ob.matrix_world @ v.co
    
    bm.normal_update()
    
    return bm


def create_simple_bm(self, ob):

    #turn off generative modifiers
    for mod in ob.modifiers:
        self._objects_mod_status.append([mod.show_viewport, mod.show_render])

        if mod.type != 'MIRROR':
            mod.show_viewport = False
            mod.show_render = False
    
    
    
    #worldspace object data in bmesh
    bm = ob_to_bm_world(ob)
    
    
    
    fac = 1
    if ob.scale[0] < .0:
        fac = -1
    if ob.scale[1] < .0:
        fac = -1
    if ob.scale[2] < .0:
        fac = -1
    
    if fac == -1:
        all_faces = [f for f in bm.faces]
        bmesh.ops.reverse_faces(bm, faces=all_faces)
    
    
    refresh_bm(bm)
    
    return bm




def force_scene_update():
    bpy.context.scene.cursor.location = bpy.context.scene.cursor.location
    return


def generate_matrix(v1,v2,v3, cross, normalized):
    a = (v2-v1)
    b = (v3-v1)
    
    if normalized:
        a = a.normalized()
        b = b.normalized()
        
    c = a.cross(b).normalized()
    
    if cross:
        b2 = c.cross(a)
    
        m = mathutils.Matrix([-c, b2, a]).transposed()
    else:
        m = mathutils.Matrix([-c, b, a]).transposed()
    matrix = mathutils.Matrix.Translation(v1) @ m.to_4x4()
    #matrix.translation = v1
    
    return matrix


def ray_cast_view_occlude_test(co, mouse_co, bvh):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    
    orig_co = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_co)
    direction_to = (orig_co - co).normalized()
    
    
    occluded = False
    hit_to_view, norm_to_view, ind_to_view, dist_to_view = bvh.ray_cast(co+direction_to*.001, direction_to, 1000000)
    
    if hit_to_view != None:
        occluded = True
    
    return occluded


def ray_cast_to_mouse(self, context):
    # get the context arguments
    scn = context.scene
    region = context.region
    rv3d = context.region_data
    
    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, self._mouse_loc)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, self._mouse_loc)
    
    hit, norm, ind, dist = self._object_bvh.ray_cast(ray_origin, view_vector, 10000)
    
    return ind




def get_outer_v(axis, min, cos, unavail=[]):
    val = 0
    ind = None
    
    for c, co in enumerate(cos):
        if c not in unavail:
            if min:
                if ind == None or co[axis] < val:
                    ind = c
                    val = co[axis]
            else:
                if ind == None or co[axis] > val:
                    ind = c
                    val = co[axis]
    
    return ind, val

def bounding_box_filter(shape_cos, cos):
    #GET BOUNDING BOX TO FILTER LASSO TESTING POINTS
    min_x_ind, min_x = get_outer_v(0, True, shape_cos)
    max_x_ind, max_x = get_outer_v(0, False, shape_cos)
    min_y_ind, min_y = get_outer_v(1, True, shape_cos)
    max_y_ind, max_y = get_outer_v(1, False, shape_cos)

    in_range_cos = [c for c, co in enumerate(cos) if min_x < co[0] < max_x and min_y < co[1] < max_y]

    return in_range_cos

def test_point_in_shape(shape_cos, test_co):
    tot_rot = 0

    l_vec = mathutils.Vector((shape_cos[0][0], shape_cos[0][1])) - test_co
    prev_vec = l_vec.copy()
    for lv in shape_cos:
        s_co = mathutils.Vector((lv[0], lv[1]))

        c_vec = s_co - test_co
        
        ang = math.degrees(prev_vec.xy.angle_signed(c_vec.xy))
        
        tot_rot += ang
        prev_vec = c_vec.copy()
    
    ang = math.degrees(prev_vec.xy.angle_signed(l_vec.xy))
    
    tot_rot += ang
    if abs(tot_rot) > 180:
        return True
    else:
        return False



def vec_to_dashed(co, vec, segments):
    cos = []
    length_vec = vec / ((segments*2)+1)
    
    for i in range(segments+1):
        
        cos.append(co+(length_vec*i*2))
        cos.append(co+(length_vec*((i*2)+1)))
    
    return cos

    new_cos = coords.copy()
    
    first_ind = None
    #smooth geo
    for x in range(iter):
        co_changes = []
        for c, co in enumerate(new_cos):
            if c in inds:
                
            #    if cyclic == False:
            #        if c == 0 or c == len(new_cos)-1:
            #            co_changes.append(co)
            #            continue
                
                test_cos = []
                if c > 0 or cyclic:
                    prev_co = new_cos[c-1]
                    test_cos.append(prev_co)
                if c < len(new_cos)-1:
                    next_co = new_cos[c+1]
                    test_cos.append(next_co)
                if cyclic and c == len(new_cos)-1:
                    next_co = new_cos[0]
                    test_cos.append(next_co)
                
                
                nco = mathutils.Vector((0,0,0))
                for l_co in test_cos:
                    vec = l_co - co
                    
                    nco += co + vec*fac
                
                nco /= len(test_cos)
                
                co_changes.append(nco)
                
            else:
                co_changes.append(co)
        
        for c, co_change in enumerate(co_changes):
            new_cos[c] = co_change
        
    
    return new_cos





def get_linked_geo(bm, inds):

    v_list = []
    for ind in inds:
        still_going = True
        if ind not in v_list:
            verts = [ind]
            v_list.append(ind)

            while still_going:
                found = False
                
                next_verts = []
                for v_ind in verts:
                    vert = bm.verts[v_ind]
                    
                    link_eds = [ed for ed in vert.link_edges]
                    
                    for ed in link_eds:
                        ov = ed.other_vert(vert)
                        if ov.index not in v_list:
                            next_verts.append(ov.index)
                            v_list.append(ov.index)
                            found = True
                
                
                verts = next_verts.copy()
                still_going = found
    return v_list


