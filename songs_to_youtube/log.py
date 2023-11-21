import logging
import sys
import traceback

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTextEdit

from songs_to_youtube.const import *
from songs_to_youtube.settings import *


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    https://stackoverflow.com/a/35804945

    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError("{} already defined in logging module".format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError("{} already defined in logging module".format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError("{} already defined in logger class".format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


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
        "WARNING": QColor("orange"),
        "INFO": QColor("black"),
        "DEBUG": QColor("blue"),
        "CRITICAL": QColor("red"),
        "ERROR": QColor("red"),
        "SUCCESS": QColor("green"),
    }

    def __init__(self, parent: QTextEdit):
        super().__init__()
        self.widget = parent
        self.widget.setReadOnly(True)

    def emit(self, record):
        color = self.COLORS[record.levelname]
        self.widget.setTextColor(color)
        self.widget.append(self.format(record))
        self.widget.verticalScrollBar().setValue(
            self.widget.verticalScrollBar().maximum()
        )


class LogWidget(QTextEdit):
    def __init__(self, *args):
        super().__init__(*args)

        self.logger = logging.getLogger(APPLICATION)

        log_handler = LogWidgetLogger(self)
        log_handler.setFormatter(
            LogWidgetFormatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")
        )
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.INFO)
        sys.excepthook = self.exception_handler
        self.update_settings()

    def exception_handler(self, type, value, trace):
        self.logger.error("".join(traceback.format_tb(trace)))
        self.logger.error(f"{type} {value}")
        sys.__excepthook__(type, value, trace)

    def update_settings(self):
        try:
            new_level = convert_log_level(get_setting("logLevel"))
        except:
            new_level = logging.ERROR
        self.logger.setLevel(new_level)
