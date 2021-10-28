from .functions_modal import *


class GEN_Modal_Container:
    def __init__(self):
        self.tools = []
        self.pass_through_events = []
        self.cancel_keys = []
        self.confirm_keys = []
        self.end_tool_function = None
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

        if self.end_tool_function is not None:
            tool.set_end_tool_function(self.end_tool_function)

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

    def set_end_tool_function(self, func):
        self.end_tool_function = func
        return

    #

    def __str__(self):
        return 'Generic Modal Tool Container'


class GEN_Modal_Tool:
    def __init__(self):
        self.start_arguments = []
        self.arguments = []
        self.pass_through_events = []
        self.cancel_keys = []
        self.confirm_keys = []

        self.use_start = False
        self.initialized = False
        self.passing_through = False
        self.mouse_pass_through = False

        self.timer_function = None
        self.always_function = None
        self.mouse_function = None
        self.cancel_function = None
        self.confirm_function = None
        self.pre_pass_through_function = None
        self.post_pass_through_function = None
        self.end_tool_function = None
        self.end_tool_confirm = True
        self.end_tool_cancel = True
        return

    def test_mode(self, modal, context, event, keymap, pass_in_data):
        status = {"RUNNING_MODAL"}

        if self.passing_through:
            self.passing_through = False
            if self.post_pass_through_function is not None:
                self.post_pass_through_function(
                    modal, context, event, pass_in_data)

        is_started = True
        # Check start function
        if self.use_start and self.initialized == False:
            is_started = False

        # Call timer function
        if self.always_function is not None:
            self.always_function(modal, context, event, pass_in_data)

        # Call timer function
        if self.timer_function is not None:
            self.timer_function(modal, context, event, pass_in_data)

        # Call mouse move function
        if self.mouse_function is not None and is_started:
            if event.type == 'MOUSEMOVE':
                if self.mouse_pass_through:
                    status = {"PASS_THROUGH"}
                self.mouse_function(modal, context, event, pass_in_data)
                return status

        # Get keys from keymap
        keys = keys_find(keymap.keymap_items, event)

        if len(keys) > 0:
            # Check for cancelation key
            if self.cancel_function is not None or self.end_tool_function is not None:
                for c_key in self.cancel_keys:
                    if c_key in keys:
                        if self.cancel_function is not None:
                            # Call cancel function
                            canc_status = self.cancel_function(
                                modal, context, event, keys, pass_in_data)
                            if canc_status is not None:
                                status = canc_status

                        if self.use_start:
                            self.initialized = False

                        if self.end_tool_function is not None and self.end_tool_cancel:
                            self.end_tool_function(
                                modal, context, event, keys, pass_in_data)
                        return status

            # Check for confirm key
            if (self.confirm_function is not None or self.end_tool_function is not None) and is_started:
                for c_key in self.confirm_keys:
                    if c_key in keys:
                        if self.confirm_function is not None:
                            # Call confirm function
                            conf_status = self.confirm_function(
                                modal, context, event, keys, pass_in_data)
                            if conf_status is not None:
                                status = conf_status

                        if self.use_start:
                            self.initialized = False

                        if self.end_tool_function is not None and self.end_tool_confirm:
                            self.end_tool_function(
                                modal, context, event, keys, pass_in_data)
                        return status

            # Check for argument key
            for argument in self.arguments:
                if (is_started == False and argument.pre_start) or (is_started and argument.pre_start == False):
                    if argument.key in keys:
                        # Call argument function
                        arg_status = argument.function(modal, context, event,
                                                       keys, pass_in_data)
                        if arg_status is not None:
                            status = arg_status
                        return status

            if is_started == False:
                for start_argument in self.start_arguments:
                    if start_argument.key in keys:
                        # Call argument function
                        arg_status = start_argument.function(
                            modal, context, event, keys, pass_in_data)
                        self.initialized = True
                        if arg_status is not None:
                            status = arg_status
                        return status

        # Check for a passthrough event type
        pass_keys = keys_find(self.pass_through_events, event)
        if len(pass_keys) > 0:
            status = {'PASS_THROUGH'}
            self.passing_through = True
            if self.pre_pass_through_function is not None:
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

    def set_end_tool_cancel(self, status):
        self.end_tool_cancel = status
        return

    def set_end_tool_confirm(self, status):
        self.end_tool_confirm = status
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

    def set_end_tool_function(self, func):
        self.end_tool_function = func
        return

    def set_mouse_function(self, func):
        self.mouse_function = func
        return

    def set_timer_function(self, func):
        self.timer_function = func
        return

    def set_always_function(self, func):
        self.always_function = func
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
        self.start_arguments.append(arg)
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
