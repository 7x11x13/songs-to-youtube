import os
import posixpath
import shutil

from PySide6.QtCore import *
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *

from songs_to_youtube.const import *
from songs_to_youtube.field import *
from songs_to_youtube.utils import *


def get_settings():
    """Returns the QSettings for this application"""
    settings = QSettings(
        QSettings.IniFormat, QSettings.UserScope, ORGANIZATION, SETTINGS_FILENAME
    )
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
        self.dirs = []
        self.objectNameChanged.connect(self.set_dir)

    def set_dir(self, object_name):
        # take screenshot and quit
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        commands_dir = posixpath.join(appdata_path, "commands")
        os.makedirs(commands_dir, exist_ok=True)
        if object_name == "commandName":
            render_dir = posixpath.join(commands_dir, "render")
            os.makedirs(render_dir, exist_ok=True)
            self.dirs = [resource_path("commands/render"), render_dir]
        elif object_name == "concatCommandName":
            concat_dir = posixpath.join(commands_dir, "concat")
            os.makedirs(concat_dir, exist_ok=True)
            self.dirs = [resource_path("commands/concat"), concat_dir]
        else:
            raise Exception(f"ComboBox has name {self.objectName()}")
        self.reload()

    def reload(self):
        commands = set()
        for d in self.dirs:
            for file in os.listdir(d):
                file_path = posixpath.join(d, file)
                if os.path.isfile(file_path) and file.endswith(".command"):
                    name = file[: -len(".command")]
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
            path = APPLICATION_IMAGES[":/image/default.jpg"]
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
            width = min(self._get_scroll_area_width() * 1 / 2, pixmap.size().width())
            super().setPixmap(pixmap.scaledToWidth(width))
            return True
        except:
            return False

    def scroll_area_width_resized(self, width):
        if self.full_pixmap and not self.full_pixmap.isNull():
            width = min(width * 1 / 2, self.full_pixmap.size().width())
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


class AddUserWindow(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        self.ui = load_ui("adduser.ui")
        self.connect_actions()

    def connect_actions(self):
        self.ui.buttonBox.accepted.connect(self.save_user)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.cookiesButton.clicked.connect(self.open_cookies)

    def open_cookies(self):
        cookie_file = QFileDialog.getOpenFileName(
            self, "Select cookies.txt or json file", filter="Cookies (*.txt *.json)"
        )[0]
        if cookie_file:
            self.ui.cookiesFile.setText(cookie_file)

    def save_user(self):
        cookie_folder = YouTubeLogin.get_cookie_path_from_username(
            self.ui.username.text()
        )
        os.makedirs(cookie_folder, exist_ok=True)
        cookie_file = self.ui.cookiesFile.text()
        if cookie_file.endswith("json"):
            cookie_file = posixpath.join(cookie_folder, "youtube.com.json")
        else:
            cookie_file = posixpath.join(cookie_folder, "cookies.txt")
        shutil.copyfile(self.ui.cookiesFile.text(), cookie_file)

    def show(self):
        self.ui.show()


class SettingsWindow(QDialog):
    settings_changed = Signal()

    SAVE_PRESET_TEXT = "Save preset"
    LOAD_PRESET_TEXT = "Load preset"

    def __init__(self, *args):
        super().__init__(*args)
        self.ui = load_ui(
            "settingswindow.ui",
            (CoverArtDisplay, SettingCheckBox, SettingsScrollArea, FileComboBox),
        )
        # rename default buttons
        self.ui.buttonBox.addButton(
            SettingsWindow.SAVE_PRESET_TEXT, QDialogButtonBox.ApplyRole
        )
        self.ui.buttonBox.addButton(
            SettingsWindow.LOAD_PRESET_TEXT, QDialogButtonBox.ApplyRole
        )
        SettingsWindow.init_combo_boxes(self.ui)
        self.connect_actions()
        self.load_settings()

    def add_new_user(self):
        self.msg_box = AddUserWindow()
        self.msg_box.ui.buttonBox.accepted.connect(self.reload_users)
        self.msg_box.show()

    def remove_user(self):
        if self.ui.username.currentText():
            cookie_folder = YouTubeLogin.get_cookie_path_from_username(
                self.ui.username.currentText()
            )
            shutil.rmtree(cookie_folder)
            self.ui.username.removeItem(self.ui.username.currentIndex())

    def save_preset(self):
        presets_dir = resource_path("config")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        file = QFileDialog.getSaveFileName(
            self,
            SettingsWindow.SAVE_PRESET_TEXT,
            presets_dir,
            "Configuration files (*.ini)",
        )[0]
        if file:
            settings = QSettings(file, QSettings.IniFormat)
            self.save_settings_from_fields(settings)

    def load_preset(self):
        presets_dir = resource_path("config")
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir)
        file = QFileDialog.getOpenFileName(
            self,
            SettingsWindow.LOAD_PRESET_TEXT,
            presets_dir,
            "Configuration files (*.ini)",
        )[0]
        if file:
            settings = QSettings(file, QSettings.IniFormat)
            self.set_fields_from_settings(settings)

    def reload_users(self):
        self.ui.username.clear()
        for username in YouTubeLogin.get_all_usernames():
            self.ui.username.addItem(username, username)
            self.ui.username.setCurrentText(username)

    def save_settings(self):
        settings = get_settings()
        self.save_settings_from_fields(settings)
        self.settings_changed.emit()

    def load_settings(self):
        self.reload_users()
        settings = get_settings()
        self.set_fields_from_settings(settings)

    def set_fields_from_settings(self, settings):
        for field in get_all_fields(self.ui):
            field.set(get_setting(field.name, settings))

    def save_settings_from_fields(self, settings):
        for field in get_all_fields(self.ui):
            settings.setValue(field.name, field.get())

    def change_cover_art(self):
        file = QFileDialog.getOpenFileName(
            self, "Import album artwork", "", SUPPORTED_IMAGE_FILTER
        )[0]
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
        find_child_text(
            self.ui.buttonBox, SettingsWindow.SAVE_PRESET_TEXT
        ).clicked.connect(self.save_preset)
        find_child_text(
            self.ui.buttonBox, SettingsWindow.LOAD_PRESET_TEXT
        ).clicked.connect(self.load_preset)
        self.ui.coverArtButton.clicked.connect(self.change_cover_art)
        self.ui.addNewUserButton.clicked.connect(self.add_new_user)
        self.ui.removeUserButton.clicked.connect(self.remove_user)
