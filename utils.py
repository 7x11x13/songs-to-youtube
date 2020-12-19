# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QDirIterator, QDir, QFileInfo, QMimeDatabase, QObject

import logging


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
    children = []
    for child in obj.children():
        children.append(child)
        children += get_all_children(child)
    return children

def load_ui(name: str):
    pass
