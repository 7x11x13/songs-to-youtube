# This Python file uses the following encoding: utf-8

from PySide6.QtCore import Qt, QFile, QDir

from enum import Enum, IntEnum

import resource
import atexit

class TreeWidgetType(IntEnum):
    SONG = 0
    ALBUM = 1


class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole
    ITEMDATA = Qt.UserRole + 1

ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"

SUPPORTED_IMAGE_FILTER = "Images (*.bmp *.cur *.gif *.icns *.ico *.jpeg *.jpg *.pbm *.pgm *.png *.ppm *.svg *.svgz *.tga *.tif *.tiff *.wbmp *.webp *.xbm *.xpm)"

class SETTINGS_VALUES:

    MULTIPLE_VALUES = "<<Multiple values>>"
    MULTIPLE_VALUES_IMG = ":/image/multiple-values.png"

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
        PUBLIC = "Public"
        UNLISTED = "Unlisted"

    class CheckBox(str, Enum):
        UNCHECKED = "PySide2.QtCore.Qt.CheckState.Unchecked"
        PARTIALLY_CHECKED = "PySide2.QtCore.Qt.CheckState.PartiallyChecked"
        CHECKED = "PySide2.QtCore.Qt.CheckState.Checked"


SETTINGS_DEFAULTS = {
    "deleteAfterUploading": SETTINGS_VALUES.CheckBox.CHECKED,
    "fileOutputDir": "~{song_dir}",
    "fileOutputName": "~{song_file}.avi",
    "fileOutputDirAlbum": "~{album_dir}",
    "fileOutputNameAlbum": "~{song.tags.album}.avi",
    "coverArt": ":/image/default.jpg",
    "extractCoverArt": SETTINGS_VALUES.CheckBox.CHECKED,
    "backgroundColor": "black",
    "dragAndDropBehavior": SETTINGS_VALUES.DragAndDrop.ALBUM_MODE,
    "maxProcesses": "8",
    "logLevel": SETTINGS_VALUES.LogLevel.DEBUG,
    "videoHeight": "720",
    "videoWidth": "1280",
    "uploadYouTube": SETTINGS_VALUES.CheckBox.CHECKED,
    "albumPlaylist": SETTINGS_VALUES.AlbumPlaylist.MULTIPLE,
    "videoDescription": "Uploaded with https://github.com/7x11x13/songs-to-youtube",
    "videoTags": "",
    "playlistName": "~{tags.artist} - ~{tags.album}",
    "videoTitle": "~{tags.artist} - ~{tags.title}",
    "videoDescriptionAlbum": "~{timestamps}\nUploaded with https://github.com/7x11x13/songs-to-youtube",
    "videoTagsAlbum": "",
    "videoTitleAlbum": "~{song.tags.artist} - ~{song.tags.album}",
    "videoVisibility": SETTINGS_VALUES.VideoVisibility.PUBLIC,
    "inputFrameRate": "5"
}

SONG_FIELDS = set(('inputFrameRate', 'backgroundColor', 'videoHeight', 'videoWidth',
                   'uploadYouTube', 'coverArt', 'videoDescription', 'videoTags',
                   'videoTitle', 'videoVisibility', 'fileOutputDir', 'fileOutputName',
                   'playlistName'))
ALBUM_FIELDS = set(('albumPlaylist', 'fileOutputDirAlbum', 'fileOutputNameAlbum',
                    'uploadYouTube', 'videoDescriptionAlbum', 'videoTagsAlbum', 'videoTitleAlbum'))


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
    temp_dir.setNameFilters(["*.cover"])
    for file in temp_dir.entryList():
        temp_dir.remove(file)

atexit.register(clean_up_images)
