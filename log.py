# This Python file uses the following encoding: utf-8
from PySide2 import QtCore
from PySide2.QtWidgets import QTextEdit
from PySide2.QtGui import QColor

import logging
import sys
import traceback

from settings import get_setting


def convert_log_level(level: str):
    """Converts from LogLevel combobox text to Python log level value"""
    return getattr(logging, level)

class LogWidgetFormatter(logging.Formatter):
    def __init__(self, *args):
        logging.Formatter.__init__(self, *args)

    def format(self, record):
        return super().format(record).strip()


class LogWidgetLogger(logging.Handler):

    COLORS = {
        "WARNING": QColor("yellow"),
        "INFO": QColor("darkGray"),
        "DEBUG": QColor("blue"),
        "CRITICAL": QColor("red"),
        "ERROR": QColor("red")
    }

    def __init__(self, parent: QTextEdit):
        super().__init__()
        self.widget = parent
        self.widget.setReadOnly(True)

    def emit(self, record):
        color = self.COLORS[record.levelname]
        self.widget.setTextColor(color)
        self.widget.append(self.format(record))


class LogWidget(QTextEdit):

    def __init__(self, *args):
        super().__init__(*args)

        log_handler = LogWidgetLogger(self)
        log_handler.setFormatter(LogWidgetFormatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)
        sys.excepthook = self.exception_handler

    def exception_handler(self, type, value, trace):
        logging.error("".join(traceback.format_tb(trace)))
        logging.error("Uncaught exception: {0}".format(value))
        sys.__excepthook__(type, value, trace)

    def update_settings(self):
        new_level = convert_log_level(get_setting("logLevel"))
        logging.getLogger().setLevel(new_level)
