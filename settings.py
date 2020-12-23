# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Signal, QSettings, Qt
from PySide2.QtWidgets import QDialog

import logging
from enum import Enum

from utils import get_all_children, load_ui, get_all_fields, InputField

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


SETTINGS_DEFAULTS = {
    "dragAndDropBehavior": SETTINGS_VALUES.DragAndDrop.ALBUM_MODE,
    "logLevel": SETTINGS_VALUES.LogLevel.DEBUG,
    "audioBitrate": "384k",
    "videoHeight": "720",
    "videoWidth": "1280",
    "uploadYouTube": "PySide2.QtCore.Qt.CheckState.Checked",
    "albumPlaylist": SETTINGS_VALUES.AlbumPlaylist.MULTIPLE,
    "userSelect": 0,
    "videoDescription": "Uploaded with https://github.com/7x11x13/songs-to-youtube",
    "videoTags": "",
    "videoTitle": "%filename%",
    "videoVisibility": SETTINGS_VALUES.VideoVisibility.PUBLIC
}

def get_settings():
    """Returns the QSettings for this application"""
    return QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION, APPLICATION)

def get_setting(setting: str):
    """Returns the value of the given setting (as a string) or None if it has no value"""
    settings = get_settings()
    if setting not in SETTINGS_DEFAULTS:
        logging.error("Setting {} is not recognized".format(setting))
        return None
    return settings.value(setting, SETTINGS_DEFAULTS[setting])


class SettingsWindow(QDialog):

    settings_changed = Signal()

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = load_ui("settingswindow.ui")
        self.connect_actions()
        self.load_settings()

    def save_settings(self):
        settings = get_settings()
        for field in get_all_fields(self.ui):
            settings.setValue(field.name, field.get())
        self.settings_changed.emit()

    def load_settings(self):
        settings = get_settings()
        for field in get_all_fields(self.ui):
            field.set(get_setting(field.name))

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.buttonBox.rejected.connect(self.reject)
