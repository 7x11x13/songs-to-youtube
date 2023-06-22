from enum import IntEnum, auto

from PySide6.QtCore import *


class TreeWidgetType(IntEnum):
    SONG = auto()
    ALBUM = auto()


class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole
    ITEMDATA = Qt.UserRole + 1


ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"
VERSION = "v0.11.22"
SETTINGS_FILENAME = "v0.8settings"

SUPPORTED_IMAGE_FILTER = "Images (*.bmp *.cur *.gif *.icns *.ico *.jpeg *.jpg *.pbm *.pgm *.png *.ppm *.svg *.svgz *.tga *.tif *.tiff *.wbmp *.webp *.xbm *.xpm)"
