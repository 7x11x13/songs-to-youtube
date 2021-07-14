# This Python file uses the following encoding: utf-8

from PySide6.QtCore import Qt, QFile, QDir

from enum import Enum, IntEnum

import atexit

class TreeWidgetType(IntEnum):
    SONG = 0
    ALBUM = 1


class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole
    ITEMDATA = Qt.UserRole + 1

ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"
VERSION = "v0.11.2"
SETTINGS_FILENAME = "v0.8settings"

SUPPORTED_IMAGE_FILTER = "Images (*.bmp *.cur *.gif *.icns *.ico *.jpeg *.jpg *.pbm *.pgm *.png *.ppm *.svg *.svgz *.tga *.tif *.tiff *.wbmp *.webp *.xbm *.xpm)"

class SETTINGS_VALUES:

    MULTIPLE_VALUES = "<<Multiple values>>"
    MULTIPLE_VALUES_IMG = ":/image/multiple-values.png"

    # combo box values

    class DragAndDrop(str, Enum):
        ALBUM_MODE = "Album mode"
        SONG_MODE = "Song mode"

    class LogLevel(str, Enum):
        DEBUG = "DEBUG"
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"

    class AlbumPlaylist(str, Enum):
        MULTIPLE = "Multiple videos"
        SINGLE = "Single video"

    class VideoVisibility(str, Enum):
        PUBLIC = "PUBLIC"
        UNLISTED = "UNLISTED"

    COMBO_BOX_VALUES = {
        "dragAndDropBehavior": [item.value for item in DragAndDrop],
        "logLevel": [item.value for item in LogLevel],
        "albumPlaylist": [item.value for item in AlbumPlaylist],
        "videoVisibility": [item.value for item in VideoVisibility],
        "videoVisibilityAlbum": [item.value for item in VideoVisibility]
    }

    class CheckBox(str, Enum):
        UNCHECKED = "PySide6.QtCore.Qt.CheckState.Unchecked"
        PARTIALLY_CHECKED = "PySide6.QtCore.Qt.CheckState.PartiallyChecked"
        CHECKED = "PySide6.QtCore.Qt.CheckState.Checked"

SONG_FIELDS = set(('backgroundColor', 'videoHeight', 'videoWidth',
                   'uploadYouTube', 'coverArt', 'videoDescription', 'videoTags',
                   'videoTitle', 'videoVisibility', 'fileOutputDir', 'fileOutputName',
                   'playlistName', 'commandName', 'notifySubs'))
ALBUM_FIELDS = set(('albumPlaylist', 'fileOutputDirAlbum', 'fileOutputNameAlbum',
                    'uploadYouTube', 'videoDescriptionAlbum', 'videoTagsAlbum', 'videoTitleAlbum',
                    'videoVisibilityAlbum', 'notifySubsAlbum', 'concatCommandName'))


QDir.temp().mkdir(APPLICATION)
QRC_TO_FILE_PATH = {
    ":/image/default.jpg": QDir.temp().absoluteFilePath("./{}/qrc_default.jpg".format(APPLICATION))
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
