import logging
import os
import posixpath
import shutil
import sys

from PySide6.QtCore import *
from PySide6.QtUiTools import QUiLoader

from songs_to_youtube.const import *

logger = logging.getLogger(APPLICATION)


# Cookies utils
class YouTubeLogin:
    @staticmethod
    def get_cookie_path_from_username(username):
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        general_cookies_folder_path = posixpath.join(appdata_path, "cookies")
        os.makedirs(general_cookies_folder_path, exist_ok=True)
        return posixpath.join(general_cookies_folder_path, username)

    @staticmethod
    def get_all_usernames():
        appdata_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        general_cookies_folder_path = posixpath.join(appdata_path, "cookies")
        os.makedirs(general_cookies_folder_path, exist_ok=True)
        return next(os.walk(general_cookies_folder_path))[1]

    @staticmethod
    def remove_user_cookies(username):
        cookie_folder = YouTubeLogin.get_cookie_path_from_username(username)
        shutil.rmtree(cookie_folder)


# File utils

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _GetShortPathNameW = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD

    def get_short_path_name(long_name):
        """
        Gets the short path name of a given long path.
        http://stackoverflow.com/a/23598461/200291
        """
        output_buf_size = 0
        while True:
            output_buf = ctypes.create_unicode_buffer(output_buf_size)
            needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
            if needed == 0:
                raise ctypes.WinError(ctypes.get_last_error())
            if output_buf_size >= needed:
                return output_buf.value
            else:
                output_buf_size = needed


def files_in_directory(dir_path: str):
    """Generates all the files of the given directory"""
    file = QDirIterator(dir_path, QDir.AllEntries | QDir.NoDotAndDotDot)
    while file.hasNext():
        yield file.next()


def files_in_directory_and_subdirectories(dir_path: str):
    """Generates all the files in the given directory and subdirectories"""
    file = QDirIterator(
        dir_path,
        QDir.AllEntries | QDir.NoDotAndDotDot,
        QDirIterator.Subdirectories | QDirIterator.FollowSymlinks,
    )
    while file.hasNext():
        yield file.next()


def file_is_type(file_path: str, mime_prefix: str, exclude=[]):
    info = QFileInfo(file_path)
    if not info.isReadable():
        logger.info("File {} is not readable".format(info.filePath()))
        return False
    db = QMimeDatabase()
    mime_type = db.mimeTypeForFile(info)
    return mime_type.name().startswith(mime_prefix) and mime_type.name() not in exclude


def file_is_audio(file_path: str):
    """Returns true if the given file is a readable audio file"""
    return file_is_type(file_path, "audio", ["audio/x-mpegurl"])


def file_is_image(file_path: str):
    """Returns true if the given file is a readable image file"""
    return file_is_type(file_path, "image")


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return posixpath.join(base_path, relative_path)


# Qt utils


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


def find_ancestor(obj: QObject, type: str = "", name: str = ""):
    """Returns the closest ancestor of obj with type and name given"""
    obj = obj.parent()
    if not obj:
        return None
    # used recursion here before but pyside
    # deleted the object before returning
    while not (
        (name == "" or obj.objectName() == name)
        and (type == "" or obj.metaObject().className() == str(type))
    ):
        obj = obj.parent()
    return obj


def load_ui(name, custom_widgets=[], parent=None):
    loader = QUiLoader()
    for cw in custom_widgets:
        loader.registerCustomWidget(cw)
    path = resource_path(posixpath.join("ui", name))
    ui_file = QFile(path)
    if not ui_file.open(QFile.ReadOnly):
        logger.error("Cannot open {}: {}".format(path, ui_file.errorString()))
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


def make_value_qt_safe(value):
    if isinstance(value, list):
        if len(value) > 0:
            return str(value[0])
        else:
            return ""
    return str(value)
