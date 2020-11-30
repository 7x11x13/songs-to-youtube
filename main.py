# This Python file uses the following encoding: utf-8
import sys
import os
import logging

from PySide2.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QListView, QTreeView, QAbstractItemView
from PySide2.QtCore import QFile
from PySide2.QtUiTools import QUiLoader

# Custom widgets
from song_tree_widget import SongTreeWidget
CUSTOM_WIDGETS = [SongTreeWidget]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_ui()
        self.connectActions()
        self.setAcceptDrops(True)

    def load_ui(self):
        loader = QUiLoader()
        for cw in CUSTOM_WIDGETS:
            loader.registerCustomWidget(cw)
        path = os.path.join(os.path.dirname(__file__), "ui", "mainwindow.ui")
        ui_file = QFile(path)
        if not ui_file.open(QFile.ReadOnly):
            print("Cannot open {}: {}".format(path, ui_file.errorString()))
            sys.exit(-1)
        self.ui = loader.load(ui_file)
        ui_file.close()

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

    def show(self):
        self.ui.show()

    def connectActions(self):
        self.ui.actionAlbums.triggered.connect(self.load_albums)
        self.ui.actionSongs.triggered.connect(self.load_songs)


if __name__ == "__main__":
    app = QApplication([])
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
