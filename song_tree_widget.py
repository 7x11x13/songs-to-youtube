# This Python file uses the following encoding: utf-8
from PySide6.QtCore import Qt, QFileInfo, QModelIndex, QItemSelection, QItemSelectionModel, QDir, QFile, QByteArray
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QStandardItemModel, QStandardItem, QImage
from PySide6.QtWidgets import QTreeView, QAbstractItemView, QAbstractScrollArea

import logging
from enum import IntEnum

from utils import file_is_audio, files_in_directory, files_in_directory_and_subdirectories
from settings import SETTINGS_VALUES, get_setting
from song_tree_widget_item import *
from render import *


class SongTreeModel(QStandardItemModel):
    def __init__(self, *args):
        super().__init__(*args)

    def dropMimeData(self, data, action, row, column, parent):
        # If any albums were dropped into another album,
        # add all the songs in the dropped album
        # but not the album item itself
        if parent.isValid():
            dummy_model = QStandardItemModel()
            dummy_model.dropMimeData(data, action, 0, 0, QModelIndex())
            indexes = []
            for r in range(dummy_model.rowCount()):
                for c in range(dummy_model.columnCount()):
                    index = dummy_model.index(r, c)
                    # QStandardItemModel doesn't recognize our items as our custom classes
                    # so we have to treat them as QStandardItems
                    item = dummy_model.item(r, c)
                    if item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                        indexes += [child.index() for child in AlbumTreeWidgetItem.getChildrenFromStandardItem(item)]
                    elif item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                        indexes.append(index)
            data = dummy_model.mimeData(indexes)
        return super().dropMimeData(data, action, row, column, parent)


class SongTreeSelectionModel(QItemSelectionModel):
    def __init__(self, *args):
        super().__init__(*args)

    def _going_to_select_item(self, index, command):
        if command & QItemSelectionModel.Select:
            return True
        if command & QItemSelectionModel.Toggle and not self.isSelected(index):
            return True
        return False

    def select(self, selected, command):
        # If one of the selected items is an album,
        # deselect all song items to make sure
        # we only edit items of the same type
        # at the same time
        indexes = []
        if isinstance(selected, QModelIndex):
            # turn single selected index into a QItemSelection
            # so we only have to deal with one type
            selected = QItemSelection(selected, selected)

        # check if after this selection action
        # we would have an album selected
        # this will emit selectionChanged
        super().select(selected, command)
        album_selected = False
        for index in self.selection().indexes():
            if index.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                album_selected = True
                break

        if album_selected:
            deselect = None
            if album_selected:
                # deselect all song items
                for index in self.selection().indexes():
                    if index.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                        if deselect:
                            deselect.append(QItemSelection(index, index))
                        else:
                            deselect = QItemSelection(index, index)
            if deselect:
                super().select(deselect, QItemSelectionModel.Deselect)


class SongTreeWidget(QTreeView):

    def __init__(self, *args):
        super().__init__(*args)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.setModel(SongTreeModel())
        self.setSelectionModel(SongTreeSelectionModel(self.model()))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)

    def _create_album_item(self, dir_path, songs):
        return AlbumTreeWidgetItem(dir_path, songs)

    def _create_song_item(self, file_path):
        return SongTreeWidgetItem(file_path)

    def addTopLevelItem(self, item):
        self.model().appendRow(item)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.source() is self:
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.source() is self:
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.source():
            super().dropEvent(event)
        else:
            for url in event.mimeData().urls():

                info = QFileInfo(url.toLocalFile())
                if not info.isReadable():
                    logging.warning("File {} is not readable".format(info.filePath()))
                    continue
                if info.isDir():
                    if get_setting("dragAndDropBehavior") == SETTINGS_VALUES.DragAndDrop.ALBUM_MODE:
                        self.addAlbum(url.toLocalFile())
                    else:
                        for file_path in files_in_directory_and_subdirectories(info.filePath()):
                            self.addSong(file_path)
                else:
                    self.addSong(info.filePath())

    def addAlbum(self, dir_path: str):
        songs = []
        for file_path in files_in_directory(dir_path):
            info = QFileInfo(file_path)
            if not info.isReadable():
                logging.warning("File {} is not readable".format(file_path))
                continue
            if info.isDir():
                self.addAlbum(file_path)
            elif file_is_audio(file_path):
                item = self._create_song_item(file_path)
                item.setText(info.fileName())
                songs.append(item)
        if len(songs) > 0:
            album_item = self._create_album_item(dir_path, songs)
            album_item.setText(dir_path)
            self.addTopLevelItem(album_item)

    def addSong(self, path: str):
        if not file_is_audio(path):
            logging.info("File {} is not audio".format(path))
            return
        item = self._create_song_item(path)
        item.setText(QFileInfo(path).fileName())
        self.addTopLevelItem(item)

    def get_renderer(self):
        renderer = Renderer()
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.item_type() == TreeWidgetType.ALBUM:
                renderer.add_render_album_job(item)
            elif item.item_type() == TreeWidgetType.SONG:
                renderer.add_render_song_job(item)
        return renderer
