import numpy as np
import os
import blf
import bpy


def scale_font_size(text, font_size, font_id, scale):
    if bpy.app.version[0] >= 4:
        blf.size(font_id, font_size)
    else:
        blf.size(font_id, font_size, 72)
    blf.position(font_id, 0, 0, 0)
    size_w = blf.dimensions(font_id, text)

    # Get the width of the text at the set font size scaled down as a target
    targ_width = size_w[0] * scale
    cur_size = font_size
    # If the target width is too large and the scale is not 1.0 then
    # we need to search for what font size is closest to the target size since
    # font size does not scale correctly
    if targ_width > 0.0 and scale != 1.0:
        cur_width = 0
        cur_size = 0
        # Starting from 0 keep increasing the font size until
        # A size is found that is just over the target width of the scaled size
        while cur_width <= targ_width:
            cur_size += 1
            if bpy.app.version[0] >= 4:
                blf.size(font_id, cur_size)
            else:
                blf.size(font_id, cur_size, 72)
            cur_width, cur_height = blf.dimensions(
                font_id, text)

        # When the font size that is just larger is found set the current font size to 1 below that
        cur_size -= 1
        if bpy.app.version[0] >= 4:
            blf.size(font_id, cur_size)
        else:
            blf.size(font_id, cur_size, 72)
        size_w = blf.dimensions(font_id, text)

    return cur_size

#


def calc_box(x, y, width, height, bev_inds, bev_width, bev_res):
    #
    # Create a rectangular beveled box from the given position and shape data
    #
    points = np.array([[x, y],
                       [x+width, y],
                       [x+width, y-height],
                       [x, y-height]],
                      dtype=np.float32)

    if bev_width > 0.0 and bev_res > 1:
        points = bevel_ui(points, bev_inds, 0, bev_width, bev_res)

    lines = np.roll(points, -1, axis=0) - points

    return points, lines


#


def get_vec_lengths(array):
    lengths = np.sqrt(np.sum(np.square(array), axis=1))
    return lengths


def get_prev_next_path_inds(array, inds, cyclic):
    #
    # Get the indices of the points next and previous point on the path
    #
    prev_inds = inds-1
    next_inds = np.mod(inds+1, array.shape[0])
    if cyclic == False:
        if np.isin(0, inds):
            prev_inds[0] = 1
        if np.isin(array.shape[0]-1, inds):
            next_inds[-1] = array.shape[0]-2

    return prev_inds, next_inds


def get_prev_next_inds(array, inds):
    prev_inds = np.mod(inds-1, array.shape[0])
    next_inds = np.mod(inds+1, array.shape[0])
    return prev_inds, next_inds


def get_prev_next_path_vecs(cos, inds, prev_inds, next_inds, cyclic, handle_vecs=False, normalize=False):
    #
    # Get vectors for each point to next and previous points
    #
    next_vecs = cos[next_inds] - cos[inds]
    prev_vecs = cos[inds] - cos[prev_inds]

    if normalize:
        next_vecs = get_normalized_vecs(next_vecs)
        prev_vecs = get_normalized_vecs(prev_vecs)

    if cyclic == False:
        if np.isin(0, inds):
            prev_vecs[0] = next_vecs[0]
        if np.isin(cos.shape[0]-1, inds):
            next_vecs[-1] = prev_vecs[-1]

    if handle_vecs:
        prev_vecs *= -1

    return prev_vecs, next_vecs


def get_normalized_vecs(array):
    scale = get_vec_lengths(array)

    scale[scale == 0.0] = 1.0

    norm_array = array / scale[:, np.newaxis]

    return norm_array


def get_vec_angles(vecs_a, vecs_b):
    dots = get_normalized_vecs(vecs_a) * get_normalized_vecs(vecs_b)

    angs = np.arccos(np.clip(np.sum(dots, axis=1), -1.0, 1.0))

    return angs


def get_vec_angles_signed(vecs_a, vecs_b, switch=False, full_range=False):
    #
    # Get the signed angles between 2 sets of vectors
    # Only uses the X and Y coords to get the angle
    # Z axis should be 0.0
    #
    angs = get_vec_angles(vecs_a, vecs_b)

    vecs_a_3d = vecs_a[:, [0, 1, 0]]
    vecs_b_3d = vecs_b[:, [0, 1, 0]]

    vecs_a_3d[:, 2] = 0.0
    vecs_b_3d[:, 2] = 0.0

    cross = np.cross(vecs_a_3d, vecs_b_3d)
    cross = cross[:, 2] >= 0.0
    cross.shape = angs.shape

    angs[cross] *= -1

    # Reverse angle if going backwards
    if switch:
        angs *= -1

    # Convert negative counter clockwise values to 0-2pi range
    if full_range:
        angs[angs < 0.0] = np.pi*2 + angs[angs < 0.0]

    return angs


def interweave_arrays(arrays):
    #
    # Given a tuple of numpy arrays vertically stack them
    # And reshape so the rows are in order they are given
    # Output-Row 1 is Array1-Row 1
    # Output-Row 2 is Array2-Row 1
    # Output-Row 3 is Array3-Row 1
    # Output-Row 4 is Array1-Row 2
    # Output-Row 5 is Array2-Row 2
    # ............................
    # ............................
    #
    #
    weaved_array = np.vstack(arrays)

    idx = np.arange(
        weaved_array.shape[0]).reshape(-1, arrays[0].shape[0]).T.flatten()
    weaved_array = weaved_array[idx]
    return weaved_array


def get_nearest_co_on_curve(coords, curve_pos_amnt, test_co):
    #
    # Get closest point on a path/curve from a test coordinate
    #

    co, dist, ind = get_nearest_co_on_coord_set(test_co, coords)

    curve_po_inds = np.arange(curve_pos_amnt)
    betweens = (coords.shape[0]-curve_pos_amnt) // (curve_pos_amnt-1)
    curve_po_inds += (betweens * curve_po_inds)

    near_ind = np.searchsorted(curve_po_inds, ind+1)

    return co, dist, near_ind, ind


def get_nearest_co_on_coord_set(test_co, coords):
    #
    # Get closest point on a numpy path/curve array from a test numpy coordinate
    #
    line_cos, line_dists, on_line = get_nearest_cos_on_lines(
        test_co, coords[:-1], coords[1:])

    ind = line_dists.argmin()
    place_ind = ind+1

    if ind == 0 and on_line[0] == False:
        place_ind = 0

    if ind == coords.shape[0]-2 and on_line[-1] == False:
        place_ind = coords.shape[0]

    return line_cos[ind], line_dists[ind], place_ind


def get_nearest_cos_on_lines(cos, line_edges_v1, line_edges_v2):
    #
    # Get the nearest coordinate on a line clipped to the ends of the lines from a test coordinated
    #
    line_cos, dot_dists = project_cos_on_lines(
        cos, line_edges_v1, line_edges_v2)

    line_len = get_vec_lengths(line_edges_v2 - line_edges_v1)

    line_cos[dot_dists < 0.0] = line_edges_v1[dot_dists < 0.0]
    line_cos[dot_dists > line_len] = line_edges_v2[dot_dists > line_len]

    on_line = dot_dists > 0.0
    on_line[dot_dists >= line_len] = False

    dists = get_vec_lengths(line_cos-cos)
    return line_cos, dists, on_line


def project_cos_on_lines(cos, line_edges_v1, line_edges_v2):
    #
    # Get the nearest coordinate on an infinite line from a test coordinated
    #
    vecs = get_normalized_vecs(line_edges_v2 - line_edges_v1)

    v1_vecs = cos - line_edges_v1

    dots = np.sum(v1_vecs * vecs, axis=1)

    line_cos = line_edges_v1 + vecs * dots[:, np.newaxis]
    return line_cos, dots


def get_np_matrix_transformed_vecs(array, mat):
    #
    # Array is a Nx3 array of 3d vectors
    # Matrix is a 4x4 object matrix
    # turns array into an Nx4 array to perform matrix multiplication on it and
    # returns a Nx3 array of the end vectors transformed
    #
    n_mat = np.array(mat)

    full_array = np.ones(shape=(array.size // 3, 4), dtype=np.float32)
    full_array[:, :-1] = array

    transformed_array = (n_mat @ full_array.T).T[:, :-1]

    return transformed_array


def ray_cast_2d_loc(co_2d, ray_origin, ray_vector, bvhs):
    near_ind, hit, norm, dist, hit_ind = ray_cast_direction(ray_origin,
                                                            ray_vector,
                                                            bvhs)

    if hit:
        return hit, norm, near_ind, dist, hit_ind
    return None


def ray_cast_direction(origin, direction, bvhs):
    coord, normal, near_ind, face_ind = None, None, None, None
    nearest = -1.0
    for i, bvh in enumerate(bvhs):
        hit, norm, ind, dist = bvh.ray_cast(origin,
                                            direction,
                                            10000)

        if hit:
            if near_ind is None or dist < nearest:
                near_ind = i
                nearest = dist
                face_ind = ind

                coord = hit
                normal = norm

    return near_ind, coord, normal, nearest, face_ind


#


def bevel_ui(pos, bevel_inds, ind_offset, width, res):
    #
    # Bevel the points of the given shape
    #
    cos = np.array(pos, dtype=np.float32)

    width = round_up_num(width)

    b_inds = np.sort(bevel_inds).astype(np.int32)

    p_inds, n_inds = get_prev_next_inds(cos, np.arange(cos.shape[0]))

    p_vec = cos[p_inds] - cos
    n_vec = cos[n_inds] - cos

    p_len = get_vec_lengths(p_vec)
    n_len = get_vec_lengths(n_vec)

    bev_sizes = np.where(n_len < p_len, n_len, p_len)
    # All points being beveled
    if b_inds.size == 0:
        bev_sizes = np.clip(bev_sizes / 2, 0.0, width)

    # Check bevel inds for smallest length based on edge length and bev width
    else:
        non_bev_mask = np.ones(cos.shape[0], dtype=np.bool8)
        non_bev_mask[bevel_inds] = False

        p_check = np.isin(p_inds[b_inds], b_inds)
        n_check = np.isin(n_inds[b_inds], b_inds)

        both_check = n_check.copy()
        both_check[~p_check] = False

        p_check[both_check] = False
        n_check[both_check] = False

        p_half = p_len[b_inds[p_check]] / 2
        n_half = n_len[b_inds[n_check]] / 2

        bev_sizes[b_inds[p_check]] = np.where(
            p_half < bev_sizes[b_inds[p_check]], p_half, bev_sizes[b_inds[p_check]])
        bev_sizes[b_inds[n_check]] = np.where(
            n_half < bev_sizes[b_inds[n_check]], n_half, bev_sizes[b_inds[n_check]])
        bev_sizes[b_inds[both_check]] /= 2

        bev_sizes = np.clip(bev_sizes, 0.0, width)

        bev_sizes[non_bev_mask] = 0.0

    #

    ang_check = get_vec_angles_signed(n_vec, p_vec) < 0.0

    p_vec_norm = get_normalized_vecs(p_vec)
    n_vec_norm = get_normalized_vecs(n_vec)

    vecs_a = n_vec_norm.copy()
    vecs_a[ang_check] = p_vec_norm[ang_check]

    vecs_b = p_vec_norm.copy()
    vecs_b[ang_check] = n_vec_norm[ang_check]

    cross_vec = vecs_b[:, [1, 0]]
    cross_vec[:, 0] *= -1

    halfang = np.arccos(np.sum((vecs_a*-1) * (vecs_b*-1), axis=1)) / 2
    # TOA tan of corner angle = opposite/adjancent   we don't know opposite len which is the radius
    # so tan of corner angle * adjacent = opposite   fac is our adjacent length
    radius = np.tan(halfang) * bev_sizes

    po1 = cos+vecs_a*bev_sizes.reshape(-1, 1)
    po2 = cos+vecs_b*bev_sizes.reshape(-1, 1)

    origins = po2 + cross_vec * radius.reshape(-1, 1)

    ang_facs = ((np.arange(res, dtype=np.float32)+1) / (res+1))[::-1]

    comb_cos = []
    for c in range(cos.shape[0]):
        if bev_sizes[c] == 0.0:
            comb_cos.append(cos[c].reshape(-1, 2))

        else:
            other_ang = np.radians(90) - halfang[c]

            angs = ang_facs * other_ang * 2

            v1 = po1[c] - origins[c]

            cos_angs = np.cos(angs)
            sin_angs = np.sin(angs)

            rot_cos = np.zeros(res*2, dtype=np.float32).reshape(-1, 2)

            rot_cos[:, 0] = cos_angs * v1[0] - sin_angs * v1[1]
            rot_cos[:, 1] = sin_angs * v1[0] + cos_angs * v1[1]
            rot_cos += origins[c]

            comb_cos.append(po2[c])
            comb_cos.append(rot_cos)
            comb_cos.append(po1[c])

    return np.vstack(comb_cos)


def rotate_2d(origin, point, angle):
    x = np.cos(angle) * (point[0] - origin[0]) - \
        np.sin(angle) * (point[1] - origin[1])
    y = np.sin(angle) * (point[0] - origin[0]) + \
        np.cos(angle) * (point[1] - origin[1])

    vec = np.array([x, y])
    vec += np.array(origin)
    return vec


def insert_modal(arguments, modal):
    if arguments is not None:
        arguments.insert(0, modal)
    else:
        arguments = [modal]
    return arguments


def cui_img_load(img_name, path):
    script_file = os.path.realpath(path)
    directory = os.path.dirname(script_file)

    img_fp = directory.replace('/', '\\') + '\\' + img_name

    not_there = True
    for img in bpy.data.images:
        if img.filepath == img_fp:
            not_there = False
            break

    if not_there:
        img = bpy.data.images.load(img_fp)
    try:
        img.colorspace_settings.name = 'Raw'
    except:
        pass

    if img.gl_load():
        raise Exception()

    return img


#


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


def mix_colors(color1, color2, mix=0.5):
    mix_color = [0, 0, 0, 0]
    mix_color[0] = color1[0]*mix + color2[0]*(1-mix)
    mix_color[1] = color1[1]*mix + color2[1]*(1-mix)
    mix_color[2] = color1[2]*mix + color2[2]*(1-mix)
    mix_color[3] = color1[3]*mix + color2[3]*(1-mix)
    return mix_color


def desaturate_color(col, fac):
    new_val = col[0]*.3 + col[1]*.59 + col[2]*.11
    diff = [new_val-col[0], new_val-col[1], new_val-col[2]]

    new_col = [col[0]+diff[0]*fac, col[1] +
               diff[1]*fac, col[2]+diff[2]*fac, col[3]]

    return new_col


def modify_color(col, desat_fac, value_fac):
    new_val = col[0]*.3 + col[1]*.59 + col[2]*.11
    diff = [new_val-col[0], new_val-col[1], new_val-col[2]]

    new_col = [
        (col[0]+diff[0]*desat_fac)*value_fac,
        (col[1]+diff[1]*desat_fac)*value_fac,
        (col[2]+diff[2]*desat_fac)*value_fac,
        col[3]
    ]

    return new_col


def get_modified_color(col, desat_fac, value_fac, alpha_fac):
    color = (
        col[0], col[1]*desat_fac, col[2]*value_fac, col[3]*alpha_fac)

    return color


def get_enabled_color(col, enabled):
    color = col

    if enabled == False:
        color = (
            col[0], 0.0, col[2]*0.7, col[3]*0.5)

    color_render = hsv_to_rgb_list(color)

    return color_render


#


def cui_calc_point_handles(cos, cyclic, smooth_ends):
    #
    # Calculate the auto handles of a bezier curve
    # If smooth ends is used the first and last handles rotate out to point at the handles of the neighbor points
    #
    if cos.shape[0] < 2:
        return None

    inds = np.arange(cos.shape[0])
    prev_inds, next_inds = get_prev_next_path_inds(cos, inds, cyclic)

    # Handle vectors
    prev_vecs, next_vecs = get_prev_next_path_vecs(
        cos, inds, prev_inds, next_inds, cyclic, handle_vecs=True)

    # Cyclic line with 2 points so set handles to avoid a 0 length vec
    if cyclic and cos.shape[0] == 2:
        prev_vecs = prev_vecs[::-1]

    prev_lens = get_vec_lengths(prev_vecs) * .390464
    next_lens = get_vec_lengths(next_vecs) * .390464

    handle_vecs = get_normalized_vecs((get_normalized_vecs(
        next_vecs) - get_normalized_vecs(prev_vecs)) * 0.5)

    # orient first and last points handles towards the handles of the connected points for a smoother transition
    if cyclic == False and smooth_ends and cos.shape[0] > 2:
        handle_vecs[0] = get_normalized_vecs(
            (cos[1] - handle_vecs[1] * prev_lens[1]) - cos[0])
        handle_vecs[-1] = get_normalized_vecs(
            ((cos[-2] + handle_vecs[-2] * next_lens[-2]) - cos[-1]) * -1)

    return cos - handle_vecs * prev_lens[:, np.newaxis], cos + handle_vecs * next_lens[:, np.newaxis]


def cui_calc_modified_point_handles(cos, cyclic, rotations, scales, smooth_ends):
    #
    # Calculate the auto handles of a bezier curve
    # If smooth ends is used the first and last handles rotate out to point at the handles of the neighbor points
    # Rotations and scales occur after the initial auto calculation
    # Rotation is around the provided normal vector
    #
    handles_a, handles_b = cui_calc_point_handles(cos, cyclic, smooth_ends)
    handle_a_vecs = handles_a - cos
    handle_b_vecs = handles_b - cos

    # Rotate handles
    rot_mask = rotations != 0.0
    if rot_mask.any():
        cross_vecs_a = (
            handle_a_vecs[rot_mask, [1, 0]] * np.array([-1.0, 1.0]))
        cross_vecs_b = (
            handle_b_vecs[rot_mask, [1, 0]] * np.array([-1.0, 1.0]))

        rot_x = -np.sin(-rotations[rot_mask])
        rot_y = np.cos(-rotations[rot_mask])

        handle_a_vecs[rot_mask] = (
            handle_a_vecs[rot_mask] * rot_y[:, np.newaxis]) + (cross_vecs_a * rot_x[:, np.newaxis])
        handle_b_vecs[rot_mask] = (
            handle_b_vecs[rot_mask] * rot_y[:, np.newaxis]) + (cross_vecs_b * rot_x[:, np.newaxis])

    # Scale Handles
    handle_a_vecs *= scales[:, np.newaxis]
    handle_b_vecs *= scales[:, np.newaxis]

    handles_a = cos + handle_a_vecs
    handles_b = cos + handle_b_vecs

    return handles_a, handles_b


def cui_get_bezier_coords(pos_a, handles_a, handles_b, pos_b, t_values, connected=False):
    #
    # Interpolate bezier curves
    # This is slower than using mathutils.geometry.interpolate_bezier for smaller sets of data
    # Once operating on multiple bezier segments and connected them it is faster or similar speed but easier to use
    #
    t_vals = t_values.reshape(-1, 1)[:, np.newaxis]
    facs = 1.0 - t_vals

    vec1 = (pos_a*facs + handles_a*t_vals)*facs
    vec2 = (handles_a*facs + handles_b*t_vals)*t_vals
    vec3 = (handles_a*facs + handles_b*t_vals)*facs
    vec4 = (handles_b*facs + pos_b*t_vals)*t_vals
    t_cos = ((vec1 + vec2)*facs + (vec3 + vec4)*t_vals).reshape(-1, 2)

    if connected:
        inds = np.arange(t_values.size) * pos_a.shape[0]
        inds = np.tile(inds, (pos_a.shape[0], 1)).reshape(pos_a.shape[0], -1)

        inds += np.arange(pos_a.shape[0])[:, np.newaxis]
        inds[1:, 0] = -1

        inds = inds[inds != -1]
        t_cos = t_cos[inds.ravel()]

    return t_cos
