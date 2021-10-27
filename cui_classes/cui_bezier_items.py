import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from .cui_functions import *
from .cui_items import *


#
#
#


class CUISpacedLines(CUIItemWidget):
    #
    # A box with option for lines in both directions and secondary lines inbetween the main lines
    #
    def __init__(self, height, amount):
        self.color = (0.0, 0.0, 0.3, 0.4)
        self.color_axis_lines = (0.0, 0.0, 0.9, 0.25)
        self.color_inbtwn_lines = (0.0, 0.0, 0.5, 0.15)

        super().__init__(height, '')

        self.hover_highlight = False

        self.draw_box = True

        self.line_amount = amount
        self.line_inbetweens = True
        self.line_both_directions = False

        self.line_thickness = 2.0
        self.inbtwn_thickness = 1.0

        self.axis = 1

        # self.create_shape_data()
        return

    #

    def create_shape_data(self):
        super().create_shape_data()

        cos = []
        i_cos = []

        if self.line_amount > 1:
            line_amount = self.line_amount

            if self.line_both_directions:
                line_amount *= 2
                line_amount += 1

            axis_cos = (np.arange(line_amount, dtype=np.float32) /
                        (line_amount-1)).reshape(-1, 1)

            if self.line_both_directions:
                axis_cos *= 2
                axis_cos -= 1.0

            cos = np.tile(axis_cos, (1, 4))
            cos[:, self.axis] = 0.0
            cos[:, self.axis+2] = 1.0
            cos = cos.reshape(-1, 2)

            #

            if self.line_inbetweens:
                i_axis_cos = (axis_cos - (axis_cos[1]-axis_cos[0])/2)[1:]

                i_cos = np.tile(i_axis_cos, (1, 4))
                i_cos[:, self.axis] = 0.0
                i_cos[:, self.axis+2] = 1.0
                i_cos = i_cos.reshape(-1, 2)

        self.lines = cos
        self.inbtwn_lines = i_cos

        return

    def update_batches(self, position):
        super().update_batches(position)

        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        cos = self.lines.copy()
        cos[:, 0] *= self.width
        cos[:, 1] *= self.height
        line_cos = (cos * self.scale + pos).tolist()

        inbtwn_line_cos = []
        if self.line_inbetweens:
            icos = self.inbtwn_lines.copy()
            icos[:, 0] *= self.width
            icos[:, 1] *= self.height
            inbtwn_line_cos = (icos * self.scale + pos).tolist()

        self.batch_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": line_cos})
        self.batch_inbtwn_lines = batch_for_shader(
            self.shader, 'LINES', {"pos": inbtwn_line_cos})
        return

    def init_shape_data(self):
        self.lines = np.array([], dtype=np.float32)
        self.inbtwn_lines = np.array([], dtype=np.float32)
        super().init_shape_data()
        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_axis_lines_render = get_enabled_color(
            self.color_axis_lines, self.enabled)

        self.color_inbtwn_lines_render = get_enabled_color(
            self.color_inbtwn_lines, self.enabled)

        return

    def draw(self, color_override=None, click_down=False):
        if self.visible:
            super().draw()

            bgl.glEnable(bgl.GL_BLEND)

            self.shader.bind()
            bgl.glLineWidth(self.line_thickness)
            self.shader.uniform_float("color", self.color_axis_lines_render)
            self.batch_lines.draw(self.shader)

            self.shader.bind()
            bgl.glLineWidth(self.inbtwn_thickness)
            self.shader.uniform_float("color", self.color_inbtwn_lines_render)
            self.batch_inbtwn_lines.draw(self.shader)

            bgl.glDisable(bgl.GL_BLEND)
        return

    #

    def set_line_amount(self, amount):
        self.line_amount = amount
        if amount < 2:
            self.line_amount = 2
        return

    def set_line_inbetweens(self, status):
        self.line_inbetweens = status
        return

    def set_line_both_directions(self, status):
        self.line_both_directions = status
        return

    def set_axis(self, axis):
        self.axis = axis
        return

    def set_color(self, color=None, color_axis=None, color_inbtwn=None):
        if color:
            self.color = color
        if color_axis:
            self.color_axis_lines = color_axis
        if color_inbtwn:
            self.color_inbtwn_lines = color_inbtwn

        self.update_color_render()
        return

    #

    def __str__(self):
        return 'CUI Grid Box'


#


class CUIFrameGrid(CUIItem):
    #
    # A grid box to be used for a graph editor or dopesheet
    #
    def __init__(self, cont, height, frame_start, frame_end):
        super().__init__(cont, height)

        self.item_type = 'FRAME_GRID'

        self.frame_start = frame_start
        self.frame_end = frame_end
        self.frame_total = frame_end-frame_start+1

        self.scale_x = 1.0
        self.scale_y = 1.0

        self.init_scale_x = 1.0
        self.init_scale_y = 1.0

        self.line_min_gap = 50.0

        self.interval_y_factor = 0.1

        self.interval_x_step = 10
        self.interval_y_step = 1

        self.x_axis_lines = CUISpacedLines(height, 0)
        self.y_axis_lines = CUISpacedLines(height, 0)
        self.y_axis_lines.set_axis(0)

        self.x_axis_lines.draw_box = False
        self.y_axis_lines.draw_box = False

        self.use_x_axis = False
        self.use_y_axis = False

        self.pan_prev_mouse = np.array([0.0, 0.0], dtype=np.float32)

        print()
        print()
        print()
        print()
        print()

        # self.calc_init_layout(20)
        # self.calc_init_layout(50)
        # self.calc_init_layout(75)
        # self.calc_init_layout(100)
        # self.calc_init_layout(200)
        # self.calc_init_layout(300)
        # self.calc_init_layout(500)
        # self.calc_init_layout(1000)

        return

    #

    def calc_init_layout(self, size):
        print()
        print('INIT LAYEOUTs')

        self.calc_init_scale(size)

        scale_size = size * self.init_scale_x

        self.scale_x = 0.9
        self.scale_y = 0.9
        print(scale_size)

        self.interval_x_step = self.calc_interval_step(
            size * self.scale * self.scale_x)
        self.interval_y_step = round_up_num(self.calc_interval_step(
            size * self.scale * self.scale_y) * self.interval_y_factor)
        return

    def calc_init_scale(self, size):

        max_size = self.line_min_gap * (self.frame_total-1)

        print(max_size, size)

        scale = size/max_size

        self.init_scale_x = scale
        self.init_scale_y = scale

        print(scale)

        return

    def calc_interval_step(self, size):
        def round_interval(interval):
            tot_digits = len(str(interval))

            num_str = '1'
            for i in range(tot_digits-1):
                num_str += '0'

            num = int(num_str)
            if tot_digits > 1:
                rem = interval % num

                if rem > 0:
                    interval += num-rem

            first_num = int(str(interval)[0])

            if first_num > 5:
                fit_interval = num*10
            elif first_num > 2:
                fit_interval = num*5
            elif first_num > 1:
                fit_interval = num*2
            else:
                fit_interval = num*1

            return fit_interval

        scale_interval = size / (self.frame_total-1)
        print(scale_interval)

        fit = round_interval(round_up_num(self.line_min_gap / scale_interval))
        return fit

    def create_shape_data(self):
        # self.calc_init_layout(self.width)

        if self.use_x_axis:
            self.x_axis_lines.set_width(self.width*self.scale_x)
            self.x_axis_lines.set_height(self.height)

            fits = 2 ** (int(np.log2((self.x_axis_lines.scale_width) /
                         self.line_min_gap)) + 1)
            if fits > self.frame_total:
                fits = self.frame_total
                self.interval_x_step = 1

            else:
                print(round_up_num(self.frame_total / (fits-1)))
                print(round_up_num(self.frame_total / (fits-1)) * fits)

                # self.interval_x_step = self.calc_interval_step(self.x_axis_lines.scale_width)
                self.interval_x_step = round_up_num(
                    self.frame_total / (fits-1))

            gap = self.x_axis_lines.scale_width / fits
            print('GAp')
            print(self.frame_total)
            print(gap)
            tot_needed = round_up_num(self.scale_width / gap)
            print(tot_needed, fits)

            self.x_axis_lines.set_line_amount(fits)

            self.x_axis_lines.set_line_inbetweens(self.interval_x_step > 1)
            self.x_axis_lines.create_shape_data()

        if self.use_y_axis:
            self.y_axis_lines.set_height(self.height*self.scale_y)
            self.y_axis_lines.set_width(self.width)

            fits = 2 ** (int(np.log2((self.y_axis_lines.scale_height) /
                         self.line_min_gap)) + 1)

            self.y_axis_lines.set_line_amount(fits)

            self.interval_y_step = round_up_num(self.calc_interval_step(
                self.y_axis_lines.scale_height) * self.interval_y_factor)

            self.y_axis_lines.set_line_inbetweens(self.interval_y_step > 1)
            self.y_axis_lines.create_shape_data()

        # # super().create_shape_data()
        # for part in self.parts:
        #     part.set_height(self.height)
        #     part.set_width(self.width)
        #     part.create_shape_data()

        return

    def update_batches(self, position):
        super().update_batches(position)

        if self.use_x_axis:
            self.x_axis_lines.update_batches(position)

        if self.use_y_axis:
            self.y_axis_lines.update_batches(position)

        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        # for spline in self.splines:
        #     spline.update_batches(pos, self.width, self.height)
        return

    #
    # GRAPH BOX FUNCS
    #

    def graph_box_delete_points(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.delete_points()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return

    def graph_box_sharpen_points(self, position, offset, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.sharpen_points(offset)
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def graph_box_rotate_points(self, position, angle, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        cent_co = np.array([0.0, 0.0], dtype=np.float32)
        cnt = 0
        for spline in self.splines:
            mid_co = spline.get_selected_avg_pos()
            mid_co[0] *= self.scale_width
            mid_co[1] *= self.scale_height
            mid_co += pos

            if get_vec_lengths(mid_co.reshape(-1, 2))[0] > 0.0:
                cent_co += mid_co
                cnt += 1

            status = spline.rotate_points(angle)
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        cent_co = cent_co / cnt

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed, cent_co

    def graph_box_clear_sharpness(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.clear_sharpness()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def graph_box_clear_rotation(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.clear_rotation()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def graph_box_store_data(self, position, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.store_data(
                coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def graph_box_restore_stored_data(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.restore_store_data()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def graph_box_clear_stored_data(self):
        for spline in self.splines:
            spline.clear_store_data()
        return

    def graph_box_select_points(self, status):
        for spline in self.splines:
            spline.select_points(status)
        return

    def graph_box_eval_curve(self, x_val):
        val = None
        for spline in self.splines:
            val = spline.eval_curve(x_val)
        return val

    def graph_box_pan(self, mouse_co, start=False):

        if start == False:
            offset = mouse_co - self.pan_prev_mouse

            if self.use_x_axis:
                self.x_axis_lines.offset_pos_offset_x(offset[0])
            if self.use_y_axis:
                self.y_axis_lines.offset_pos_offset_y(offset[1])

            self.update_batches(self.final_pos)

        self.pan_prev_mouse[:] = mouse_co
        return

    def graph_box_zoom(self, mouse_co, factor):
        if self.use_x_axis:
            w_offset_fac = np.abs(
                self.x_axis_lines.final_pos[0] - mouse_co[0]) / self.x_axis_lines.scale_width
            prev_width = self.x_axis_lines.scale_width
            self.scale_x *= factor

        if self.use_y_axis:
            h_offset_fac = np.abs(
                self.y_axis_lines.final_pos[1] - mouse_co[1]) / self.y_axis_lines.scale_height
            prev_height = self.y_axis_lines.scale_height
            self.scale_y *= factor

        self.create_shape_data()

        if self.use_x_axis:
            offset = (prev_width - self.x_axis_lines.scale_width)
            self.x_axis_lines.offset_pos_offset_x(offset*w_offset_fac)

            fits = 2 ** (int(np.log2((self.x_axis_lines.scale_width) /
                         self.line_min_gap)) + 1)

            self.x_axis_lines.set_line_amount(fits)

            # self.interval_x_step = self.calc_interval_step(self.x_axis_lines.scale_width)
            self.interval_x_step = round_up_num(self.frame_total / (fits-1))
            self.x_axis_lines.set_line_inbetweens(self.interval_x_step > 1)

        if self.use_y_axis:
            offset = (prev_height - self.y_axis_lines.scale_height)
            self.y_axis_lines.offset_pos_offset_y(offset*h_offset_fac)

            fits = 2 ** (int(np.log2((self.y_axis_lines.scale_height) /
                         self.line_min_gap)) + 1)

            self.y_axis_lines.set_line_amount(fits)

            self.interval_y_step = round_up_num(self.calc_interval_step(
                self.y_axis_lines.scale_height) * self.interval_y_factor)
            self.y_axis_lines.set_line_inbetweens(self.interval_y_step > 1)

        self.update_batches(self.final_pos)
        return

    def graph_box_home(self):
        print('HOME')
        # pos = self.scale_pos_offset + position

        return

    #
    # CLICK TEST FUNCS
    #

    def click_down_func(self, mouse_co, shift, position, arguments=None):
        self.x_axis_lines.offset_pos_offset_x(10)
        self.create_shape_data()
        self.update_batches(position)

        # pos = self.scale_pos_offset + position
        # pos[1] -= self.height*self.scale

        # # Test selection of spline points
        # unselecting = True
        # nearest = None
        # small_ind = None

        # test_dist = 10
        # for s, spline in enumerate(self.splines):
        #     # Get the line coordinates for drawing
        #     po_cos = spline.get_po_screen_cos(pos, self.width, self.height)

        #     dists = get_vec_lengths(po_cos - mouse_co)

        #     order = dists.argsort()
        #     dists = dists[order]
        #     in_range = dists <= test_dist

        #     dists = dists[in_range]
        #     order = order[in_range]

        #     if dists.size == 0:
        #         continue

        #     # All in range are selected
        #     if spline.po_select[order].all():
        #         # Check that no previous points are in range to be selected
        #         # if a previous point is in range to be selected do that before unselecting any
        #         if unselecting:
        #             nearest = dists[0]
        #             small_ind = [s, order[0]]

        #     # Some in range are unselected so set those to be selected if smaller than current
        #     else:
        #         first_unselected = (~spline.po_select[order]).nonzero()[0][0]

        #         # We have a point in range that is not selected
        #         # So if we have no previous selection,
        #         # or we have a selection but are unselecting that selection,
        #         # or this point is closer than the current selection
        #         # Then we should selec this point
        #         if nearest is None or unselecting or nearest < dists[first_unselected]:
        #             unselecting = False
        #             nearest = dists[first_unselected]
        #             small_ind = [s, order[first_unselected]]

        # # A point in range is found so make changes
        # if small_ind is not None:
        #     if shift == False:
        #         for s, spline in enumerate(self.splines):
        #             spline.po_select[:] = False

        #         self.splines[small_ind[0]].po_select[small_ind[1]] = True

        #     else:
        #         self.splines[small_ind[0]].po_select[small_ind[1]
        #                                              ] = not self.splines[small_ind[0]].po_select[small_ind[1]]

        #     self.splines[small_ind[0]].update_batches(
        #         pos, self.width, self.height)

        # #

        # # No selection so add new point to spline and recalc whole spline
        # else:
        #     test_dist = 10
        #     small_dist = -1
        #     small_item = None
        #     small_ind = None
        #     for s, spline in enumerate(self.splines):
        #         line_cos = spline.get_curve_screen_cos(
        #             pos, self.width, self.height)

        #         near_co, near_dist, near_ind, path_ind = get_nearest_co_on_curve(
        #             line_cos, spline.po_cos.shape[0], mouse_co)

        #         if near_dist < test_dist and (small_ind is None or near_dist < small_dist):
        #             small_item = s
        #             small_ind = near_ind
        #             small_dist = near_dist

        #     # If an edge and point index was found then add in a new point
        #     if small_ind is not None and small_item is not None:
        #         # Convert mouse co into the 0-1 space
        #         co = mouse_co - pos
        #         co[0] /= self.width
        #         co[1] /= self.height
        #         co /= self.scale

        #         # Add point, update batches and select the new point
        #         self.splines[small_item].add_point(co, index=small_ind)
        #         self.splines[small_item].po_select[:] = False
        #         self.splines[small_item].po_select[small_ind] = True
        #         spline.reorder_points()
        #         spline.update_data()
        #         spline.update_batches(pos, self.width, self.height)

        # self.click_down = True
        # self.init_click_loc[:] = mouse_co
        # self.prev_loc[:] = mouse_co

        # status = super().click_down_func(mouse_co, shift, position, arguments)
        return [self.item_type, self.custom_id]

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        # pos = self.scale_pos_offset + position
        # pos[1] -= self.height*self.scale

        self.click_down = False
        # status = super().click_up_func(mouse_co, shift, position, arguments)
        return [self.item_type, self.custom_id]

    def click_down_move(self, mouse_co, shift, position, arguments=None):
        # pos = self.scale_pos_offset + position
        # pos[1] -= self.height*self.scale

        # # Get the offset value from previous mouse in 0-1 space
        # offset = (mouse_co[:] - self.prev_loc) / self.scale
        # offset[0] /= self.width
        # offset[1] /= self.height

        # # Move the selected spline points and update
        # for spline in self.splines:
        #     if shift:
        #         offset *= .1

        #     spline.move_points(offset)
        #     spline.update_data()
        #     spline.update_batches(pos, self.width, self.height)
        #     self.prev_loc[:] = mouse_co
        #     # super().click_down_move(mouse_co, shift, position, arguments)

        #     if self.curve_change_function:
        #         skip_update = self.curve_change_function(
        #             self, arguments)

        return

    #

    def draw(self):
        # Get a currently in use scissor to reenable after the new scissor
        cur_scissor = None
        if bgl.glIsEnabled(bgl.GL_SCISSOR_TEST) == 1:
            cur_scissor = bgl.Buffer(bgl.GL_INT, 4)
            bgl.glGetIntegerv(bgl.GL_SCISSOR_BOX, cur_scissor)

        bgl.glEnable(bgl.GL_SCISSOR_TEST)
        bgl.glScissor(
            int(round(self.final_pos[0])),
            int(round(self.final_pos[1]-self.scale_height)),
            int(round(self.scale_width)),
            int(round(self.scale_height))
        )

        if self.use_x_axis:
            self.x_axis_lines.draw()

        if self.use_y_axis:
            self.y_axis_lines.draw()

        # Disable scissor as there is no previous scissor to continue with
        if cur_scissor is None:
            bgl.glDisable(bgl.GL_SCISSOR_TEST)

        # Reenable previous scissor
        else:
            bgl.glEnable(bgl.GL_SCISSOR_TEST)
            bgl.glScissor(
                cur_scissor[0], cur_scissor[1], cur_scissor[2], cur_scissor[3])
        return

    #

    def set_line_min_gap(self, size):
        self.line_min_gap = size
        return

    def set_use_x_axis(self, status):
        self.use_x_axis = status
        return

    def set_use_y_axis(self, status):
        self.use_y_axis = status
        return

    def offset_grid(self, offset):
        self.x_axis_lines.offset_pos_offset_x(offset[0])
        self.y_axis_lines.offset_pos_offset_y(offset[1])
        return

    #

    def __str__(self):
        return 'CUI Frame Grid'


class CUIDopeSheet(CUIFrameGrid):
    def __init__(self, cont, height, frame_start, frame_end):
        super().__init__(cont, height, frame_start, frame_end)

        return


class CUIGraphEditor(CUIFrameGrid):
    def __init__(self, cont, height, frame_start, frame_end):
        super().__init__(cont, height, frame_start, frame_end)

        return


#


class CUICurveBox(CUIItem):
    #
    # Curve box item class for basic curve profile/shapes inside a fixed non moving box
    #
    def __init__(self, cont, height, bez_type, points):
        self.color = (0.0, 0.0, 0.3, 0.4)
        self.color_axis_lines = (0.0, 0.0, 0.9, 0.1)

        super().__init__(cont, height)

        self.item_type = 'CURVE_BOX'

        self.hover_highlight = False

        self.init_click_loc = np.array([0.0, 0.0], dtype=np.float32)
        self.prev_loc = np.array([0.0, 0.0], dtype=np.float32)

        self.draw_box = True

        self.use_outline = True

        self.curve_change_function = None

        self.axis_res = 9

        self.bezier_type = bez_type
        self.splines = []

        self.spline_change_function = None

        hor_lines = CUISpacedLines(height, self.axis_res)
        hor_lines.set_axis(0)
        vert_lines = CUISpacedLines(height, self.axis_res)

        self.parts.append(hor_lines)
        self.parts.append(vert_lines)

        if bez_type == 'FCURVE':
            spline = CUIFcurveSpline()
            for c, co in enumerate(points):
                spline.add_point(co)
            spline.po_sharpness[[0, -1]] = 0.0
            spline.update_data()
            self.splines.append(spline)

        if bez_type == 'SHAPE':
            spline = CUIShapeSpline()
            spline.add_point([0.5, 0.7])
            spline.add_point([0.8, 0.3])
            spline.add_point([0.2, 0.3])
            spline.update_data()
            self.splines.append(spline)

        return

    #

    def create_shape_data(self):
        # super().create_shape_data()
        for part in self.parts:
            part.set_height(self.height)
            part.set_width(self.width)
            part.create_shape_data()

        return

    def update_batches(self, position):
        super().update_batches(position)

        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        for spline in self.splines:
            spline.update_batches(pos, self.width, self.height)
        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_axis_lines_render = get_enabled_color(
            self.color_axis_lines, self.enabled)

        return

    def draw(self):
        if self.visible:
            super().draw()

            for spline in self.splines:
                spline.draw()
        return

    #

    #
    # CURVE BOX FUNCS
    #

    def curve_box_delete_points(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.delete_points()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return

    def curve_box_sharpen_points(self, position, offset, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.sharpen_points(offset)
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def curve_box_rotate_points(self, position, angle, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        cent_co = np.array([0.0, 0.0], dtype=np.float32)
        cnt = 0
        for spline in self.splines:
            mid_co = spline.get_selected_avg_pos()
            mid_co[0] *= self.scale_width
            mid_co[1] *= self.scale_height
            mid_co += pos

            if get_vec_lengths(mid_co.reshape(-1, 2))[0] > 0.0:
                cent_co += mid_co
                cnt += 1

            status = spline.rotate_points(angle)
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        cent_co = cent_co / cnt

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed, cent_co

    def curve_box_clear_sharpness(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.clear_sharpness()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def curve_box_clear_rotation(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.clear_rotation()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def curve_box_store_data(self, position, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.store_data(
                coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def curve_box_restore_stored_data(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        changed = False
        for spline in self.splines:
            status = spline.restore_store_data()
            if status:
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)
                changed = True

        if self.curve_change_function and changed:
            skip_update = self.curve_change_function(
                self, arguments)
        return changed

    def curve_box_clear_stored_data(self):
        for spline in self.splines:
            spline.clear_store_data()
        return

    def curve_box_select_points(self, status):
        for spline in self.splines:
            spline.select_points(status)
        return

    def curve_box_eval_curve(self, x_val):
        val = None
        for spline in self.splines:
            val = spline.eval_curve(x_val)
        return val

    #
    # CLICK TEST FUNCS
    #

    def click_down_func(self, mouse_co, shift, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        # Test selection of spline points
        unselecting = True
        nearest = None
        small_ind = None

        test_dist = 10
        for s, spline in enumerate(self.splines):
            # Get the line coordinates for drawing
            po_cos = spline.get_po_screen_cos(pos, self.width, self.height)

            dists = get_vec_lengths(po_cos - mouse_co)

            order = dists.argsort()
            dists = dists[order]
            in_range = dists <= test_dist

            dists = dists[in_range]
            order = order[in_range]

            if dists.size == 0:
                continue

            # All in range are selected
            if spline.po_select[order].all():
                # Check that no previous points are in range to be selected
                # if a previous point is in range to be selected do that before unselecting any
                if unselecting:
                    nearest = dists[0]
                    small_ind = [s, order[0]]

            # Some in range are unselected so set those to be selected if smaller than current
            else:
                first_unselected = (~spline.po_select[order]).nonzero()[0][0]

                # We have a point in range that is not selected
                # So if we have no previous selection,
                # or we have a selection but are unselecting that selection,
                # or this point is closer than the current selection
                # Then we should selec this point
                if nearest is None or unselecting or nearest < dists[first_unselected]:
                    unselecting = False
                    nearest = dists[first_unselected]
                    small_ind = [s, order[first_unselected]]

        # A point in range is found so make changes
        if small_ind is not None:
            if shift == False:
                for s, spline in enumerate(self.splines):
                    spline.po_select[:] = False

                self.splines[small_ind[0]].po_select[small_ind[1]] = True

            else:
                self.splines[small_ind[0]].po_select[small_ind[1]
                                                     ] = not self.splines[small_ind[0]].po_select[small_ind[1]]

            self.splines[small_ind[0]].update_batches(
                pos, self.width, self.height)

        #

        # No selection so add new point to spline and recalc whole spline
        else:
            test_dist = 10
            small_dist = -1
            small_item = None
            small_ind = None
            for s, spline in enumerate(self.splines):
                line_cos = spline.get_curve_screen_cos(
                    pos, self.width, self.height)

                near_co, near_dist, near_ind, path_ind = get_nearest_co_on_curve(
                    line_cos, spline.po_cos.shape[0], mouse_co)

                if near_dist < test_dist and (small_ind is None or near_dist < small_dist):
                    small_item = s
                    small_ind = near_ind
                    small_dist = near_dist

            # If an edge and point index was found then add in a new point
            if small_ind is not None and small_item is not None:
                # Convert mouse co into the 0-1 space
                co = mouse_co - pos
                co[0] /= self.width
                co[1] /= self.height
                co /= self.scale

                # Add point, update batches and select the new point
                self.splines[small_item].add_point(co, index=small_ind)
                self.splines[small_item].po_select[:] = False
                self.splines[small_item].po_select[small_ind] = True
                spline.reorder_points()
                spline.update_data()
                spline.update_batches(pos, self.width, self.height)

        self.click_down = True
        self.init_click_loc[:] = mouse_co
        self.prev_loc[:] = mouse_co

        # status = super().click_down_func(mouse_co, shift, position, arguments)
        return [self.item_type, self.custom_id]

    def click_up_func(self, mouse_co, shift, position, arguments=None):
        # pos = self.scale_pos_offset + position
        # pos[1] -= self.height*self.scale

        self.click_down = False
        # status = super().click_up_func(mouse_co, shift, position, arguments)
        return [self.item_type, self.custom_id]

    def click_down_move(self, mouse_co, shift, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] -= self.height*self.scale

        # Get the offset value from previous mouse in 0-1 space
        offset = (mouse_co[:] - self.prev_loc) / self.scale
        offset[0] /= self.width
        offset[1] /= self.height

        # Move the selected spline points and update
        for spline in self.splines:
            if shift:
                offset *= .1

            spline.move_points(offset)
            spline.update_data()
            spline.update_batches(pos, self.width, self.height)
            self.prev_loc[:] = mouse_co
            # super().click_down_move(mouse_co, shift, position, arguments)

            if self.curve_change_function:
                skip_update = self.curve_change_function(
                    self, arguments)

        return

    #

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
                else:
                    spline = None

                if spline is not None:
                    self.splines.append(spline)

        return

    def replace_curve(self, curve_points, curve_sharp, curve_rotate):
        for s, sp in enumerate(self.splines):
            sp.clear_data()

            # for co in curve_points[s]:
            #     po = sp.add_point(co)
            #     po.sharpness = curve_sharp[s]
            #     po.rotation = curve_rotate[s]

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

    def set_color(self, color=None, color_axis=None, color_spline=None, color_area=None, color_point=None, color_pos_sel=None, color_handles=None):
        if color:
            self.color = color
        if color_axis:
            self.color_axis_lines = color_axis
        if color_spline:
            for spline in self.splines:
                spline.color = color_spline
                spline.update_color_render()
        if color_area:
            for spline in self.splines:
                spline.color_area = color_area
                spline.update_color_render()
        if color_point:
            for spline in self.splines:
                spline.color_pos = color_point
                spline.update_color_render()
        if color_pos_sel:
            for spline in self.splines:
                spline.color_pos_sel = color_point
                spline.update_color_render()
        if color_handles:
            for spline in self.splines:
                spline.color_handles = color_handles
                spline.update_color_render()

        self.update_color_render()
        return

    def set_thickness(self, spline_thick=None, handle_thick=None):
        if spline_thick:
            for spline in self.splines:
                spline.spline_thickness = spline_thick
        if handle_thick:
            for spline in self.splines:
                spline.handle_thickness = handle_thick
        return

    def set_enabled(self, status):
        super().set_enabled(status)
        for spline in self.splines:
            spline.set_enabled(status)
        return

    #

    def __str__(self):
        return 'CUI Curve Box'


#
#
#


class CUIBaseSpline:
    #
    # Basic spline class to be used for shape splines and fcurves
    #
    def __init__(self):
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

        self.scale = 1.0

        self.resolution = 8
        self.spline_thickness = 3
        self.handle_thickness = 1

        self.cyclic = False
        self.color = (0.0, 0.0, 0.1, 1.0)
        self.color_handles = (0.0, 0.0, 0.9, 1.0)
        self.color_pos = (0.06, 0.4, 0.7, 1.0)
        self.color_pos_sel = (0.08, 0.8, 0.9, 1.0)

        self.enabled = True

        self.init_spline_data()

        self.update_color_render()
        return

    #

    def update_data(self):

        self.po_handles_a, self.po_handles_b = self.calc_auto_handles()
        self.calc_curve_geo()
        return

    def update_batches(self, position, width, height):

        pos = np.array(position, dtype=np.float32)

        # Get the line coordinates for drawing
        line_cos = self.get_curve_screen_cos(pos, width, height)
        po_cos = self.get_po_screen_cos(pos, width, height)
        handle_cos = self.get_handle_screen_cos(pos, width, height)

        # Offset line coords based on positon and scale
        lines = line_cos.tolist()
        handles = handle_cos.tolist()

        points = po_cos[~self.po_select]
        points_sel = po_cos[self.po_select]

        if pos.size > 0:
            points = points

        if points_sel.size > 0:
            points_sel = points_sel

        points = points.tolist()
        points_sel = points_sel.tolist()

        self.batch = batch_for_shader(
            self.shader, 'LINES', {"pos": lines})
        self.batch_handles = batch_for_shader(
            self.shader, 'LINES', {"pos": handles})
        self.batch_pos = batch_for_shader(
            self.shader, 'POINTS', {"pos": points})
        self.batch_pos_sel = batch_for_shader(
            self.shader, 'POINTS', {"pos": points_sel})
        return

    def get_po_screen_cos(self, position, width, height):
        po_cos = self.po_cos.copy()
        po_cos[:, 0] *= width
        po_cos[:, 1] *= height

        po_cos *= self.scale
        po_cos += position

        return po_cos

    def get_curve_screen_cos(self, position, width, height):
        line_cos = np.hstack(
            [self.curve_geo[:-1], self.curve_geo[1:]]).reshape(-1, 2)
        line_cos[:, 0] *= width
        line_cos[:, 1] *= height

        line_cos *= self.scale
        line_cos += position

        return line_cos

    def get_handle_screen_cos(self, position, width, height):
        handle_cos = interweave_arrays([
            (self.po_handles_a-self.po_cos) * 0.5 + self.po_cos,
            (self.po_handles_b-self.po_cos) * 0.5 + self.po_cos])
        # handle_cos[0] = self.po_cos[0]
        # handle_cos[-1] = self.po_cos[-1]
        handle_cos[:, 0] *= width
        handle_cos[:, 1] *= height

        handle_cos *= self.scale
        handle_cos += position

        return handle_cos

    #

    def init_spline_data(self):
        self.curve_geo = np.array([], dtype=np.float32)
        self.po_cos = np.array([], dtype=np.float32)
        self.po_handles_a = np.array([], dtype=np.float32)
        self.po_handles_b = np.array([], dtype=np.float32)
        self.po_select = np.array([], dtype=np.bool8)
        self.po_sharpness = np.array([], dtype=np.float32)
        self.po_rotations = np.array([], dtype=np.float32)
        self.clear_store_data()
        return

    def update_color_render(self):
        self.color_render = get_enabled_color(
            self.color, self.enabled)
        self.color_handles_render = get_enabled_color(
            self.color_handles, self.enabled)
        self.color_pos_render = get_enabled_color(
            self.color_pos, self.enabled)
        self.color_pos_sel_render = get_enabled_color(
            self.color_pos_sel, self.enabled)

        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)

        bgl.glLineWidth(self.spline_thickness)
        self.shader.bind()
        self.shader.uniform_float("color", self.color_render)
        self.batch.draw(self.shader)

        bgl.glLineWidth(self.handle_thickness)
        self.shader.bind()
        self.shader.uniform_float("color", self.color_handles_render)
        self.batch_handles.draw(self.shader)

        self.shader.bind()
        self.shader.uniform_float("color", self.color_pos_render)
        self.batch_pos.draw(self.shader)

        self.shader.bind()
        self.shader.uniform_float("color", self.color_pos_sel_render)
        self.batch_pos_sel.draw(self.shader)

        bgl.glDisable(bgl.GL_BLEND)

        return

    #

    def add_point(self, co, index=None):
        if index == None:
            index = self.po_select.size

        self.po_cos = np.insert(self.po_cos, index, co, axis=0).reshape(-1, 2)
        self.po_handles_a = np.insert(
            self.po_handles_a, index, co, axis=0).reshape(-1, 2)
        self.po_handles_b = np.insert(
            self.po_handles_b, index, co, axis=0).reshape(-1, 2)

        self.po_select = np.insert(self.po_select, index, False)

        self.po_sharpness = np.insert(self.po_sharpness, index, 1.0)
        self.po_rotations = np.insert(self.po_rotations, index, 0.0)

        # po.set_enabled(self.enabled)
        return

    def clear_data(self):
        self.init_spline_data()
        return

    def calc_curve_geo(self):
        t_values = np.arange(
            self.resolution, dtype=np.float32) / (self.resolution-1)
        self.curve_geo = cui_get_bezier_coords(
            self.po_cos[:-1], self.po_handles_b[:-1], self.po_handles_a[1:], self.po_cos[1:], t_values, connected=True)
        return

    #

    def move_points(self, offset):
        self.po_cos[self.po_select] = np.clip(
            self.po_cos[self.po_select] + offset, 0.0, 1.0)
        return

    def invert_selection(self):
        self.po_select[:] = ~self.po_select
        return

    def select_points(self, mask):
        self.po_select[mask] = True
        return

    def deselect_points(self, mask):
        self.po_select[mask] = False
        return

    def set_points_selection(self, mask, status):
        self.po_select[mask] = status
        return

    def set_selection_status(self, status):
        self.po_select[:] = status
        return

    #

    def store_data(self,
                   coords=False, handles=False, sharpness=False, rotations=False):
        changed = False
        if coords:
            changed = True
            self.cache_po_cos = self.po_cos.copy()

        if handles:
            changed = True
            self.cache_po_handles_a = self.po_handles_a.copy()
            self.cache_po_handles_b = self.po_handles_b.copy()

        if sharpness:
            changed = True
            self.cache_po_sharps = self.po_sharpness.copy()

        if rotations:
            changed = True
            self.cache_po_rots = self.po_rotations.copy()

        return changed

    def restore_store_data(self):
        changed = False
        if self.cache_po_cos is not None:
            changed = True
            self.po_cos[:] = self.cache_po_cos

        if self.cache_po_handles_a is not None:
            changed = True
            self.po_handles_a[:] = self.cache_po_handles_a

        if self.cache_po_handles_b is not None:
            changed = True
            self.po_handles_b[:] = self.cache_po_handles_b

        if self.cache_po_sharps is not None:
            changed = True
            self.po_sharpness[:] = self.cache_po_sharps

        if self.cache_po_rots is not None:
            changed = True
            self.po_rotations[:] = self.cache_po_rots

        self.clear_store_data()
        return changed

    def clear_store_data(self):
        self.cache_po_cos = None
        self.cache_po_handles_a = None
        self.cache_po_handles_b = None
        self.cache_po_sharps = None
        self.cache_po_rots = None
        return

    #

    def rotate_points(self, angle):
        did_change = self.po_select.any()
        self.po_rotations[self.po_select] += angle
        return did_change

    def clear_rotation(self):
        did_change = self.po_select.any()
        self.po_rotations[self.po_select] = 0.0
        return did_change

    #

    def sharpen_points(self, offset):
        did_change = self.po_select.any()
        self.po_sharpness[self.po_select] = np.clip(
            self.po_sharpness[self.po_select] + offset, 0.0, 5.0)
        return did_change

    def clear_sharpness(self):
        did_change = self.po_select.any()
        self.po_sharpness[self.po_select] = 1.0
        return did_change

    #

    def get_selected_avg_pos(self):
        if self.po_select.any():
            avg_co = np.mean(self.po_cos[self.po_select], axis=0)
        else:
            avg_co = np.array([0.0, 0.0], dtype=np.float32)
        return avg_co

    def get_t_cos(self, t_vals):
        if self.curve_geo is None:
            return None

        # Get the lengths of each vector segment of the paths coords
        path_seg_lengths = get_vec_lengths(
            self.curve_geo[1:] - self.curve_geo[:-1])

        # Get the target path legnths of the t values
        tar_vec_lengths = t_vals * path_seg_lengths[-1]

        # Search for the indces where the target lengths would be inserted into the path
        tar_inds = np.searchsorted(path_seg_lengths, tar_vec_lengths)

        # Create masks for the T values less than 0 and above 1
        # These values need different indices as they extend beyond the path
        greater_mask = tar_inds >= path_seg_lengths.size
        lesser_mask = tar_inds == 0

        tar_inds[greater_mask] = path_seg_lengths.size-1
        start_inds = tar_inds - 1
        start_inds[lesser_mask] = 1

        # Get the vectors that each t value co will be placed along
        vecs = self.curve_geo[tar_inds] - self.curve_geo[start_inds]

        start_inds[greater_mask] = path_seg_lengths.size-1
        start_inds[lesser_mask] = 0

        # Get the length along these vectors that the coords will be placed
        tar_vec_lengths = np.abs(
            tar_vec_lengths - path_seg_lengths[start_inds])

        # Get scale factors of for the tar vecs
        scales = tar_vec_lengths/get_vec_lengths(vecs)

        # Scale the vectors and add to the start coords
        t_cos = scales[:, np.newaxis] * vecs + self.curve_geo[start_inds]

        return t_cos

    #

    def set_scale(self, scale):
        self.scale = scale
        return

    def set_color(self, color=None):
        if color is not None:
            self.color = color

        self.update_color_render()
        return

    def set_enabled(self, status):
        self.enabled = status
        return

    #

    def __str__(self):
        return 'CUI Bezier Spline Base'


class CUIFcurveSpline(CUIBaseSpline):
    #
    # Fcurve spline constrained so it cant overlap itself
    #
    def __init__(self):
        self.color_area = (0.1, 0.3, 0.35, 0.4)
        super().__init__()
        return

    #

    def init_spline_data(self):
        super().init_spline_data()
        self.area_pos = np.array([], dtype=np.float32)
        return

    def update_batches(self, position, width, height):
        self.reorder_points()
        super().update_batches(position, width, height)
        pos = np.array(position, dtype=np.float32)

        self.area_pos = interweave_arrays([self.curve_geo, self.curve_geo])
        self.area_pos[np.arange(self.curve_geo.shape[0])*2, 1] = 0.0

        area_cos = self.area_pos.copy()
        area_cos[:, 0] *= width
        area_cos[:, 1] *= height

        tri_pos = (area_cos * self.scale + pos).tolist()

        self.batch_area = batch_for_shader(
            self.shader, 'TRI_STRIP', {"pos": tri_pos})
        return

    #

    def update_color_render(self):
        super().update_color_render()

        self.color_area_render = get_enabled_color(
            self.color_area, self.enabled)

        return

    def draw(self):
        bgl.glEnable(bgl.GL_BLEND)
        self.shader.bind()
        self.shader.uniform_float("color", self.color_area_render)
        self.batch_area.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)

        super().draw()

        return

    #

    def calc_auto_handles(self):
        #
        # Calculate the handles of the given spline so that their is no overlap of the curve along the X axis
        #
        handles_a, handles_b = cui_calc_modified_point_handles(
            self.po_cos, self.cyclic, self.po_rotations, self.po_sharpness, False)
        bot_mask = self.po_cos[:, 1] <= 0.0
        top_mask = self.po_cos[:, 1] >= 1.0
        mid_mask = bot_mask.copy()
        mid_mask[top_mask] = True

        handles_a[bot_mask, 1] = 0.0
        handles_b[bot_mask, 1] = 0.0
        handles_a[top_mask, 1] = 1.0
        handles_b[top_mask, 1] = 1.0

        hand_a_mask = handles_a[:, 1] < 0.0
        hand_a_mask[handles_a[:, 1] > 1.0] = True
        hand_a_mask[mid_mask] = False

        mid_mask[hand_a_mask] = True

        hand_b_mask = handles_b[:, 1] < 0.0
        hand_b_mask[handles_b[:, 1] > 1.0] = True
        hand_b_mask[mid_mask] = False

        #

        # Skew/Shear the handles to stay inside the top/bottom of box
        hand_skew_vals = np.ones(self.po_select.size, np.float32)

        hand_a_dist = handles_a[hand_a_mask, 1] - self.po_cos[hand_a_mask, 1]
        hand_a_over = handles_a[hand_a_mask, 1]
        hand_a_over[hand_a_over > 1.0] -= 1.0
        hand_skew_vals[hand_a_mask] = 1.0 - (hand_a_over / hand_a_dist)

        hand_b_dist = handles_b[hand_b_mask, 1] - self.po_cos[hand_b_mask, 1]
        hand_b_over = handles_b[hand_b_mask, 1]
        hand_b_over[hand_b_over > 1.0] -= 1.0
        hand_skew_vals[hand_b_mask] = 1.0 - (hand_b_over / hand_b_dist)

        handles_a[:, 1] = (handles_a[:, 1] - self.po_cos[:, 1]
                           ) * hand_skew_vals + self.po_cos[:, 1]
        handles_b[:, 1] = (handles_b[:, 1] - self.po_cos[:, 1]
                           ) * hand_skew_vals + self.po_cos[:, 1]

        #

        # Scale/Clip the handles to not go beyond the next/previous points X co
        handles_a[0] = self.po_cos[0]
        handles_b[-1] = self.po_cos[-1]

        l_mask = (handles_a[1:, 0] < self.po_cos[:-1, 0]).nonzero()[0] + 1
        r_mask = (handles_b[:-1, 0] > self.po_cos[1:, 0]).nonzero()[0]

        l_dists = self.po_cos[:, 0] - handles_a[:, 0]
        l_clip_vals = (self.po_cos[l_mask, 0] -
                       self.po_cos[l_mask-1, 0]) / l_dists[l_mask]

        r_dists = handles_b[:, 0] - self.po_cos[:, 0]
        r_clip_vals = (self.po_cos[r_mask+1, 0] -
                       self.po_cos[r_mask, 0]) / r_dists[r_mask]

        handles_a[l_mask] = (handles_a[l_mask] - self.po_cos[l_mask]) * \
            l_clip_vals.reshape(-1, 1) + self.po_cos[l_mask]
        handles_b[r_mask] = (handles_b[r_mask] - self.po_cos[r_mask]) * \
            r_clip_vals.reshape(-1, 1) + self.po_cos[r_mask]

        #

        # Clamp the handles to not go beyond the left/right of their own point
        l_mask = (handles_a[1:, 0] > self.po_cos[1:, 0]).nonzero()[0] + 1
        r_mask = (handles_b[:-1, 0] < self.po_cos[:-1, 0]).nonzero()[0]

        handles_a[l_mask, 0] = self.po_cos[l_mask, 0]
        handles_b[r_mask, 0] = self.po_cos[r_mask, 0]

        return handles_a, handles_b

    def reorder_points(self):
        new_order = self.po_cos[:, 0].argsort()

        self.po_cos = self.po_cos[new_order]
        self.po_handles_a = self.po_handles_a[new_order]
        self.po_handles_b = self.po_handles_b[new_order]
        self.po_select = self.po_select[new_order]
        self.po_sharpness = self.po_sharpness[new_order]
        self.po_rotations = self.po_rotations[new_order]
        return

    def delete_points(self):
        indices = self.po_select.nonzero()[0]
        indices = indices[indices > 0]
        indices = indices[indices < self.po_select.size-1]

        did_delete = indices.size > 0

        self.po_cos = np.delete(self.po_cos, indices, axis=0).reshape(-1, 2)
        self.po_handles_a = np.delete(
            self.po_handles_a, indices, axis=0).reshape(-1, 2)
        self.po_handles_b = np.delete(
            self.po_handles_b, indices, axis=0).reshape(-1, 2)

        self.po_select = np.delete(self.po_select, indices)

        self.po_sharpness = np.delete(self.po_sharpness, indices)
        self.po_rotations = np.delete(self.po_rotations, indices)

        return did_delete

    def move_points(self, offset):
        super().move_points(offset)
        self.po_cos[0, 0] = 0.0
        self.po_cos[-1, 0] = 1.0
        return

    def eval_curve(self, x_val):
        #
        # Evaluate the curves value at the given X value
        # Do so by finding the previous and next points of the spline path
        #

        over_inds = (self.curve_geo[:, 0] > x_val).nonzero()[0]

        if over_inds.size == 0:
            y_val = self.curve_geo[-1, 1]

        else:
            first_ind = over_inds[0]

            if first_ind == 0:
                y_val = self.curve_geo[0, 1]

            else:
                min_x = self.curve_geo[first_ind-1, 0]
                max_x = self.curve_geo[first_ind, 0]

                fac = (x_val-min_x) / (max_x-min_x)

                y_val = self.curve_geo[first_ind, 1] * \
                    fac + self.curve_geo[first_ind-1, 1] * (1-fac)

        return y_val

    def set_color(self, color=None, color_area=None):
        if color_area is not None:
            self.color_area = color_area
        super().set_color(color)
        return

    #

    def __str__(self):
        return 'CUI Fcurve Spline'


class CUIShapeSpline(CUIBaseSpline):
    #
    # Bezier shape spline unconstrained 2d spline
    #
    def __init__(self):
        super().__init__()
        self.cyclic = True
        self.mirror_shape = True
        return

    #

    def draw(self):
        super().draw()
        return

    #

    def calc_auto_handles(self):
        #
        # Calculate the auto matic handles of the spline
        #
        for p, po in enumerate(self.points):
            if po.handle_type != 'AUTO':
                continue

            next_ind = (p+1) % len(self.points)
            prev_ind = p-1

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

        return handles_a, handles_b

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
