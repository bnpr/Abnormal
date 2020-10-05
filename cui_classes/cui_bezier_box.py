import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import mathutils
import math
import copy
from .cui_functions import *
from .cui_items import *


#
#
#


class CUIBezierBox(CUIItem):
    def __init__(self, height, type, points):
        self.color = (0.3, 0.3, 0.3, 0.4)
        self.color_axis_lines = (0.9, 0.9, 0.9, 0.1)

        super().__init__(height)

        self.item_type = 'BEZIER_BOX'

        self.hover_highlight = False

        self.init_click_loc = [0, 0]
        self.prev_loc = [0, 0]

        self.draw_box = True

        self.use_outline = True

        self.curve_change_function = None

        self.axis_lines = []
        self.axis_res = 10

        self.bezier_type = type
        self.splines = []

        self.spline_change_function = None

        if type == 'FCURVE':
            spline = CUIFcurveSpline()
            for c, co in enumerate(points):
                po = spline.add_point(mathutils.Vector(co))
                if c == 0 or c == len(points)-1:
                    po.sharpness = 0.0
            self.splines.append(spline)

        if type == 'SHAPE':
            spline = CUIShapeSpline()
            po = spline.add_point(mathutils.Vector((0.5, 0.7)))
            po = spline.add_point(mathutils.Vector((0.8, 0.3)))
            po = spline.add_point(mathutils.Vector((0.2, 0.3)))
            self.splines.append(spline)
        return

    #

    def update_batches(self, position):
        super().update_batches(position)

        pos = [position[0]+self.scale_pos_offset[0],
               position[1]+self.scale_pos_offset[1]-self.height*self.scale]

        line_cos = []
        for co in self.axis_lines:
            po_co = co.copy()
            po_co[0] *= self.width
            po_co[1] *= self.height
            line_cos.append(po_co)

        lines = draw_cos_offset(pos, self.scale, line_cos)

        self.batch_axis_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})

        for spline in self.splines:
            spline.update_batches(pos, self.width, self.height)
        return

    def create_shape_data(self):
        super().create_shape_data()
        interval = 1/(self.axis_res+1)

        for i in range(self.axis_res):
            self.axis_lines.append(mathutils.Vector((interval*(i+1), 0)))
            self.axis_lines.append(mathutils.Vector((interval*(i+1), 1)))
            self.axis_lines.append(mathutils.Vector((0, interval*(i+1))))
            self.axis_lines.append(mathutils.Vector((1, interval*(i+1))))
        return

    def init_shape_data(self):
        self.axis_lines = []
        super().init_shape_data()
        return

    def draw(self):
        if self.visible == True:
            super().draw()

            bgl.glEnable(bgl.GL_BLEND)
            self.shader.bind()
            bgl.glLineWidth(1)
            self.shader.uniform_float("color", self.color_axis_lines)
            self.batch_axis_lines.draw(self.shader)
            bgl.glDisable(bgl.GL_BLEND)

            for spline in self.splines:
                spline.draw()
        return

    #

    def bezier_box_delete_points(self, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        for spline in self.splines:
            status = spline.delete_points()
            if status:
                spline.update_batches(position, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return

    def bezier_box_sharpen_points(self, pos, offset, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        for spline in self.splines:
            status = spline.sharpen_points(offset)
            if status:
                spline.update_batches(position, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def bezier_box_rotate_points(self, pos, angle, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        cent_co = mathutils.Vector((0, 0))
        cnt = 0
        for spline in self.splines:
            mid_co = spline.get_selected_avg_pos()
            mid_co[0] *= self.width * self.scale
            mid_co[1] *= self.height * self.scale
            mid_co += mathutils.Vector(position)

            if mid_co.length > 0.0:
                cent_co += mid_co
                cnt += 1

            status = spline.rotate_points(angle)
            if status:
                spline.update_batches(position, self.width, self.height)
                changed = True

        cent_co = cent_co / cnt

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed, cent_co

    def bezier_box_clear_sharpness(self, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        for spline in self.splines:
            status = spline.clear_sharpness()
            if status:
                spline.update_batches(position, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def bezier_box_clear_rotation(self, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        for spline in self.splines:
            status = spline.clear_rotation()
            if status:
                spline.update_batches(position, self.width, self.height)

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def bezier_box_reset_sharpness(self, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        for spline in self.splines:
            status = spline.reset_sharpness()
            if status:
                spline.update_batches(position, self.width, self.height)

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def bezier_box_reset_rotation(self, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        changed = False
        for spline in self.splines:
            status = spline.reset_rotation()
            if status:
                spline.update_batches(position, self.width, self.height)

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def bezier_box_confirm_sharpness(self):
        for spline in self.splines:
            spline.confirm_sharpness()
        return

    def bezier_box_confirm_rotation(self):
        for spline in self.splines:
            spline.confirm_rotation()
        return

    def bezier_box_select_points(self, status):
        for spline in self.splines:
            spline.select_points(status)
        return

    def bezier_box_eval_curve(self, x_val):
        val = None
        for spline in self.splines:
            val = spline.eval_curve(x_val)
        return val

    def copy_curve(self, curves):
        for s, sp in enumerate(curves):
            if s <= len(self.splines)-1:
                spline = self.splines[s]
                spline.clear_data()
            else:
                if self.bezier_type == 'FCURVE':
                    spline = CUIFcurveSpline()
                if self.bezier_type == 'SHAPE':
                    spline = CUIShapeSpline()
                self.splines.append(spline)

            for copy_po in sp.points:
                po = spline.add_point(copy_po.co)
                po.sharpness = copy_po.sharpness
                po.rotation = copy_po.rotation

        return

    def replace_curve(self, curve_points, curve_sharp, curve_rotate):
        for s, sp in enumerate(self.splines):
            sp.clear_data()

            for co in curve_points[s]:
                po = spline.add_point(co)
                po.sharpness = curve_sharp[s]
                po.rotation = curve_rotate[s]

        return

    #

    def click_down_func(self, mouse_co, shift, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        # Test selection
        selected = False
        nearest = None
        small_ind = None
        test_dist = 10
        for s, spline in enumerate(self.splines):
            for po in spline.points:
                po_co = po.co.copy()
                po_co[0] *= self.width * self.scale
                po_co[1] *= self.height * self.scale
                po_co[0] += position[0]
                po_co[1] += position[1]

                dist = (mathutils.Vector(mouse_co) - po_co).length
                if dist < test_dist:
                    nearest = po.index
                    small_ind = s
                    test_dist = dist

            if shift == False:
                for po in spline.points:
                    po.select = False

        if nearest != None and small_ind != None:
            selected = True
            po = self.splines[s].points[nearest]
            if shift and po.select:
                po.select = False
            else:
                po.select = True

        # No selection so add new point to spline and recalc
        if selected == False:
            small_ind = None
            po_index = None
            small_dist = 10
            create_new = False
            for s, spline in enumerate(self.splines):
                for p, po in enumerate(spline.curve_geo):
                    for point in spline.points:
                        if (point.co-po).length < .0001:
                            po_index = point.index+1
                            break
                    if p > 0:
                        po_co = po.copy()
                        po_co[0] *= self.width * self.scale
                        po_co[1] *= self.height * self.scale
                        po_co[0] += position[0]
                        po_co[1] += position[1]

                        ppo_co = spline.curve_geo[p-1].copy()
                        ppo_co[0] *= self.width * self.scale
                        ppo_co[1] *= self.height * self.scale
                        ppo_co[0] += position[0]
                        ppo_co[1] += position[1]

                        ed_vec = po_co - ppo_co
                        vec = mathutils.Vector(mouse_co) - ppo_co
                        if ed_vec.length > 0.0 and vec.length > 0.0:
                            ang = ed_vec.angle(vec)
                            adj_len = math.cos(ang) * vec.length
                            dist = math.sin(ang) * vec.length

                            if ang >= math.radians(90):
                                dist = vec.length

                            if adj_len > ed_vec.length:
                                dist = (mathutils.Vector(
                                    mouse_co) - po_co).length

                            if dist < small_dist:
                                create_new = True
                                small_ind = s
                                small_dist = dist
                                break

            if create_new and small_ind != None and po_index != None:
                co = mathutils.Vector(mouse_co) - \
                    mathutils.Vector(position)
                co[0] /= self.width
                co[0] /= self.scale
                co[1] /= self.height
                co[1] /= self.scale

                new_po = self.splines[s].add_point(co, index=po_index)
                spline.update_batches(position, self.width, self.height)
                new_po.select = True

        self.click_down = True
        self.init_click_loc = mouse_co
        self.prev_loc = mouse_co

        # status = super().click_down_func(mouse_co, shift, pos, arguments)
        return [self.item_type, self.custom_id]

    def click_up_func(self, mouse_co, shift, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        self.click_down = False
        # status = super().click_up_func(mouse_co, shift, pos, arguments)
        return [self.item_type, self.custom_id]

    def click_down_move(self, mouse_co, shift, pos, arguments=None):
        position = [pos[0]+self.scale_pos_offset[0], pos[1] +
                    self.scale_pos_offset[1]-self.height*self.scale]

        offset = (mathutils.Vector(mouse_co) -
                  mathutils.Vector(self.prev_loc)) / self.scale
        offset[0] /= self.width
        offset[1] /= self.height

        for spline in self.splines:
            spline.move_points(offset)
            spline.update_batches(position, self.width, self.height)
            self.prev_loc = mouse_co
            # super().click_down_move(mouse_co, shift, pos, arguments)

            if self.curve_change_function:
                skip_update = self.curve_change_function(
                    self, arguments)

        return

    #

    def set_curve_change_func(self, func):
        self.curve_change_function = func
        return

    def set_scale(self, scale):
        super().set_scale(scale)
        for spline in self.splines:
            spline.set_scale(scale)
        return

    def set_color(self, color=None, color_spline=None, color_area=None, color_point=None, color_handles=None):
        if color:
            self.color = color
        if color_spline:
            for spline in self.splines:
                spline.color = color_spline
        if color_area:
            for spline in self.splines:
                spline.color_area = color_area
        if color_point:
            for spline in self.splines:
                for po in spline.points:
                    po.color = color_point
        if color_handles:
            for spline in self.splines:
                for po in spline.points:
                    po.color_handles = color_handles
        return

    def set_thickness(self, spline_thick=None, handle_thick=None):
        if spline_thick:
            for spline in self.splines:
                spline.spline_thickness = spline_thick
        if handle_thick:
            for spline in self.splines:
                for po in spline.points:
                    po.handle_thickness = handle_thick
        return

    #

    def __str__(self):
        return 'CUI Bezier Box'

#
#
#


class CUIBaseSpline:
    def __init__(self):
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.resolution = 8
        self.points = []
        self.curve_geo = []
        self.color = (0.1, 0.1, 0.1, 1.0)
        self.spline_thickness = 3
        self.scale = 1.0
        self.cyclic = False
        return

    #

    def update_batches(self, position, width, height):
        self.calc_auto_handles()
        self.calc_curve_geo()

        line_cos = []
        for p, po in enumerate(self.curve_geo):
            if p > 0:
                prev_co = self.curve_geo[p-1].copy()
                co = po.copy()

                prev_co[0] *= width
                prev_co[1] *= height
                co[0] *= width
                co[1] *= height

                line_cos.append(prev_co)
                line_cos.append(co)

        lines = draw_cos_offset(position, self.scale, line_cos)

        self.batch = batch_for_shader(self.shader, 'LINES', {"pos": lines})

        for p, po in enumerate(self.points):
            if p == 0:
                handle_type = 0
            elif p == len(self.points)-1:
                handle_type = 2
            else:
                handle_type = 1

            po.update_batches(position, width, height, handle_type)
        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(self.spline_thickness)
        self.shader.bind()
        self.shader.uniform_float("color", self.color)
        self.batch.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

        return

    def draw_points(self):
        for po in self.points:
            po.draw()
        return

    #

    def add_point(self, co, index=None):
        if index == None:
            index = len(self.points)

        po = CUIBezierPoint(index, co)

        self.points.append(po)
        return po

    def clear_data(self):
        self.points.clear()
        self.curve_geo.clear()
        return

    def calc_curve_geo(self):
        self.curve_geo.clear()
        for p, po in enumerate(self.points):
            if p > 0:
                prev_po = self.points[p-1]
                seg_pos = mathutils.geometry.interpolate_bezier(
                    prev_po.co, prev_po.handle_right, po.handle_left, po.co, self.resolution)
                self.curve_geo += seg_pos

        return

    #

    def move_points(self, offset):
        for po in self.points:
            if po.select:
                po.co += offset
                if po.co[0] < 0.0:
                    po.co[0] = 0.0
                if po.co[0] > 1.0:
                    po.co[0] = 1
                if po.co[1] < 0.0:
                    po.co[1] = 0.0
                if po.co[1] > 1.0:
                    po.co[1] = 1.0
        return

    def select_points(self, status):
        for po in self.points:
            po.select = status
        return

    #

    def rotate_points(self, angle):
        pos = [po.index for po in self.points if po.select]

        if len(pos) == 0:
            did_change = False
        else:
            did_change = True
            for ind in pos:
                if self.points[ind].cache_rotation == None:
                    self.points[ind].cache_rotation = self.points[ind].rotation

                self.points[ind].rotation += angle
        return did_change

    def clear_rotation(self):
        pos = [po.index for po in self.points if po.select]

        if len(pos) == 0:
            did_change = False
        else:
            did_change = True
            for ind in pos:
                self.points[ind].rotation = 0.0
        return did_change

    def reset_rotation(self):
        pos = [po.index for po in self.points if po.select]

        if len(pos) == 0:
            did_change = False
        else:
            did_change = True
            for ind in pos:
                if self.points[ind].cache_rotation != None:
                    self.points[ind].rotation = self.points[ind].cache_rotation
                    self.points[ind].cache_rotation = None
        return did_change

    def confirm_rotation(self):
        for po in self.points:
            po.cache_rotation = None
        return

    #

    def sharpen_points(self, offset):
        pos = [po.index for po in self.points if po.select]

        if len(pos) == 0:
            did_change = False
        else:
            did_change = True
            for ind in pos:
                if self.points[ind].cache_sharpness == None:
                    self.points[ind].cache_sharpness = self.points[ind].sharpness

                self.points[ind].sharpness += offset
                if self.points[ind].sharpness < 0.0:
                    self.points[ind].sharpness = 0.0
                if self.points[ind].sharpness > 5.0:
                    self.points[ind].sharpness = 5.0
        return did_change

    def clear_sharpness(self):
        pos = [po.index for po in self.points if po.select]

        if len(pos) == 0:
            did_change = False
        else:
            did_change = True
            for ind in pos:
                self.points[ind].sharpness = 1.0
        return did_change

    def reset_sharpness(self):
        pos = [po.index for po in self.points if po.select]

        if len(pos) == 0:
            did_change = False
        else:
            did_change = True
            for ind in pos:
                if self.points[ind].cache_sharpness != None:
                    self.points[ind].sharpness = self.points[ind].cache_sharpness
                    self.points[ind].cache_sharpness = None
        return did_change

    def confirm_sharpness(self):
        for po in self.points:
            po.cache_sharpness = None
        return

    #

    def get_selected_avg_pos(self):
        co = mathutils.Vector((0, 0))
        cnt = 0
        for po in self.points:
            if po.select:
                co += po.co
                cnt += 1

        if cnt == 0:
            co[0] = 0.5
            co[1] = 0.5
        else:
            co /= cnt

        return co

    def get_selected_points(self):
        sel_inds = []
        for po in self.points:
            if po.select:
                sel_inds.append(po.index)
        return sel_inds

    def get_spline_length(self):
        length = 0
        for p, po in enumerate(self.curve_geo):
            prev_po = self.curve_geo[p-1]
            if p > 0:
                length += (po-prev_po).length

        return length

    def get_t_co(self, t):
        t_co = None
        if self.points:
            spline_len = self.get_spline_length()
            targ_len = spline_len*t

            cur_len = 0
            for p, po in enumerate(self.curve_geo):
                prev_po = self.curve_geo[p-1]
                if p > 0:
                    next_len += (po-prev_po).length
                    if next_len > targ_len:
                        rem_len = targ_len - cur_len
                        vec = (po - prev_po).normalized() * rem_len
                        t_co = prev_po + vec
                        break
                    else:
                        cur_len += (po-prev_po).length

        return t_co

    #

    def set_scale(self, scale):
        self.scale = scale
        for po in self.points:
            po.set_scale(scale)
        return

    #

    def __str__(self):
        return 'CUI Bezier Spline Base'


class CUIFcurveSpline(CUIBaseSpline):
    def __init__(self):
        super().__init__()
        self.area_pos = []
        self.area_tris = []
        self.color_area = (0.1, 0.1, 0.15, 0.25)
        return

    #

    def update_batches(self, position, width, height):
        self.reorder_points()
        super().update_batches(position, width, height)

        area_cos = []
        for po in self.area_pos:
            co = po.copy()

            co[0] *= width
            co[1] *= height

            area_cos.append(co)

        tri_pos = draw_cos_offset(position, self.scale, area_cos)

        self.batch_area = batch_for_shader(
            self.shader, 'TRIS', {"pos": tri_pos}, indices=self.area_tris)
        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)
        self.shader.bind()
        self.shader.uniform_float("color", self.color_area)
        self.batch_area.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

        super().draw()
        super().draw_points()

        return

    #

    def copy(self):
        new_spline = CUIFcurveSpline()
        new_spline.resolution = self.resolution
        new_spline.curve_geo = copy.deepcopy(self.curve_geo)
        new_spline.area_pos = copy.deepcopy(self.area_pos)
        new_spline.area_tris = copy.deepcopy(self.area_tris)
        new_spline.color = copy.deepcopy(self.color)
        new_spline.color_area = copy.deepcopy(self.color_area)
        new_spline.spline_thickness = self.spline_thickness
        new_spline.scale = self.scale
        new_spline.cyclic = self.cyclic

        for po in self.points:
            new_spline.points.append(po.copy())

        return new_spline

    def calc_auto_handles(self):
        for p, po in enumerate(self.points):
            next_ind = p+1
            prev_ind = p-1
            if p == len(self.points)-1:
                next_ind = 0

            prev_co = self.points[prev_ind].co
            next_co = self.points[next_ind].co

            next_vec = (next_co - po.co) * .390464
            prev_vec = (po.co - prev_co) * .390464

            if p == 0:
                hand_vec = next_vec
            elif p == len(self.points)-1:
                hand_vec = prev_vec
            else:
                tot_dist = next_co[0] - prev_co[0]
                prev_dist = po.co[0] - prev_co[0]

                if tot_dist == 0.0:
                    fac = 0.0
                else:
                    fac = prev_dist/tot_dist

                hand_vec = prev_vec.lerp(next_vec, fac)

            hand_vec = hand_vec.normalized()

            hand_a_vec = hand_vec*-1
            hand_b_vec = hand_vec

            hand_a_vec = rotate_2d([0, 0], hand_a_vec, po.rotation)
            hand_b_vec = rotate_2d([0, 0], hand_b_vec, po.rotation)

            hand_a_vec *= prev_vec.length
            hand_b_vec *= next_vec.length

            if po.sharpness < 1.0:
                hl_norm = po.co+hand_a_vec*po.sharpness
                hr_norm = po.co+hand_b_vec*po.sharpness
            else:
                hl_norm = po.co+hand_a_vec
                hr_norm = po.co+hand_b_vec

            hand_a_vec *= po.sharpness
            hand_b_vec *= po.sharpness

            po.handle_left = po.co+hand_a_vec
            po.handle_right = po.co+hand_b_vec

            # Clip handles bottom and top
            if po.co[1] <= 0.0:
                po.handle_left[1] = 0.0
                po.handle_right[1] = 0.0
            elif po.co[1] >= 1.0:
                po.handle_left[1] = 1.0
                po.handle_right[1] = 1.0
            else:
                # Flatten handles to top/bottom if it is beyond limits
                if hl_norm[1] < 0.0 or hl_norm[1] > 1.0:
                    val = 0.0
                    if hl_norm[1] > 1.0:
                        val = 1.0

                    vec = po.handle_left - po.co
                    if vec.length > 0.0:
                        po.handle_left[0] = hl_norm[0]
                        po.handle_left[1] = val
                        hand_a_vec = po.handle_left-po.co
                        hand_b_vec = hand_a_vec * -1

                        ang = hand_a_vec.angle(mathutils.Vector((-1, 0)))
                        fac = (po.handle_right[0]-po.co[0]) / math.cos(ang)
                        po.handle_right = po.co + hand_b_vec.normalized()*fac
                # If no flattening needed then clip if beyond limits
                elif po.handle_left[1] < 0.0 or po.handle_left[1] > 1.0:
                    val = 0.0
                    if po.handle_left[1] > 1.0:
                        val = 1.0

                    vec = po.handle_left - po.co
                    if vec.length > 0.0:
                        fac = abs(po.handle_left[1] - val) / \
                            abs(po.handle_left[1]-po.co[1])
                        po.handle_left = po.co + hand_a_vec*(1-fac)

                # Flatten handles to top/bottom if it is beyond limits
                if hr_norm[1] < 0.0 or hr_norm[1] > 1.0:
                    val = 0.0
                    if hr_norm[1] > 1.0:
                        val = 1.0

                    vec = po.handle_right - po.co
                    if vec.length > 0.0:
                        po.handle_right[0] = hr_norm[0]
                        po.handle_right[1] = val
                        hand_b_vec = po.handle_right-po.co
                        hand_a_vec = hand_b_vec * -1

                        ang = hand_b_vec.angle(mathutils.Vector((1, 0)))
                        fac = (po.co[0]-po.handle_left[0]) / math.cos(ang)
                        po.handle_left = po.co + hand_a_vec.normalized()*fac
                # If no flattening needed then clip if beyond limits
                elif po.handle_right[1] > 1.0 or po.handle_right[1] < 0.0:
                    val = 0.0
                    if po.handle_right[1] > 1.0:
                        val = 1.0

                    vec = po.handle_right - po.co
                    if vec.length > 0.0:
                        fac = abs(po.handle_right[1] - val) / \
                            abs(po.handle_right[1]-po.co[1])
                        po.handle_right = po.co + hand_b_vec*(1-fac)

            # Clip handles on right side
            if p < len(self.points)-1:
                if po.handle_right[0] > next_co[0]:
                    vec = po.handle_right - po.co
                    if vec.length > 0.0:
                        ang = vec.angle(mathutils.Vector((1, 0)))
                        fac = (next_co[0] - po.co[0]) / math.cos(ang)
                        if fac < vec.length:
                            po.handle_right = po.co + vec.normalized()*fac
                if po.handle_right[0] < po.co[0]:
                    po.handle_right[0] = po.co[0]

            # Clip handes on left side
            if p > 0:
                if po.handle_left[0] < prev_co[0]:
                    vec = po.handle_left - po.co
                    if vec.length > 0.0:
                        ang = vec.angle(mathutils.Vector((-1, 0)))
                        fac = (po.co[0] - prev_co[0]) / math.cos(ang)
                        if fac < vec.length:
                            po.handle_left = po.co + vec.normalized()*fac
                if po.handle_left[0] > po.co[0]:
                    po.handle_left[0] = po.co[0]

        return

    def calc_curve_geo(self):
        super().calc_curve_geo()

        self.area_pos.clear()
        self.area_tris.clear()
        for p, po in enumerate(self.curve_geo):
            co1 = po.copy()
            co2 = po.copy()

            co1[1] = 0.0

            self.area_pos.append(co1)
            self.area_pos.append(co2)

            if p > 0:
                self.area_tris.append([(p-1)*2, (p-1)*2+1, (p-1)*2+3])
                self.area_tris.append([(p-1)*2, (p-1)*2+3, (p-1)*2+2])

        return

    def reorder_points(self):
        order = []
        x_cos = [po.co[0] for po in self.points]
        sorted_cos = sorted(x_cos.copy())

        restack_inds = []
        for c, co in enumerate(sorted_cos):
            ind = x_cos.index(co)
            order.append(ind)
            if x_cos.count(co) > 1:
                restack_inds = [i for i in range(len(x_cos)) if x_cos[i] == co]
            else:
                restack_inds = []
            x_cos[ind] = None

        for i, ind in enumerate(order):
            self.points[ind].index = i

        self.points = [self.points[i] for i in order]
        return

    def delete_points(self):
        del_pos = [po.index for po in self.points if po.select and po.index !=
                   0 and po.index != len(self.points)-1]

        if len(del_pos) == 0:
            did_delete = False
        else:
            did_delete = True
            del_pos.reverse()
            for ind in del_pos:
                self.points.pop(ind)

        for p, po in enumerate(self.points):
            po.index = p
        return did_delete

    def move_points(self, offset):
        super().move_points(offset)
        if self.points[0].co[0] > 0.0:
            self.points[0].co[0] = 0.0

        if self.points[len(self.points)-1].co[0] < 1.0:
            self.points[len(self.points)-1].co[0] = 1.0
        return

    def eval_curve(self, x_val):
        y_val = 0
        for c, co in enumerate(self.curve_geo):
            if c > 0:
                if co[0] >= x_val >= self.curve_geo[c-1][0]:
                    vec = (co - self.curve_geo[c-1]).normalized()
                    ang = vec.angle(mathutils.Vector((1, 0)))

                    vec_len = (x_val-self.curve_geo[c-1][0]) / math.cos(ang)
                    y_val = (self.curve_geo[c-1] + vec * vec_len)[1]
                    break
                else:
                    y_val = co[1]

        if y_val > 1.0:
            y_val = 1.0
        if y_val < 0.0:
            y_val = 0.0

        return y_val

    #

    def __str__(self):
        return 'CUI Fcurve Spline'


class CUIShapeSpline(CUIBaseSpline):
    def __init__(self):
        super().__init__()
        self.cyclic = True
        self.mirror_shape = True
        return

    #

    def draw(self):
        super().draw()
        super().draw_points()
        return

    #

    def copy(self):
        new_spline = CUIFcurveSpline()
        new_spline.resolution = self.resolution
        new_spline.curve_geo = copy.deepcopy(self.curve_geo)
        new_spline.color = copy.deepcopy(self.color)
        new_spline.color_area = copy.deepcopy(self.color_area)
        new_spline.spline_thickness = self.spline_thickness
        new_spline.scale = self.scale
        new_spline.cyclic = self.cyclic
        new_spline.mirror_shape = self.mirror_shape

        for po in self.points:
            new_spline.points.append(po.copy())

        return new_spline

    def calc_auto_handles(self):
        for p, po in enumerate(self.points):
            if po.handle_type != 'AUTO':
                continue

            next_ind = p+1
            prev_ind = p-1
            if p == len(self.points)-1:
                next_ind = 0

            prev_co = self.points[prev_ind].co
            next_co = self.points[next_ind].co

            next_vec = (next_co - po.co) * .390464
            prev_vec = (po.co - prev_co) * .390464

            if p == 0:
                hand_vec = next_vec
            elif p == len(self.points)-1:
                hand_vec = prev_vec
            else:
                hand_vec = prev_vec.lerp(next_vec, 0.5)

            hand_vec = hand_vec.normalized()

            hand_a_vec = hand_vec*-1
            hand_b_vec = hand_vec

            hand_a_vec = rotate_2d([0, 0], hand_a_vec, po.rotation)
            hand_b_vec = rotate_2d([0, 0], hand_b_vec, po.rotation)

            hand_a_vec *= prev_vec.length
            hand_b_vec *= next_vec.length

            hand_a_vec *= po.sharpness
            hand_b_vec *= po.sharpness

            po.handle_left = po.co+hand_a_vec
            po.handle_right = po.co+hand_b_vec
        return

    def delete_points(self):
        del_pos = [po.index for po in self.points if po.select]

        if len(del_pos) == 0:
            did_delete = False
        else:
            did_delete = True
            del_pos.reverse()
            for ind in del_pos:
                if len(self.points) > 2:
                    self.points.pop(ind)

        for p, po in enumerate(self.points):
            po.index = p
        return did_delete

    #

    def set_mirror_status(self, status):
        self.mirror_shape = status
        return

    def set_cyclic_status(self, status):
        self.cyclic = status
        return

    #

    def __str__(self):
        return 'CUI Shape Spline'


class CUIBezierPoint:
    def __init__(self, index, co):
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.index = index
        self.co = co
        self.handle_left = co
        self.handle_right = co
        self.handle_type = 'ALIGNED'

        self.select = False

        self.handle_thickness = 1
        self.point_size = 5

        self.color = (0.5, 0.5, 0.5, 1.0)
        self.color_select = (1.0, 1.0, 1.0, 1.0)
        self.color_handles = (0.6, 0.6, 0.6, 0.8)

        self.rotation = 0.0
        self.cache_rotation = None
        self.sharpness = 1.0
        self.cache_sharpness = None
        self.scale = 1.0
        return

    #

    def update_batches(self, position, width, height, handle_type):
        point = [[self.co[0] * width, self.co[1] * height]]

        points = draw_cos_offset(position, self.scale, point)

        handle_line_cos = []
        co = self.co.copy()
        lco = self.handle_left.copy()
        rco = self.handle_right.copy()

        co[0] *= width
        co[1] *= height
        lco[0] *= width
        lco[1] *= height
        rco[0] *= width
        rco[1] *= height

        if handle_type > 0:
            vec = lco-co
            handle_line_cos.append(co)
            handle_line_cos.append(co+vec*0.4)
        if handle_type < 2:
            vec = rco-co
            handle_line_cos.append(co)
            handle_line_cos.append(co+vec*0.4)

        handle_lines = draw_cos_offset(position, self.scale, handle_line_cos)

        self.batch = batch_for_shader(self.shader, 'POINTS', {"pos": points})
        self.batch_handles = batch_for_shader(
            self.shader, 'LINES', {"pos": handle_lines})
        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(self.handle_thickness)
        self.shader.bind()
        self.shader.uniform_float("color", self.color_handles)
        self.batch_handles.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glPointSize(self.point_size)
        self.shader.bind()
        if self.select:
            self.shader.uniform_float("color", self.color_select)
        else:
            self.shader.uniform_float("color", self.color)
        self.batch.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

        return

    #

    def copy(self):
        new_po = CUIBezierPoint(self.index, copy.deepcopy(self.co))
        new_po.color = copy.deepcopy(self.color)
        new_po.color_select = copy.deepcopy(self.color_select)
        new_po.color_handles = copy.deepcopy(self.color_handles)
        new_po.handle_left = copy.deepcopy(self.handle_left)
        new_po.handle_right = copy.deepcopy(self.handle_right)
        new_po.handle_type = self.handle_type
        new_po.select = self.select
        new_po.handle_thickness = self.handle_thickness
        new_po.point_size = self.point_size
        new_po.scale = self.scale
        new_po.sharpness = self.sharpness
        new_po.rotation = self.rotation

        return new_po

    #

    def set_scale(self, scale):
        self.scale = scale
        return

    #

    def __str__(self):
        return 'CUI Bezier Spline Point'
