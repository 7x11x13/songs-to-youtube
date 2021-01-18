# This Python file uses the following encoding: utf-8
from PySide6.QtCore import Signal, QSettings, Qt
from PySide6.QtWidgets import QDialog, QCheckBox, QLabel, QFileDialog, QScrollArea, QMessageBox, QDialogButtonBox
from PySide6.QtGui import QPixmap

import logging
import traceback
import time
import os
from threading import Thread

from utils import *
from youtube_uploader_selenium import YouTubeLogin
from const import *

def get_settings():
    """Returns the QSettings for this application"""
    return QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION, APPLICATION)

def get_setting(setting: str, settings=get_settings()):
    """Returns the value of the given setting (as a string) or None if it has no value"""
    if setting not in SETTINGS_DEFAULTS:
        logging.warning("Setting {} is not recognized".format(setting))
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
        # The full artwork pixmap, so we can scale down
        # as the scroll area gets resized
        self.full_pixmap = None

        # Path to original image file
        self.image_path = ""

        super().__init__(*args)
        self.setAcceptDrops(True)

    def get(self):
        if self.image_path == SETTINGS_VALUES.MULTIPLE_VALUES_IMG:
            return SETTINGS_VALUES.MULTIPLE_VALUES
        return self.image_path

    def set(self, path):
        if path == SETTINGS_VALUES.MULTIPLE_VALUES:
            path = SETTINGS_VALUES.MULTIPLE_VALUES_IMG
        if path == self.image_path:
            return
        self.image_path = path
        self.setPixmap(QPixmap(path))
        self.imageChanged.emit(path)

    def _get_scroll_area_width(self):
        return find_ancestor(self, "SettingsScrollArea").size().width()

    def setPixmap(self, pixmap):
        if pixmap.isNull():
            return
        self.full_pixmap = pixmap
        width = min(self._get_scroll_area_width() * 1/2, pixmap.size().width())
        super().setPixmap(pixmap.scaledToWidth(width))

    def scroll_area_width_resized(self, width):
        if self.full_pixmap and not self.full_pixmap.isNull():
            width = min(width * 1/2, self.full_pixmap.size().width())
            scaled = self.full_pixmap.scaledToWidth(width)
            super().setPixmap(scaled)         

    def dragEnterEvent(self, event):
        if event.source() is None and mimedata_has_image(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() is None and mimedata_has_image(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if (path := get_image_from_mimedata(event.mimeData())) is not None:
            self.set(path)


class SettingsScrollArea(QScrollArea):
    def __init__(self, *args):
        super().__init__(*args)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.findChild(CoverArtDisplay).scroll_area_width_resized(event.size().width())

class LoginThread(Thread):

    def __init__(self, callback=lambda: None):
        super().__init__()
        self.callback = callback

    def run(self):
        try:
            self.login = YouTubeLogin()
            time.sleep(5)
            username = self.login.get_login()
            self.callback(True, username)
        except Exception as e:
            logging.error("Error while getting login")
            logging.error(traceback.format_exc())
            logging.error(e)
            self.callback(False, None)

class SettingsWindow(QDialog):

    settings_changed = Signal()

    SAVE_PRESET_TEXT = "Save preset"
    LOAD_PRESET_TEXT = "Load preset"

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = load_ui("settingswindow.ui", (CoverArtDisplay, SettingCheckBox, SettingsScrollArea))
        # rename default buttons
        self.ui.buttonBox.addButton(SettingsWindow.SAVE_PRESET_TEXT, QDialogButtonBox.ApplyRole)
        self.ui.buttonBox.addButton(SettingsWindow.LOAD_PRESET_TEXT, QDialogButtonBox.ApplyRole)
        self.connect_actions()
        self.load_settings()
        self.login_thread = None

    def save_preset(self):
        presets_dir = os.path.join(os.path.dirname(__file__), "presets")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        file = QFileDialog.getSaveFileName(self, SettingsWindow.SAVE_PRESET_TEXT, presets_dir, "Configuration files (*.ini)")[0]
        if file:
            settings = QSettings(file, QSettings.IniFormat)
            self.save_settings_from_fields(settings)

    def load_preset(self):
        presets_dir = os.path.join(os.path.dirname(__file__), "presets")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        file = QFileDialog.getOpenFileName(self, SettingsWindow.LOAD_PRESET_TEXT, presets_dir, "Configuration files (*.ini)")[0]
        if file:
            settings = QSettings(file, QSettings.IniFormat)
            self.set_fields_from_settings(settings)

    def save_settings(self):
        settings = get_settings()
        self.save_settings_from_fields(settings)
        self.settings_changed.emit()

    def load_settings(self):
        for username in YouTubeLogin.get_all_usernames():
            self.ui.username.addItem(username)
        settings = get_settings()
        self.set_fields_from_settings(settings)

    def set_fields_from_settings(self, settings):
        for field in get_all_fields(self.ui):
            field.set(get_setting(field.name, settings))

    def save_settings_from_fields(self, settings):
        for field in get_all_fields(self.ui):
            settings.setValue(field.name, field.get())

    def on_login(self, success, username):
        self.ui.setEnabled(True)
        self.login_thread = None
        if success:
            self.ui.username.addItem(username)
            self.ui.username.setCurrentText(username)

    def add_new_user(self):
        if self.login_thread is None:
            self.ui.setEnabled(False)
            self.login_thread = LoginThread(self.on_login)
            self.login_thread.start()
            QMessageBox.information(self, "Add new user",
                                             "Please log in to your YouTube account. "
                                             "The window will close automatically when you log in.")

    def remove_user(self):
        combo_box = self.ui.username
        username = combo_box.currentText()
        if username != "":
            combo_box.removeItem(combo_box.currentIndex())
            YouTubeLogin.remove_user_cookies(username)

    def change_cover_art(self):
        file = QFileDialog.getOpenFileName(self, "Import album artwork", "", SUPPORTED_IMAGE_FILTER)[0]
        self.ui.coverArt.set(file)

    def reset_ffmpeg_command(self):
        self.ui.commandString.setPlainText(SETTINGS_DEFAULTS["commandString"])

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.buttonBox.rejected.connect(self.reject)
        find_child_text(self.ui.buttonBox, SettingsWindow.SAVE_PRESET_TEXT).clicked.connect(self.save_preset)
        find_child_text(self.ui.buttonBox, SettingsWindow.LOAD_PRESET_TEXT).clicked.connect(self.load_preset)
        self.ui.coverArtButton.clicked.connect(self.change_cover_art)
        self.ui.addNewUserButton.clicked.connect(self.add_new_user)
        self.ui.removeUserButton.clicked.connect(self.remove_user)
        self.ui.resetCommandString.clicked.connect(self.reset_ffmpeg_command)
