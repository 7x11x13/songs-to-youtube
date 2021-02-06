# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QDirIterator, QDir, QFileInfo, QMimeDatabase, QObject, QFile, Qt, QByteArray, QBuffer, QIODevice
from PySide6.QtWidgets import QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap

from const import SETTINGS_VALUES

import logging
import os
import sys


# File utils

def files_in_directory(dir_path: str):
    """Generates all the files of the given directory"""
    file = QDirIterator(dir_path, QDir.AllEntries | QDir.NoDotAndDotDot)
    while file.hasNext():
        yield file.next()

def files_in_directory_and_subdirectories(dir_path: str):
    """Generates all the files in the given directory and subdirectories"""
    file = QDirIterator(dir_path, QDir.AllEntries | QDir.NoDotAndDotDot,
                        QDirIterator.Subdirectories | QDirIterator.FollowSymlinks)
    while file.hasNext():
        yield file.next()

def file_is_x(file_path: str, mime_prefix: str):
    info = QFileInfo(file_path)
    if not info.isReadable():
        logging.info("File {} is not readable".format(info.filePath()))
        return False
    db = QMimeDatabase()
    mime_type = db.mimeTypeForFile(info)
    return mime_type.name().startswith(mime_prefix)

def file_is_audio(file_path: str):
    """Returns true if the given file is a readable audio file"""
    return file_is_x(file_path, "audio")

def file_is_image(file_path: str):
    """Returns true if the given file is a readable image file"""
    return file_is_x(file_path, "image")


# Qt utils

def str_to_checkstate(s):
    STR_TO_CHECKSTATE = {
        SETTINGS_VALUES.CheckBox.UNCHECKED: Qt.Unchecked,
        SETTINGS_VALUES.CheckBox.PARTIALLY_CHECKED: Qt.PartiallyChecked,
        SETTINGS_VALUES.CheckBox.CHECKED: Qt.Checked,
        SETTINGS_VALUES.MULTIPLE_VALUES: Qt.PartiallyChecked
    }
    if s not in STR_TO_CHECKSTATE:
        logging.error("String {} is not a valid CheckState".format(s))
        return Qt.Checked
    return STR_TO_CHECKSTATE[s]

def checkstate_to_str(state):
    CHECKSTATE_TO_STR = {
        Qt.Unchecked: SETTINGS_VALUES.CheckBox.UNCHECKED,
        Qt.PartiallyChecked: SETTINGS_VALUES.MULTIPLE_VALUES,
        Qt.Checked: SETTINGS_VALUES.CheckBox.CHECKED
    }
    return CHECKSTATE_TO_STR[state]


# methods for various QWidgets
# all getters return values as strings
# all setters take in values as strings
# all on_update callbacks take in values as strings
WIDGET_FUNCTIONS = {
    "QPlainTextEdit": {
        "getter": lambda widget: widget.toPlainText(),
        "setter": lambda widget, text: widget.setPlainText(text),
        "on_update": lambda widget, cb: widget.textChanged.connect(lambda: cb(widget.toPlainText()))
    },
    "QComboBox": {
        "getter": lambda widget: widget.currentText(),
        "setter": lambda widget, text: widget.setCurrentText(text),
        "on_update": lambda widget, cb: widget.currentTextChanged.connect(cb)
    },
    "SettingCheckBox": {
        "getter": lambda widget: checkstate_to_str(widget.checkState()),
        "setter": lambda widget, text: widget.setCheckState(str_to_checkstate(text)),
        "on_update": lambda widget, cb: widget.stateChanged.connect(lambda state: cb(checkstate_to_str(state)))
    },
    "CoverArtDisplay": {
        "getter": lambda widget: widget.get(),
        "setter": lambda widget, text: widget.set(text),
        "on_update": lambda widget, cb: widget.imageChanged.connect(cb)
    },
    "QSpinBox": {
        "getter": lambda widget: "{}{}{}".format(widget.prefix(), widget.value(), widget.suffix()),
        "setter": lambda widget, text: widget.setValue(int(text[len(widget.prefix()):len(text)-len(widget.suffix())])),
        "on_update": lambda widget, cb: widget.textChanged.connect(cb)
    },
    "QLineEdit": {
        "getter": lambda widget: widget.text(),
        "setter": lambda widget, text: widget.setText(text),
        "on_update": lambda widget, cb: widget.textChanged.connect(cb)
    }
}


class InputField:
    def __init__(self, widget):
        self.widget = widget
        self.class_name = widget.metaObject().className()
        self.name = widget.objectName()

    def get(self):
        return WIDGET_FUNCTIONS[self.class_name]["getter"](self.widget)

    def set(self, value):
        WIDGET_FUNCTIONS[self.class_name]["setter"](self.widget, value)

    def on_update(self, function):
        WIDGET_FUNCTIONS[self.class_name]["on_update"](self.widget, function)


def get_all_children(obj: QObject):
    """Returns all the children (recursive) of the given object"""
    for child in obj.children():
        yield child
        yield from get_all_children(child)

def find_child_text(obj: QObject, text: str):
    """Returns the child of obj with the given text"""
    for child in obj.children():
        get_text = getattr(child, "text", None)
        if callable(get_text) and get_text() == text:
            return child
    return None

def get_field(obj: QObject, field):
    for widget in get_all_children(obj):
        class_name = widget.metaObject().className()
        obj_name = widget.objectName()
        if field == obj_name and class_name in WIDGET_FUNCTIONS:
            return InputField(widget)
    logging.warning("Could not find field {}".format(field))
    return None

def get_all_fields(obj: QObject):
    """Returns all the input widget children of the given object as InputFields"""
    for widget in get_all_children(obj):
        class_name = widget.metaObject().className()
        if class_name in WIDGET_FUNCTIONS and widget.objectName() != "qt_spinbox_lineedit" and "NOFIELD" not in widget.objectName():
            yield InputField(widget)

def get_all_visible_fields(obj: QObject):
    """Returns all visible InputFields"""
    for widget in get_all_children(obj):
        if isinstance(widget, QWidget) and widget.isVisible():
            class_name = widget.metaObject().className()
            if class_name in WIDGET_FUNCTIONS and widget.objectName() != "qt_spinbox_lineedit" and "NOFIELD" not in widget.objectName():
                yield InputField(widget)

def find_ancestor(obj: QObject, type: str="", name: str=""):
    """Returns the closest ancestor of obj with type and name given"""
    obj = obj.parent()
    if not obj:
        return None
    # used recursion here before but pyside
    # deleted the object before returning
    while not ((name == "" or obj.objectName() == name) and (type == "" or obj.metaObject().className() == str(type))):
        obj = obj.parent()
    return obj

def load_ui(name, custom_widgets=[], parent=None):
    loader = QUiLoader()
    for cw in custom_widgets:
        loader.registerCustomWidget(cw)
    path = os.path.join(os.path.dirname(__file__), "ui", name)
    ui_file = QFile(path)
    if not ui_file.open(QFile.ReadOnly):
        logging.critical("Cannot open {}: {}".format(path, ui_file.errorString()))
        sys.exit(-1)
    ui = loader.load(ui_file, parent)
    ui_file.close()
    return ui

def mimedata_has_image(data):
    """Returns True if the given mimedata contains a valid image file"""
    return any(file_is_image(url.toLocalFile()) for url in data.urls())

def get_image_from_mimedata(data):
    """Returns a valid image path from the given mimedata if possible, otherwise returns None"""
    for url in data.urls():
        if file_is_image(url.toLocalFile()):
            return url.toLocalFile()
    return None


# Other utils

def flatten_metadata(d, old_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = old_key + sep + k if old_key else k
        if isinstance(v, list):
            # tags such as artist, track name
            # can be stored as arrays
            # use only the first value for simplicity
            if len(v) == 0:
                continue
            else:
                v = v[0]
        try:
            items.extend(flatten_metadata(v, new_key, sep).items())
        except:
            if isinstance(v, (str, int, float)):
                # Qt doesn't like storing non standard types
                # in widget items, we don't need them anyways
                # so just ignore them
                items.append((new_key, v))
    return dict(items)
