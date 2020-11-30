# This Python file uses the following encoding: utf-8
from enum import IntEnum
from PySide2.QtCore import Qt

class TreeWidgetType(IntEnum):
    SONG = 0
    ALBUM = 1
    PLACEHOLDER = 2

class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole
