# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QDirIterator, QDir, QFileInfo, QMimeDatabase, QObject, QFile
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

def get_all_children(obj: QObject):
    """Returns all the children (recursive) of the given object"""
    for child in obj.children():
        yield child
        yield from get_all_children(child)

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
