# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Qt, QFileInfo, QModelIndex, QItemSelection, QItemSelectionModel
from PySide2.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QStandardItemModel, QStandardItem
from PySide2.QtWidgets import QTreeView, QAbstractItemView, QAbstractScrollArea

import logging
from enum import IntEnum

from utils import file_is_audio, files_in_directory, files_in_directory_and_subdirectories
from settings import SETTINGS_VALUES, get_setting


class TreeWidgetType(IntEnum):
    SONG = 0
    ALBUM = 1
    PLACEHOLDER = 2


class CustomDataRole(IntEnum):
    ITEMTYPE = Qt.UserRole
    ITEMDATA = Qt.UserRole + 1


class TreeWidgetItemData:
    FIELDS = ('audioBitrate', 'videoHeight', 'videoWidth',
              'uploadYouTube', 'albumPlaylist', 'coverArt', 'userSelect',
              'videoDescription', 'videoTags', 'videoTitle', 'videoVisibility')
    def __init__(self, **kwargs):
        self.dict = {}
        for field in set(kwargs.keys()) | set(TreeWidgetItemData.FIELDS):
            # set all mandatory settings to their defaults if not
            # specified in the parameters
            # and any extra settings specified in the parameters
            if field in kwargs:
                self.dict[field] = kwargs[field]
            else:
                #set to default setting
                self.dict[field] = get_setting(field)

    def to_dict(self):
        return self.dict

    def get_value(self, field):
        return self.dict[field]

    def set_value(self, field, value):
        self.dict[field] = value

    def __repr__(self):
        return str(self.dict)


class PlaceholderTreeWidgetItem(QStandardItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlags(Qt.NoItemFlags)
        self.setText("<placeholder>")
        self.setData(TreeWidgetType.PLACEHOLDER, CustomDataRole.ITEMTYPE)
        self.setData(TreeWidgetItemData(), CustomDataRole.ITEMDATA)


class SongTreeWidgetItem(QStandardItem):
    def __init__(self, file_path, *args):
        super().__init__(*args)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled)
        self.setData(TreeWidgetType.SONG, CustomDataRole.ITEMTYPE)
        self.setData(TreeWidgetItemData(file_path=file_path), CustomDataRole.ITEMDATA)


class AlbumTreeWidgetItem(QStandardItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.setData(TreeWidgetType.ALBUM, CustomDataRole.ITEMTYPE)
        self.setData(TreeWidgetItemData(), CustomDataRole.ITEMDATA)

    def addChild(self, item):
        self.appendRow(item)

    def childCount(self):
        return self.rowCount()

    def getChildren(self):
        for i in range(self.childCount()):
            yield self.child(i)

    @staticmethod
    def getChildrenFromStandardItem(item: QStandardItem):
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
            print("selected is single")
            # turn single selected index into a QItemSelection
            # so we can add more selected indexes if we want
            selected = QItemSelection(selected, selected)

        for index in selected.indexes():
            # only add child indexes if we are selecting an album
            if self._going_to_select_item(index, command):
               r, c = index.row(), index.column()
               item = self.model().item(r, c)
               if index.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM and item.child(0) is not None:
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
               item.setText(file_path)
               album_item.addChild(item)
       if album_item.childCount() > 0:
           self.addTopLevelItem(album_item)

   def addSong(self, path: str):
       if not file_is_audio(path):
           logging.info("File {} is not audio".format(path))
           return
       item = self._create_song_item(path)
       item.setText(path)
       self.addTopLevelItem(item)
