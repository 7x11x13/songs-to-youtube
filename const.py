# This Python file uses the following encoding: utf-8
from enum import IntEnum
from PySide2.QtCore import Qt

class TreeWidgetType(IntEnum):
    SONG = 0
    ALBUM = 1
    PLACEHOLDER = 2

class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole

ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"

SETTINGS_WIDGETS = {
    "application/dragAndDrop": {
        "widget_name": "dragAndDropBehavior",
        "getter": "currentIndex",
        "setter": "setCurrentIndex",
        "default": 0
    },
    "application/logLevel": {
        "widget_name": "logLevel",
        "getter": "currentIndex",
        "setter": "setCurrentIndex",
        "default": 2
    }
}

class SETTINGS_VALUES:
    class DragAndDrop(IntEnum):
        ALBUM_MODE = 0
        SONG_MODE = 1

    class LogLevel(IntEnum):
        DEBUG = 0
        INFO = 1
        WARNING = 2
        ERROR = 3
        CRITICAL = 4
