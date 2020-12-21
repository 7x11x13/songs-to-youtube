# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QFile, Signal, QSettings, Qt
from PySide2.QtWidgets import QDialog, QWidget, QComboBox
from PySide2.QtUiTools import QUiLoader

import os
import logging
import dataclasses
from enum import Enum

from utils import get_all_children, load_ui

ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"

class SETTINGS_VALUES:
    class DragAndDrop(Enum):
        ALBUM_MODE = "Album mode"
        SONG_MODE = "Song mode"

    class LogLevel(Enum):
        DEBUG = "DEBUG"
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"

    class AlbumPlaylist(Enum):
        MULTIPLE = "Multiple videos"
        SINGLE = "Single video"
        MULTIPLE_PLAYLIST = "Multiple videos (playlist)"

    class VideoVisibility(Enum):
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


STR_TO_CHECK = {
    "PySide2.QtCore.Qt.CheckState.Unchecked": Qt.Unchecked,
    "PySide2.QtCore.Qt.CheckState.PartiallyChecked": Qt.PartiallyChecked,
    "PySide2.QtCore.Qt.CheckState.Checked": Qt.Checked,
    "<<Multiple values>>": Qt.PartiallyChecked
}


def str_to_checkstate(s):
    """Have to do this since QCheckBox.setCheckState does not work with ints in PySide2"""
    if s not in STR_TO_CHECK:
        logging.error("String {} is not a valid CheckState".format(s))
        return None
    return STR_TO_CHECK[s]


# getter and setter methods for various QWidgets
# all getters return values as strings
# all setters take in values as strings
WIDGET_FUNCTIONS = {
    "QPlainTextEdit": {
        "getter": lambda x: x.toPlainText(),
        "setter": lambda x, v: x.setPlainText(v)
    },
    "QComboBox": {
        "getter": lambda x: x.currentText(),
        "setter": lambda x, v: x.setCurrentText(v)
    },
    "SettingCheckBox": {
        "getter": lambda x: str(x.checkState()),
        "setter": lambda x, v: x.setCheckState(str_to_checkstate(v))
    }
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
        for widget in get_all_children(self.ui):
            class_name = widget.metaObject().className()
            if class_name in WIDGET_FUNCTIONS:
                setting = widget.objectName()
                value = WIDGET_FUNCTIONS[class_name]["getter"](widget)
                settings.setValue(setting, value)
        self.settings_changed.emit()

    def load_settings(self):
        settings = get_settings()
        for widget in get_all_children(self.ui):
            class_name = widget.metaObject().className()
            if class_name in WIDGET_FUNCTIONS:
                setting = widget.objectName()
                value = get_setting(setting)
                WIDGET_FUNCTIONS[class_name]["setter"](widget, value)

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.buttonBox.rejected.connect(self.reject)
