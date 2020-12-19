# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QFile, Signal, QSettings, Qt
from PySide2.QtWidgets import QDialog, QWidget
from PySide2.QtUiTools import QUiLoader

import os
import logging
from enum import IntEnum

from utils import get_all_children

ORGANIZATION = "7x11x13"
APPLICATION = "songs-to-youtube"

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

    class AlbumPlaylist(IntEnum):
        MULTIPLE = 0
        SINGLE = 1
        MULTIPLE_PLAYLIST = 2

    class VideoVisibility(IntEnum):
        PUBLIC = 0
        UNLISTED = 1


SETTINGS_DEFAULTS = {
    "dragAndDropBehavior": SETTINGS_VALUES.DragAndDrop.ALBUM_MODE,
    "logLevel": SETTINGS_VALUES.LogLevel.DEBUG,
    "audioBitrate": "384k",
    "videoHeight": "720",
    "videoWidth": "1280",
    "uploadYouTube": "2",
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
    "PySide2.QtCore.Qt.CheckState.Checked": Qt.Checked
}


def str_to_checkstate(s):
    """Have to do this hack since QCheckBox.setCheckState does not work with ints in PySide2"""
    if s not in STR_TO_CHECK:
        logging.error("String {} is not a valid CheckState".format(s))
        return None
    return STR_TO_CHECK[s]


WIDGET_FUNCTIONS = {
    "QPlainTextEdit": {
        "getter": "toPlainText",
        "updated": "textChanged",
        "setter": "setPlainText",
        "str_to_val": str,
    },
    "QComboBox": {
        "getter": "currentIndex",
        "updated": "currentIndexChanged",
        "setter": "setCurrentIndex",
        "str_to_val": int,
    },
    "QCheckBox": {
        "getter": "checkState",
        "updated": "stateChanged",
        "setter": "setCheckState",
        "str_to_val": str_to_checkstate
    }
}


def get_settings():
    """Returns the QSettings for this application"""
    return QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION, APPLICATION)

def get_setting(setting: str):
    """Returns the value of the given setting or None if it has no value"""
    settings = get_settings()
    if setting not in SETTINGS_DEFAULTS:
        logging.error("Setting {} is not recognized".format(setting))
        return None
    return settings.value(setting, SETTINGS_DEFAULTS[setting])


class SettingsWindow(QDialog):

    settings_changed = Signal()

    def __init__(self, *args):
        super().__init__(*args)
        self.load_ui()
        self.connect_actions()
        self.load_settings()

    def accept(self):
        self.save_settings()

    def save_settings(self):
        settings = get_settings()
        for widget in get_all_children(self.ui):
            class_name = widget.metaObject().className()
            if class_name in WIDGET_FUNCTIONS:
                setting = widget.objectName()
                getter = getattr(widget, WIDGET_FUNCTIONS[class_name]["getter"])
                settings.setValue(setting, str(getter()))
        self.settings_changed.emit()

    def load_settings(self):
        settings = get_settings()
        for widget in get_all_children(self.ui):
            class_name = widget.metaObject().className()
            if class_name in WIDGET_FUNCTIONS:
                setting = widget.objectName()
                value = get_setting(setting)
                print(setting, value, type(value))
                print("----")
                # We have to convert from str since settings can only be stored as str
                # unless we store in registry but then there would be a size limit
                value = WIDGET_FUNCTIONS[class_name]["str_to_val"](value)
                setter = getattr(widget, WIDGET_FUNCTIONS[class_name]["setter"])
                setter(value)

    def load_ui(self):
        loader = QUiLoader()
        path = os.path.join(os.path.dirname(__file__), "ui", "settingswindow.ui")
        ui_file = QFile(path)
        if not ui_file.open(QFile.ReadOnly):
            print("Cannot open {}: {}".format(path, ui_file.errorString()))
            sys.exit(-1)
        self.ui = loader.load(ui_file)
        ui_file.close()

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
