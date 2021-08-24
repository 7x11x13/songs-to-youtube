import atexit
from enum import IntEnum

from PySide6.QtCore import *


class TreeWidgetType(IntEnum):
    SONG = 0
    ALBUM = 1


class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole
    ITEMDATA = Qt.UserRole + 1


ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"
VERSION = "v0.11.12"
SETTINGS_FILENAME = "v0.8settings"

SUPPORTED_IMAGE_FILTER = "Images (*.bmp *.cur *.gif *.icns *.ico *.jpeg *.jpg *.pbm *.pgm *.png *.ppm *.svg *.svgz *.tga *.tif *.tiff *.wbmp *.webp *.xbm *.xpm)"


QDir.temp().mkdir(APPLICATION)
QRC_TO_FILE_PATH = {
    ":/image/default.jpg": QDir.temp().absoluteFilePath(
        "./{}/qrc_default.jpg".format(APPLICATION)
    )
}

for qrc, file in QRC_TO_FILE_PATH.items():
    # unpack resources so ffmpeg can use them
    QFile.copy(qrc, file)

# clear temp dir on exit
def clean_up_images():
    temp_dir = QDir("{}/{}".format(QDir().tempPath(), APPLICATION))
    for file in temp_dir.entryList():
        temp_dir.remove(file)


atexit.register(clean_up_images)
