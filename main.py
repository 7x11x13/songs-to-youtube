# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QListView, QTreeView, QAbstractItemView


import sys
import os
import logging

from utils import load_ui

# Custom widgets
from song_settings_widget import SongSettingsWidget
from song_tree_widget import SongTreeWidget
from log import LogWidget
from settings import SettingsWindow
CUSTOM_WIDGETS = (SongSettingsWidget, SongTreeWidget, LogWidget)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = load_ui("mainwindow.ui", CUSTOM_WIDGETS)
        self.connect_actions()
        self.setAcceptDrops(True)

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

    def load_songs(self):
        file_names = QFileDialog.getOpenFileNames(self, "Import Songs")[0]
        for file in file_names:
            self.ui.treeWidget.addSong(file)

    def open_settings(self):
        window = SettingsWindow(self)
        window.settings_changed.connect(self.ui.logWindow.update_settings)
        window.show()

    def show(self):
        self.ui.show()

    def connect_actions(self):
        self.ui.actionAlbums.triggered.connect(self.load_albums)
        self.ui.actionSongs.triggered.connect(self.load_songs)
        self.ui.actionSettings.triggered.connect(self.open_settings)
        self.ui.treeWidget.selectionModel().selectionChanged.connect(self.ui.songSettingsWindow.song_tree_selection_changed)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
