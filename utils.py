# This Python file uses the following encoding: utf-8
from PySide2.QtCore import QDirIterator, QDir, QFileInfo, QMimeDatabase
import logging

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
        logging.warning("File %s is not readable" % info.filePath())
        return False
    db = QMimeDatabase()
    mime_type = db.mimeTypeForFile(info)
    return mime_type.name().startswith("audio")
