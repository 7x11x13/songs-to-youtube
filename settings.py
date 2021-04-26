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
    return settings.value(setting, None)

def load_combobox_data_from_settings(field, settings):
    widget = field.widget
    widget.clear()
    size = settings.beginReadArray("{}Data".format(field.name))
    for i in range(size):
        settings.setArrayIndex(i)
        widget.addItem(settings.value("text"), settings.value("data"))
    settings.endArray()


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

    def __init__(self, browser, callback=lambda: None):
        super().__init__()
        self.callback = callback
        self.login = browser

    def run(self):
        try:
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
        SettingsWindow.init_combo_boxes(self.ui)
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
            self.ui.username.addItem(username, username)
        settings = get_settings()
        self.set_fields_from_settings(settings)

    def set_fields_from_settings(self, settings):
        for field in get_all_fields(self.ui):
            # load combobox data
            if field.name.startswith("SAVE"):
                load_combobox_data_from_settings(field, settings)
            field.set(get_setting(field.name, settings))

    def save_settings_from_fields(self, settings):
        for field in get_all_fields(self.ui):
            # save combobox data
            if field.name.startswith("SAVE"):
                widget = field.widget
                settings.beginWriteArray("{}Data".format(field.name))
                for i in range(widget.count()):
                    settings.setArrayIndex(i)
                    settings.setValue("text", widget.itemText(i))
                    settings.setValue("data", widget.itemData(i))
                settings.endArray()
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
            self.login_thread = LoginThread(YouTubeLogin(), self.on_login)
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

    def ffmpeg_command_changed(self, index):
        name = self.ui.SAVEcommandString.itemText(index)
        self.ui.NOFIELDcommandStringName.setText(name)
        command_string = self.ui.SAVEcommandString.itemData(index)
        self.ui.NOFIELDcommandString.setPlainText(command_string)

    def save_ffmpeg_command(self):
        # if name is different, delete old item
        # and create new one with new name (rename)
        # otherwise, just update the item data
        command_select = self.ui.SAVEcommandString
        index = command_select.currentIndex()
        new_name = self.ui.NOFIELDcommandStringName.text()
        old_name = command_select.currentText()
        new_text = self.ui.NOFIELDcommandString.toPlainText()
        if new_name != old_name:
            command_select.removeItem(index)
            command_select.addItem(new_name, new_text)
            command_select.setCurrentText(new_name)
        else:
            command_select.setItemData(index, new_text)

    def add_ffmpeg_command(self):
        command_select = self.ui.SAVEcommandString
        i = 1
        while command_select.findText(name := "New command {}".format(i)) != -1:
            i += 1
        command_select.addItem(name, "ffmpeg -loglevel error -progress pipe:1 -y -r {inputFrameRate} -loop 1 -i \"{coverArt}\" -i \"{song_path}\" -r 30 -shortest \"{tempFileOutput}\"")
        command_select.setCurrentText(name)

    def remove_ffmpeg_command(self):
        self.ui.SAVEcommandString.removeItem(self.ui.SAVEcommandString.currentIndex())

    def show(self):
        self.ui.show()

    @staticmethod
    def init_combo_boxes(window):
        for child in get_all_children(window):
            if child.metaObject().className() == "QComboBox":
                name = child.objectName()
                # do not init combo boxes with dynamic contents
                if not name.startswith("SAVE"):
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
        self.ui.removeUserButton.clicked.connect(self.remove_user)
        self.ui.addCommandString.clicked.connect(self.add_ffmpeg_command)
        self.ui.removeCommandString.clicked.connect(self.remove_ffmpeg_command)
        self.ui.saveCommandString.clicked.connect(self.save_ffmpeg_command)
        self.ui.SAVEcommandString.currentIndexChanged.connect(self.ffmpeg_command_changed)
