# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QDirIterator, QDir, QFileInfo, QMimeDatabase, QObject, QFile, Qt
from PySide2.QtUiTools import QUiLoader

import logging
import os


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

def file_is_audio(file_path: str):
    """Returns true if the given file is a readable audio file"""
    info = QFileInfo(file_path)
    if not info.isReadable():
        logging.warning("File {} is not readable".format(info.filePath()))
        return False
    db = QMimeDatabase()
    mime_type = db.mimeTypeForFile(info)
    return mime_type.name().startswith("audio")



# Qt utils


def str_to_checkstate(s):
    """Have to do this since QCheckBox.setCheckState does not work with ints in PySide2"""

    STR_TO_CHECKSTATE = {
        "PySide2.QtCore.Qt.CheckState.Unchecked": Qt.Unchecked,
        "PySide2.QtCore.Qt.CheckState.PartiallyChecked": Qt.PartiallyChecked,
        "PySide2.QtCore.Qt.CheckState.Checked": Qt.Checked,
        "<<Multiple values>>": Qt.PartiallyChecked
    }

    if s not in STR_TO_CHECKSTATE:
        logging.error("String {} is not a valid CheckState".format(s))
        return None
    return STR_TO_CHECKSTATE[s]

def checkstate_to_str(state):
    CHECKSTATE_TO_STR = {
        Qt.Unchecked: "PySide2.QtCore.Qt.CheckState.Unchecked",
        Qt.PartiallyChecked: "<<Multiple values>>",
        Qt.Checked: "PySide2.QtCore.Qt.CheckState.Checked"
    }

    if state not in CHECKSTATE_TO_STR:
        logging.error("State {} is not a valid CheckState".format(state))
        return None
    return CHECKSTATE_TO_STR[state]

# methods for various QWidgets
# all getters return values as strings
# all setters take in values as strings
# all on_update callbacks take in values as strings
WIDGET_FUNCTIONS = {
    "QPlainTextEdit": {
        "getter": lambda x: x.toPlainText(),
        "setter": lambda x, v: x.setPlainText(v),
        "on_update": lambda x, f: x.textChanged.connect(lambda: f(x.toPlainText()))
    },
    "QComboBox": {
        "getter": lambda x: x.currentText(),
        "setter": lambda x, v: x.setCurrentText(v),
        "on_update": lambda x, f: x.currentTextChanged.connect(f)
    },
    "SettingCheckBox": {
        "getter": lambda x: checkstate_to_str(x.checkState()),
        "setter": lambda x, v: x.setCheckState(str_to_checkstate(v)),
        "on_update": lambda x, f: x.stateChanged.connect(lambda state: f(checkstate_to_str(state)))
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


def get_all_fields(obj: QObject):
    """Returns all the input widget children of the given object as InputFields"""
    for widget in get_all_children(obj):
        class_name = widget.metaObject().className()
        if class_name in WIDGET_FUNCTIONS:
            yield InputField(widget)

def find_ancestor(obj: QObject, type: str="", name: str=""):
    """Returns the closest ancestor of obj with type and name given"""
    if (name == "" or obj.objectName() == name) and (type == "" or obj.metaObject().className() == str(type)):
        return obj
    if not obj.parent():
        return None
    return find_ancestor(obj.parent(), type, name)

def load_ui(name, custom_widgets=[], parent=None):
    loader = QUiLoader()
    for cw in custom_widgets:
        loader.registerCustomWidget(cw)
    path = os.path.join(os.path.dirname(__file__), "ui", name)
    ui_file = QFile(path)
    if not ui_file.open(QFile.ReadOnly):
        print("Cannot open {}: {}".format(path, ui_file.errorString()))
        sys.exit(-1)
    ui = loader.load(ui_file, parent)
    ui_file.close()
    return ui
