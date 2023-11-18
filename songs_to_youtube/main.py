import atexit
import glob
import logging
import os
import posixpath
import shutil
import sys

from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import *

from songs_to_youtube.const import *
from songs_to_youtube.field import *
from songs_to_youtube.log import *
from songs_to_youtube.progress_window import ProgressWindow
from songs_to_youtube.settings import *
from songs_to_youtube.song_settings_widget import SongSettingsWidget
from songs_to_youtube.song_tree_widget import SongTreeWidget
from songs_to_youtube.utils import *

logger = logging.getLogger(APPLICATION)


class MainWindow(QMainWindow):
    def __init__(self, first_time=False):
        super().__init__()
        self.ui = load_ui(
            "mainwindow.ui",
            (SongSettingsWidget, SongTreeWidget, LogWidget, ProgressWindow),
        )
        self.first_time = first_time
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
        file_view = file_dialog.findChild(QListView, "listView")

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
            logger.success(
                "{}/{} uploads successful".format(
                    sum(int(s) for s in results.values()), len(results)
                )
            )
            self.uploader = None
            if get_setting("deleteAfterUploading") == SETTINGS_VALUES.CheckBox.CHECKED:
                for path, success in results.items():
                    if success:
                        os.remove(path)
            # remove successful uploads
            self.ui.treeWidget.remove_by_file_paths(
                {path for path in results if results[path]}
            )

    def on_render_finished(self, results):
        if self.cancelled:
            logger.error("Render cancelled")
            self.on_upload_finished(results)
        else:
            logger.success(
                "{}/{} renders successful".format(
                    sum(int(s) for s in results.values()), len(results)
                )
            )
            # remove successful renders that will not be uploaded
            self.ui.treeWidget.remove_by_file_paths(
                {path for path in results if results[path]}, False
            )
            # upload to youtube;
            self.uploader = self.ui.treeWidget.get_uploader(results)
            self.uploader.finished.connect(self.on_upload_finished)
            self.ui.progressWindow.on_upload_start(self.uploader)
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
        if (
            get_setting("uploadYouTube") == SETTINGS_VALUES.CheckBox.CHECKED
            and len(YouTubeLogin.get_all_usernames()) == 0
        ):
            msg_box = QMessageBox.warning(
                self,
                "Warning",
                "No users detected, but upload to YouTube is the default. Add new user for uploading?",
                QMessageBox.Ok | QMessageBox.Cancel,
            )
            if msg_box == QMessageBox.Ok:
                self.msg_box = AddUserWindow()
                self.msg_box.show()

    def connect_actions(self):
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionAlbums.triggered.connect(self.load_albums)
        self.ui.actionSongs.triggered.connect(self.load_songs)
        self.ui.actionSettings.triggered.connect(self.open_settings)
        self.ui.treeWidget.selectionModel().selectionChanged.connect(
            self.ui.songSettingsWindow.song_tree_selection_changed
        )
        self.ui.renderButton.clicked.connect(self.render)
        self.ui.cancelButton.clicked.connect(self.cancel)


def main():
    # no idea why this is necessary but it is... otherwise
    # future calls to QUiLoader completely freeze the app
    _ = QUiLoader()
    addLoggingLevel("SUCCESS", 60, "success")
    # initialize default settings
    settings_path = get_settings().fileName()
    if not os.path.exists(settings_path):
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        shutil.copy(resource_path("config/default.ini"), settings_path)

    os.makedirs(posixpath.join(QDir().tempPath(), APPLICATION), exist_ok=True)

    def clean_up():
        for file in glob.glob(posixpath.join(QDir().tempPath(), APPLICATION, "*")):
            os.remove(file)

    atexit.register(clean_up)
    app = QApplication([])
    app.setWindowIcon(QIcon(APPLICATION_IMAGES[":/image/icon.ico"]))
    app.setOrganizationName(ORGANIZATION)
    app.setApplicationName(APPLICATION)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
