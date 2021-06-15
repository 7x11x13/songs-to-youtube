# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QListView, QTreeView, QAbstractItemView, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSettings


import sys
import os
import logging
import pathlib
import shutil

import resource

from utils import load_ui
from const import SETTINGS_VALUES, APPLICATION, ORGANIZATION, VERSION

# Custom widgets
from song_settings_widget import SongSettingsWidget
from song_tree_widget import SongTreeWidget
from log import LogWidget, addLoggingLevel
from settings import SettingsWindow, get_setting, get_settings
from progress_window import ProgressWindow

logger = logging.getLogger(APPLICATION)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = load_ui("mainwindow.ui", (SongSettingsWidget, SongTreeWidget, LogWidget, ProgressWindow))
        self.ui.cancelButton.setVisible(False)
        self.connect_actions()
        self.setAcceptDrops(True)
        self.renderer = None
        self.uploader = None
        self.cancelled = False

    def load_albums(self):
        file_dialog = QFileDialog(self, "Import Albums")
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QListView, 'listView')

        if file_view:
            file_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        if file_dialog.exec() == QDialog.Accepted:
            paths = file_dialog.selectedFiles()
            for album in paths:
                self.ui.treeWidget.addAlbum(album)

    def on_upload_finished(self, results):
        self.ui.treeWidget.setEnabled(True)
        self.ui.cancelButton.setVisible(False)
        self.ui.renderButton.setVisible(True)
        if self.cancelled:
            logger.error("Upload cancelled")
            # delete rendered/partially-rendered videos
            for path in results:
                try:
                    os.remove(path)
                except:
                    pass
            self.cancelled = False
        else:
            logger.success("{}/{} uploads successful".format(sum(int(s) for s in results.values()),len(results)))
            self.uploader = None
            if get_setting("deleteAfterUploading") == SETTINGS_VALUES.CheckBox.CHECKED:
                for path, success in results.items():
                    if success:
                        os.remove(path)
            # remove successful uploads
            self.ui.treeWidget.remove_by_file_paths({path for path in results if results[path]})


    def on_render_finished(self, results):
        if self.cancelled:
            logger.error("Render cancelled")
            self.on_upload_finished(results)
        else:
            logger.success("{}/{} renders successful".format(sum(int(s) for s in results.values()),len(results)))
            # remove successful renders that will not be uploaded
            self.ui.treeWidget.remove_by_file_paths({path for path in results if results[path]}, False)
            # upload to youtube
            self.uploader = self.ui.treeWidget.get_uploader(results)
            self.uploader.finished.connect(self.on_upload_finished)
            self.uploader.upload()
        self.renderer = None

    def render(self):
        self.ui.treeWidget.setEnabled(False)
        self.ui.cancelButton.setVisible(True)
        self.ui.renderButton.setVisible(False)
        self.renderer = self.ui.treeWidget.get_renderer()
        self.renderer.finished.connect(self.on_render_finished)
        self.ui.progressWindow.on_render_start(self.renderer)
        self.renderer.render()

    def cancel(self):
        self.cancelled = True
        if self.renderer:
            self.renderer.cancel()
            self.ui.treeWidget.setEnabled(True)
            self.ui.cancelButton.setVisible(False)
            self.ui.renderButton.setVisible(True)
        if self.uploader:
            self.uploader.cancel()

    def load_songs(self):
        file_names = QFileDialog.getOpenFileNames(self, "Import Songs")[0]
        for file in file_names:
            self.ui.treeWidget.addSong(file)

    def open_settings(self):
        window = SettingsWindow(self)
        window.settings_changed.connect(self.ui.logWindow.update_settings)
        window.show()

    def about(self):
        QMessageBox.about(self, APPLICATION, f"{VERSION}\nMade by {ORGANIZATION}")

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionAlbums.triggered.connect(self.load_albums)
        self.ui.actionSongs.triggered.connect(self.load_songs)
        self.ui.actionSettings.triggered.connect(self.open_settings)
        self.ui.treeWidget.selectionModel().selectionChanged.connect(self.ui.songSettingsWindow.song_tree_selection_changed)
        self.ui.renderButton.clicked.connect(self.render)
        self.ui.cancelButton.clicked.connect(self.cancel)


if __name__ == "__main__":
    addLoggingLevel("SUCCESS", 60, "success")
    # initialize default settings
    if not os.path.exists(get_settings().fileName()):
        settings_path = get_settings().fileName()
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        shutil.copy(os.path.join(os.path.dirname(__file__), "config", "default.ini"), settings_path)
    app = QApplication([])
    app.setWindowIcon(QIcon(":/image/icon.ico"))
    app.setOrganizationName(ORGANIZATION)
    app.setApplicationName(APPLICATION)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
