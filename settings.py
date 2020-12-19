# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QFile, Signal
from PySide2.QtWidgets import QDialog
from PySide2.QtUiTools import QUiLoader

import os
import logging
from enum import IntEnum

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


def get_settings():
    """Returns the QSettings for this application"""
    return QSettings(ORGANIZATION, APPLICATION)

def get_setting(setting: str):
    """Returns the value of the given setting or None if it has no value"""
    settings = get_settings()
    if setting not in SETTINGS_WIDGETS:
        logging.error("Setting {} is not recognized".format(setting))
        return None
    return settings.value(setting, SETTINGS_WIDGETS[setting]["default"])


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
        for setting in SETTINGS_WIDGETS:
            widget_name = SETTINGS_WIDGETS[setting]["widget_name"]
            if not hasattr(self.ui, widget_name):
                logging.error("Settings window UI has no attribute {}".format(widget_name))
                continue
            widget = getattr(self.ui, widget_name)
            if not hasattr(widget, SETTINGS_WIDGETS[setting]["getter"]):
                logging.error("Widget {} has no attribute {}".format(widget, SETTINGS_WIDGETS[setting]["getter"]))
                continue
            getter = getattr(widget, SETTINGS_WIDGETS[setting]["getter"])
            settings.setValue(setting, getter())
        self.settings_changed.emit()

    def load_settings(self):
        settings = get_settings()
        for setting in SETTINGS_WIDGETS:
            widget_name = SETTINGS_WIDGETS[setting]["widget_name"]
            if not hasattr(self.ui, widget_name):
                logging.error("Settings window UI has no attribute {}".format(widget_name))
                continue
            widget = getattr(self.ui, widget_name)
            value = settings.value(setting, SETTINGS_WIDGETS[setting]["default"])
            if not hasattr(widget, SETTINGS_WIDGETS[setting]["setter"]):
                logging.error("Widget %s has no attribute {}".format((widget, SETTINGS_WIDGETS[setting]["setter"])))
                continue
            setter = getattr(widget, SETTINGS_WIDGETS[setting]["setter"])
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
