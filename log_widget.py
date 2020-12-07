# This Python file uses the following encoding: utf-8
from PySide2 import QtCore
from PySide2.QtWidgets import QPlainTextEdit

import logging


class LogWidgetFormatter(logging.Formatter):

    COLORS = {
        "WARNING": "<font color='Yellow'>%s</font>",
        "INFO": "<font color='Gray'>%s</font>",
        "DEBUG": "<font color='Blue'>%s</font>",
        "CRITICAL": "<font color='Yellow'>%s</font>",
        "ERROR": "<font color='Red'>%s</font>"
    }

    def __init__(self, *args):
        logging.Formatter.__init__(self, *args)

    def format(self, record):
        color_format = self.COLORS[record.levelname]
        return color_format % super().format(record)


class LogWidgetLogger(logging.Handler):
    def __init__(self, parent: QPlainTextEdit):
        super().__init__()
        self.widget = parent
        self.widget.setReadOnly(True)

    def emit(self, record):
        self.widget.appendHtml(self.format(record))


class LogWidget(QPlainTextEdit):
    def __init__(self, *args):
        super().__init__(*args)

        log_handler = LogWidgetLogger(self)
        log_handler.setFormatter(LogWidgetFormatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.DEBUG)
