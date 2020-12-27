# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QByteArray, QTemporaryFile, QIODevice
from PySide6.QtGui import QStandardItem

from enum import IntEnum
import audio_metadata
import logging
import os

from const import *
from settings import get_setting
from utils import flatten_metadata


class TreeWidgetItemData:
    FIELDS = ('audioBitrate', 'backgroundColor', 'videoHeight', 'videoWidth',
              'uploadYouTube', 'albumPlaylist', 'coverArt', 'userSelect',
              'videoDescription', 'videoTags', 'videoTitle', 'videoVisibility')
    def __init__(self, **kwargs):
        self.metadata = {}
        self.dict = {}
        for field in set(kwargs.keys()) | set(TreeWidgetItemData.FIELDS):
            # set all mandatory settings to their defaults if not
            # specified in the parameters
            # and any extra settings specified in the parameters
            if field in kwargs:
                self.dict[field] = kwargs[field]
            else:
                # set to default setting
                self.dict[field] = get_setting(field)

            if field == 'coverArt' and self.dict[field] in QRC_TO_FILE_PATH:
                # convert resource path to real file path for ffmpeg
                self.dict[field] = QRC_TO_FILE_PATH[get_setting(field)]

        if 'file_path' in self.dict:
            # add metadata
            try:
                metadata = audio_metadata.load(self.dict['file_path'])

                if get_setting('extractCoverArt') == SETTINGS_VALUES.CheckBox.CHECKED:
                    # extract cover art if it exists
                    if metadata.pictures and len(metadata.pictures) > 0:
                        bytes = QByteArray(metadata.pictures[0].data)
                        cover = QTemporaryFile(os.path.join(QDir().tempPath(), APPLICATION, "XXXXXX.cover"))
                        cover.setAutoRemove(False)
                        cover.open(QIODevice.WriteOnly)
                        cover.write(bytes)
                        cover.close()
                        self.set_value('coverArt', cover.fileName())


                self.metadata = flatten_metadata(metadata)


            except Exception as e:
                logging.warning(e)
                logging.warning(self.dict['file_path'])


    def to_dict(self):
        return self.dict

    def get_value(self, field):
        return self.dict[field]

    def set_value(self, field, value):
        self.dict[field] = value

    def get_duration_ms(self):
        if 'streaminfo.duration' in self.metadata:
            return self.metadata['streaminfo.duration'] * 1000
        else:
            logging.warning("Could not find duration of file {}".format(self.dict['file_path']))
            logging.debug(self.metadata)
            return 180 * 1000

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

    def to_dict(self):
        return self.data(CustomDataRole.ITEMDATA).to_dict()

    def item_type(self):
        return self.data(CustomDataRole.ITEMTYPE)

    def get_duration_ms(self):
        return self.data(CustomDataRole.ITEMDATA).get_duration_ms()


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
