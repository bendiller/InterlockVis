import logging

gui_log_formatter = logging.Formatter("%(levelname)s: %(message)s")


class GuiHandler(logging.Handler):
    """
    Custom handler to allow for overriding emit() with function call to PySimpleGui's preferred method of passing data
    between threads (window.write_event_value).
    """

    def __init__(self, level=logging.NOTSET, window_writer=None):
        self.window_writer = window_writer  # Will always be write_event_value method belonging to a Window instance
        super().__init__(level)

    def emit(self, record):
        self.window_writer('-LOG-', f"{self.format(record)}")
