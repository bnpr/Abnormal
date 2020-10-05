import bpy
import blf
import bgl
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
import mathutils
import math


def check_tri(cos, f_inds, inds):
    # check that 3 verts exist for the non bevel portions and create a triangle if it can
    #vec_a = cos[f_inds[0]] - cos[f_inds[1]]
    #vec_b = cos[f_inds[0]] - cos[f_inds[2]]

    inds.append([f_inds[0], f_inds[1], f_inds[2]])

    f_inds.pop(1)
    return


def bevel_ui(pos, bevel_inds, ind_offset, fac, res):
    cos = []
    for po in pos:
        cos.append(mathutils.Vector((po[0], po[1])))

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

            cross_vec = mathutils.Vector((-vec2_norm[1], vec2_norm[0]))

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


def ui_hover_test(mouse_co, position, width, height):
    box_x_min = position[0]
    box_x_max = position[0]+width

    box_y_min = position[1]-height
    box_y_max = position[1]

    if box_x_max > mouse_co[0] > box_x_min and box_y_max > mouse_co[1] > box_y_min:
        return True
    else:
        return False


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


def rotate_2d(origin, point, angle):

    x = origin[0] + math.cos(angle) * (point[0] - origin[0]) - \
        math.sin(angle) * (point[1] - origin[1])
    y = origin[1] + math.sin(angle) * (point[0] - origin[0]) + \
        math.cos(angle) * (point[1] - origin[1])

    vec = mathutils.Vector((x, y))
    return vec


def tris_between_boxes(box_pos1, box_pos2):
    if len(box_pos1) != len(box_pos2):
        print("Error the 2 boxes supplied foe tris_between_boxes don't have the same amount of points")

    tris = []
    pos = box_pos1 + box_pos2
    po_len = len(box_pos1)
    for p in range(len(box_pos1)):
        if p < len(box_pos1)-1:
            next_ind = p+1
        else:
            next_ind = 0

        face_ind = [p, p+po_len, next_ind+po_len]
        tris.append(face_ind)

        face_ind = [p, next_ind+po_len, next_ind]
        tris.append(face_ind)

    return pos, tris


def fit_text(text, text_size, font_id, box_size, value=''):
    text_width, text_height = calc_text_size(text, text_size, font_id)

    tot_text = text
    num_width = 0
    if value != '':
        tot_text = text + ': ' + value
        num_width, num_height = calc_text_size(value, text_size, font_id)

    tot_width, tot_height = calc_text_size(tot_text, text_size, font_id)

    if tot_width > box_size:
        if value != '':
            if num_width > box_size:
                new_text = ''
                for i in range(len(value)):
                    render_txt = value[:-1-i]

                    render_size = calc_text_size(
                        render_txt, text_size, font_id)

                    if render_size[0] < box_size:
                        new_text = render_txt
                        break

                return new_text

            else:
                new_text = value
                for i in range(len(text)):
                    render_txt = text[:-1-i] + ': ' + value

                    render_size = calc_text_size(
                        render_txt, text_size, font_id)

                    if render_size[0] < box_size:
                        new_text = render_txt
                        break

                return new_text

        else:
            new_text = ''
            for i in range(len(text)):
                render_txt = text[:-1-i] + '...'

                render_size = calc_text_size(render_txt, text_size, font_id)

                if render_size[0] < box_size:
                    new_text = render_txt
                    break

            return new_text

    else:
        return tot_text


def calc_text_size(text, text_size, font_id):
    blf.size(font_id, text_size, 72)
    size = text_size_int(font_id, text)

    return round_up_num(size[0]), round_up_num(size[1])


def place_text_in_box(align, box_height, box_width, margin, text_height, text_width, text, x_offset=0):
    if align == 'Center':
        x = (box_width/2 - text_width/2) + x_offset
    if align == 'Right':
        x = (box_width - text_width) + x_offset
    if align == 'Left':
        x = 0 + x_offset

    y = -box_height + (box_height-text_height)*.666
    if 'q' in text or 'y' in text or 'p' in text or 'j' in text or 'g' in text:
        y += 2

    return x, y


def round_up_num(num):
    if num % 1 > 0.0:
        return int(num+1)
    else:
        return int(num)


def round_up_array(arr):
    new_arr = []
    for num in arr:
        new_arr.append(round_up_num(num))

    return new_arr


def round_array(arr):
    new_arr = []
    for num in arr:
        new_arr.append(round(num))

    return new_arr


def text_size_int(font_id, text):
    size = blf.dimensions(font_id, text)

    return [round_up_num(size[0]), round_up_num(size[1])]


def offset_list_cos(co_list, offset):
    for c in range(len(co_list)):
        co_list[c] = round_up_array(
            [co_list[c][0]+offset[0], co_list[c][1]+offset[1]])
    return


def draw_cos_offset(offset_x, offset_y, cos):
    co_list = []
    for co in cos:
        co_list.append([co[0]+offset_x, co[1]+offset_y])

    return co_list


class UIWindow:
    def __init__(self, shader_2d, shader_3d, shader_img):
        self.border = None
        self.panels = []
        self.gizmo_sets = []
        self.shader_2d = shader_2d
        self.shader_3d = shader_3d
        self.shader_img = shader_img
        self.width = bpy.context.region.width
        self.height = bpy.context.region.height
        self.scale = round(bpy.context.window.width/1920, 2)

        self.num_slide_cache = []
        self.panel_move_cache = []
        self.panel_resize_cache = []
        self.gizmo_moving_cache = []

        self.status = ''
        self.status_pos = [0, 0]
        self.status_size = 16
        self.status_font = 0
        self.status_color = (1.0, 1.0, 1.0, 1.0)
        return

    def check_border_change(self):
        if self.width != bpy.context.region.width or self.height != bpy.context.region.height:
            if self.width > 0 and self.height > 0:
                perc_w = bpy.context.region.width/self.width
                perc_h = bpy.context.region.height/self.height
                for panel in self.panels:
                    self.reposition_panel(panel.index, round_array(
                        [panel.position[0]*perc_w, panel.position[1]*perc_h]))

            if self.border != None:
                self.border.create_shape_data()

            self.width = bpy.context.region.width
            self.height = bpy.context.region.height

        return

    def create_all_drawing_data(self):
        if self.border != None:
            self.border.create_shape_data()

        for panel in self.panels:
            panel.init_shape_data()
            for subp in panel.subpanels:
                subp.init_shape_data()
                for row in subp.rows:
                    row.init_shape_data()
                    for item in row.items:
                        if item.type != 'LABEL':
                            item.init_shape_data()

            panel.create_shape_data()

        return

    def gizmo_draw(self):
        for i in range(len(self.gizmo_sets)):
            self.gizmo_sets[i*-1-1].draw()

    def draw(self):

        for i in range(len(self.panels)):
            self.panels[i*-1-1].draw()

        if self.border != None:
            self.border.draw()

        if self.status != '':
            blf.position(self.status_font,
                         self.status_pos[0], self.status_pos[1], 0)
            blf.color(
                self.status_font, self.status_color[0], self.status_color[1], self.status_color[2], self.status_color[3])
            blf.size(self.status_font, round(self.status_size), 72)
            blf.draw(self.status_font, self.status)

        return

    def set_status(self, text):
        self.status = text
        self.place_status_text()
        return

    def clear_status(self):
        self.status = ''
        return

    def place_status_text(self,):
        text_width, text_height = calc_text_size(
            self.status, self.status_size, self.status_font)
        self.status_pos[0] = round(bpy.context.region.width/2 - text_width/2)
        self.status_pos[1] = 15
        return

    def add_border(self, header_text='', thickness=5, color=(0.3, 0.3, 0.3, 0.5), use_header=True, bevel_size=0.5):
        self.border = UIBorder(self.shader_2d, header_text, thickness, color, round(
            bevel_size*self.scale), use_header, self.scale)
        return

    def clear_border(self):
        self.border = None
        return

    def clear_popup(self):
        self.popup = None
        return

    def add_panel(self, header_text='', header_text_size=18, position=[200, 200], alignment='TL', x_size=250, hover_highlight=False):
        panel = UIPanel(self.shader_2d, self.shader_img, len(self.panels), header_text,
                        header_text_size, position, alignment, x_size, hover_highlight, self.scale)
        panel.init_shape_data()
        self.panels.append(panel)

        return panel

    def clear_panel(self, index):
        self.panels.pop(index)

    def add_rot_gizmo(self, mat, size, axis, thickness):
        gizmo_cont = UIGizmoContainer(
            self.shader_3d, len(self.gizmo_sets), mat, size, axis)

        if axis[0]:
            giz = UIRotateGizmo(self.shader_3d, len(
                gizmo_cont.gizmos), size, 1.0, 0, 'ROT_X', [0.8, 0.0, 0.0, 0.35], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[1]:
            giz = UIRotateGizmo(self.shader_3d, len(
                gizmo_cont.gizmos), size, 1.0, 1, 'ROT_Y', [0.0, 0.8, 0.0, 0.35], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[2]:
            giz = UIRotateGizmo(self.shader_3d, len(
                gizmo_cont.gizmos), size, 1.0, 2, 'ROT_Z', [0.0, 0.0, 0.8, 0.35], thickness)
            gizmo_cont.gizmos.append(giz)
        self.gizmo_sets.append(gizmo_cont)

        gizmo_cont.create_shape_data(mat)
        return gizmo_cont

    def add_scale_gizmo(self, mat, size, axis, thickness):
        gizmo_cont = UIGizmoContainer(
            self.shader_3d, len(gizmo_cont.gizmos), mat, size, axis)

        if axis[0]:
            giz = UIRotateGizmo(self.shader_3d, len(gizmo_cont.gizmos), size, 1.0, 0, [
                                0.8, 0.0, 0.0, 0.5], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[1]:
            giz = UIRotateGizmo(self.shader_3d, len(gizmo_cont.gizmos), size, 1.0, 1, [
                                0.0, 0.8, 0.0, 0.5], thickness)
            gizmo_cont.gizmos.append(giz)
        if axis[2]:
            giz = UIRotateGizmo(self.shader_3d, len(gizmo_cont.gizmos), size, 1.0, 2, [
                                0.0, 0.0, 0.8, 0.5], thickness)
            gizmo_cont.gizmos.append(giz)
        self.gizmo_sets.append(gizmo_cont)

        gizmo_cont.create_shape_data(mat)
        return

    def update_gizmo_pos(self, matrix, ang=0):
        for giz_set in self.gizmo_sets:
            giz_set.update_position(matrix, ang=ang)
        return

    def update_gizmo_rot(self, ang, start_ang):
        for giz_set in self.gizmo_sets:
            giz_set.update_rot(ang, start_ang)
        return

    def update_gizmo_orientation(self, matrix):
        for giz_set in self.gizmo_sets:
            giz_set.update_orientation(matrix)
        return

    def test_gizmo_hover(self, mouse_loc):
        for giz_set in self.gizmo_sets:
            for gizmo in giz_set.gizmos:
                gizmo.hover = False

        for giz_set in self.gizmo_sets:
            for gizmo in giz_set.gizmos:
                if gizmo.active:
                    hov = gizmo.test_hover(mouse_loc)
                    if hov:
                        return True
        return False

    def test_gizmo_click(self):
        for giz_set in self.gizmo_sets:
            for gizmo in giz_set.gizmos:
                if gizmo.hover and gizmo.active:
                    return gizmo.type, [giz_set.index, gizmo.index]
        return None
    # RESIZING

    def start_resize(self, mouse_co):
        for panel in self.panels:
            if panel.edge_hover:
                self.panel_resize_cache.clear()
                self.panel_resize_cache.append([panel.index])
                self.panel_resize_cache.append(mouse_co)
                self.panel_resize_cache.append(mouse_co[0] < panel.position[0])
                break
        return

    def resize_panel(self, mouse_co):
        panel = self.panels[self.panel_resize_cache[0][0]]
        offset = round_array([mouse_co[0]-self.panel_resize_cache[1]
                              [0], mouse_co[1]-self.panel_resize_cache[1][1]])

        if self.panel_resize_cache[2]:
            size_check = panel.width-offset[0] > panel.min_width
        else:
            size_check = panel.width+offset[0] > panel.min_width

        if abs(offset[0]) > 0 and size_check:
            # check for and prevent panel from leaving view
            if panel.bounding_corner[0] + offset[0] < 0:
                offset[0] = -panel.bounding_corner[0]
            if panel.bounding_corner[0] + panel.width + offset[0] > bpy.context.region.width:
                offset[0] = bpy.context.region.width - \
                    panel.bounding_corner[0] - panel.width

            if self.panel_resize_cache[2]:
                panel.width -= offset[0]
                panel.header_bar_width -= offset[0]
                for subp in panel.subpanels:
                    subp.width -= offset[0]
                    subp.header_bar_width -= offset[0]

                    for row in subp.rows:
                        row.width = subp.width - subp.margin*2
                        if len(row.items) > 0:
                            width_tot = row.width - row.margin*2
                            width_tot -= (len(row.items)-1) * \
                                row.item_separation
                            width = width_tot/(len(row.items))

                            x_pos = row.margin
                            for item in row.items:
                                item.position[0] = x_pos
                                item.position[1] = -row.margin
                                item.width = width
                                x_pos += width
                                x_pos += row.item_separation

                panel.header_corner[0] += offset[0]
                panel.bounding_corner[0] += offset[0]

                if 'L' in panel.alignment:
                    panel.position[0] += offset[0]

                if 'C' in panel.alignment:
                    panel.position[0] = round(
                        panel.bounding_corner[0] + panel.width/2)

            else:
                panel.width += offset[0]
                panel.header_bar_width += offset[0]
                for subp in panel.subpanels:
                    subp.width += offset[0]
                    subp.header_bar_width += offset[0]

                    for row in subp.rows:
                        row.width = subp.width - subp.margin*2
                        if len(row.items) > 0:
                            width_tot = row.width - row.margin*2
                            width_tot -= (len(row.items)-1) * \
                                row.item_separation
                            width = width_tot/(len(row.items))

                            x_pos = row.margin
                            for item in row.items:
                                item.position[0] = x_pos
                                item.position[1] = -row.margin
                                item.width = width
                                x_pos += width
                                x_pos += row.item_separation

                if 'C' in panel.alignment:
                    panel.position[0] = round(
                        panel.bounding_corner[0] + panel.width/2)

                if 'R' in panel.alignment:
                    panel.position[0] += offset[0]
            panel.create_shape_data()

        self.panel_resize_cache[1] = mouse_co
        return

    def confirm_resize(self):
        self.panel_resize_cache.clear()
        return
    # MOVING

    def start_move(self, mouse_co):
        for panel in self.panels:
            if panel.hover:
                self.panel_move_cache.clear()
                self.panel_move_cache.append([panel.index])
                self.panel_move_cache.append(mouse_co)
                break
        return

    def move_panel(self, mouse_co):
        panel = self.panels[self.panel_move_cache[0][0]]

        offset = round_array(
            [mouse_co[0]-self.panel_move_cache[1][0], mouse_co[1]-self.panel_move_cache[1][1]])

        if abs(offset[0]) > 0 or abs(offset[1]) > 0:
            # check for and prevent panel from leaving view
            if panel.bounding_corner[0] + offset[0] < 0:
                offset[0] = -panel.bounding_corner[0]
            if panel.bounding_corner[0] + panel.width + offset[0] > bpy.context.region.width:
                offset[0] = bpy.context.region.width - \
                    panel.bounding_corner[0] - panel.width

            if panel.bounding_corner[1] - panel.height + offset[1] < 0:
                offset[1] = -panel.bounding_corner[1] + panel.height
            if panel.bounding_corner[1] + offset[1] > bpy.context.region.height:
                offset[1] = bpy.context.region.height - \
                    panel.bounding_corner[1]

            panel.header_corner[0] += offset[0]
            panel.header_corner[1] += offset[1]
            panel.bounding_corner[0] += offset[0]
            panel.bounding_corner[1] += offset[1]
            panel.position[0] += offset[0]
            panel.position[1] += offset[1]

            panel.update_position()

            self.panel_move_cache[1] = mouse_co
        return

    def confirm_move(self):
        self.panel_move_cache.clear()
        return

    def reposition_panel(self, panel_ind, position):
        panel = self.panels[panel_ind]
        panel.header_corner[0] = position[0]+panel.x_offset
        panel.header_corner[1] = position[1]+panel.y_offset
        panel.bounding_corner[0] = position[0]+panel.x_offset
        panel.bounding_corner[1] = position[1]+panel.y_offset
        panel.position[0] = position[0]
        panel.position[1] = position[1]

        panel.update_position()
        return
    # NUM PROP CHANGING

    def num_change(self, shift):
        for panel in self.panels:
            if panel.hover:
                for subp in panel.subpanels:
                    if subp.hover:
                        for row in subp.rows:
                            for item in row.items:
                                if item.type == 'NUMBER':
                                    if item.hover:
                                        fac = item.change_factor
                                        if item.left_hover:
                                            fac *= -1

                                        if shift:
                                            fac *= 10

                                        item.value = round(
                                            item.value+fac, item.decimals)
                                        if item.value < item.min:
                                            item.value = item.min
                                        if item.value > item.max:
                                            item.value = item.max

                                        item.update_slider(
                                            [panel.position[0]+subp.position[0]+row.position[0], panel.position[1]+subp.position[1]+row.position[1]])
                                        return item.value
        return None

    def start_num_slide(self, mouse_co):
        for panel in self.panels:
            if panel.hover:
                for subp in panel.subpanels:
                    if subp.hover:
                        for row in subp.rows:
                            for item in row.items:
                                if item.type == 'NUMBER':
                                    if item.hover and item.bar_hover:
                                        self.num_slide_cache.clear()
                                        self.num_slide_cache.append(
                                            [panel.index, subp.index, row.index, item.index])
                                        self.num_slide_cache.append(mouse_co)
                                        self.num_slide_cache.append(item.value)
                                        self.num_slide_cache.append(item.id)
                                        self.num_slide_cache.append(item.value)
                                        break
        return

    def slide_number(self, mouse_co, shift, fac=0.01):
        panel = self.panels[self.num_slide_cache[0][0]]
        subp = panel.subpanels[self.num_slide_cache[0][1]]
        row = subp.rows[self.num_slide_cache[0][2]]
        num = row.items[self.num_slide_cache[0][3]]

        offset = round_array(
            [mouse_co[0]-self.num_slide_cache[1][0], mouse_co[1]-self.num_slide_cache[1][1]])
        if shift:
            val_shift = round(offset[0]*fac*0.1, num.decimals)
        else:
            val_shift = round(offset[0]*fac, num.decimals)

        new_val = round(self.num_slide_cache[4] + val_shift, num.decimals)
        if val_shift != 0.0:

            if new_val < num.min:
                new_val = num.min
            if new_val > num.max:
                new_val = num.max

            if num.decimals == 0:
                new_val = int(new_val)

            self.num_slide_cache[4] = new_val
            num.value = new_val
            num.update_slider([panel.position[0]+subp.position[0]+row.position[0],
                               panel.position[1]+subp.position[1]+row.position[1]])

            self.num_slide_cache.pop(1)
            self.num_slide_cache.insert(1, mouse_co)
        return new_val

    def confirm_num_slide(self):
        self.num_slide_cache.clear()
        return

    def cancel_num_slide(self):
        num = self.panels[self.num_slide_cache[0][0]].subpanels[self.num_slide_cache[0]
                                                                [1]].rows[self.num_slide_cache[0][2]].items[self.num_slide_cache[0][3]]
        num.value = self.num_slide_cache[2]
        og_val = self.num_slide_cache[2]
        self.num_slide_cache.clear()
        num.update_slider()
        return og_val

    def panel_collapse_test(self):
        for panel in self.panels:
            if panel.hover:
                if panel.header_hover:
                    self.panel_toggle_collapse()
                    return
                else:
                    self.subpanel_toggle_collapse()
                    return
        return

    def subpanel_toggle_collapse(self):
        for panel in self.panels:
            if panel.hover:
                y_pos = abs(panel.subp_stacking_offset) + panel.margin
                for subp in panel.subpanels:
                    collapsed = False
                    og_height = subp.height
                    if subp.hover:
                        if subp.header_hover:
                            collapsed = True
                            subp.toggle_collapse()

                            if 'T' in panel.alignment:
                                subp.create_shape_data(
                                    y_pos, panel.horizontal_margin, panel.width, panel.alignment)
                            else:
                                subp.create_shape_data(
                                    subp.position[1]-subp.height, panel.horizontal_margin, panel.width, panel.alignment)

                    if collapsed == False:
                        if 'T' in panel.alignment:
                            subp.position[1] = -y_pos
                        else:
                            subp.position[1] = y_pos+subp.height
                        subp.update_position(panel.position)

                    y_pos += subp.height
                    y_pos += panel.panel_separation
                    del(collapsed)

                panel.collapse_recreate_bg()

                del(og_height)
                del(y_pos)
                break
        return

    def panel_toggle_collapse(self):
        for panel in self.panels:
            if panel.hover:
                panel.toggle_collapse()
                break
        return

    def test_hover(self, mouse_co):
        # unset all hover status
        for panel in self.panels:
            panel.hover = False
            panel.edge_hover = False
            panel.header_hover = False
            for subp in panel.subpanels:
                subp.hover = False
                subp.header_hover = False
                for row in subp.rows:
                    for item in row.items:
                        if item.type != 'LABEL':
                            item.hover = False
                            if item.type == 'NUMBER':
                                item.bar_hover = False
                                item.left_hover = False
                                item.right_hover = False

        # find hover status of panels will stop at first panel hovered in case of overlaps
        for panel in self.panels:
            if panel.visible or panel.visible_on_hover:
                hov_part = panel.test_hover(mouse_co)
                if hov_part != None:
                    if hov_part == 'EDGE':
                        bpy.context.window.cursor_modal_set('MOVE_X')

                    elif hov_part == 'PANEL_HEADER' or hov_part == 'PANEL' or hov_part == 'SUBPANEL':
                        bpy.context.window.cursor_modal_set('HAND')

                    elif hov_part == 'SUBPANEL_NUM_BAR':
                        bpy.context.window.cursor_modal_set('SCROLL_X')

                    else:
                        bpy.context.window.cursor_modal_set('DEFAULT')

                    if panel.visible_on_hover:
                        panel.visible = True
                        for subp in panel.subpanels:
                            subp.visible = True
                            for row in subp.rows:
                                row.visible = True
                                for item in row.items:
                                    item.visible = True
                    return hov_part

                else:
                    if panel.visible_on_hover:
                        panel.visible = False
                        for subp in panel.subpanels:
                            subp.visible = False
                            for row in subp.rows:
                                row.visible = False
                                for item in row.items:
                                    item.visible = False

        bpy.context.window.cursor_modal_set('DEFAULT')
        return None

    def test_click(self):
        # unset all hover status
        for panel in self.panels:
            if panel.visible:
                if panel.header_hover:
                    return 'PANEL_HEADER', panel.index, None

                if panel.hover:
                    for subp in panel.subpanels:
                        if subp.header_hover:
                            return 'SUBP_HEADER', panel.index, None
                        if subp.hover:
                            for row in subp.rows:
                                for item in row.items:
                                    if item.type != 'LABEL':
                                        if item.hover:
                                            if item.type == 'NUMBER':
                                                if item.bar_hover:
                                                    return 'NUM_BAR', panel.index, item.id
                                                if item.left_hover:
                                                    return 'NUM_LEFT_ARROW', panel.index, item.id
                                                if item.right_hover:
                                                    return 'NUM_RIGHT_ARROW', panel.index, item.id

                                            return item.type, panel.index, item.id

                    return None, panel.index, None

        return None

    def boolean_toggle_hover(self):
        for panel in self.panels:
            if panel.hover:
                for subp in panel.subpanels:
                    if subp.hover:
                        for row in subp.rows:
                            for item in row.items:
                                if item.type == 'BOOLEAN':
                                    if item.hover:
                                        item.bool = not item.bool

        return

    def boolean_toggle_id(self, id):
        for panel in self.panels:
            for subp in panel.subpanels:
                for row in subp.rows:
                    for item in row.items:
                        if item.type == 'BOOLEAN':
                            if item.id == id:
                                item.bool = not item.bool

        return

    def __str__(self, ):
        return 'UI Window'


class UIBorder:
    def __init__(self, shader, text, thick, color, bevel, header, scale):
        self.thickness = round(thick*scale)
        self.color = color
        self.text_color = [1, 1, 1, 1]
        self.shader = shader
        self.bevel_size = round(bevel*scale)
        self.use_header = header
        self.bevel_res = 10
        self.width = 1920
        self.height = 1080

        self.text = text
        self.font_id = 0
        self.font_size = round(22*scale)
        #self.create_shape_data(text, self.color)
        return

    def create_shape_data(self, text=None, color=None):
        if text != None:
            self.text = text
        if color != None:
            self.color = color

        self.width = bpy.context.region.width
        self.height = bpy.context.region.height

        thick = self.thickness

        center = self.width/2

        draw_border_pos = [
            [0, 0], [0, self.height], [self.width, self.height], [self.width, 0],
            [thick, thick], [thick, self.height-thick], [self.width -
                                                         thick, self.height-thick], [self.width-thick, thick],
        ]

        draw_border_inds = [
            [0, 1, 5], [1, 2, 5], [2, 3, 6], [7, 3, 4],
            [0, 5, 4], [5, 2, 6], [6, 3, 7], [3, 0, 4],
        ]

        blf.size(self.font_id, round_up_num(self.font_size), 72)
        size = text_size_int(self.font_id, self.text)
        bottom = (44-size[1]) / 2 + size[1]

        self.text_x = center-(size[0]/2)
        self.text_y = self.height-thick-bottom

        if self.use_header:
            offset = len(draw_border_pos)

            init_pos = [
                mathutils.Vector((center-size[0]-65, self.height-thick)), mathutils.Vector(
                    (center+size[0]+65, self.height-thick)),
                mathutils.Vector((center+size[0]+10, self.height-thick-size[1]*1.5)), mathutils.Vector(
                    (center-size[0]-10, self.height-thick-size[1]*1.5)),
            ]

            init_inds = [
                [0, 1, 3], [1, 2, 3],
            ]

            if self.bevel_size > 0.0:
                mode_init_pos, mode_init_inds = bevel_ui(
                    init_pos, [2, 3], offset, self.bevel_size, self.bevel_res)

                draw_border_pos += mode_init_pos
                draw_border_inds += mode_init_inds

        self.points = draw_border_pos
        self.tris = draw_border_inds

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.points}, indices=self.tris)
        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)
        self.shader.bind()
        self.shader.uniform_float("color", self.color)
        self.batch.draw(self.shader)
        bgl.glEnable(bgl.GL_BLEND)

        if self.text != '':
            blf.size(self.font_id, self.font_size, 72)
            blf.position(self.font_id, self.text_x, self.text_y, 0)
            blf.color(
                self.font_id, self.text_color[0], self.text_color[1], self.text_color[2], self.text_color[3])
            blf.draw(self.font_id, self.text)
        return

    def __str__(self, ):
        return 'UI Border'


class UIPanel:
    def __init__(self, shader, icon_shader, ind, header_text, header_text_size, position, alignment, x_size, hover_highlight, scale):
        self.subpanels = []
        self.shader = shader
        self.icon_shader = icon_shader

        self.index = ind

        self.position = round_array(position)
        self.bounding_corner = round_array(position)
        self.header_corner = round_array(position)
        self.subp_corner_offset = [0, 0]
        self.subp_stacking_offset = 0

        self.subp_use_header_box = True

        self.header_offset = [0, 0]
        self.header_bar_offset = [0, 0]
        self.header_text = header_text
        self.header_text_render = header_text
        self.header_text_size = round(header_text_size*scale)
        self.subp_header_text_size = None
        self.header_text_x = 0
        self.header_text_y = 0
        self.header_arrow_size = round(8*scale)
        self.header_align = 'Center'
        self.text_align = 'Center'
        self.moveable = True

        self.reposition_offset = None

        self.x_offset = 0
        self.y_offset = 0
        self.panel_y_pos = 0

        self.alignment = 'TL'

        self.header_icon = None
        self.header_icon_pos = []
        self.header_icon_size = 0
        self.icon_margin = 0
        self.icon_separation = round(5*scale)

        self.width = round(x_size*scale)
        self.height = round(75*scale)
        self.border_size = round(4*scale)
        self.draw_border = False
        self.header_bar_height = round(30*scale)
        self.header_bar_width = 0
        self.subp_header_height = round(20*scale)
        self.text_margin = round(5*scale)
        self.horizontal_margin = 0
        self.vert_margin = 0
        self.margin = round(5*scale)
        self.row_margin = round(2*scale)
        self.panel_separation = round(6*scale)
        self.subp_row_height = round(24*scale)
        self.subp_row_separation = round(2*scale)
        self.min_width = round(50*scale)
        self.arrow_width = round(10*scale)

        self.visible = True
        self.visible_on_hover = False
        self.collapse = False
        self.use_collapse = False
        self.closeable = False
        self.hover = False
        self.header_hover = False
        self.hov_highlight = hover_highlight

        self.color_bg = [0.1, 0.1, 0.1, 0.3]
        self.color_subp_bg = [0.1, 0.1, 0.1, 0.9]
        self.color_border = [0.0, 0.0, 0.0, 0.5]
        self.color_button = [0.2, 0.2, 0.2, 1.0]
        self.color_button_hov = [0.37, 0.37, 0.37, 1.0]
        self.color_button_part = [0.3, 0.3, 0.3, 1.0]
        self.color_slider_perc = [0.3, 0.3, 0.3, 1.0]
        self.color_slider_hov = [0.18, 0.18, 0.18, 1.0]
        self.color_click = [0.5, 0.5, 0.5, 1.0]
        self.color_arrows = [0.8, 0.8, 0.8, 1.0]
        self.color_outline = [0.6, 0.6, 0.6, 0.5]
        self.color_subp_outline = [0.6, 0.6, 0.6, 0.5]
        self.color_text = [1.0, 1.0, 1.0, 1.0]
        self.color_header_text = [1.0, 1.0, 1.0, 1.0]
        self.color_header_bar = [0.3, 0.3, 0.3, 1.0]
        self.color_header_hov = [0.5, 0.5, 0.5, 1.0]
        self.color_subp_header_text = [1.0, 1.0, 1.0, 1.0]
        self.color_subp_header_bar = [0.15, 0.15, 0.15, 1.0]
        self.color_subp_header_hov = [0.4, 0.4, 0.4, 1.0]
        self.color_set = [0.6, 0.6, 0.7, 1.0]

        self.font_id = 0
        self.subp_font_size = round(12*scale)

        self.bevel_size = 0
        self.bevel_res = 0

        self.header_bevel_size = 0
        self.header_bevel_res = 0

        self.button_bevel_size = 0
        self.button_bevel_res = 0

        self.use_visible_hov_icon = False

        return

    def init_shape_data(self):
        self.box_points = []
        self.box_tris = []
        self.box_lines = []
        self.border_points = []
        self.border_tris = []
        self.header_points = []
        self.header_tris = []
        self.header_lines = []
        self.subp_box_points = []
        self.subp_box_tris = []
        self.subp_box_lines = []
        self.subp_border_points = []
        self.subp_border_tris = []
        self.header_icon_pos = []
        return

    # CREATE DRAWING DATA
    def create_shape_data(self):
        self.init_shape_data()

        # self.scale_og_data(scale)
        # HEADERBAR SIZE CALC
        self.header_bar_width = self.width - self.horizontal_margin*2

        total_height = 0
        total_height += self.vert_margin
        total_height += self.header_bar_height
        total_height += self.margin
        header_height = round(total_height)

        offset = 0
        if self.header_icon != None:
            self.header_icon_size = self.header_bar_height-self.icon_margin*2
            offset = self.header_icon_size + self.icon_separation*2

        # CHECK TEXT FIT HEADER BAR
        self.header_render = fit_text(self.header_text, self.header_text_size,
                                      self.font_id, self.width-self.margin*2-self.text_margin-offset)
        text_width, text_height = calc_text_size(
            self.header_render, self.header_text_size, self.font_id)

        header_label_width = text_width
        if self.header_icon != None:
            header_label_width = text_width + offset

        self.header_text_x, self.header_text_y = place_text_in_box(
            self.header_align, self.header_bar_height, self.width-self.margin*2, self.text_margin, text_height, header_label_width, self.header_render, x_offset=offset)

        if self.header_icon != None:
            self.header_icon_pos.append(
                [self.header_text_x-offset, -self.header_bar_height+self.icon_margin])
            self.header_icon_pos.append(
                [self.header_text_x-offset+self.header_icon_size, -self.header_bar_height+self.icon_margin])
            self.header_icon_pos.append(
                [self.header_text_x-offset+self.header_icon_size, -self.icon_margin])
            self.header_icon_pos.append(
                [self.header_text_x-offset, -self.icon_margin])

        end_height = total_height

        total_height += self.panel_separation
        if len(self.subpanels) > 0:
            total_height += self.subpanels[0].margin
        self.panel_y_pos = total_height
        # CALCING HEIGHT AND UPDATING SUBPANELS
        for subp in self.subpanels:
            subp.create_shape_data(
                self.panel_y_pos, self.horizontal_margin, self.width, self.alignment)
            total_height += subp.height
            total_height += self.panel_separation
            self.panel_y_pos = total_height
        total_height -= self.panel_separation

        total_height += self.margin
        total_height += self.vert_margin

        if self.collapse == False:
            end_height = total_height
        self.height = round(end_height)
        # ALIGNMENT OFFSETS
        if 'L' in self.alignment:
            self.header_offset[0] = 0
            x_offset = 0
        elif 'R' in self.alignment:
            self.header_offset[0] = -self.width
            x_offset = -self.width
        elif 'C' in self.alignment:
            self.header_offset[0] = round(-self.width/2)
            x_offset = round(-self.width/2)

        if 'T' in self.alignment:
            self.header_offset[1] = 0
            y_offset = 0
            header_y_offset = 0
            self.subp_corner_offset = round_array(
                [0, -self.header_bar_height-self.panel_separation-self.vert_margin*2])
            self.subp_stacking_offset = -self.header_bar_height - \
                self.panel_separation-self.vert_margin*2
        elif 'B' in self.alignment:
            self.header_offset[1] = self.vert_margin*2 + self.header_bar_height
            y_offset = self.height
            header_y_offset = header_height
            self.subp_corner_offset = round_array([0, 0])
            self.subp_stacking_offset = self.header_bar_height + \
                self.panel_separation+self.vert_margin*2
        self.header_bar_offset = [self.margin, -self.margin]

        self.x_offset = x_offset
        self.y_offset = y_offset

        self.bounding_corner = round_array(
            [self.position[0]+self.x_offset, self.position[1]+self.y_offset])
        self.header_corner = round_array(
            [self.position[0]+self.x_offset, self.position[1]+header_y_offset])

        self.box_points, self.box_tris, self.box_lines = calc_box(
            0, 0, self.width, self.height, [], self.bevel_size, self.bevel_res)
        border_out_points, border_out_tris, border_out_lines = calc_box(
            -self.border_size, self.border_size, self.width+self.border_size*2, self.height+self.border_size*2, [], self.bevel_size, self.bevel_res)

        self.border_points, self.border_tris = tris_between_boxes(
            self.box_points, border_out_points)

        self.header_points, self.header_tris, self.header_lines = calc_box(
            0, 0, self.header_bar_width, self.header_bar_height, [], self.header_bevel_size, self.header_bevel_res)

        self.subp_box_points, self.subp_box_tris, self.subp_box_lines = calc_box(
            0, 0, self.width, self.height-self.margin-header_height-self.border_size*2, [], self.bevel_size, self.bevel_res)
        border_out_points, border_out_tris, border_out_lines = calc_box(
            -self.border_size, self.border_size, self.width+self.border_size*2, self.height-self.margin-header_height, [], self.bevel_size, self.bevel_res)

        self.subp_border_points, self.subp_border_tris = tris_between_boxes(
            self.subp_box_points, border_out_points)

        self.update_position()

        # DELETE VARIABLES TO CLEAR FROM MEMORY
        del(border_out_points)
        del(border_out_tris)
        del(border_out_lines)
        del(header_y_offset)
        del(header_height)
        del(total_height)
        del(end_height)
        del(text_height)
        del(text_width)
        del(x_offset)
        del(y_offset)

        return

    def update_position(self):
        x_co = self.position[0]
        y_co = self.position[1]
        header_x = x_co+self.header_offset[0]
        header_y = y_co+self.header_offset[1]
        header_bar_x = header_x+self.header_bar_offset[0]
        header_bar_y = header_y+self.header_bar_offset[1]

        box_points = draw_cos_offset(
            self.header_corner[0], self.header_corner[1], self.box_points)
        box_lines = draw_cos_offset(
            self.header_corner[0], self.header_corner[1], self.box_lines)
        border_points = draw_cos_offset(
            self.header_corner[0], self.header_corner[1], self.border_points)
        header_points = draw_cos_offset(
            header_bar_x, header_bar_y, self.header_points)
        header_lines = draw_cos_offset(
            header_bar_x, header_bar_y, self.header_lines)
        subp_box_points = draw_cos_offset(
            self.bounding_corner[0]+self.subp_corner_offset[0], self.bounding_corner[1]+self.subp_corner_offset[1], self.subp_box_points)
        subp_box_lines = draw_cos_offset(
            self.bounding_corner[0]+self.subp_corner_offset[0], self.bounding_corner[1]+self.subp_corner_offset[1], self.subp_box_lines)
        subp_border_points = draw_cos_offset(
            self.bounding_corner[0]+self.subp_corner_offset[0], self.bounding_corner[1]+self.subp_corner_offset[1], self.subp_border_points)

        if self.header_icon != None:
            icon_pos = draw_cos_offset(
                header_bar_x, header_bar_y, self.header_icon_pos)
            tex_cos = [[0, 0], [1, 0], [1, 1], [0, 1]]
            self.batch_icon = batch_for_shader(self.icon_shader, 'TRI_FAN', {
                                               "pos": icon_pos, "texCoord": tex_cos})

        for subp in self.subpanels:
            subp.update_position(self.position)

        self.batch_bg = batch_for_shader(
            self.shader, 'TRIS', {"pos": box_points}, indices=self.box_tris)
        self.batch_bg_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": box_lines})
        self.batch_border = batch_for_shader(
            self.shader, 'TRIS', {"pos": border_points}, indices=self.border_tris)
        self.batch_subp_bg = batch_for_shader(
            self.shader, 'TRIS', {"pos": subp_box_points}, indices=self.subp_box_tris)
        self.batch_subp_bg_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": subp_box_lines})
        self.batch_subp_border = batch_for_shader(
            self.shader, 'TRIS', {"pos": subp_border_points}, indices=self.subp_border_tris)
        self.batch_header = batch_for_shader(
            self.shader, 'TRIS', {"pos": header_points}, indices=self.header_tris)
        self.batch_header_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": header_lines})

        if self.use_visible_hov_icon:
            vis_hov_bg_points = draw_cos_offset(
                self.header_corner[0], self.header_corner[1], self.visible_icon_bg_points)
            vis_hov_points = draw_cos_offset(
                self.header_corner[0], self.header_corner[1], self.visible_icon_points)
            self.batch_visible_hov_icon_bg = batch_for_shader(
                self.shader, 'TRIS', {"pos": vis_hov_bg_points}, indices=self.visible_icon_bg_tris)
            self.batch_visible_hov_icon = batch_for_shader(
                self.shader, 'TRIS', {"pos": vis_hov_points}, indices=self.visible_icon_tris)

        del(x_co)
        del(y_co)
        del(header_x)
        del(header_y)
        del(box_points)
        del(box_lines)
        del(border_points)
        del(header_points)
        del(header_lines)
        del(subp_box_points)
        del(subp_box_lines)
        del(subp_border_points)
        return

    def collapse_recreate_bg(self):
        self.subp_box_points = []
        self.subp_box_tris = []
        self.subp_box_lines = []
        self.subp_border_points = []
        self.subp_border_tris = []

        total_height = 0
        total_height += self.vert_margin
        total_height += self.header_bar_height
        total_height += self.margin
        header_height = round(total_height)

        if self.collapse == False:
            for subp in self.subpanels:
                # if subp.collapse == False:
                total_height += subp.height
                total_height += self.panel_separation

            total_height -= self.panel_separation
        total_height += self.margin
        total_height += self.vert_margin
        self.height = round(total_height)
        # ALIGNMENT OFFSETS
        if 'L' in self.alignment:
            x_offset = 0
        elif 'R' in self.alignment:
            x_offset = -self.width
        elif 'C' in self.alignment:
            x_offset = round(-self.width/2)

        if 'T' in self.alignment:
            y_offset = 0
        elif 'B' in self.alignment:
            y_offset = self.height

        self.x_offset = x_offset
        self.y_offset = y_offset
        self.bounding_corner = round_array(
            [self.position[0]+self.x_offset, self.position[1]+self.y_offset])

        self.box_points, self.box_tris, self.box_lines = calc_box(
            0, 0, self.width, self.height, [], self.bevel_size, self.bevel_res)
        border_out_points, border_out_tris, border_out_lines = calc_box(
            -self.border_size, self.border_size, self.width+self.border_size*2, self.height+self.border_size*2, [], self.bevel_size, self.bevel_res)

        self.border_points, self.border_tris = tris_between_boxes(
            self.box_points, border_out_points)

        self.update_position()

        # DELETE VARIABLES TO CLEAR FROM MEMORY
        del(total_height)
        del(x_offset)
        del(y_offset)

        return

    def draw(self):
        if self.visible == True:
            # DRAW PANEL BG BOX
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_bg)
            self.batch_bg.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            if self.draw_border:
                # DRAW PANEL SELECTION BORDER
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glLineWidth(1)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_border)
                self.batch_border.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

            # DRAW PANEL HEADER TEXT IF IT IS SET
            if self.header_text != '':
                header_pos = [self.position[0]+self.header_offset[0]+self.header_bar_offset[0],
                              self.position[1]+self.header_offset[1]+self.header_bar_offset[1]]
                blf.position(
                    self.font_id, header_pos[0]+self.header_text_x, header_pos[1]+self.header_text_y, 0)
                blf.color(self.font_id, self.color_header_text[0], self.color_header_text[1],
                          self.color_header_text[2], self.color_header_text[3])
                blf.size(self.font_id, round(self.header_text_size), 72)
                blf.draw(self.font_id, self.header_render)

                del(header_pos)

            if self.header_icon != None:
                if self.header_icon.gl_load():
                    raise Exception()

                bgl.glEnable(bgl.GL_BLEND)
                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.header_icon.bindcode)
                self.icon_shader.bind()
                self.icon_shader.uniform_int("image", 0)
                self.batch_icon.draw(self.icon_shader)
                bgl.glDisable(bgl.GL_BLEND)

            for subp in self.subpanels:
                if self.collapse == False:
                    subp.draw(self.position)
        else:
            if self.visible_on_hover and self.use_visible_hov_icon:
                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_subp_bg)
                self.batch_visible_hov_icon.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_bg)
                self.batch_visible_hov_icon_bg.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)
        return

    def add_visible_oh_hov_icon(self, size):
        self.visible_icon_bg_points = [
            [0, -size], [0, 0], [size, 0], [size, -size]]
        self.visible_icon_bg_tris = [[0, 1, 2], [0, 2, 3]]
        self.visible_icon_points = [
            [2, -size+2], [2, -2], [size-2, -2], [size-7, -7], [7, -7], [7, -size+7]]
        self.visible_icon_tris = [[0, 1, 4], [1, 2, 4], [2, 3, 4], [0, 4, 5]]

        self.use_visible_hov_icon = True
        return
    # INTERACTIONS

    def test_hover(self, mouse_co):
        hov_item = None
        self.edge_hover = ui_hover_test(mouse_co, [
                                        self.bounding_corner[0]-self.border_size*2, self.bounding_corner[1]], self.width+self.border_size*4, self.height)

        if self.edge_hover:
            self.hover = ui_hover_test(
                mouse_co, self.bounding_corner, self.width, self.height)
            if self.hover:
                self.header_hover = ui_hover_test(mouse_co, [self.position[0]+self.header_offset[0]+self.header_bar_offset[0],
                                                             self.position[1]+self.header_offset[1]+self.header_bar_offset[1]], self.header_bar_width, self.header_bar_height)
                if self.header_hover:
                    hov_item = 'PANEL_HEADER'

                else:
                    one_hov = False

                    for subp in self.subpanels:
                        subp.hover = ui_hover_test(mouse_co, [
                                                   self.position[0]+subp.position[0], self.position[1]+subp.position[1]], subp.width, subp.height)
                        if subp.hover:
                            if subp.use_header:
                                subp.header_hover = ui_hover_test(mouse_co, [self.position[0]+subp.position[0]+subp.header_bar_offset[0],
                                                                             self.position[1]+subp.position[1]+subp.header_bar_offset[1]], subp.header_bar_width, subp.header_bar_height)
                            else:
                                subp.header_hover = False

                            if subp.header_hover == False:
                                item_hov = False
                                for row in subp.rows:
                                    for item in row.items:
                                        item.hover = ui_hover_test(mouse_co, [self.position[0]+subp.position[0]+row.position[0]+item.position[0],
                                                                              self.position[1]+subp.position[1]+row.position[1]+item.position[1]], item.width, item.height)

                                        if item.hover:
                                            if item.type == 'BOOLEAN':
                                                hov_item = 'SUBPANEL_BOOL'
                                                one_hov = True
                                                item_hov = True
                                                break
                                            if item.type == 'BUTTON':
                                                hov_item = 'SUBPANEL_BUTTON'
                                                one_hov = True
                                                item_hov = True
                                                break
                                            elif item.type == 'NUMBER':
                                                item.bar_hover = ui_hover_test(mouse_co, [self.position[0]+subp.position[0]+row.position[0]+item.position[0]+item.box_arrow_size,
                                                                                          self.position[1]+subp.position[1]+row.position[1]+item.position[1]], item.width-item.box_arrow_size*2, item.height)
                                                item.left_hover = ui_hover_test(mouse_co, [
                                                                                self.position[0]+subp.position[0]+row.position[0]+item.position[0], self.position[1]+subp.position[1]+row.position[1]+item.position[1]], item.box_arrow_size, item.height)
                                                item.right_hover = ui_hover_test(mouse_co, [self.position[0]+subp.position[0]+row.position[0]+item.position[0]+item.width -
                                                                                            item.box_arrow_size, self.position[1]+subp.position[1]+row.position[1]+item.position[1]], item.box_arrow_size, item.height)

                                                if item.bar_hover:
                                                    hov_item = 'SUBPANEL_NUM_BAR'
                                                    one_hov = True
                                                    item_hov = True
                                                    break
                                                if item.left_hover:
                                                    hov_item = 'SUBPANEL_NUM_LEFT'
                                                    one_hov = True
                                                    item_hov = True
                                                    break
                                                if item.right_hover:
                                                    hov_item = 'SUBPANEL_NUM_RIGHT'
                                                    one_hov = True
                                                    item_hov = True
                                                    break

                                    if item_hov:
                                        break

                                if item_hov == False:
                                    hov_item = 'SUBPANEL'
                                    one_hov = True

                            else:
                                hov_item = 'SUBPANEL_HEADER'
                                one_hov = True

                            break

                    if one_hov == False:
                        hov_item = 'PANEL'

                self.edge_hover = False

            else:
                hov_item = 'EDGE'

        else:
            self.hover = False
            self.header_hover = False
            for subp in self.subpanels:
                subp.hover = False

        return hov_item

    def toggle_collapse(self):
        self.collapse = not self.collapse
        self.collapse_recreate_bg()
        return
    # ADD SUBPANEL

    def add_subpanel(self, scale, header_text='', header_text_size=14):
        header_text_size = round(header_text_size*scale)
        subp = UISubpanel(self.shader, self.icon_shader, len(
            self.subpanels), self.index, self.width-self.horizontal_margin*2, header_text, header_text_size)

        subp.visible = self.visible
        subp.hov_highlight = self.hov_highlight

        subp.color_bg = self.color_subp_bg
        subp.color_button = self.color_button
        subp.color_button_hov = self.color_button_hov
        subp.color_click = self.color_click
        subp.color_button_part = self.color_button_part
        subp.color_slider_perc = self.color_slider_perc
        subp.color_slider_hov = self.color_slider_hov
        subp.color_arrows = self.color_arrows
        subp.color_outline = self.color_subp_outline
        subp.color_text = self.color_text
        subp.color_header_text = self.color_subp_header_text
        subp.color_header_bar = self.color_subp_header_bar
        subp.color_header_hov = self.color_subp_header_hov
        subp.color_set = self.color_set

        subp.header_bar_height = self.subp_header_height
        subp.row_height = self.subp_row_height
        subp.row_separation = self.subp_row_separation

        subp.font_id = self.font_id
        subp.font_size = self.subp_font_size
        if self.subp_header_text_size != None:
            subp.header_text_size = self.subp_header_text_size

        subp.header_align = self.header_align
        subp.text_align = self.text_align
        subp.text_margin = self.text_margin
        subp.margin = self.margin
        subp.horizontal_margin = self.horizontal_margin
        subp.vert_margin = self.vert_margin
        subp.row_margin = self.row_margin

        subp.header_icon = self.header_icon
        subp.header_icon_pos = self.header_icon_pos
        subp.header_icon_size = self.header_icon_size
        subp.icon_margin = self.icon_margin
        subp.icon_separation = self.icon_separation

        subp.bevel_size = self.bevel_size
        subp.bevel_res = self.bevel_res

        subp.header_bevel_size = self.header_bevel_size
        subp.header_bevel_res = self.header_bevel_res

        subp.button_bevel_size = self.button_bevel_size
        subp.button_bevel_res = self.button_bevel_res

        subp.use_header_box = self.subp_use_header_box
        subp.header_arrow_size = self.header_arrow_size

        subp.init_shape_data()

        self.subpanels.append(subp)

        return subp

    def __str__(self, ):
        return 'UI Panel'


class UISubpanel:
    def __init__(self, shader, icon_shader, index, panel_index, width, header_text, header_text_size):
        self.shader = shader
        self.icon_shader = icon_shader
        self.rows = []
        self.index = index

        self.panel_index = panel_index
        self.position = [0, 0]
        self.width = round(width)
        self.height = 25
        self.row_height = 24

        self.use_header_box = True
        self.use_header = True
        self.header_text = header_text
        self.header_render = header_text
        self.header_text_size = header_text_size
        self.header_text_x = 0
        self.header_text_y = 0
        self.header_arrow_size = 8
        self.header_align = 'Center'
        self.text_align = 'Center'

        self.header_icon = None
        self.header_icon_pos = []
        self.header_icon_size = 0
        self.icon_margin = 0
        self.icon_separation = 5
        self.header_bar_offset = [0, 0]
        self.header_bar_width = 0
        self.header_bar_height = 18
        self.text_margin = 5
        self.margin = 5
        self.horizontal_margin = 0
        self.vert_margin = 5
        self.row_margin = 2
        self.row_separation = 1
        self.item_separation = 2
        self.panel_y_pos = 0
        self.arrow_width = 10

        self.visible = True
        self.collapse = False
        self.hover = False
        self.header_hover = False
        self.hov_highlight = False

        self.color_bg = [0.1, 0.1, 0.1, 0.5]
        self.color_button = [0.25, 0.25, 0.27, 1.0]
        self.color_click = [0.5, 0.5, 0.5, 1.0]
        self.color_button_part = [0.35, 0.35, 0.35, 1.0]
        self.color_slider_perc = [0.35, 0.35, 0.55, 1.0]
        self.color_slider_hov = [0.45, 0.45, 0.45, 1.0]
        self.color_arrows = [0.9, 0.9, 0.9, 1.0]
        self.color_outline = [0.6, 0.6, 0.6, 0.5]
        self.color_text = [1.0, 1.0, 1.0, 1.0]
        self.color_button_hov = [0.45, 0.45, 0.75, 1.0]
        self.color_header_text = [1.0, 1.0, 1.0, 1.0]
        self.color_header_bar = [0.3, 0.3, 0.32, 1.0]
        self.color_header_hov = [0.5, 0.5, 0.5, 1.0]
        self.color_set = [0.6, 0.6, 0.7, 1.0]

        self.font_id = 0
        self.font_size = 12

        self.bevel_size = 0
        self.bevel_res = 0

        self.header_bevel_size = 0
        self.header_bevel_res = 0

        self.button_bevel_size = 4
        self.button_bevel_res = 1

        return

    def init_shape_data(self):
        self.arrow_right_cos = []
        self.arrow_dwn_cos = []
        self.box_points = []
        self.box_tris = []
        self.box_lines = []
        self.header_points = []
        self.header_tris = []
        self.header_lines = []
        return

    def create_shape_data(self, y_pos, margin, p_width, align):
        self.init_shape_data()

        self.position = [margin, -y_pos]

        total_height = 0
        total_height += self.margin
        if self.use_header:
            # HEADERBAR SIZE CALC
            self.header_bar_width = self.width - self.margin*2
            total_height += self.header_bar_height
            # HEADER ARROW CREATION
            arrow_gap = round(
                (self.header_bar_height - self.header_arrow_size)/2)
            self.arrow_right_cos = [[self.margin, -arrow_gap], [self.margin+self.header_arrow_size, -
                                                                arrow_gap-round(self.header_arrow_size/2)], [self.margin, -self.header_bar_height+arrow_gap]]
            self.arrow_dwn_cos = [[self.margin, -arrow_gap], [self.margin+self.header_arrow_size, -arrow_gap], [
                self.margin+round(self.header_arrow_size/2), -self.header_bar_height+arrow_gap]]

            arrow_width = self.margin + self.header_arrow_size
            del(arrow_gap)
            # CHECK TEXT FIT HEADER BAR
            self.header_render = fit_text(self.header_text, self.header_text_size,
                                          self.font_id, self.header_bar_width-arrow_width-self.text_margin)
            text_width, text_height = calc_text_size(
                self.header_render, self.header_text_size, self.font_id)

            # FIND TEXT POSITION INSIDE HEADER
            self.header_text_x, self.header_text_y = place_text_in_box(self.header_align, self.header_bar_height, self.width-self.margin *
                                                                       3-self.header_arrow_size, self.text_margin, text_height, text_width, self.header_render, x_offset=self.header_arrow_size)

            del(text_height)
            del(text_width)
            del(arrow_width)

            total_height += self.margin
        self.panel_y_pos = total_height

        end_height = total_height
        # ADD SUBPANEL HEIGHTS TO TOTAL
        for row in self.rows:
            row.create_shape_data(self.panel_y_pos, self.margin)

            total_height += row.height
            total_height += self.row_separation
            self.panel_y_pos = total_height
        if len(self.rows) > 0:
            total_height -= self.row_separation

        total_height += self.margin

        if self.collapse == False:
            end_height = total_height
        self.height = round(end_height)

        if 'L' in align:
            self.position[0] = margin
        elif 'R' in align:
            self.position[0] = -p_width+margin
        elif 'C' in align:
            self.position[0] = round(-p_width/2)+margin

        if 'T' in align:
            self.position[1] = -y_pos
        elif 'B' in align:
            self.position[1] = y_pos+self.height

        self.header_bar_offset = [self.margin, -self.margin]
        self.box_points, self.box_tris, self.box_lines = calc_box(
            0, 0, self.width, self.height, [], self.bevel_size, self.bevel_res)
        if self.use_header:
            self.header_points, self.header_tris, self.header_lines = calc_box(
                0, 0, self.header_bar_width, self.header_bar_height, [], self.header_bevel_size, self.header_bevel_res)

        del(end_height)
        del(total_height)

        return

    def update_position(self, p_pos):
        x_co = p_pos[0]+self.position[0]
        y_co = p_pos[1]+self.position[1]

        box_points = draw_cos_offset(x_co, y_co, self.box_points)
        box_lines = draw_cos_offset(x_co, y_co, self.box_lines)
        header_points = draw_cos_offset(
            x_co+self.header_bar_offset[0], y_co+self.header_bar_offset[1], self.header_points)
        header_lines = draw_cos_offset(
            x_co+self.header_bar_offset[0], y_co+self.header_bar_offset[1], self.header_lines)

        self.batch_bg = batch_for_shader(
            self.shader, 'TRIS', {"pos": box_points}, indices=self.box_tris)
        self.batch_header = batch_for_shader(
            self.shader, 'TRIS', {"pos": header_points}, indices=self.header_tris)
        self.batch_header_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": header_lines})

        arrow_right_cos = draw_cos_offset(
            x_co+self.header_bar_offset[0], y_co+self.header_bar_offset[1], self.arrow_right_cos)
        arrow_dwn_cos = draw_cos_offset(
            x_co+self.header_bar_offset[0], y_co+self.header_bar_offset[1], self.arrow_dwn_cos)
        self.batch_arrow_right = batch_for_shader(
            self.shader, 'TRIS', {"pos": arrow_right_cos}, indices=[[0, 1, 2]])
        self.batch_arrow_down = batch_for_shader(
            self.shader, 'TRIS', {"pos": arrow_dwn_cos}, indices=[[0, 1, 2]])

        for row in self.rows:
            row.update_position([x_co, y_co])

        del(x_co)
        del(y_co)
        del(box_points)
        del(box_lines)
        del(header_points)
        del(header_lines)

        return

    def toggle_collapse(self):
        self.collapse = not self.collapse
        return

    def draw(self, position):
        if self.visible:
            pos = [position[0]+self.position[0], position[1]+self.position[1]]
            # DRAW SUBPANEL BG BOX
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_bg)
            self.batch_bg.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            if self.use_header:
                # ##DRAW SUBPANEL HEADER BOX
                # if self.hov_highlight and self.header_hover or self.use_header_box:
                #     bgl.glEnable(bgl.GL_BLEND)
                #     self.shader.bind()
                #     if self.hov_highlight and self.header_hover:
                #         self.shader.uniform_float("color", self.color_header_hov)
                #     else:
                #         self.shader.uniform_float("color", self.color_header_bar)
                #     self.batch_header.draw(self.shader)
                #     bgl.glDisable(bgl.GL_BLEND)

                # if self.use_header_box:
                #     ##DRAW SUBPANEL HEADER OUTLINE
                #     bgl.glEnable(bgl.GL_BLEND)
                #     self.shader.bind()
                #     self.shader.uniform_float("color", self.color_outline)
                #     self.batch_header_lines.draw(self.shader)
                #     bgl.glDisable(bgl.GL_BLEND)

                # DRAW SUBPANEL HEADER TEXT IF IT IS SET
                if self.header_text != '':
                    blf.position(self.font_id, pos[0]+self.header_text_x+self.header_bar_offset[0],
                                 pos[1]+self.header_text_y+self.header_bar_offset[1], 0)
                    blf.color(
                        self.font_id, self.color_header_text[0], self.color_header_text[1], self.color_header_text[2], self.color_header_text[3])
                    blf.size(self.font_id, int(self.header_text_size), 72)
                    blf.draw(self.font_id, self.header_render)

            if self.collapse == False:
                for row in self.rows:
                    if self.collapse == False:
                        row.draw(pos)
                arrow_batch = self.batch_arrow_down
            else:
                arrow_batch = self.batch_arrow_right

            if self.use_header:
                # DRAW SUBPANEL ARROW
                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_arrows)
                arrow_batch.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

                del(pos)

        return

    def add_row(self):
        row = UIRow(self.shader, self.icon_shader, len(self.rows), self.width-self.margin*2, self.row_height,
                    [self.position[0]+self.margin, self.position[1]-self.panel_y_pos-self.row_separation])

        row.visible = self.visible
        row.hov_highlight = self.hov_highlight
        row.item_separation = self.item_separation

        row.color_bg = self.color_bg
        row.color_outline = self.color_outline
        row.color_button = self.color_button
        row.color_button_hov = self.color_button_hov
        row.color_slider_perc = self.color_slider_perc
        row.color_slider_hov = self.color_slider_hov
        row.color_click = self.color_click
        row.color_button_part = self.color_button_part
        row.color_arrows = self.color_arrows
        row.color_text = self.color_text
        row.color_set = self.color_set

        row.font_id = self.font_id
        row.font_size = self.font_size

        row.text_align = self.text_align
        row.text_margin = self.text_margin
        row.margin = self.row_margin

        row.arrow_width = self.arrow_width

        row.bevel_size = self.bevel_size
        row.bevel_res = self.bevel_res

        row.button_bevel_size = self.button_bevel_size
        row.button_bevel_res = self.button_bevel_res

        row.init_shape_data()

        self.rows.append(row)

        return row

    def add_text_row(self, text, size):
        row = UIRow(self.shader, self.icon_shader, len(self.rows), self.width-self.margin*2, self.row_height,
                    [self.position[0]+self.margin, self.position[1]-self.panel_y_pos-self.row_separation])
        row.font_size = size
        row.draw_backdrop = False

        row.visible = self.visible
        row.hov_highlight = False
        row.item_separation = self.item_separation

        row.color_bg = self.color_bg
        row.color_outline = self.color_outline
        row.color_button = self.color_button
        row.color_slider_perc = self.color_slider_perc
        row.color_slider_hov = self.color_slider_hov
        row.color_click = self.color_click
        row.color_button_part = self.color_button_part
        row.color_arrows = self.color_arrows
        row.color_text = self.color_text
        row.color_button_hov = self.color_button_hov
        row.color_set = self.color_set

        row.font_id = self.font_id

        row.text_align = self.text_align
        row.text_margin = self.text_margin
        row.margin = self.row_margin

        row.arrow_width = self.arrow_width

        row.bevel_size = self.bevel_size
        row.bevel_res = self.bevel_res

        row.button_bevel_size = self.button_bevel_size
        row.button_bevel_res = self.button_bevel_res

        row.init_shape_data()

        text_width, text_height = calc_text_size(text, size, row.font_id)
        row.height = text_height + row.margin*2
        label = row.add_label(text)

        label.init_shape_data()

        self.rows.append(row)

        return

    def clear_rows(self):
        self.rows.clear()

    def __str__(self, ):
        return 'UI Subpanel'


class UIRow:
    def __init__(self, shader, icon_shader, index, width, height, position):
        self.shader = shader
        self.icon_shader = icon_shader
        self.items = []
        self.index = index
        self.position = round_array(position)
        self.visible = True
        self.hov_highlight = False
        self.row_backdrop = True
        self.item_separation = 2
        self.draw_backdrop = False

        self.width = round(width)
        self.height = round(height)

        self.text_align = 'Center'
        self.text_margin = 5
        self.margin = 5
        self.arrow_width = 10
        self.color_bg = [0.1, 0.1, 0.1, 0.5]
        self.color_button = [0.25, 0.25, 0.27, 1.0]
        self.color_click = [0.5, 0.5, 0.5, 1.0]
        self.color_button_part = [0.35, 0.35, 0.35, 1.0]
        self.color_slider_perc = [0.35, 0.35, 0.55, 1.0]
        self.color_slider_hov = [0.45, 0.45, 0.45, 1.0]
        self.color_arrows = [0.9, 0.9, 0.9, 1.0]
        self.color_outline = [0.6, 0.6, 0.6, 0.5]
        self.color_text = [1.0, 1.0, 1.0, 1.0]
        self.color_button_hov = [0.45, 0.45, 0.75, 1.0]
        self.color_set = [0.6, 0.6, 0.7, 1.0]

        self.font_id = 0
        self.font_size = 12

        self.bevel_size = 0
        self.bevel_res = 0

        self.button_bevel_size = 4
        self.button_bevel_res = 1

        return

    def init_shape_data(self):
        self.box_points = []
        self.box_tris = []
        self.box_lines = []
        return

    def create_shape_data(self, y_pos, margin):
        self.init_shape_data()

        self.position = [margin, -y_pos]
        # FIND BIGGEST HEIGHT FOR ROW
        x_co = self.margin
        for item in self.items:
            item.create_shape_data(self.margin, x_co)
            x_co += item.width
            x_co += self.item_separation

        self.box_points, self.box_tris, self.box_lines = calc_box(
            0, 0, self.width, self.height, [], self.bevel_size, self.bevel_res)

        del(x_co)

        return

    def update_position(self, p_pos):
        x_co = p_pos[0]+self.position[0]
        y_co = p_pos[1]+self.position[1]

        box_points = draw_cos_offset(x_co, y_co, self.box_points)
        box_lines = draw_cos_offset(x_co, y_co, self.box_lines)

        for item in self.items:
            item.update_position([x_co, y_co])
        self.batch_bg = batch_for_shader(
            self.shader, 'TRIS', {"pos": box_points}, indices=self.box_tris)
        self.batch_bg_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": box_lines})

        del(x_co)
        del(y_co)
        del(box_points)
        del(box_lines)

        return

    def draw(self, position):
        if self.visible:
            if self.draw_backdrop:
                # DRAW ROW BG BOX
                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_bg)
                self.batch_bg.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

                # DRAW ROW BG OUTLINE
                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                bgl.glLineWidth(1)
                self.shader.uniform_float("color", self.color_outline)
                self.batch_bg_lines.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

            pos = [position[0]+self.position[0], position[1]+self.position[1]]
            for item in self.items:
                item.draw(pos)
            del(pos)

        return

    def add_button(self, id, text):
        width_tot = self.width - self.margin*2
        width_tot -= (len(self.items)) * self.item_separation
        width = width_tot/(len(self.items)+1)

        but = UIButton(self.shader, self.icon_shader, len(
            self.items), id, text, width, self.height-self.margin*2, [self.margin, -self.margin])

        x_pos = self.margin
        for item in self.items:
            item.position[0] = x_pos
            item.position[1] = -self.margin
            item.width = width
            x_pos += width
            x_pos += self.item_separation

        but.visible = self.visible
        but.hov_highlight = self.hov_highlight

        but.color_button = self.color_button
        but.color_click = self.color_click
        but.color_text = self.color_text
        but.color_button_hov = self.color_button_hov
        but.color_set = self.color_set

        but.font_id = self.font_id
        but.font_size = self.font_size

        but.text_align = self.text_align
        but.text_margin = self.text_margin

        but.bevel_size = self.button_bevel_size
        but.bevel_res = self.button_bevel_res

        but.init_shape_data()

        self.items.append(but)
        return but

    def add_label(self, text):
        width_tot = self.width - self.margin*2
        width_tot -= (len(self.items)) * self.item_separation
        width = width_tot/(len(self.items)+1)

        label = UILabel(self.shader, self.icon_shader, len(
            self.items), text, width, self.height-self.margin*2, [self.margin, -self.margin])

        x_pos = self.margin
        for item in self.items:
            item.position[0] = x_pos
            item.position[1] = -self.margin
            item.width = width
            x_pos += width
            x_pos += self.item_separation

        label.visible = self.visible

        label.color_text = self.color_text

        label.font_id = self.font_id
        label.font_size = self.font_size

        label.text_align = self.text_align
        label.text_margin = self.text_margin

        label.init_shape_data()

        self.items.append(label)
        return label

    def add_bool_prop(self, id, text, box_size, default):
        width_tot = self.width - self.margin*2
        width_tot -= (len(self.items)) * self.item_separation
        width = width_tot/(len(self.items)+1)

        boolean = UIBoolProp(self.shader, self.icon_shader, len(self.items), id, text,
                             box_size, default, width, self.height-self.margin*2, [self.margin, -self.margin])

        x_pos = self.margin
        for item in self.items:
            item.position[0] = x_pos
            item.position[1] = -self.margin
            item.width = width
            x_pos += width
            x_pos += self.item_separation

        boolean.visible = self.visible
        boolean.hov_highlight = self.hov_highlight

        boolean.color_button = self.color_button
        boolean.color_click = self.color_click
        boolean.color_button_part = self.color_button_part
        boolean.color_arrows = self.color_arrows
        boolean.color_text = self.color_text
        boolean.color_button_hov = self.color_button_hov
        boolean.color_set = self.color_set

        boolean.font_id = self.font_id
        boolean.font_size = self.font_size

        boolean.text_margin = self.text_margin

        boolean.bevel_size = self.button_bevel_size
        boolean.bevel_res = self.button_bevel_res

        boolean.init_shape_data()

        self.items.append(boolean)
        return boolean

    def add_num_prop(self, id, text, num, decimals, factor, min_val, max_val):
        width_tot = self.width - self.margin*2
        width_tot -= (len(self.items)) * self.item_separation
        width = width_tot/(len(self.items)+1)

        num = UINumProp(self.shader, self.icon_shader, len(self.items), id, text, num, int(
            decimals), factor, min_val, max_val, width, self.height-self.margin*2, [self.margin, -self.margin])

        x_pos = self.margin
        for item in self.items:
            item.position[0] = x_pos
            item.position[1] = -self.margin
            item.width = width
            x_pos += width
            x_pos += self.item_separation

        num.visible = self.visible
        num.hov_highlight = self.hov_highlight

        num.color_button = self.color_button
        num.color_slider_perc = self.color_slider_perc
        num.color_slider_hov = self.color_slider_hov
        num.color_click = self.color_click
        num.color_button_part = self.color_button_part
        num.color_arrows = self.color_arrows
        num.color_text = self.color_text
        num.color_button_hov = self.color_button_hov
        num.color_set = self.color_set

        num.arrow_width = self.arrow_width

        num.font_id = self.font_id
        num.font_size = self.font_size

        num.text_margin = self.text_margin

        num.bevel_size = self.button_bevel_size
        num.bevel_res = self.button_bevel_res

        num.init_shape_data()

        self.items.append(num)
        return num

    def __str__(self, ):
        return 'UI Row'


class UILabel:
    def __init__(self, shader, icon_shader, index, text, width, height, position):
        self.shader = shader
        self.icon_shader = icon_shader

        self.id = id
        self.index = index
        self.position = round_array(position)
        self.width = round(width)
        self.height = round(height)
        self.text = text
        self.text_render = text
        self.text_align = 'Center'
        self.text_margin = 5
        self.type = 'LABEL'
        self.visible = True

        self.text_x = 0
        self.text_y = 0

        self.icon = None
        self.icon_align = 'Left'
        self.icon_size = 0
        self.icon_margin = 0
        self.icon_separation = 5

        self.color_text = [1.0, 1.0, 1.0, 1.0]

        self.font_id = 0
        self.font_size = 12
        return

    def init_shape_data(self):
        self.icon_pos = []
        return

    def create_shape_data(self, y_pos, margin):
        self.init_shape_data()

        self.position = [margin, -y_pos]
        offset = 0
        if self.icon != None:
            self.icon_size = self.height-self.icon_margin*2
            offset = self.icon_size
            if self.text != '':
                offset += self.icon_separation*2

        # CHECK TEXT FIT
        self.text_render = fit_text(
            self.text, self.font_size, self.font_id, self.width-self.text_margin-offset)
        text_width, text_height = calc_text_size(
            self.text_render, self.font_size, self.font_id)

        label_width = text_width
        if self.icon != None:
            label_width = text_width + offset

        self.text_x, self.text_y = place_text_in_box(
            self.text_align, self.height, self.width, self.text_margin, text_height, label_width, self.text_render, x_offset=offset)

        if self.icon != None:
            self.icon_pos.append(
                [self.text_x-offset, -self.height+self.icon_margin])
            self.icon_pos.append(
                [self.text_x-offset+self.icon_size, -self.height+self.icon_margin])
            self.icon_pos.append(
                [self.text_x-offset+self.icon_size, -self.icon_margin])
            self.icon_pos.append([self.text_x-offset, -self.icon_margin])

        del(label_width)
        del(text_width)
        del(text_height)

        return

    def update_position(self, p_pos):
        x_co = p_pos[0] + self.position[0]
        y_co = p_pos[1] + self.position[1]
        if self.icon != None:
            icon_pos = draw_cos_offset(x_co, y_co, self.icon_pos)
            tex_cos = [[0, 0], [1, 0], [1, 1], [0, 1]]
            self.batch_icon = batch_for_shader(self.icon_shader, 'TRI_FAN', {
                                               "pos": icon_pos, "texCoord": tex_cos})

        return

    def draw(self, position):
        if self.visible == True:
            # DRAW TEXT IF IT IS SET
            pos = [position[0]+self.position[0], position[1]+self.position[1]]
            if self.text_render != '':
                blf.position(
                    self.font_id, pos[0]+self.text_x, pos[1]+self.text_y, 0)
                blf.color(
                    self.font_id, self.color_text[0], self.color_text[1], self.color_text[2], self.color_text[3])
                blf.size(self.font_id, int(self.font_size), 72)
                blf.draw(self.font_id, self.text_render)

            if self.icon != None:
                if self.icon.gl_load():
                    raise Exception()

                bgl.glEnable(bgl.GL_BLEND)
                bgl.glActiveTexture(bgl.GL_TEXTURE0)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.icon.bindcode)

                self.icon_shader.bind()
                self.icon_shader.uniform_int("image", 0)
                self.batch_icon.draw(self.icon_shader)
                bgl.glDisable(bgl.GL_BLEND)

            del(pos)
        return

    def __str__(self, ):
        return 'UI Row Label'


class UINumProp:
    def __init__(self, shader, icon_shader, index, id, text, value, decimals, factor, min_val, max_val, width, height, position):
        self.shader = shader
        self.icon_shader = icon_shader

        self.id = id
        self.index = index
        self.position = round_array(position)
        self.width = round(width)
        self.height = round(height)
        self.text = text
        self.text_render = text
        self.text_align = 'Center'
        self.text_margin = 5

        self.hover = False
        self.left_hover = False
        self.right_hover = False
        self.bar_hover = False

        self.draw_arrows = True

        self.value = value
        self.decimals = decimals
        self.change_factor = factor
        self.min = min_val
        self.max = max_val

        self.box_arrow_size = self.height
        self.arrow_width = 8
        self.type = 'NUMBER'
        self.visible = True
        self.hov_highlight = True

        self.text_x = 0
        self.text_y = 0

        self.bevel_size = 0
        self.bevel_res = 0

        self.color_button = [0.25, 0.25, 0.27, 1.0]
        self.color_slider_perc = [0.35, 0.35, 0.55, 1.0]
        self.color_slider_hov = [0.45, 0.45, 0.45, 1.0]
        self.color_click = [0.5, 0.5, 0.5, 1.0]
        self.color_button_part = [0.35, 0.35, 0.35, 1.0]
        self.color_arrows = [0.9, 0.9, 0.9, 1.0]
        self.color_text = [1.0, 1.0, 1.0, 1.0]
        self.color_button_hov = [0.45, 0.45, 0.75, 1.0]
        self.color_set = [0.6, 0.6, 0.7, 1.0]

        self.font_id = 0
        self.font_size = 12
        return

    def init_shape_data(self):
        self.box_points = []
        self.box_tris = []
        self.box_lines = []
        self.prec_points = []
        self.perc_tris = []
        self.perc_lines = []
        self.box_right_points = []
        self.box_right_tris = []
        self.box_right_lines = []
        self.box_left_points = []
        self.box_left_tris = []
        self.box_left_lines = []
        self.arrow_left_lines = []
        self.arrow_right_lines = []
        return

    def create_shape_data(self, y_pos, margin):
        self.init_shape_data()

        self.position = [margin, -y_pos]
        if self.max-self.min == 0:
            perc = 1.0
        else:
            perc = (self.value-self.min)/(self.max-self.min)
        if self.height*3 < self.width:
            self.box_arrow_size = self.height
            self.box_points, self.box_tris, self.box_lines = calc_box(
                0, 0, self.width-self.box_arrow_size*2, self.height, [], 0, 0)
            self.perc_points, self.perc_tris, self.perc_lines = calc_box(
                0, 0, (self.width-self.box_arrow_size*2)*perc, self.height, [], 0, 0)
        else:
            self.box_arrow_size = round(self.width/3)
            self.box_points, self.box_tris, self.box_lines = calc_box(
                0, 0, self.box_arrow_size, self.height, [], 0, 0)
            self.perc_points, self.perc_tris, self.perc_lines = calc_box(
                0, 0, self.box_arrow_size*perc, self.height, [], 0, 0)

        # CHECK TEXT FIT HEADER BAR
        self.text_render = fit_text(self.text, self.font_size, self.font_id,
                                    self.width-self.box_arrow_size*2-self.text_margin, value=str(self.value))
        text_width, text_height = calc_text_size(
            self.text_render, self.font_size, self.font_id)
        self.text_x, self.text_y = place_text_in_box(self.text_align, self.height, self.width-self.box_arrow_size*2,
                                                     self.text_margin, text_height, text_width, self.text_render, x_offset=self.box_arrow_size)

        self.box_right_points, self.box_right_tris, self.box_right_lines = calc_box(
            0, 0, self.box_arrow_size, self.height, [1, 2], self.bevel_size, self.bevel_res)
        self.box_left_points, self.box_left_tris, self.box_left_lines = calc_box(
            0, 0, self.box_arrow_size, self.height, [0, 3], self.bevel_size, self.bevel_res)

        self.arrow_left_lines = []
        self.arrow_right_lines = []
        if self.box_arrow_size > self.arrow_width:
            y_gap = round((self.height - self.arrow_width)/2)
            x_gap = round((self.box_arrow_size - self.arrow_width)/2)
            self.arrow_left_lines = [[self.box_arrow_size-x_gap, -y_gap], [
                x_gap, round(-self.height/2)], [self.box_arrow_size-x_gap, -self.height+y_gap], ]
            self.arrow_right_lines = [[x_gap, -y_gap], [self.box_arrow_size -
                                                        x_gap, round(-self.height/2)], [x_gap, -self.height+y_gap], ]

            del(y_gap)
            del(x_gap)
        else:
            self.arrow_lines = []

        del(perc)
        del(text_width)
        del(text_height)

        return

    def update_position(self, p_pos):
        x_co = p_pos[0]+self.position[0]
        y_co = p_pos[1]+self.position[1]

        box_points = draw_cos_offset(
            x_co+self.box_arrow_size, y_co, self.box_points)
        box_lines = draw_cos_offset(
            x_co+self.box_arrow_size, y_co, self.box_lines)
        perc_points = draw_cos_offset(
            x_co+self.box_arrow_size, y_co, self.perc_points)
        perc_lines = draw_cos_offset(
            x_co+self.box_arrow_size, y_co, self.perc_lines)

        bool_left_points = draw_cos_offset(x_co, y_co, self.box_left_points)
        bool_right_points = draw_cos_offset(
            x_co+self.width-self.box_arrow_size, y_co, self.box_right_points)
        bool_left_lines = draw_cos_offset(x_co, y_co, self.box_left_lines)
        bool_right_lines = draw_cos_offset(
            x_co+self.width-self.box_arrow_size, y_co, self.box_right_lines)

        arrow_left_lines = draw_cos_offset(x_co, y_co, self.arrow_left_lines)
        arrow_right_lines = draw_cos_offset(
            x_co+self.width-self.box_arrow_size, y_co, self.arrow_right_lines)

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": box_points}, indices=self.box_tris)
        self.batch_perc = batch_for_shader(
            self.shader, 'TRIS', {"pos": perc_points}, indices=self.perc_tris)

        self.batch_bool_left = batch_for_shader(
            self.shader, 'TRIS', {"pos": bool_left_points}, indices=self.box_left_tris)
        self.batch_bool_right = batch_for_shader(
            self.shader, 'TRIS', {"pos": bool_right_points}, indices=self.box_right_tris)

        if len(arrow_left_lines) == 0 or len(arrow_right_lines) == 0:
            self.draw_arrows = False
        else:
            self.draw_arrows = True

        self.batch_arrow_left = batch_for_shader(
            self.shader, 'TRIS', {"pos": arrow_left_lines}, indices=[[0, 1, 2]])
        self.batch_arrow_right = batch_for_shader(
            self.shader, 'TRIS', {"pos": arrow_right_lines}, indices=[[0, 1, 2]])

        del(x_co)
        del(y_co)
        del(box_points)
        del(box_lines)
        del(perc_points)
        del(perc_lines)
        del(bool_left_points)
        del(bool_right_points)
        del(arrow_left_lines)
        del(arrow_right_lines)
        del(bool_left_lines)
        del(bool_right_lines)

        return

    def update_slider(self, p_pos):
        x_co = p_pos[0]+self.position[0]
        y_co = p_pos[1]+self.position[1]

        if self.max-self.min == 0:
            perc = 1.0
        else:
            perc = (self.value-self.min)/(self.max-self.min)
        if self.height*3 < self.width:
            self.box_arrow_size = self.height
            self.box_points, self.box_tris, self.box_lines = calc_box(
                0, 0, self.width-self.box_arrow_size*2, self.height, [], 0, 0)
            self.perc_points, self.perc_tris, self.perc_lines = calc_box(
                0, 0, (self.width-self.box_arrow_size*2)*perc, self.height, [], 0, 0)
        else:
            self.box_arrow_size = round(self.width/3)
            self.box_points, self.box_tris, self.box_lines = calc_box(
                0, 0, self.box_arrow_size, self.height, [], 0, 0)
            self.perc_points, self.perc_tris, self.perc_lines = calc_box(
                0, 0, self.box_arrow_size*perc, self.height, [], 0, 0)

        # CHECK TEXT FIT HEADER BAR
        self.text_render = fit_text(self.text, self.font_size, self.font_id,
                                    self.width-self.box_arrow_size*2-self.text_margin, value=str(self.value))
        text_width, text_height = calc_text_size(
            self.text_render, self.font_size, self.font_id)
        self.text_x, self.text_y = place_text_in_box(self.text_align, self.height, self.width-self.box_arrow_size*2,
                                                     self.text_margin, text_height, text_width, self.text_render, x_offset=self.box_arrow_size)

        perc_points = draw_cos_offset(
            x_co+self.box_arrow_size, y_co, self.perc_points)
        perc_lines = draw_cos_offset(
            x_co+self.box_arrow_size, y_co, self.perc_lines)

        self.batch_perc = batch_for_shader(
            self.shader, 'TRIS', {"pos": perc_points}, indices=self.perc_tris)

        del(x_co)
        del(y_co)
        del(perc)
        del(perc_points)
        del(perc_lines)
        del(text_width)
        del(text_height)

        return

    def draw(self, position):
        if self.visible == True:
            # DRAW BUTTON
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            if self.hov_highlight and self.bar_hover:
                self.shader.uniform_float("color", self.color_slider_hov)
            else:
                self.shader.uniform_float("color", self.color_button)
            self.batch.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            # DRAW PERCENT BOX
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_slider_perc)
            self.batch_perc.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)
            # DRAW LEFT BOX
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            if self.hov_highlight and self.left_hover:
                self.shader.uniform_float("color", self.color_button_hov)
            else:
                self.shader.uniform_float("color", self.color_button_part)
            self.batch_bool_left.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            # DRAW RIGHT BOX
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            if self.hov_highlight and self.right_hover:
                self.shader.uniform_float("color", self.color_button_hov)
            else:
                self.shader.uniform_float("color", self.color_button_part)
            self.batch_bool_right.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            if self.draw_arrows:
                # DRAW ARROWS
                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_arrows)
                self.batch_arrow_left.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

                bgl.glEnable(bgl.GL_BLEND)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_arrows)
                self.batch_arrow_right.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

            # DRAW BUTTON TEXT IF IT IS SET
            pos = [position[0]+self.position[0], position[1]+self.position[1]]

            if self.text_render != '':
                blf.position(
                    self.font_id, pos[0]+self.text_x, pos[1]+self.text_y, 0)
                blf.color(
                    self.font_id, self.color_text[0], self.color_text[1], self.color_text[2], self.color_text[3])
                blf.size(self.font_id, int(self.font_size), 72)
                blf.draw(self.font_id, self.text_render)

            del(pos)
        return

    def __str__(self, ):
        return 'UI Row Number Prop'


class UIBoolProp:
    def __init__(self, shader, icon_shader, index, id, text, box_size, value, width, height, position):
        self.shader = shader
        self.icon_shader = icon_shader

        self.id = id
        self.index = index
        self.position = round_array(position)
        self.width = round(width)
        self.height = round(height)
        self.text = text
        self.text_render = text
        self.text_align = 'Center'
        self.text_margin = 5
        self.hover = False
        self.bool = value
        self.box_bool_size = round(box_size)
        self.type = 'BOOLEAN'
        self.visible = True
        self.hov_highlight = True

        self.position_bool = round_array(
            [(self.height-self.box_bool_size)/2, ((self.height-self.box_bool_size)/2)*-1])

        self.text_x = 0
        self.text_y = 0

        self.bevel_size = 0
        self.bevel_res = 0

        self.color_button = [0.25, 0.25, 0.27, 1.0]
        self.color_click = [0.5, 0.5, 0.5, 1.0]
        self.color_button_part = [0.35, 0.35, 0.35, 1.0]
        self.color_arrows = [0.9, 0.9, 0.9, 1.0]
        self.color_text = [1.0, 1.0, 1.0, 1.0]
        self.color_button_hov = [0.45, 0.45, 0.75, 1.0]
        self.color_set = [0.6, 0.6, 0.7, 1.0]

        self.font_id = 0
        self.font_size = 12
        return

    def init_shape_data(self):
        self.box_points = []
        self.box_tris = []
        self.box_lines = []
        self.box_bool_points = []
        self.box_bool_tris = []
        self.box_bool_lines = []
        self.bool_lines = []
        return

    def create_shape_data(self, y_pos, margin):
        self.init_shape_data()
        self.position = [margin, -y_pos]

        bool_marg = (self.height-self.box_bool_size)/2
        # CHECK TEXT FIT HEADER BAR
        self.text_render = fit_text(self.text, self.font_size, self.font_id,
                                    self.width-bool_marg-self.box_bool_size-self.text_margin)
        text_width, text_height = calc_text_size(
            self.text_render, self.font_size, self.font_id)
        self.text_x, self.text_y = place_text_in_box(self.text_align, self.height, self.width, self.text_margin,
                                                     text_height, text_width+bool_marg+self.box_bool_size, self.text_render, x_offset=bool_marg+self.box_bool_size)

        self.position_bool = round_array(
            [self.text_x-bool_marg-self.box_bool_size, -((self.height-self.box_bool_size)/2)])

        self.box_points, self.box_tris, self.box_lines = calc_box(
            0, 0, self.width, self.height, [], self.bevel_size, self.bevel_res)
        self.box_bool_points, self.box_bool_tris, self.box_bool_lines = calc_box(
            0, 0, self.box_bool_size, self.box_bool_size, [], 0, 0)
        self.bool_lines = [[2, -2], [self.box_bool_size-2, -self.box_bool_size+2],
                           [2, -self.box_bool_size+2], [self.box_bool_size-2, -2]]

        del(bool_marg)
        del(text_width)
        del(text_height)

        return

    def update_position(self, p_pos):
        x_co = p_pos[0]+self.position[0]
        y_co = p_pos[1]+self.position[1]
        x_bool_co = x_co+self.position_bool[0]
        y_bool_co = y_co+self.position_bool[1]

        box_points = draw_cos_offset(x_co, y_co, self.box_points)
        box_lines = draw_cos_offset(x_co, y_co, self.box_lines)
        box_bool_points = draw_cos_offset(
            x_bool_co, y_bool_co, self.box_bool_points)
        box_bool_lines = draw_cos_offset(
            x_bool_co, y_bool_co, self.box_bool_lines)
        bool_lines = draw_cos_offset(x_bool_co, y_bool_co, self.bool_lines)

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": box_points}, indices=self.box_tris)

        if self.box_bool_size > self.width:
            self.batch_bool_box = batch_for_shader(
                self.shader, 'TRIS', {"pos": []}, indices=[])
            self.batch_bool = batch_for_shader(
                self.shader, 'LINES', {"pos": []})
        else:
            self.batch_bool_box = batch_for_shader(
                self.shader, 'TRIS', {"pos": box_bool_points}, indices=self.box_bool_tris)
            self.batch_bool = batch_for_shader(
                self.shader, 'LINES', {"pos": bool_lines})

        del(x_co)
        del(y_co)
        del(box_points)
        del(box_lines)
        del(box_bool_points)
        del(box_bool_lines)
        del(bool_lines)

        return

    def draw(self, position):
        if self.visible == True:
            # DRAW BUTTON
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            self.shader.uniform_float("color", self.color_button)
            self.batch.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            # DRAW BOOL BOX
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            if self.hov_highlight and self.hover:
                self.shader.uniform_float("color", self.color_button_hov)
            else:
                self.shader.uniform_float("color", self.color_button_part)
            self.batch_bool_box.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            if self.bool:
                # DRAW BOOL LINES
                bgl.glEnable(bgl.GL_BLEND)
                bgl.glLineWidth(3)
                self.shader.bind()
                self.shader.uniform_float("color", self.color_arrows)
                self.batch_bool.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)

            # DRAW BUTTON TEXT IF IT IS SET
            pos = [position[0]+self.position[0], position[1]+self.position[1]]
            if self.text_render != '':
                blf.position(
                    self.font_id, pos[0]+self.text_x, pos[1]+self.text_y, 0)
                blf.color(
                    self.font_id, self.color_text[0], self.color_text[1], self.color_text[2], self.color_text[3])
                blf.size(self.font_id, int(self.font_size), 72)
                blf.draw(self.font_id, self.text_render)

            del(pos)
        return

    def __str__(self, ):
        return 'UI Row Boolean Prop'


class UIButton:
    def __init__(self, shader, icon_shader, index, id, text, width, height, position):
        self.shader = shader
        self.icon_shader = icon_shader

        self.id = id
        self.index = index
        self.position = round_array(position)
        self.width = round(width)
        self.height = round(height)
        self.text = text
        self.text_render = text
        self.text_align = 'Center'
        self.text_margin = 5
        self.hover = False
        self.bool = False
        self.type = 'BUTTON'
        self.visible = True
        self.hov_highlight = True

        self.text_x = 0
        self.text_y = 0

        self.icon = None
        self.icon_align = 'Left'

        self.bevel_size = 0
        self.bevel_res = 0

        self.color_button = [0.25, 0.25, 0.27, 1.0]
        self.color_click = [0.5, 0.5, 0.5, 1.0]
        self.color_text = [1.0, 1.0, 1.0, 1.0]
        self.color_button_hov = [0.45, 0.45, 0.75, 1.0]
        self.color_set = [0.6, 0.6, 0.7, 1.0]

        self.font_id = 0
        self.font_size = 12
        return

    def init_shape_data(self):
        self.box_points = []
        self.box_tris = []
        self.box_lines = []
        return

    def create_shape_data(self, y_pos, margin):
        self.init_shape_data()

        self.position = [margin, -y_pos]
        # CHECK TEXT FIT HEADER BAR
        self.text_render = fit_text(
            self.text, self.font_size, self.font_id, self.width-self.text_margin)
        text_width, text_height = calc_text_size(
            self.text_render, self.font_size, self.font_id)
        self.text_x, self.text_y = place_text_in_box(
            self.text_align, self.height, self.width, self.text_margin, text_height, text_width, self.text_render)

        self.box_points, self.box_tris, self.box_lines = calc_box(
            0, 0, self.width, self.height, [], self.bevel_size, self.bevel_res)

        del(text_width)
        del(text_height)

        return

    def update_position(self, p_pos):
        x_co = p_pos[0]+self.position[0]
        y_co = p_pos[1]+self.position[1]

        box_points = draw_cos_offset(x_co, y_co, self.box_points)
        box_lines = draw_cos_offset(x_co, y_co, self.box_lines)
        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": box_points}, indices=self.box_tris)

        del(x_co)
        del(y_co)
        del(box_points)
        del(box_lines)

        return

    def draw(self, position):
        if self.visible == True:
            # DRAW BUTTON
            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            if self.hov_highlight and self.hover:
                self.shader.uniform_float("color", self.color_button_hov)
            else:
                self.shader.uniform_float("color", self.color_button)
            self.batch.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            # DRAW BUTTON TEXT IF IT IS SET
            pos = [position[0]+self.position[0], position[1]+self.position[1]]
            if self.text_render != '':
                blf.position(
                    self.font_id, pos[0]+self.text_x, pos[1]+self.text_y, 0)
                blf.color(
                    self.font_id, self.color_text[0], self.color_text[1], self.color_text[2], self.color_text[3])
                blf.size(self.font_id, int(self.font_size), 72)
                blf.draw(self.font_id, self.text_render)

            del(pos)
        return

    def __str__(self, ):
        return 'UI Row Button'


class UIGizmoContainer:
    def __init__(self, shader, index, mat, size, axis):
        self.shader = shader
        self.index = index
        self.gizmos = []
        self.matrix = mat
        self.scale_factor = None
        self.size = size

        return

    def update_size(self, size):
        self.size = size
        for giz in self.gizmos:
            giz.size = self.size
        return

    def create_shape_data(self, matrix):
        for gizmo in self.gizmos:
            gizmo.create_shape_data()

        self.update_position(matrix)
        return

    def update_position(self, matrix, ang=0):
        self.matrix = matrix
        self.scale_factor = None
        for gizmo in self.gizmos:
            self.scale_factor = gizmo.update_position(
                matrix, self.scale_factor, ang)
        return

    def update_rot(self, ang, start_ang):
        for gizmo in self.gizmos:
            if gizmo.in_use:
                gizmo.update_rot_fan(
                    self.matrix, self.scale_factor, ang, start_ang)
        return

    def update_orientation(self, matrix):
        self.matrix = matrix
        for gizmo in self.gizmos:
            gizmo.update_position(self.matrix, self.scale_factor)
        return

    def draw(self):
        for i in range(len(self.gizmos)):
            if self.gizmos[i*-1-1].active:
                self.gizmos[i*-1-1].draw()
        return


class UIRotateGizmo:
    def __init__(self, shader, index, size, scale, axis, giz_type, color, thickness=6):
        self.shader = shader
        self.index = index

        self.size = size
        self.scale = scale
        self.resolution = 36
        self.points = []
        self.mat_points = []
        self.axis = axis
        self.color = color
        self.active = True
        self.hover = False
        self.thickness = thickness
        self.type = giz_type
        self.in_use = False
        self.prev_screen_size = size

        return

    def test_hover(self, mouse_loc):
        region = bpy.context.region
        rv3d = bpy.context.region_data

        mouse_co = mathutils.Vector((mouse_loc[0], mouse_loc[1]))

        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0
        rcos = []
        for c, co in enumerate(self.mat_points):
            rco = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
            if rco == None:
                rcos.append(None)
                continue

            if c == 0:
                min_x = rco[0]
                max_x = rco[0]
                min_y = rco[1]
                max_y = rco[1]
            else:
                if rco[0] < min_x:
                    min_x = rco[0]
                if rco[0] > max_x:
                    max_x = rco[0]
                if rco[1] < min_y:
                    min_y = rco[1]
                if rco[1] > max_y:
                    max_y = rco[1]

            rcos.append(rco)

        self.hover = False
        if min_x < mouse_co[0] < max_x and min_y < mouse_co[1] < max_y:
            for tri in self.tris:
                co1 = rcos[tri[0]]
                co2 = rcos[tri[1]]
                co3 = rcos[tri[2]]

                if co1 == None or co2 == None or co3 == None:
                    continue

                vec1 = mouse_co - co1
                vec2 = mouse_co - co2
                vec3 = mouse_co - co3

                tri_vec1 = co2-co1
                tri_vec2 = co3-co1
                tri_vec3 = co2-co3

                t_ang = tri_vec1.angle_signed(tri_vec2)
                m_ang = tri_vec1.angle_signed(vec1)
                if t_ang < 0.0:
                    if m_ang < t_ang or m_ang > 0.0:
                        continue
                else:
                    if m_ang > t_ang or m_ang < 0.0:
                        continue

                t_ang = tri_vec3.angle_signed(-tri_vec2)
                m_ang = tri_vec3.angle_signed(vec3)
                if t_ang < 0.0:
                    if m_ang < t_ang or m_ang > 0.0:
                        continue
                else:
                    if m_ang > t_ang or m_ang < 0.0:
                        continue

                self.hover = True
                return self.hover

        return self.hover

    def init_shape_data(self):
        self.points = []
        self.tris = []
        self.mat_points = []
        self.fan_points = []
        self.fan_tris = []
        self.fan_lines = []
        self.mat_fan_points = []
        self.mat_fan_lines = []
        return

    def create_shape_data(self):
        self.init_shape_data()
        if self.resolution <= 12:
            self.resolution = 12
        ang = 360/self.resolution
        co1 = [0, (1+self.thickness/2)*self.scale]
        co2 = [0, 1*self.scale]
        co3 = [0, (1-self.thickness/2)*self.scale]
        co4 = [0, 1*self.scale]
        for i in range(self.resolution):
            new_co1 = rotate_2d([0, 0], co1, math.radians(ang*i)).to_3d()
            new_co2 = rotate_2d([0, 0], co2, math.radians(ang*i)).to_3d()
            new_co3 = rotate_2d([0, 0], co3, math.radians(ang*i)).to_3d()
            new_co4 = rotate_2d([0, 0], co4, math.radians(ang*i)).to_3d()

            new_co2[2] += self.thickness/2*self.scale
            new_co4[2] -= self.thickness/2*self.scale

            new_co1 *= .01
            new_co2 *= .01
            new_co3 *= .01
            new_co4 *= .01

            if self.axis == 0:
                self.points.append(new_co1.zyx)
                self.points.append(new_co2.zyx)
                self.points.append(new_co3.zyx)
                self.points.append(new_co4.zyx)
            if self.axis == 1:
                self.points.append(new_co1.xzy)
                self.points.append(new_co2.xzy)
                self.points.append(new_co3.xzy)
                self.points.append(new_co4.xzy)
            if self.axis == 2:
                self.points.append(new_co1)
                self.points.append(new_co2)
                self.points.append(new_co3)
                self.points.append(new_co4)

            if i < self.resolution-1:
                self.tris += [
                    [i*4+1, i*4, i*4+4], [i*4+1, i*4+4, i*4+5], [i *
                                                                 4+2, i*4+1, i*4+5], [i*4+2, i*4+5, i*4+6],
                    [i*4+3, i*4+2, i*4+6], [i*4+3, i*4+6, i*4 +
                                            7], [i*4, i*4+3, i*4+7], [i*4, i*4+7, i*4+4]
                ]
            else:
                self.tris += [
                    [i*4+1, i*4, 0], [i*4+1, 0, 1], [i *
                                                     4+2, i*4+1, 1], [i*4+2, 1, 2],
                    [i*4+3, i*4+2, 2], [i*4+3, 2, 7], [i*4, i*4+3, 7], [i*4, 3, 0]
                ]

        ang = 180/(int(self.resolution/2)-1)
        co = [0, 1*self.scale]
        self.fan_points.append(mathutils.Vector((0, 0, 0)))
        for i in range(int(self.resolution/2)+1):
            new_co = rotate_2d([0, 0], co, math.radians(ang*i)).to_3d()
            new_co *= .01

            if self.axis == 0:
                self.fan_points.append(new_co.zyx)
            if self.axis == 1:
                self.fan_points.append(new_co.xzy)
            if self.axis == 2:
                self.fan_points.append(new_co)

            if i < int(self.resolution/2):
                self.fan_tris.append([0, i+1, i+2])

        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[1])
        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[-1])
        return

    def update_position(self, matrix, scale_fac, angle=0):
        region = bpy.context.region
        rv3d = bpy.context.region_data

        self.mat_points.clear()
        for p in range(len(self.points)):
            self.mat_points.append(matrix @ self.points[p])

        if scale_fac == None:
            region = bpy.context.region
            rv3d = bpy.context.region_data

            min_x = 0
            max_x = 0
            min_y = 0
            max_y = 0
            for c, co in enumerate(self.mat_points):
                rco = view3d_utils.location_3d_to_region_2d(region, rv3d, co)
                if rco == None:
                    continue

                if c == 0:
                    min_x = rco[0]
                    max_x = rco[0]
                    min_y = rco[1]
                    max_y = rco[1]
                else:
                    if rco[0] < min_x:
                        min_x = rco[0]
                    if rco[0] > max_x:
                        max_x = rco[0]
                    if rco[1] < min_y:
                        min_y = rco[1]
                    if rco[1] > max_y:
                        max_y = rco[1]

            height = max_y - min_y
            width = max_x - min_x

            if height > width:
                max_size = height
            else:
                max_size = width

            if max_size == 0:
                max_size = self.prev_screen_size

            self.prev_screen_size = max_size
            max_size += 1

            scale_fac = self.size/max_size

        self.mat_points.clear()
        for p in range(len(self.points)):
            co = matrix @ (self.points[p]*scale_fac)
            self.mat_points.append(co)

        self.batch = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_points}, indices=self.tris)

        self.update_rot_fan(matrix, scale_fac, angle)
        return scale_fac

    def update_rot_fan(self, matrix, scale_fac, angle, start_ang=0):
        region = bpy.context.region
        rv3d = bpy.context.region_data

        if self.resolution <= 12:
            self.resolution = 12

        point_per_rot = int(360/(self.resolution/2))
        rotations = int(math.degrees(abs(angle))/360)
        point_num = point_per_rot*(rotations+1)
        ang = angle/point_num

        co = [0, 1*self.scale]
        self.fan_points.clear()
        self.fan_tris.clear()
        self.fan_points.append(mathutils.Vector((0, 0, 0)))
        for i in range(point_num+1):
            new_co = rotate_2d([0, 0], co, ang*i+start_ang).to_3d()
            new_co *= .01

            if self.axis == 0:
                eul = mathutils.Euler(
                    (math.radians(90.0), 0.0, math.radians(90.0)), 'XYZ')
                new_co.rotate(eul)
                self.fan_points.append(new_co)
            if self.axis == 1:
                eul = mathutils.Euler((math.radians(90.0), 0.0, 0.0), 'XYZ')
                new_co.rotate(eul)
                self.fan_points.append(new_co)
            if self.axis == 2:
                self.fan_points.append(new_co)

            if i < point_num:
                self.fan_tris.append([0, i+1, i+2])

        self.fan_lines.clear()
        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[1])
        self.fan_lines.append(self.fan_points[0])
        self.fan_lines.append(self.fan_points[-1])

        self.mat_fan_points.clear()
        for p in range(len(self.fan_points)):
            self.mat_fan_points.append(matrix @ (self.fan_points[p]*scale_fac))

        self.mat_fan_lines.clear()
        for p in range(len(self.fan_lines)):
            self.mat_fan_lines.append(matrix @ (self.fan_lines[p]*scale_fac))

        self.batch_fan = batch_for_shader(
            self.shader, 'TRIS', {"pos": self.mat_fan_points}, indices=self.fan_tris)
        self.batch_fan_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": self.mat_fan_lines})

        return

    def draw(self):
        if self.active:
            if self.in_use:
                bgl.glEnable(bgl.GL_BLEND)
                # bgl.glEnable(bgl.GL_DEPTH_TEST)
                self.shader.bind()
                self.shader.uniform_float(
                    "color", [self.color[0], self.color[1], self.color[2], 0.2])
                self.batch_fan.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)
                # bgl.glDisable(bgl.GL_DEPTH_TEST)

                bgl.glEnable(bgl.GL_BLEND)
                # bgl.glEnable(bgl.GL_DEPTH_TEST)
                self.shader.bind()
                self.shader.uniform_float("color", [1.0, 1.0, 1.0, 1.0])
                self.batch_fan_lines.draw(self.shader)
                bgl.glDisable(bgl.GL_BLEND)
                # bgl.glDisable(bgl.GL_DEPTH_TEST)

            bgl.glEnable(bgl.GL_BLEND)
            # bgl.glEnable(bgl.GL_DEPTH_TEST)
            self.shader.bind()
            if self.hover and self.in_use == False:
                self.shader.uniform_float("color", [1.0, 1.0, 1.0, 1.0])
            else:
                self.shader.uniform_float("color", self.color)
            self.batch.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)
            # bgl.glDisable(bgl.GL_DEPTH_TEST)

        return
