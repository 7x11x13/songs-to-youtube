import logging
from enum import Enum

from PySide6.QtCore import *
from PySide6.QtWidgets import QWidget

from songs_to_youtube.const import *
from songs_to_youtube.utils import *

logger = logging.getLogger(APPLICATION)

APPLICATION_IMAGES = {
    ":/image/default.jpg": resource_path("image/default.jpg"),
    ":/image/multiple-values.png": resource_path("image/multiple-values.png"),
    ":/image/icon.ico": resource_path("image/icon.ico"),
}


class SETTINGS_VALUES:
    MULTIPLE_VALUES = "<<Multiple values>>"
    MULTIPLE_VALUES_IMG = APPLICATION_IMAGES[":/image/multiple-values.png"]

    # combo box values

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

    class VideoVisibility(str, Enum):
        PUBLIC = "PUBLIC"
        UNLISTED = "UNLISTED"

    COMBO_BOX_VALUES = {
        "dragAndDropBehavior": [item.value for item in DragAndDrop],
        "logLevel": [item.value for item in LogLevel],
        "albumPlaylist": [item.value for item in AlbumPlaylist],
        "videoVisibility": [item.value for item in VideoVisibility],
        "videoVisibilityAlbum": [item.value for item in VideoVisibility],
    }

    class CheckBox(str, Enum):
        UNCHECKED = "PySide6.QtCore.Qt.CheckState.Unchecked"
        PARTIALLY_CHECKED = "PySide6.QtCore.Qt.CheckState.PartiallyChecked"
        CHECKED = "PySide6.QtCore.Qt.CheckState.Checked"


def str_to_checkstate(s):
    STR_TO_CHECKSTATE = {
        SETTINGS_VALUES.CheckBox.UNCHECKED: Qt.Unchecked,
        SETTINGS_VALUES.CheckBox.PARTIALLY_CHECKED: Qt.PartiallyChecked,
        SETTINGS_VALUES.CheckBox.CHECKED: Qt.Checked,
        SETTINGS_VALUES.MULTIPLE_VALUES: Qt.PartiallyChecked,
    }
    if s not in STR_TO_CHECKSTATE:
        raise Exception(f"String {s} is not a valid CheckState")
    return STR_TO_CHECKSTATE[s]


def checkstate_to_str(state: Qt.CheckState):
    c = [
        SETTINGS_VALUES.CheckBox.UNCHECKED,
        SETTINGS_VALUES.MULTIPLE_VALUES,
        SETTINGS_VALUES.CheckBox.CHECKED,
    ]
    try:
        return c[state]
    except TypeError:
        try:
            return c[state.value]
        except AttributeError:
            return c[(b"Unchecked", b"PartiallyChecked", b"Checked").index(state.name)]


class InputField:
    SONG_FIELDS = {
        "backgroundColor",
        "videoHeight",
        "videoWidth",
        "uploadYouTube",
        "coverArt",
        "videoDescription",
        "videoTags",
        "videoTitle",
        "videoVisibility",
        "fileOutputDir",
        "fileOutputName",
        "playlistName",
        "commandName",
        "notifySubs",
    }

    ALBUM_FIELDS = {
        "albumPlaylist",
        "fileOutputDirAlbum",
        "fileOutputNameAlbum",
        "uploadYouTube",
        "videoDescriptionAlbum",
        "videoTagsAlbum",
        "videoTitleAlbum",
        "videoVisibilityAlbum",
        "notifySubsAlbum",
        "concatCommandName",
    }

    # methods for various QWidgets
    # all getters return values as strings
    # all setters take in values as strings
    # all on_update callbacks take in values as strings
    WIDGET_FUNCTIONS = {
        "QPlainTextEdit": {
            "getter": lambda widget: widget.toPlainText(),
            "setter": lambda widget, text: widget.setPlainText(text),
            "on_update": lambda widget, cb: widget.textChanged.connect(
                lambda: cb(widget.toPlainText())
            ),
        },
        "QComboBox": {
            "getter": lambda widget: widget.currentData(),
            "setter": lambda widget, data: widget.setCurrentIndex(
                widget.findData(data)
            ),
            "on_update": lambda widget, cb: widget.currentIndexChanged.connect(
                lambda: cb(widget.currentData())
            ),
        },
        "FileComboBox": {
            "getter": lambda widget: widget.currentData(),
            "setter": lambda widget, data: widget.setCurrentIndex(
                widget.findData(data)
            ),
            "on_update": lambda widget, cb: widget.currentIndexChanged.connect(
                lambda: cb(widget.currentData())
            ),
        },
        "SettingCheckBox": {
            "getter": lambda widget: checkstate_to_str(widget.checkState()),
            "setter": lambda widget, text: widget.setCheckState(
                str_to_checkstate(text)
            ),
            "on_update": lambda widget, cb: widget.stateChanged.connect(
                lambda state: cb(checkstate_to_str(state))
            ),
        },
        "CoverArtDisplay": {
            "getter": lambda widget: widget.get(),
            "setter": lambda widget, text: widget.set(text),
            "on_update": lambda widget, cb: widget.imageChanged.connect(cb),
        },
        "QSpinBox": {
            "getter": lambda widget: f"{widget.prefix()}{widget.value()}{widget.suffix()}",
            "setter": lambda widget, text: widget.setValue(
                int(text[len(widget.prefix()) : len(text) - len(widget.suffix())])
            ),
            "on_update": lambda widget, cb: widget.textChanged.connect(cb),
        },
        "QLineEdit": {
            "getter": lambda widget: widget.text(),
            "setter": lambda widget, text: widget.setText(text),
            "on_update": lambda widget, cb: widget.textChanged.connect(cb),
        },
    }

    def __init__(self, widget):
        self.widget = widget
        self.class_name = widget.metaObject().className()
        self.name = widget.objectName()

    def get(self):
        return self.WIDGET_FUNCTIONS[self.class_name]["getter"](self.widget)

    def set(self, value):
        self.WIDGET_FUNCTIONS[self.class_name]["setter"](self.widget, value)

    def on_update(self, function):
        self.WIDGET_FUNCTIONS[self.class_name]["on_update"](self.widget, function)

    def is_song_field(self):
        return self.name in self.SONG_FIELDS

    def is_album_field(self):
        return self.name in self.ALBUM_FIELDS


def get_field(obj: QObject, field):
    for widget in get_all_children(obj):
        class_name = widget.metaObject().className()
        obj_name = widget.objectName()
        if field == obj_name and class_name in InputField.WIDGET_FUNCTIONS:
            return InputField(widget)
    logger.warning("Could not find field {}".format(field))
    return None


def get_all_fields(obj: QObject):
    """Returns all the input widget children of the given object as InputFields"""
    for widget in get_all_children(obj):
        class_name = widget.metaObject().className()
        if (
            class_name in InputField.WIDGET_FUNCTIONS
            and widget.objectName() != "qt_spinbox_lineedit"
            and "NOFIELD" not in widget.objectName()
        ):
            yield InputField(widget)


def get_all_visible_fields(obj: QObject):
    """Returns all visible InputFields"""
    for widget in get_all_children(obj):
        if isinstance(widget, QWidget) and widget.isVisible():
            class_name = widget.metaObject().className()
            if (
                class_name in InputField.WIDGET_FUNCTIONS
                and widget.objectName() != "qt_spinbox_lineedit"
                and "NOFIELD" not in widget.objectName()
            ):
                yield InputField(widget)
