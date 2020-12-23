# This Python file uses the following encoding: utf-8

from enum import Enum

ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"

class SETTINGS_VALUES:

    MULTIPLE_VALUES = "<<Multiple values>>"

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
        MULTIPLE_PLAYLIST = "Multiple videos (playlist)"

    class VideoVisibility(str, Enum):
        PUBLIC = "Public"
        UNLISTED = "Unlisted"

    class CheckBox(str, Enum):
        UNCHECKED = "PySide2.QtCore.Qt.CheckState.Unchecked"
        PARTIALLY_CHECKED = "PySide2.QtCore.Qt.CheckState.PartiallyChecked"
        CHECKED = "PySide2.QtCore.Qt.CheckState.Checked"
