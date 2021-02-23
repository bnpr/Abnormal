from .functions_modal import *


class GEN_Modal_Container:
    def __init__(self):
        self.tools = []
        self.pass_through_events = []
        self.cancel_keys = []
        self.confirm_keys = []
        return

    #

    def add_tool(self, inherit_pass_thru=True, inherit_cancel=True, inherit_confirm=True):
        tool = GEN_Modal_Tool()
        if inherit_pass_thru:
            tool.pass_through_events += self.pass_through_events
        if inherit_cancel:
            tool.cancel_keys += self.cancel_keys
        if inherit_confirm:
            tool.confirm_keys += self.confirm_keys

        self.tools.append(tool)
        return tool

    def add_cancel_key(self, key):
        self.cancel_keys.append(key)
        return

    def add_confirm_key(self, key):
        self.confirm_keys.append(key)
        return

    def add_pass_through_event(self, event):
        self.pass_through_events.append(event)
        return

    #

    def add_cancel_keys(self, keys):
        self.cancel_keys += keys
        return

    def add_confirm_keys(self, keys):
        self.confirm_keys += keys
        return

    def add_pass_through_events(self, events):
        self.pass_through_events += events
        return

    #

    def set_cancel_keys(self, keys):
        self.cancel_keys = keys
        return

    def set_confirm_keys(self, keys):
        self.confirm_keys = keys
        return

    def set_pass_through_events(self, events):
        self.pass_through_events = events
        return

    #

    def __str__(self):
        return 'Generic Modal Tool Container'


class GEN_Modal_Tool:
    def __init__(self):
        self.arguments = []
        self.pass_through_events = []
        self.cancel_keys = []
        self.confirm_keys = []

        self.use_start = True
        self.initialized = False
        self.passing_through = False
        self.mouse_pass_through = False

        self.start_argument = None
        self.mouse_function = None
        self.cancel_function = None
        self.confirm_function = None
        self.pre_pass_through_function = None
        self.post_pass_through_function = None
        return

    def test_mode(self, modal, context, event, keymap, pass_in_data):
        status = {"RUNNING_MODAL"}

        if self.passing_through:
            self.passing_through = False
            if self.post_pass_through_function != None:
                self.post_pass_through_function(
                    modal, context, event, pass_in_data)

        is_started = True
        # Check start function
        if self.use_start and self.start_argument != None and self.initialized == False:
            is_started = False

        # Call mouse move function
        if self.mouse_function != None and is_started:
            if event.type == 'MOUSEMOVE':
                if self.mouse_pass_through:
                    status = {"PASS_THROUGH"}
                self.mouse_function(modal, context, event, pass_in_data)
                return status

        # Get keys from keymap
        keys = keys_find(keymap.keymap_items, event)

        if len(keys) > 0:
            # Check for cancelation key
            if self.cancel_function != None:
                for c_key in self.cancel_keys:
                    if c_key in keys:
                        # Call cancel function
                        self.cancel_function(
                            modal, context, event, keys, pass_in_data)
                        if self.use_start:
                            self.initialized = False
                        return status

            # Check for confirm key
            if self.confirm_function != None and is_started:
                for c_key in self.confirm_keys:
                    if c_key in keys:
                        # Call confirm function
                        self.confirm_function(
                            modal, context, event, keys, pass_in_data)
                        if self.use_start:
                            self.initialized = False
                        return status

            # Check for argument key
            for argument in self.arguments:
                if (is_started == False and argument.pre_start) or (is_started and argument.pre_start == False):
                    if argument.key in keys:
                        # Call argument function
                        argument.function(modal, context, event,
                                          keys, pass_in_data)
                        return status

            if is_started == False:
                if self.start_argument.key in keys:
                    # Call argument function
                    self.start_argument.function(
                        modal, context, event, keys, pass_in_data)
                    self.initialized = True
                    return status

        # Check for a passthrough event type
        nav_status = test_navigation_key(self.pass_through_events, event)
        if nav_status:
            status = {'PASS_THROUGH'}
            self.passing_through = True
            if self.pre_pass_through_function != None:
                self.pre_pass_through_function(
                    modal, context, event, pass_in_data)

        return status

    #

    def restart(self):
        self.initialized = False
        return

    def clear_data(self):
        for arg in self.arguments:
            arg.clear_data()

        self.arguments.clear()
        self.pass_through_events.clear()
        self.cancel_keys.clear()
        self.confirm_keys.clear()

        self.cancel_function = None
        self.confirm_function = None
        return

    #

    def set_mouse_pass(self, status):
        self.mouse_pass_through = status
        return

    def set_use_start(self, status):
        self.use_start = status
        return

    def set_cancel_function(self, func):
        self.cancel_function = func
        return

    def set_confirm_function(self, func):
        self.confirm_function = func
        return

    def set_pre_pass_through_function(self, func):
        self.pre_pass_through_function = func
        return

    def set_post_pass_through_function(self, func):
        self.post_pass_through_function = func
        return

    def set_mouse_function(self, func):
        self.mouse_function = func
        return

    #

    def add_cancel_key(self, key):
        self.cancel_keys.append(key)
        return

    def add_confirm_key(self, key):
        self.confirm_keys.append(key)
        return

    def add_keymap_argument(self, key, func, pre_start=False):
        arg = GEN_Argument_Function(key, func, pre_start)
        self.arguments.append(arg)
        return arg

    def add_start_argument(self, key, func):
        arg = GEN_Argument_Function(key, func)
        self.start_argument = arg
        return arg

    #

    def __str__(self):
        return 'Generic Modal Tool'


class GEN_Argument_Function:
    def __init__(self, key, func, pre_start=False):
        self.key = key
        self.function = func
        self.pre_start = pre_start
        return

    def set_pre_start(self, status):
        self.pre_start = status
        return

    def clear_data(self):
        self.key = None
        self.function = None
        return

    def __str__(self):
        return 'Generic Modal Function Argument'
