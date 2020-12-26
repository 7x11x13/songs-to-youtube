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
        # When an album is selected, also select all its songs
        # so when we change an album's properties all its songs
        # properties also change
        indexes = []
        if isinstance(selected, QModelIndex):
            # turn single selected index into a QItemSelection
            # so we can add more selected indexes if we want
            selected = QItemSelection(selected, selected)

        for index in selected.indexes():
            # only add child indexes if we are selecting an album
            if self._going_to_select_item(index, command):
                r, c = index.row(), index.column()
                item = self.model().item(r, c)
                if item.item_type() == TreeWidgetType.ALBUM and item.child(0) is not None:
                    first_child = item.child(0).index()
                    last_child = item.child(item.rowCount() - 1).index()
                    selected.append(QItemSelection(first_child, last_child))
        super().select(selected, command)


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

    def _create_album_item(self):
        return AlbumTreeWidgetItem()

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
        album_item = self._create_album_item()
        album_item.setText(dir_path)
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
                album_item.addChild(item)
        if album_item.childCount() > 0:
            self.addTopLevelItem(album_item)

    def addSong(self, path: str):
        if not file_is_audio(path):
            logging.info("File {} is not audio".format(path))
            return
        item = self._create_song_item(path)
        item.setText(QFileInfo(path).fileName())
        self.addTopLevelItem(item)

    def render(self):
        renderer = Renderer()
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.item_type() == TreeWidgetType.ALBUM:
                renderer.render_album(item)
            elif item.item_type() == TreeWidgetType.SONG:
                renderer.render_song(item)
        return renderer
