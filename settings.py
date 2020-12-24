# This Python file uses the following encoding: utf-8
from PySide6.QtCore import Signal, QSettings, Qt
from PySide6.QtWidgets import QDialog, QCheckBox, QLabel, QFileDialog, QScrollArea
from PySide6.QtGui import QPixmap

import logging

from utils import load_ui, get_all_fields, pixmap_to_base64_str, base64_str_to_pixmap, find_ancestor
from const import SETTINGS_DEFAULTS, SETTINGS_VALUES, ORGANIZATION, APPLICATION, SUPPORTED_IMAGE_FILTER

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


class SettingCheckBox(QCheckBox):
    def __init__(self, *args):
        super().__init__(*args)
        self.setTristate()

    def nextCheckState(self):
        # don't let user select inbetween state
        if self.checkState() == Qt.PartiallyChecked:
            self.setCheckState(Qt.Checked)
        else:
            self.setChecked(not self.isChecked())
        self.stateChanged.emit(self.checkState())


class CoverArtDisplay(QLabel):

    imageChanged = Signal(str)

    def __init__(self, *args):
        self.multiple_values = False
        self.full_pixmap = None
        super().__init__(*args)

    def get(self):
        if self.multiple_values:
            return SETTINGS_VALUES.MULTIPLE_VALUES
        return pixmap_to_base64_str(self.full_pixmap)

    def set(self, text):
        self.multiple_values = (text == SETTINGS_VALUES.MULTIPLE_VALUES)
        if self.multiple_values:
            text = SETTINGS_VALUES.MULTIPLE_VALUES_IMG
        if pixmap := base64_str_to_pixmap(text):
            self.setPixmap(pixmap)

    def _get_scroll_area_width(self):
        return find_ancestor(self, "SettingsScrollArea").size().width()

    def setPixmap(self, pixmap):
        if pixmap.isNull():
            return
        self.full_pixmap = pixmap
        width = min(self._get_scroll_area_width() * 3/4, pixmap.size().width())
        super().setPixmap(pixmap.scaledToWidth(width))
        self.imageChanged.emit(pixmap_to_base64_str(pixmap))

    def scroll_area_width_resized(self, width):
        if self.full_pixmap and not self.full_pixmap.isNull():
            width = min(width * 3/4, self.full_pixmap.size().width())
            scaled = self.full_pixmap.scaledToWidth(width)
            super().setPixmap(scaled)


class SettingsScrollArea(QScrollArea):
    def __init__(self, *args):
        super().__init__(*args)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.findChild(CoverArtDisplay).scroll_area_width_resized(event.size().width())


class SettingsWindow(QDialog):

    settings_changed = Signal()

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = load_ui("settingswindow.ui", [CoverArtDisplay, SettingCheckBox, SettingsScrollArea])
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

    def change_cover_art(self):
        file = QFileDialog.getOpenFileName(self, "Import album artwork", "", SUPPORTED_IMAGE_FILTER)[0]
        pixmap = QPixmap(file)
        self.ui.coverArt.setPixmap(pixmap)

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.coverArtButton.clicked.connect(self.change_cover_art)
