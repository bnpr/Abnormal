from mathutils import Vector
import math


def draw_cos_offset(position, scale, cos):
    co_list = []
    for co in cos:
        co_list.append([position[0]+(co[0]*scale), position[1]+(co[1]*scale)])

    return co_list


#


def calc_box(x, y, width, height, bev_inds, bev_width, bev_res):
    v1 = [x, y]
    v2 = [x+width, y]
    v3 = [x+width, y-height]
    v4 = [x, y-height]

    points = [v1, v2, v3, v4]
    tris = [[0, 1, 2], [0, 2, 3]]

    if bev_width > 0.0:
        points, tris = bevel_ui(points, bev_inds, 0, bev_width, bev_res)

    lines = []
    for p, po in enumerate(points):
        lines.append(points[p])

        if p < len(points)-1:
            lines.append(points[p+1])
        else:
            lines.append(points[0])

    return points, tris, lines


def bevel_ui(pos, bevel_inds, ind_offset, fac, res):
    cos = []
    for po in pos:
        cos.append(Vector((po[0], po[1])))

    bev_cos = []
    inds = []

    fac = round_up_num(fac)

    non_bev_face = []
    bev_faces = []
    bev_seg_inds = []
    bev_ind = 0
    for c, co in enumerate(cos):
        # if point is to be beveled then do it and create the triangles
        if c in bevel_inds or bevel_inds == []:
            next_ind = c+1
            if c+1 >= len(cos):
                next_ind = 0

            tri_bv = cos[c]
            triv1 = cos[next_ind]
            triv2 = cos[c-1]

            vec1 = triv1-tri_bv
            vec2 = triv2-tri_bv

            if vec1.length == 0.0 or vec2.length == 0.0:
                continue

            if vec1.length/2 < fac or vec2.length/2 < fac:
                if vec1.length < vec2.length:
                    fac = int(vec1.length/2)-2
                else:
                    fac = int(vec2.length/2)-2

            ang_check = vec1.angle_signed(vec2)
            if ang_check < 0.0:
                triv1 = cos[c-1]
                triv2 = cos[next_ind]

                vec1 = triv1-tri_bv
                vec2 = triv2-tri_bv

            vec1_norm = vec1.normalized()
            vec2_norm = vec2.normalized()
            vec1_rev = vec1_norm * -1
            vec2_rev = vec2_norm * -1

            cross_vec = Vector((-vec2_norm[1], vec2_norm[0]))

            halfang = math.acos(vec1_rev.dot(vec2_rev))/2
            # TOA tan of corner angle = opposite/adjancent   we don't know opposite len which is the radius
            # so tan of corner angle * adjacent = opposite   fac is our adjacent length
            radius = math.tan(halfang) * fac

            other_ang = 90 - math.degrees(halfang)

            po1 = tri_bv+vec1_norm*fac
            po2 = tri_bv+vec2_norm*fac
            origin = po2 + cross_vec * radius

            bev_seg_inds = []

            bev_cos.append([po2[0], po2[1]])
            non_bev_face.append(bev_ind)
            bev_seg_inds.append(bev_ind)
            bev_ind += 1

            interval = other_ang*2/(res+1)
            for i in range(res):
                new_co = rotate_2d(origin, po2, math.radians(-interval*(i+1)))
                bev_cos.append([new_co[0], new_co[1]])

                bev_seg_inds.append(bev_ind)
                bev_ind += 1

                if len(bev_seg_inds) >= 3:
                    check_tri(bev_cos, bev_seg_inds, inds)

            bev_cos.append([po1[0], po1[1]])
            non_bev_face.append(bev_ind)
            bev_seg_inds.append(bev_ind)
            bev_faces.append(bev_seg_inds)
            bev_ind += 1

        else:
            bev_cos.append([co[0], co[1]])
            non_bev_face.append(bev_ind)
            bev_ind += 1

        while len(non_bev_face) >= 3:
            check_tri(bev_cos, non_bev_face, inds)
        while len(bev_seg_inds) >= 3:
            check_tri(bev_cos, bev_seg_inds, inds)

    while len(non_bev_face) >= 3:
        check_tri(bev_cos, non_bev_face, inds)
    while len(bev_seg_inds) >= 3:
        check_tri(bev_cos, bev_seg_inds, inds)

    return bev_cos, inds


def rotate_2d(origin, point, angle):
    x = origin[0] + math.cos(angle) * (point[0] - origin[0]) - \
        math.sin(angle) * (point[1] - origin[1])
    y = origin[1] + math.sin(angle) * (point[0] - origin[0]) + \
        math.cos(angle) * (point[1] - origin[1])

    vec = Vector((x, y))
    return vec


def check_tri(cos, f_inds, inds):
    inds.append([f_inds[0], f_inds[1], f_inds[2]])

    f_inds.pop(1)
    return


#


def round_array(arr):
    new_arr = []
    for num in arr:
        new_arr.append(round(num))

    return new_arr


def round_up_num(num):
    if num % 1 > 0.0:
        return int(num+1)
    else:
        return int(num)


#


def hsv_to_rgb(h, s, v, a=1.0):
    if s == 0.0:
        return (v, v, v, a)
    i = int(h*6.)  # XXX assume int() truncates!
    f = (h*6.)-i
    p, q, t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f))
    i %= 6
    if i == 0:
        return (v, t, p, a)
    if i == 1:
        return (q, v, p, a)
    if i == 2:
        return (p, v, t, a)
    if i == 3:
        return (p, q, v, a)
    if i == 4:
        return (t, p, v, a)
    if i == 5:
        return (v, p, q, a)


def hsv_to_rgb_list(hsv):
    if len(hsv) > 3:
        rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2], hsv[3])
    else:
        rgb = hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    return rgb
