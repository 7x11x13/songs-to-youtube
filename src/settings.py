# This Python file uses the following encoding: utf-8
from PySide6.QtCore import Signal, QSettings, Qt
from PySide6.QtWidgets import *
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
    settings = QSettings(QSettings.IniFormat, QSettings.UserScope, ORGANIZATION, SETTINGS_FILENAME)
    # for some reason this doesn't work when the settings are first initialized so we do this
    return QSettings(settings.fileName(), QSettings.IniFormat)

def get_setting(setting: str, settings=get_settings()):
    """Returns the value of the given setting"""
    if not settings.contains(setting):
        # try to load from default settings
        defaults = QSettings(resource_path("config/default.ini"), QSettings.IniFormat)
        if not defaults.contains(setting):
            raise Exception(f"Setting {setting} does not exist")
        return defaults.value(setting)
    return settings.value(setting)

class FileComboBox(QComboBox):
    def __init__(self, *args):
        super().__init__(*args)
        self.dir = None
        self.objectNameChanged.connect(self.set_dir)

    def set_dir(self, object_name):
        if object_name == "commandName":
            self.dir = resource_path("commands/render")
        elif object_name == "concatCommandName":
            self.dir = resource_path("commands/concat")
        else:
            raise Exception(f'ComboBox has name {self.objectName()}')
        self.reload()

    def reload(self):
        commands = set()
        for file in os.listdir(self.dir):
            file_path = os.path.join(self.dir, file)
            if os.path.isfile(file_path) and file.endswith(".command"):
                name = file[:-len(".command")]
                commands.add(name)
                if self.findText(name) == -1:
                    self.addItem(name, name)
        for i in range(self.count()):
            if self.itemText(i) not in commands:
                self.removeItem(i)

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
        if self.setPixmap(QPixmap(path)):
            self.image_path = path
            self.imageChanged.emit(path)
        else:
            # set to default image
            path = QRC_TO_FILE_PATH[":/image/default.jpg"]
            self.setPixmap(QPixmap(path))
            self.image_path = path
            self.imageChanged.emit(path)

    def _get_scroll_area_width(self):
        return find_ancestor(self, "SettingsScrollArea").size().width()

    def setPixmap(self, pixmap):
        if pixmap.isNull():
            return False
        try:
            self.full_pixmap = pixmap
            width = min(self._get_scroll_area_width() * 1/2, pixmap.size().width())
            super().setPixmap(pixmap.scaledToWidth(width))
            return True
        except:
            return False

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

class SettingsWindow(QDialog):

    settings_changed = Signal()

    SAVE_PRESET_TEXT = "Save preset"
    LOAD_PRESET_TEXT = "Load preset"

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = load_ui("settingswindow.ui", (CoverArtDisplay, SettingCheckBox, SettingsScrollArea, FileComboBox))
        # rename default buttons
        self.ui.buttonBox.addButton(SettingsWindow.SAVE_PRESET_TEXT, QDialogButtonBox.ApplyRole)
        self.ui.buttonBox.addButton(SettingsWindow.LOAD_PRESET_TEXT, QDialogButtonBox.ApplyRole)
        SettingsWindow.init_combo_boxes(self.ui)
        self.connect_actions()
        self.load_settings()

    def add_new_user(self):
        msg_box = QMessageBox()
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setWindowTitle("Add new user")
        msg_box.setText("To add a new user, you must first log in to youtube, then save your browser cookies for youtube to<br><br>"
                        f"{os.path.join(YouTubeLogin.get_cookie_path_from_username('(username)'), 'youtube.com.json')}<br><br>"
                        "To save the cookies after logging in, you can use a"
                        " <a href='https://github.com/ktty1220/export-cookie-for-puppeteer'>browser extension.</a> Make sure you "
                        "name the file youtube.com.json")
        msg_box.exec()

    def save_preset(self):
        presets_dir = resource_path("config")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        file = QFileDialog.getSaveFileName(self, SettingsWindow.SAVE_PRESET_TEXT, presets_dir, "Configuration files (*.ini)")[0]
        if file:
            settings = QSettings(file, QSettings.IniFormat)
            self.save_settings_from_fields(settings)

    def load_preset(self):
        presets_dir = resource_path("config")
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
            self.ui.username.addItem(username, username)
        settings = get_settings()
        self.set_fields_from_settings(settings)

    def set_fields_from_settings(self, settings):
        for field in get_all_fields(self.ui):
            field.set(get_setting(field.name, settings))

    def save_settings_from_fields(self, settings):
        for field in get_all_fields(self.ui):
            settings.setValue(field.name, field.get())

    def change_cover_art(self):
        file = QFileDialog.getOpenFileName(self, "Import album artwork", "", SUPPORTED_IMAGE_FILTER)[0]
        self.ui.coverArt.set(file)

    def show(self):
        self.ui.show()

    @staticmethod
    def init_combo_boxes(window):
        for child in get_all_children(window):
            if child.metaObject().className() == "QComboBox":
                name = child.objectName()
                if name in SETTINGS_VALUES.COMBO_BOX_VALUES:
                    for value in SETTINGS_VALUES.COMBO_BOX_VALUES[name]:
                        child.addItem(value, value)

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.buttonBox.rejected.connect(self.reject)
        find_child_text(self.ui.buttonBox, SettingsWindow.SAVE_PRESET_TEXT).clicked.connect(self.save_preset)
        find_child_text(self.ui.buttonBox, SettingsWindow.LOAD_PRESET_TEXT).clicked.connect(self.load_preset)
        self.ui.coverArtButton.clicked.connect(self.change_cover_art)
        self.ui.addNewUserButton.clicked.connect(self.add_new_user)
