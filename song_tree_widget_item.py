# This Python file uses the following encoding: utf-8
from PySide6.QtGui import QStandardItem

from enum import IntEnum

from const import *
from settings import get_setting


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

    def get(self, field):
        return self.data(CustomDataRole.ITEMDATA).get_value(field)

    def item_type(self):
        return self.data(CustomDataRole.ITEMTYPE)


class AlbumTreeWidgetItem(QStandardItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.setData(TreeWidgetType.ALBUM, CustomDataRole.ITEMTYPE)
        self.setData(TreeWidgetItemData(), CustomDataRole.ITEMDATA)

    def get(self, field):
        return self.data(CustomDataRole.ITEMDATA).get_value(field)

    def item_type(self):
        return self.data(CustomDataRole.ITEMTYPE)

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
