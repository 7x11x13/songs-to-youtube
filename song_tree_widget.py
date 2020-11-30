# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Qt, QDir, QFileInfo, QDirIterator, QMimeDatabase, QMimeType, QModelIndex, QIODevice, QDataStream, QByteArray, QMetaObject
from PySide2.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QTreeView, QTreeWidgetItem, QAbstractItemView
from utils import file_is_audio, files_in_directory, files_in_directory_and_subdirectories
from const import TreeWidgetType, CustomDataRole

import logging


class PlaceholderTreeWidgetItem(QStandardItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlags(Qt.NoItemFlags)
        self.setText("<placeholder>")
        self.setData(TreeWidgetType.PLACEHOLDER, CustomDataRole.ITEMTYPE)


class SongTreeWidgetItem(QStandardItem):
    def __init__(self):
        super().__init__()
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled)
        self.setData(TreeWidgetType.SONG, CustomDataRole.ITEMTYPE)


class AlbumTreeWidgetItem(QStandardItem):
    def __init__(self):
        super().__init__()
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.setData(TreeWidgetType.ALBUM, CustomDataRole.ITEMTYPE)

    def addChild(self, item):
        self.appendRow(item)

    def childCount(self):
        return self.rowCount()

    def getChildren(self):
        for i in range(self.childCount()):
            yield self.child(i)

    @classmethod
    def getChildrenFromStandardItem(cls, item):
        for i in range(item.rowCount()):
            yield item.child(i)


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
                    item = dummy_model.item(r, c)
                    if item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                        # QStandardItemModel doesn't recognize our items as our custom classes
                        # so we have to treat them as QStandardItems
                        indexes += [child.index() for child in AlbumTreeWidgetItem.getChildrenFromStandardItem(item)]
                    else:
                        indexes.append(index)
            data = dummy_model.mimeData(indexes)
        return super().dropMimeData(data, action, row, column, parent)

class SongTreeWidget(QTreeView):

    def __init__(self, *args):
        super().__init__(*args)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDropIndicatorShown(True)
        self.setModel(SongTreeModel())

    def _create_album_item(self):
        return AlbumTreeWidgetItem()

    def _create_song_item(self):
        return SongTreeWidgetItem()

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
            # If any albums were dropped into another album,
            # add all the songs in the dropped album
            # but not the album item itself
            """album_items = filter(lambda item: isinstance(item, AlbumTreeWidgetItem), self.selectedItems())
            if (drop_item := self.itemAt(event.pos())) is not None:
                if (drop_album := drop_item.parent()) is not None:
                    for album in album_items:


            print(drop_item.text(0), event.proposedAction())"""
            super().dropEvent(event)
        else:
            for url in event.mimeData().urls():

                info = QFileInfo(url.toLocalFile())
                if not info.isReadable():
                    logging.warning("File %s is not readable" % info.filePath())
                    continue
                if info.isDir():
                    self.addAlbum(url.toLocalFile())
                else:
                    self.addSong(info.filePath())

    def addAlbum(self, dir_path: str):
        album_item = self._create_album_item()
        album_item.setText(dir_path)
        for file_path in files_in_directory(dir_path):
            info = QFileInfo(file_path)
            if not info.isReadable():
                logging.warning("File %s is not readable" % info.filePath())
                continue
            if info.isDir():
                self.addAlbum(file_path)
            elif file_is_audio(file_path):
                item = self._create_song_item()
                item.setText(file_path)
                album_item.addChild(item)
        if album_item.childCount() > 0:
            self.addTopLevelItem(album_item)

    def addSong(self, path: str):
        if not file_is_audio(path):
            return
        item = self._create_song_item()
        item.setText(path)
        self.addTopLevelItem(item)
