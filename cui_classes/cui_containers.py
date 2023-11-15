from .cui_shapes import *
from .cui_bezier_items import *
from .cui_items import *

#
#
#


class CUIContainer(CUIRectWidget):
    #
    # Basic container class
    #
    def __init__(self, modal):
        super().__init__()

        self.modal = modal

        self.horizontal_margin = 0
        self.vertical_margin = 0

        self.draw_backdrop = True
        return

    #

    def draw(self, color_override=None):
        if self.draw_backdrop:
            if color_override:
                super().draw(color_override)
            else:
                super().draw()

    #

    def set_margins(self, horizontal=None, vertical=None):
        if horizontal is not None:
            self.horizontal_margin = horizontal
        if vertical is not None:
            self.vertical_margin = vertical
        return

    #

    def __str__(self):
        return 'CUI Container'


class CUIBoxContainer(CUIContainer):
    #
    # Box container that contains other containers
    #
    def __init__(self, modal):
        super().__init__(modal)

        self.containers = []

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_box = (0.0, 0.0, 0.2, 1.0)
        self.color_row = (0.0, 0.0, 0.25, 1.0)
        self.color_item = (0.0, 0.0, 0.3, 0.7)
        self.color_hover = (0.0, 0.0, 0.5, 0.7)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.scroll_offset = 0
        self.scrolling = False
        self.scroll_bar_size = 14
        self.scroll_max_dist = 0
        self.scroll_max_move = 0
        self.scroll_bar = None
        self.scroll_click = False
        self.scroll_prev_mouse = np.array([0.0, 0.0], dtype=np.float32)

        self.horizontal_margin = 4
        self.vertical_margin = 4

        self.collapse = False
        self.header_box = None
        self.header = None

        self.cont_darken_factor = 1.0

        self.type = 'BOX'

        self.container_separation = 4
        return

    #

    def create_shape_data(self):
        total_height = 0
        total_height += self.vertical_margin

        # Loop the containers of this box calulcating their height and summing them together to get the total height of this box
        for c, cont in enumerate(self.containers):
            # Containers width is the width of the current box minus the margins
            cont.set_width(self.width - self.horizontal_margin*2)
            cont.create_shape_data()

            # Position the offsets based on height and margin
            cont.set_pos_offset_x(self.horizontal_margin)
            cont.set_pos_offset_y(-total_height)

            # If this box has a header create its data and add to height
            if self.header:
                # If this header has a shape (which is the collapsable arrow indicator) create its data
                if len(self.header.parts[0].shapes) > 0:
                    height = self.header.height
                    arrow_size = height*0.333

                    # Arrow is down if collapsed
                    if self.collapse:
                        self.header.parts[0].shapes[0].set_base_points([
                            [arrow_size*0.5, -height/2+arrow_size/2],
                            [arrow_size * 1.5, -height/2],
                            [arrow_size*0.5, -height/2-arrow_size/2]])
                    # Arrow is to side if uncollapsed
                    else:
                        self.header.parts[0].shapes[0].set_base_points([
                            [arrow_size*0.5, -height/2+arrow_size/2],
                            [arrow_size*1.5, -height/2+arrow_size/2],
                            [arrow_size, -height/2-arrow_size/2]])

                # Set width to box width minus margins
                self.header_box.set_width(
                    self.width - self.horizontal_margin*2)
                self.header_box.create_shape_data()

            # Skip adding this container to the total height as it is not visible
            if cont.visible == False:
                continue

            # Add to height
            total_height += cont.height

            # If there is another container to test then add the container separation value
            if c < len(self.containers)-1:
                total_height += self.container_separation

        # If a max height is set and this box is a panel type then figure the scaled max height
        # Only do this for panels as so far can only do 1 scissor clip scroll bar
        max_height = None
        if self.max_height is not None and (self.type == 'PANEL' or 'POPUP' in self.type):
            max_height = self.max_height/self.scale

        # If total height more than max height then set to scrolling or reset scrolling and scroll offset
        if max_height is not None:
            if total_height > max_height:
                self.scrolling = True
            else:
                self.scrolling = False
                self.scroll_offset = 0

        # Add final margin to total height and set the height
        total_height += self.vertical_margin
        self.set_height(total_height)

        # If scrolling and a panel then set up the scroll bar
        if self.scrolling and (self.type == 'PANEL' or 'POPUP' in self.type):

            # Get the max distance that the scroll needs to travel from the max height to the set height
            # And reset the scroll offset to the max if it is over
            self.scroll_max_dist = self.height - max_height
            if self.scroll_offset > self.scroll_max_dist:
                self.scroll_offset = self.scroll_max_dist

            # Resize the width of all containers to make room for the scroll bar and margins
            for cont in self.containers:
                cont.resize_width(
                    self.width-self.horizontal_margin*2-self.scroll_bar_size-4, 0.0)
                cont.create_shape_data()
                cont.set_scale(self.scale)

            # Create the scroll bar as a button
            self.scroll_bar = CUIButton(
                self, max_height*(max_height/self.height), '')
            self.scroll_bar.set_width(self.scroll_bar_size)

            self.scroll_bar.set_color(
                color=self.color_item,
                color_hover=self.color_hover,
                color_click=self.color_click,
                color_font=self.color_font
            )

            # Position the scroll bar on the right side of the panel
            self.scroll_bar.set_pos_offset_x(self.width -
                                             self.scroll_bar_size - self.horizontal_margin)
            self.scroll_bar.set_pos_offset_y(-self.vertical_margin)

            # Calculate the max movement range the scroll bar will need to go
            self.scroll_max_move = max_height - \
                self.vertical_margin*2 - self.scroll_bar.height
            self.scroll_bar.create_shape_data()

        # If collapsed reset height
        if self.collapse:
            # Set height to just the vertical margins
            self.set_height(self.vertical_margin*2)

            # If a header is present then add its height
            if self.header:
                self.offset_height(self.header_box.height)

            # If box is a panel and is set to scrolling then set the scroll bar height accordingly
            if self.scrolling and (self.type == 'PANEL' or 'POPUP' in self.type):
                self.scroll_bar.set_height(
                    self.height - self.vertical_margin * 2)
                self.scroll_bar.create_shape_data()

        super().create_shape_data()
        return

    def update_batches(self, position=[0.0, 0.0]):
        super().update_batches(position)
        pos = self.scale_pos_offset + position

        if self.scroll_bar:
            scroll_offset = int(
                (self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist)) * self.scale)

            self.scroll_bar.update_batches(pos - [0.0, scroll_offset])

        for cont in self.containers:
            cont.update_batches(
                pos + [0.0, self.scroll_offset * self.scale])
        return

    #

    def draw(self):
        if self.visible:
            super().draw()
            if self.scroll_bar and self.scrolling:
                self.scroll_bar.draw()

            # Panel is scrolling so we need to setup a scissor test to clip the panel to the correct area
            # Some test code is there for multi scissor boxes if I ever intend to try again
            if self.scrolling and (self.type == 'PANEL' or 'POPUP' in self.type):
                # Get a currently in use scissor to reenable after the new scissor
                cur_scissor = gpu.state.scissor_get()

                # clip_pos = pos.copy()
                # clip_pos[0] += self.horizontal_margin
                # clip_pos[1] -= self.vertical_margin

                offset = 0
                # if pos[1]+self.scroll_offset > position[1]:
                #     offset = pos[1]+self.scroll_offset-position[1]

                gpu.state.scissor_test_set(True)
                gpu.state.scissor_set(
                    int(round(self.final_pos[0]+self.horizontal_margin)),
                    int(round(self.final_pos[1]-self.scale_height+self.vertical_margin)),
                    int(round((self.scale_width-self.horizontal_margin*2))),
                    int(round((self.scale_height-self.vertical_margin*2-offset)))
                )

            for cont in self.containers:
                if self.collapse == False or cont == self.header_box:
                    cont.draw()

            if self.scrolling and (self.type == 'PANEL' or 'POPUP' in self.type):
                # Disable scissor as there is no previous scissor to continue with
                if cur_scissor is None:
                    gpu.state.scissor_test_set(False)

                # Reenable previous scissor
                else:
                    gpu.state.scissor_test_set(True)
                    gpu.state.scissor_set(
                        cur_scissor[0], cur_scissor[1], cur_scissor[2], cur_scissor[3])

        return

    #
    # ADD CONTAINERS FUNCS
    #

    def add_box(self, color=None):
        #
        # Add another box as a container inside this box
        #
        box = CUIBoxContainer(self.modal)
        box.set_width(self.width - self.horizontal_margin*2)

        box.set_color(
            color=get_modified_color(
                self.color_box, 1.0, self.cont_darken_factor, 1.0),
            color_outline=self.color_outline,
            color_font=self.color_font
        )

        box.set_style_color(
            color_box=get_modified_color(
                self.color_box, 1.0, self.cont_darken_factor, 1.0),
            color_row=get_modified_color(
                self.color_row, 1.0, self.cont_darken_factor, 1.0),
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        if color:
            box.set_color(
                color=color
            )

        box.set_enabled(self.enabled)
        self.containers.append(box)
        return box

    def add_invisible_box(self, color=None):
        #
        # Add another box as a container inside this box
        # This box will not be visible and has no margins it is just to contain a group of items
        #
        box = CUIBoxContainer(self.modal)
        box.set_width(self.width - self.horizontal_margin*2)

        box.horizontal_margin = 0
        box.vertical_margin = 0
        box.draw_backdrop = False

        box.set_color(
            color=get_modified_color(
                self.color_box, 1.0, self.cont_darken_factor, 1.0),
            color_outline=self.color_outline,
            color_font=self.color_font
        )

        box.set_style_color(
            color_box=get_modified_color(
                self.color_box, 1.0, self.cont_darken_factor, 1.0),
            color_row=get_modified_color(
                self.color_row, 1.0, self.cont_darken_factor, 1.0),
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        if color:
            box.set_color(
                color=color
            )

        box.set_enabled(self.enabled)
        self.containers.append(box)
        return box

    def add_header(self, collapsable, header_text, height, use_backdrop, hoverable=False, hor_marg=4, vert_marg=4, backdrop_color=None, button_color=None):
        #
        # Add a header to the box
        # The header has a function to collapse the box if enabled
        #

        # Add the box for the header to exist in

        box = CUIBoxContainer(self.modal)
        box.set_width(self.width - self.horizontal_margin*2)
        box.horizontal_margin = hor_marg
        box.vertical_margin = vert_marg
        box.draw_backdrop = use_backdrop

        box.set_color(
            color=get_modified_color(
                self.color_box, 1.0, self.cont_darken_factor, 1.0),
            color_outline=self.color_outline,
            color_font=self.color_font
        )

        box.set_style_color(
            color_box=get_modified_color(
                self.color_box, 1.0, self.cont_darken_factor, 1.0),
            color_row=get_modified_color(
                self.color_row, 1.0, self.cont_darken_factor, 1.0),
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        if backdrop_color:
            box.set_color(
                color=backdrop_color
            )

        # Add the row for the button to exist in

        row = CUIRowContainer(self.modal)
        row.set_width(box.width - box.horizontal_margin*2)

        row.set_color(
            color=get_modified_color(
                self.color_row, 1.0, self.cont_darken_factor, 1.0),
            color_outline=self.color_outline,
            color_font=self.color_font
        )

        row.set_style_color(
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        # Add the header button

        if hoverable:
            header = CUIHoverButton(row, height, header_text)
        else:
            header = CUIButton(row, height, header_text)

        # Add the arrow and collapsable function if header is collapsable
        if collapsable:
            header.set_click_up_func(self.toggle_collapse)

            arrow_size = height*0.333
            poly = header.parts[0].add_poly_shape([
                [arrow_size/2, -height/2+arrow_size/2],
                [arrow_size*1.5, -height/2],
                [arrow_size/2, -height/2-arrow_size/2]])
            poly.set_color(
                color=[0.0, 0.0, 0.9, 1.0]
            )

        header.set_color(
            color=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )
        if button_color:
            header.set_color(
                color=button_color
            )

        row.items.append(header)
        box.containers.append(row)
        self.header_box = box
        self.header = header

        box.set_enabled(self.enabled)

        self.containers.insert(0, box)
        return

    def add_text_row(self, height, text, font_size=10):
        #
        # Add a row with only a single label item
        # For convenience when adding a bunch of labels to automate the row adding
        #
        row = CUIRowContainer(self.modal)
        row.set_width(self.width - self.horizontal_margin*2)

        row.set_color(
            color=get_modified_color(
                self.color_row, 1.0, self.cont_darken_factor, 1.0),
            color_outline=self.color_outline,
            color_font=self.color_font
        )

        row.set_style_color(
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        label = row.add_label(height, text)
        label.set_font_size(font_size)
        row.set_enabled(self.enabled)
        self.containers.append(row)
        return label

    def add_row(self):
        #
        # Add an empty row container
        #
        row = CUIRowContainer(self.modal)
        row.set_width(self.width - self.horizontal_margin*2)

        row.set_color(
            color=get_modified_color(
                self.color_row, 1.0, self.cont_darken_factor, 1.0),
            color_outline=self.color_outline,
            color_font=self.color_font
        )

        row.set_style_color(
            color_item=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click
        )

        row.set_enabled(self.enabled)
        self.containers.append(row)
        return row

    #

    def test_click_down(self, mouse_co, shift, position, arguments=None):
        status = None
        if self.hover:
            # Clicking down on scroll bat so init the scroll data
            if self.scroll_bar and self.scrolling:
                if self.scroll_bar.hover:
                    self.scroll_click = True
                    self.scroll_prev_mouse[:] = mouse_co
                    status = ['BOX_SCROLL', None]

            pos = self.scale_pos_offset + position
            pos[1] += self.scroll_offset * self.scale
            for cont in self.containers:
                if cont.hover:
                    status = cont.test_click_down(
                        mouse_co, shift, pos, arguments)
                    if self.header and self.header_box == cont:
                        if self.header_box.hover:
                            if self.type == 'PANEL' or 'POPUP' in self.type:
                                status = ['PANEL_HEADER', None]
                            else:
                                status = ['BOX_HEADER', None]

            if status == None:
                status = ['PANEL', None]

        return status

    def test_click_up(self, mouse_co, shift, position, arguments=None):
        status = None
        if self.hover:

            # If scrolling then stop scrolling and reset scroll data
            if self.scroll_bar and self.scrolling:
                if self.scroll_bar.hover:
                    self.scroll_click = False
                    self.scroll_prev_mouse = np.array(
                        [0.0, 0.0], dtype=np.float32)
                    status = ['BOX_SCROLL', None]

            pos = self.scale_pos_offset + position
            pos[1] += self.scroll_offset * self.scale
            for cont in self.containers:
                if cont.hover:
                    status = cont.test_click_up(
                        mouse_co, shift, pos, arguments)
                    if self.header and self.header_box == cont:
                        if self.header_box.hover:
                            if self.type == 'PANEL' or 'POPUP' in self.type:
                                status = ['PANEL_HEADER', None]
                            else:
                                status = ['BOX_HEADER', None]

            if status == None:
                status = ['PANEL', None]
        return status

    def click_down_move(self, mouse_co, shift, position, arguments=None):
        if self.hover:
            test_containers = True

            # If scroll then offset the bar and the box if the mouse has moved far enough
            if self.scroll_bar and self.scrolling:
                if self.scroll_bar.hover and self.scroll_click:
                    test_containers = False

                    scroll_offset = int(
                        self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist))
                    fac = self.scroll_max_dist/self.scroll_max_move
                    offset = int(
                        (self.scroll_prev_mouse[1] - mouse_co[1]) * fac)
                    new_offset = int(
                        self.scroll_max_move*((self.scroll_offset+offset)/self.scroll_max_dist))

                    if abs(new_offset-scroll_offset) > 0:
                        self.scroll_box(offset)
                        self.update_batches()
                        self.scroll_prev_mouse[:] = mouse_co

            if test_containers:
                pos = self.scale_pos_offset + position
                pos[1] += self.scroll_offset * self.scale
                for cont in self.containers:
                    cont.click_down_move(mouse_co, shift, pos, arguments)
        return

    def test_hover(self, mouse_co, position):
        status = None
        if self.visible and self.enabled:
            prev_hov = self.hover

            super().test_hover(mouse_co, position)
            if self.hover:
                pos = self.scale_pos_offset + position

                # Default status is just panel
                status = 'PANEL'

                # If scrolling and a scroll bar is present check if it is hovered
                if self.scroll_bar and self.scrolling:
                    scroll_offset = int(
                        (self.scroll_max_move*(self.scroll_offset/self.scroll_max_dist)) * self.scale)
                    self.scroll_bar.test_hover(
                        mouse_co, pos - [0.0, scroll_offset])

                    # Hovering scroll bar so return early no need to test on
                    if self.scroll_bar.hover:
                        return 'PANEL_SCROLL'

                # If scrolling in a panel then test if the mouse is inside of the clip shape
                # otherwise no need to test the containers at all
                test_containers = False
                if self.scrolling and (self.type == 'PANEL' or 'POPUP' in self.type):
                    clip_pos = pos.copy()
                    clip_pos[0] += self.horizontal_margin
                    clip_pos[1] -= self.vertical_margin

                    if clip_pos[0] < mouse_co[0] < clip_pos[0]+(self.width-self.horizontal_margin*2)*self.scale:
                        if clip_pos[1] > mouse_co[1] > clip_pos[1]-(self.height+self.vertical_margin*2)*self.scale:
                            test_containers = True
                else:
                    test_containers = True

                # Test which containers/items are hovered
                if test_containers:
                    for cont in self.containers:
                        c_status = cont.test_hover(
                            mouse_co, pos + [0.0, self.scroll_offset*self.scale])
                        if c_status:
                            # If header is hovered and present return panel header
                            if self.header and self.header_box == cont and self.header.hover:
                                status = 'PANEL_HEADER'
                            # Otherwise retrun the container status
                            else:
                                status = c_status

            else:
                # Box was previously hovered so need to clear hover status since it is no longer
                if self.hover != prev_hov:
                    self.clear_hover()

        return status

    #

    def toggle_collapse(self, modal, arguments=None):
        self.collapse = not self.collapse
        self.scroll_offset = 0
        return

    def resize_width(self, width, move_fac):
        prev_width = self.scale_width
        self.set_width(width)

        # Ensure the new width is within the min/max range
        if self.min_width is not None:
            if self.width < self.min_width:
                self.set_width(self.min_width)

        if self.max_width is not None:
            if self.width > self.max_width:
                self.set_width(self.max_width)

        # If the box is a panel then reposition the panel so the resizing is clean and not jumping around
        if self.type == 'PANEL' or 'POPUP' in self.type:
            self.set_new_position(
                self.position + [(self.scale_width - prev_width)*move_fac, 0.0])

        # Resize the containers in this one
        for cont in self.containers:
            cont.resize_width(self.width-self.horizontal_margin*2, move_fac)

        return

    def scroll_box(self, value):
        self.scroll_offset += value

        if self.scroll_offset < 0:
            self.scroll_offset = 0

        elif self.scroll_offset > self.scroll_max_dist and self.collapse == False:
            self.scroll_offset = self.scroll_max_dist

        elif self.scroll_offset > 0 and self.collapse:
            self.scroll_offset = 0
        return

    def get_tooltip_lines(self):
        #
        # Check if panel has a uiitem hovered with a tooltip and reposition then make the tooltip visible
        #
        lines = None
        for cont in self.containers:
            c_lines = cont.get_tooltip_lines()
            if c_lines is not None:
                lines = c_lines
                break

        return lines

    #

    def remove_container(self, index):
        if index < len(self.containers):
            self.containers.pop(index)
        return

    def clear_rows(self):
        self.containers.clear()
        return

    def reset_item_states(self, clear_hover):
        for cont in self.containers:
            cont.reset_item_states(clear_hover)
        return

    def filter_change_custom_id(self, tar_id, new_id):
        for cont in self.containers:
            cont.filter_change_custom_id(tar_id, new_id)
        return

    def clear_hover(self):
        self.hover = False
        if self.scroll_bar:
            self.scroll_bar.clear_hover()

        for cont in self.containers:
            cont.clear_hover()
        return

    #
    # TYPE FUNCS
    #

    def type_add_key(self, key):
        for cont in self.containers:
            cont.type_add_key(key)
        return

    def type_delete_key(self):
        for cont in self.containers:
            cont.type_delete_key()
        return

    def type_move_pos(self, value):
        for cont in self.containers:
            cont.type_move_pos(value)
        return

    def type_confirm(self, arguments=None):
        for cont in self.containers:
            cont.type_confirm(arguments)
        return

    def type_cancel(self):
        for cont in self.containers:
            cont.type_cancel()
        return

    def type_backspace_key(self):
        for cont in self.containers:
            cont.type_backspace_key()
        return

    #
    # GRAPH BOX FUNCS
    #

    def graph_box_delete_points(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    status, bez_id = cont.graph_box_delete_points(
                        pos, arguments)
                    if status:
                        break
        return status, bez_id

    def graph_box_sharpen_points(self, position, offset, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, bez_id, status = cont.graph_box_sharpen_points(
                        pos, offset, arguments)
                    if status:
                        break
        return hov_status, bez_id, status

    def graph_box_rotate_points(self, position, angle, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, bez_id, status, mid_co = cont.graph_box_rotate_points(
                        pos, angle, arguments)
                    if status:
                        break
        return hov_status, bez_id, status, mid_co

    def graph_box_clear_sharpness(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.graph_box_clear_sharpness(
                        pos, arguments)
                    if status:
                        break
        return hov_status, status

    def graph_box_clear_rotation(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.graph_box_clear_rotation(
                        pos, arguments)
                    if status:
                        break
        return hov_status, status

    def graph_box_store_data(self, position, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.graph_box_store_data(
                        pos, arguments, coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
                    if status:
                        break
        return hov_status, status

    def graph_box_restore_stored_data(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.graph_box_restore_stored_data(
                        pos, arguments)
                    if status:
                        break
        return hov_status, status

    def graph_box_clear_stored_data(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.graph_box_clear_stored_data()
                    if hov_status:
                        break
        return hov_status

    def graph_box_select_points(self, status):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.graph_box_select_points(status)
                    break
        return hov_status

    def graph_box_pan(self, mouse_co, start=False):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.graph_box_pan(mouse_co, start=start)
                    if hov_status:
                        break
        return hov_status

    def graph_box_zoom(self, mouse_co, factor):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.graph_box_zoom(mouse_co, factor)
                    if hov_status:
                        break
        return hov_status

    def graph_box_home(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.graph_box_home()
                    if hov_status:
                        break
        return hov_status

    #
    # CURVE BOX FUNCS
    #

    def curve_box_delete_points(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    status, bez_id = cont.curve_box_delete_points(
                        pos, arguments)
                    if status:
                        break
        return status, bez_id

    def curve_box_sharpen_points(self, position, offset, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, bez_id, status = cont.curve_box_sharpen_points(
                        pos, offset, arguments)
                    if status:
                        break
        return hov_status, bez_id, status

    def curve_box_rotate_points(self, position, angle, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, bez_id, status, mid_co = cont.curve_box_rotate_points(
                        pos, angle, arguments)
                    if status:
                        break
        return hov_status, bez_id, status, mid_co

    def curve_box_clear_sharpness(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.curve_box_clear_sharpness(
                        pos, arguments)
                    if status:
                        break
        return hov_status, status

    def curve_box_clear_rotation(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.curve_box_clear_rotation(
                        pos, arguments)
                    if status:
                        break
        return hov_status, status

    def curve_box_store_data(self, position, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.curve_box_store_data(
                        pos, arguments, coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
                    if status:
                        break
        return hov_status, status

    def curve_box_restore_stored_data(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        pos[1] += self.scroll_offset * self.scale
        status = None
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status, status = cont.curve_box_restore_stored_data(
                        pos, arguments)
                    if status:
                        break
        return hov_status, status

    def curve_box_clear_stored_data(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.curve_box_clear_stored_data()
                    if hov_status:
                        break
        return hov_status

    def curve_box_select_points(self, status):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.curve_box_select_points(status)
                    break
        return hov_status

    def curve_box_pan(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.curve_box_pan()
                    if hov_status:
                        break
        return hov_status

    def curve_box_zoom(self):
        hov_status = False
        if self.hover:
            for cont in self.containers:
                if cont.hover:
                    hov_status = cont.curve_box_zoom()
                    if hov_status:
                        break
        return hov_status

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        if self.scroll_bar:
            self.scroll_bar.set_scale(scale)

        for cont in self.containers:
            cont.set_scale(scale)
        return

    def set_header_bev(self, size, res):
        if self.header:
            self.header.set_bev(size, res)
        return

    def set_header_color(self, color=None, color_hover=None, color_click=None, color_font=None):
        if self.header:
            self.header.set_color(
                color=color,
                color_hover=color_hover,
                color_click=color_click,
                color_font=color_font
            )
        return

    def set_header_font_size(self, size):
        if self.header:
            self.header.set_font_size(size)
        return

    def set_separation(self, sep):
        self.container_separation = sep
        return

    def set_collapsed(self, status):
        self.collapse = status
        return

    def set_button_bool(self, status, custom_id_filter=None):
        for cont in self.containers:
            cont.set_button_bool(status, custom_id_filter)
        return

    def set_color(self, color=None, color_outline=None, color_font=None):
        if color_font:
            self.color_font = color_font

        super().set_color(
            color=color,
            color_outline=color_outline
        )
        return

    def set_style_color(self, color_box=None, color_row=None, color_item=None, color_hover=None, color_click=None):
        if color_box is not None:
            self.color_box = color_box
        if color_row is not None:
            self.color_row = color_row
        if color_item is not None:
            self.color_item = color_item
        if color_hover is not None:
            self.color_hover = color_hover
        if color_click is not None:
            self.color_click = color_click
        return

    def set_header_icon_image(self, image_name, image_path):
        if self.header is not None:
            self.header.set_icon_image(image_name, image_path)
        return

    def set_header_icon_data(self, width=None, height=None, text_side=None):
        if self.header is not None:
            self.header.set_icon_data(
                width=width, height=height, text_side=text_side)
        return

    def set_enabled(self, status):
        super().set_enabled(status)
        for cont in self.containers:
            cont.set_enabled(status)
        return

    def set_cont_darken_factor(self, factor):
        self.cont_darken_factor = factor
        for cont in self.containers:
            cont.set_cont_darken_factor(factor)
        return

    #

    def __str__(self):
        return 'CUI Box Container'


class CUIRowContainer(CUIContainer):
    #
    # Row container which has all of the items
    #
    def __init__(self, modal):
        super().__init__(modal)

        self.items = []

        self.color_font = (0.0, 0.0, 1.0, 1.0)
        self.color_item = (0.0, 0.0, 0.3, 0.7)
        self.color_hover = (0.0, 0.0, 0.5, 0.7)
        self.color_click = (0.0, 0.0, 0.6, 1.0)

        self.type = 'ROW'

        self.items_separations = 4
        self.draw_backdrop = False
        return

    #

    def create_shape_data(self):
        #
        # Fit the items in the row according to min/max widths
        #
        total_height = 0
        total_height += self.vertical_margin

        x_pos = 0
        x_pos += self.horizontal_margin

        highest = 0

        # Get the available widht by subtracting the margins and separatiosn between items
        div_cnt = len(self.items)
        avail_width = self.width - self.horizontal_margin * \
            2 - self.items_separations*(div_cnt-1)
        rem_width = avail_width

        # Calc width of buttons
        # Go through all items finding if they have a max width or a special width to track
        # Items with just a normal variable fitting width are added as None
        widths = []
        for i, item in enumerate(self.items):
            # Get even width of the remaining width divded by the amount of items left
            # to factor if the special widths will fit
            even_width = rem_width/div_cnt

            # Booleans with no button are only the bool box so calculate them on their own
            if item.item_type == 'BOOLEAN' and item.use_button == False:
                # Remove from the division count add add width to list as it will fit in the even width
                if even_width > item.parts[0].bool_box_size:
                    widths.append(item.parts[0].bool_box_size)
                    div_cnt -= 1
                    rem_width -= item.parts[0].bool_box_size

                # The bool box won't fit so add None since it will need all the width it can use
                else:
                    widths.append(None)

            # If item has a max width then test if it will fit
            elif item.max_width is not None:
                # The max width is smaller than the even divisions so add it to the list and
                # Recalculate the remaining even division widths/cnts
                if even_width > item.max_width:
                    widths.append(item.max_width)
                    div_cnt -= 1
                    rem_width -= item.max_width
                else:
                    widths.append(None)
            else:
                widths.append(None)

        # If the remain division counts is more than zero then there are some items to fit inside the remaining width
        if div_cnt > 0:
            # check for any max_width items not larger than the remaining division width
            # if so scale it down accordingly

            # Get the final remaining division even widths
            even_width = rem_width/div_cnt
            for i in range(len(widths)):
                wid = widths[i]
                if wid is not None:
                    # Check if the max width is greater than the remaining divisions
                    # if so add back into the dicision count and clear the widths entry for a None
                    if wid > even_width:
                        rem_width += wid
                        div_cnt += 1
                        widths[i] = None

            # Get final even width for all items
            even_width = rem_width/div_cnt
            for i in range(len(widths)):
                if widths[i] == None:
                    widths[i] = even_width

        # Place items in row
        for i, item in enumerate(self.items):
            item.set_width(widths[i])
            item.set_pos_offset_x(x_pos)
            item.set_pos_offset_y(-total_height)
            item.create_shape_data()

            x_pos += item.width
            if i < len(self.items)-1:
                x_pos += self.items_separations

            if item.height > highest:
                highest = item.height

        # Offset the position if there is remaining space between the end x position and the right edge of the box
        # So that the items are centered in the row
        if self.width-self.horizontal_margin > x_pos:
            for i, item in enumerate(self.items):
                item.offset_pos_offset_x((self.width -
                                          self.horizontal_margin-x_pos)/2)

        # Check for items that have a smaller size than highest and replace in middle of row vertically
        for i, item in enumerate(self.items):
            if item.height < highest:
                offset = (highest-item.height) // 2
                item.offset_pos_offset_y(offset)

        # Add to total height and set height
        total_height += highest
        total_height += self.vertical_margin
        self.set_height(total_height)

        super().create_shape_data()
        return

    def update_batches(self, position=[0.0, 0.0]):
        super().update_batches(position)
        for item in self.items:
            item.update_batches(self.scale_pos_offset + position)
        return

    #

    def draw(self):
        super().draw()
        if self.visible:
            for item in self.items:
                item.draw()
        return

    #
    # ADD ITEM FUNCS
    #

    def add_button(self, height, text):
        but = CUIButton(self, height, text)

        but.set_color(
            color=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )

        but.set_enabled(self.enabled)
        self.items.append(but)
        return but

    def add_hover_button(self, height, text):
        hbut = CUIHoverButton(self, height, text)

        hbut.set_color(
            color=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )

        hbut.set_enabled(self.enabled)
        self.items.append(hbut)
        return hbut

    def add_bool(self, height, text, default=False):
        boolean = CUIBoolProp(self, height,
                              text, default_val=default)

        boolean.set_color(
            color=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )

        boolean.set_enabled(self.enabled)
        self.items.append(boolean)
        return boolean

    def add_label(self, height, text):
        label = CUILabel(self, height, text)

        label.set_color(
            color=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )

        label.set_enabled(self.enabled)
        self.items.append(label)
        return label

    def add_spacer(self, height, width):
        spacer = CUISpacer(self, height, width)
        self.items.append(spacer)
        return spacer

    def add_number(self, height, text, default, decimals, step, min, max):
        num = CUINumProp(self, height, text,
                         default, decimals, step, min, max)

        num.set_color(
            color=self.color_item,
            color_hover=self.color_hover,
            color_click=self.color_click,
            color_font=self.color_font
        )

        num.set_value(default)
        num.set_enabled(self.enabled)
        self.items.append(num)
        return num

    def add_curve_box(self, height, type, points=None):
        use_default = False
        if points == None:
            use_default = True
        if points is not None:
            if len(points) < 2:
                use_default = True

        if use_default:
            bez = CUICurveBox(
                self, height, type, [[0.0, 1.0], [1.0, 0.0]])
        else:
            bez = CUICurveBox(self, height, type, points)

        bez.set_enabled(self.enabled)
        self.items.append(bez)
        return bez

    def add_grid_box(self, height, frame_start, frame_end):
        grid = CUIFrameGrid(self, height, frame_start, frame_end)

        grid.set_enabled(self.enabled)
        self.items.append(grid)
        return grid

    #
    # TEST CLICK FUNCS
    #

    def test_click_down(self, mouse_co, shift, position, arguments=None):
        status = None
        if self.hover:
            pos = self.scale_pos_offset + position
            for item in self.items:
                if item.hover:
                    item.click_down = True
                    status = item.click_down_func(
                        mouse_co, shift, pos, arguments)
        return status

    def test_click_up(self, mouse_co, shift, position, arguments=None):
        status = None
        if self.hover:
            pos = self.scale_pos_offset + position
            for item in self.items:
                if item.hover:
                    item.click_down = False
                    status = item.click_up_func(
                        mouse_co, shift, pos, arguments)
        return status

    def click_down_move(self, mouse_co, shift, position, arguments=None):
        if self.hover:
            pos = self.scale_pos_offset + position
            for item in self.items:
                item.click_down_move(mouse_co, shift, pos, arguments)
        return

    def test_hover(self, mouse_co, position):
        prev_hov = self.hover

        status = None
        super().test_hover(mouse_co, position)
        if self.hover:
            pos = self.scale_pos_offset + position
            for item in self.items:
                i_status = item.test_hover(
                    mouse_co, pos)
                if i_status:
                    status = i_status

        else:
            # Box was previously hovered so need to clear hover status since it is no longer
            if self.hover != prev_hov:
                self.clear_hover()

        return status

    def get_tooltip_lines(self):
        #
        # Check if panel has a uiitem hovered with a tooltip and reposition then make the tooltip visible
        #
        lines = None
        for item in self.items:
            if item.hover and item.visible:
                lines = item.get_tooltip_lines()
                break

        return lines

    #

    def resize_width(self, width, move_fac):
        self.set_width(width)
        # for item in self.items:
        #     if item.item_type == 'FRAME_GRID':
        #         item.resize_width()
        return

    def filter_change_custom_id(self, tar_id, new_id):
        for item in self.items:
            if item.custom_id == tar_id:
                item.custom_id = new_id
        return

    #

    def clear_hover(self):
        self.hover = False
        for item in self.items:
            item.clear_hover()
        return

    def reset_item_states(self, clear_hover):
        for item in self.items:
            item.reset_item_states(clear_hover)
        return

    def remove_item(self, index):
        if index < len(self.items):
            self.items.pop(index)
        return

    #
    # TYPE FUNCS
    #

    def type_add_key(self, key):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_add_key(key)
        return

    def type_delete_key(self):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_delete_key()
        return

    def type_move_pos(self, value):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_move_pos(value)
        return

    def type_confirm(self, arguments=None):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_confirm(arguments)
        return

    def type_cancel(self):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_cancel()
        return

    def type_backspace_key(self):
        for item in self.items:
            if item.item_type == 'NUMBER':
                item.type_backspace_key()
        return

    #
    # GRAPH BOX FUNCS
    #

    def graph_box_delete_points(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    item.graph_box_delete_points(
                        pos, arguments)
                    status = True
                    bez_id = item.custom_id
                    break
        return status, bez_id

    def graph_box_sharpen_points(self, position, offset, arguments=None):
        pos = self.scale_pos_offset + position
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    status = item.graph_box_sharpen_points(
                        pos, offset, arguments)
                    hov_status = True
                    bez_id = item.custom_id
                    break
        return hov_status, bez_id, status

    def graph_box_rotate_points(self, position, angle, arguments=None):
        pos = self.scale_pos_offset + position
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    status, mid_co = item.graph_box_rotate_points(
                        pos, angle, arguments)
                    hov_status = True
                    bez_id = item.custom_id
                    break
        return hov_status, bez_id, status, mid_co

    def graph_box_clear_sharpness(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    status = item.graph_box_clear_sharpness(
                        pos, arguments)
                    hov_status = True
                    break
        return hov_status, status

    def graph_box_clear_rotation(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    status = item.graph_box_clear_rotation(
                        pos, arguments)
                    hov_status = True
                    break
        return hov_status, status

    def graph_box_store_data(self, position, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    status = item.graph_box_store_data(
                        pos, arguments, coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
                    hov_status = True
                    break
        return hov_status, status

    def graph_box_restore_stored_data(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    status = item.graph_box_restore_stored_data(
                        pos, arguments)
                    hov_status = True
                    break
        return hov_status, status

    def graph_box_clear_stored_data(self):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    item.graph_box_clear_stored_data()
                    hov_status = True
                    break
        return hov_status

    def graph_box_select_points(self, status):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'GRAPH_BOX':
                    item.graph_box_select_points(status)
                    hov_status = True
                    break
        return hov_status

    def graph_box_pan(self, mouse_co, start=False):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'FRAME_GRID':
                    item.graph_box_pan(mouse_co, start=start)
                    hov_status = True
                    break
        return hov_status

    def graph_box_zoom(self, mouse_co, factor):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'FRAME_GRID':
                    item.graph_box_zoom(mouse_co, factor)
                    hov_status = True
                    break
        return hov_status

    def graph_box_home(self):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'FRAME_GRID':
                    item.graph_box_home()
                    hov_status = True
                    break
        return hov_status

    #
    # CURVE BOX FUNCS
    #

    def curve_box_delete_points(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    item.curve_box_delete_points(
                        pos, arguments)
                    status = True
                    bez_id = item.custom_id
                    break
        return status, bez_id

    def curve_box_sharpen_points(self, position, offset, arguments=None):
        pos = self.scale_pos_offset + position
        status = False
        hov_status = False
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    status = item.curve_box_sharpen_points(
                        pos, offset, arguments)
                    hov_status = True
                    bez_id = item.custom_id
                    break
        return hov_status, bez_id, status

    def curve_box_rotate_points(self, position, angle, arguments=None):
        pos = self.scale_pos_offset + position
        status = False
        hov_status = False
        mid_co = None
        bez_id = None
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    status, mid_co = item.curve_box_rotate_points(
                        pos, angle, arguments)
                    hov_status = True
                    bez_id = item.custom_id
                    break
        return hov_status, bez_id, status, mid_co

    def curve_box_clear_sharpness(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    status = item.curve_box_clear_sharpness(
                        pos, arguments)
                    hov_status = True
                    break
        return hov_status, status

    def curve_box_clear_rotation(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    status = item.curve_box_clear_rotation(
                        pos, arguments)
                    hov_status = True
                    break
        return hov_status, status

    def curve_box_store_data(self, position, arguments=None, coords=False, handles=False, sharpness=False, rotations=False):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    status = item.curve_box_store_data(
                        pos, arguments, coords=coords, handles=handles, sharpness=sharpness, rotations=rotations)
                    hov_status = True
                    break
        return hov_status, status

    def curve_box_restore_stored_data(self, position, arguments=None):
        pos = self.scale_pos_offset + position
        status = None
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    status = item.curve_box_restore_stored_data(
                        pos, arguments)
                    hov_status = True
                    break
        return hov_status, status

    def curve_box_clear_stored_data(self):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    item.curve_box_clear_stored_data()
                    hov_status = True
                    break
        return hov_status

    def curve_box_select_points(self, status):
        hov_status = False
        if self.hover:
            for item in self.items:
                if item.hover and item.item_type == 'CURVE_BOX':
                    item.curve_box_select_points(status)
                    hov_status = True
                    break
        return hov_status

    #

    def set_scale(self, scale):
        super().set_scale(scale)
        for item in self.items:
            item.set_scale(scale)
        return

    def set_button_bool(self, status, custom_id_filter=None):
        for item in self.items:
            if item.item_type == 'BUTTON':
                if custom_id_filter is not None:
                    if item.custom_id == custom_id_filter:
                        item.set_bool(status)
                else:
                    item.set_bool(status)
        return

    def set_color(self, color=None, color_outline=None, color_font=None):
        if color_font:
            self.color_font = color_font

        super().set_color(
            color=color,
            color_outline=color_outline
        )

        return

    def set_style_color(self, color_item=None, color_hover=None, color_click=None):
        if color_item is not None:
            self.color_item = color_item
        if color_hover is not None:
            self.color_hover = color_hover
        if color_click is not None:
            self.color_click = color_click
        return

    def set_enabled(self, status):
        super().set_enabled(status)
        for item in self.items:
            item.set_enabled(status)
        return

    #

    def __str__(self):
        return 'CUI Row Container'
