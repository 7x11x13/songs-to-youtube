# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QByteArray, QTemporaryFile, QIODevice, QFileInfo, QDir
from PySide6.QtGui import QStandardItem

from enum import IntEnum
import logging
import os
import datetime
import subprocess
from string import Template

from const import *
from settings import get_setting
from utils import flatten_metadata
from metadata import Metadata

class SettingTemplate(Template):
    # template placeholders are of the form
    # ~{key}
    # can be escaped by writing ~~{key}
    delimiter = "~"

    # placeholder must be surrounded by braces
    idpattern = None

    # key can be anything
    braceidpattern = r"[^{}]*"

class TreeWidgetItemData:
    def __init__(self, item_type, songs=None, **kwargs):

        # metadata values
        self.metadata = None

        # application values
        # always strings
        self.dict = {}
        app_fields = SONG_FIELDS if item_type == TreeWidgetType.SONG else ALBUM_FIELDS
        for field in (set(kwargs.keys()) | app_fields):
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

        # add song metadata
        if item_type == TreeWidgetType.SONG:
            try:
                self.metadata = Metadata(self.dict['song_path'])

                if get_setting('extractCoverArt') == SETTINGS_VALUES.CheckBox.CHECKED:
                    if (cover_path := self.metadata.get_cover_art()) is not None:
                        self.set_value('coverArt', cover_path)

            except Exception as e:
                logging.warning(e)
                logging.warning(self.dict['song_path'])
        else:
            # album gets metadata from children
            # song metadata is stored as song.<key>
            # e.g. song.album would be the album name
            #
            # we will only get metadata from one song
            # because the album shouldn't care about
            # the varying metadata values for the songs
            # such as title or track number
            for song in songs:
                for key, value in song.to_dict().items():
                    key = "song.{}".format(key)
                    self.dict[key] = value
                break

        self.update_fields()

    def update_fields(self):
        for field, value in self.dict.items():
            self.set_value(field, value)

    def to_dict(self):
        dict = {**self.dict, **(self.metadata.get_tags() if self.metadata is not None else {})}
        return dict

    def get_value(self, field):
        return self.dict[field]

    def get_metadata_value(self, key):
        if key in self.metadata.get_tags():
            return self.metadata.get_tags()[key]
        return None

    def set_value(self, field, value):
        # replace {variable} with value from metadata
        value = SettingTemplate(value).safe_substitute(**self.to_dict())
        self.dict[field] = value

    def get_duration_ms(self):
        if 'length' in self.metadata.get_tags():
            return float(self.metadata.get_tags()['length']) * 1000
        else:
            logging.error("Could not find duration of file {}".format(self.dict['song_path']))
            logging.debug(self.metadata.get_tags())
            return 999999999

    def get_track_number(self):
        if 'tracknumber' in self.metadata.get_tags():
            try:
                tracknumber = self.metadata.get_tags()['tracknumber']
                if "/" in tracknumber:
                    # sometimes track number is represented as a fraction
                    tracknumber = tracknumber[:tracknumber.index("/")]
                return int(tracknumber)
            except:
                logging.warning("Could not convert {} to int".format(self.metadata.get_tags()['tracknumber']))
                return 0
        return 0

    def __str__(self):
        return str(self.dict)


class SongTreeWidgetItem(QStandardItem):
    def __init__(self, file_path, *args):
        super().__init__(*args)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled)
        self.setData(TreeWidgetType.SONG, CustomDataRole.ITEMTYPE)
        info = QFileInfo(file_path)
        self.setData(TreeWidgetItemData(
                        TreeWidgetType.SONG,
                        song_path=file_path,
                        song_dir=info.path(),
                        song_file=info.fileName()),
                     CustomDataRole.ITEMDATA)

    def get(self, field):
        return self.data(CustomDataRole.ITEMDATA).get_value(field)

    def set(self, field, value):
        self.data(CustomDataRole.ITEMDATA).set_value(field, value)

    def to_dict(self):
        return self.data(CustomDataRole.ITEMDATA).to_dict()

    def item_type(self):
        return self.data(CustomDataRole.ITEMTYPE)

    def get_duration_ms(self):
        return self.data(CustomDataRole.ITEMDATA).get_duration_ms()

    def before_render(self):
        self.set("fileOutput", os.path.join(self.get("fileOutputDir"), self.get("fileOutputName")))
        self.set("songDuration", str(self.get_duration_ms() / 1000))

    def before_upload(self):
        pass

    def get_track_number(self):
        return self.data(CustomDataRole.ITEMDATA).get_track_number()

    @classmethod
    def from_standard_item(cls, item: QStandardItem):
        for name, value in cls.__dict__.items():
            if callable(value) and name != '__init__':
                bound = value.__get__(item)
                setattr(item, name, bound)
        return item



class AlbumTreeWidgetItem(QStandardItem):
    def __init__(self, dir_path, songs, *args):
        super().__init__(*args)
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled
                      | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self.setData(TreeWidgetType.ALBUM, CustomDataRole.ITEMTYPE)

        # order songs by tracknumber if possible
        songs.sort(key=lambda song: song.get_track_number())

        self.setData(TreeWidgetItemData(
                        TreeWidgetType.ALBUM,
                        songs,
                        album_dir=dir_path
                    ), CustomDataRole.ITEMDATA)

        for song in songs:
            self.addChild(song)

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
            yield SongTreeWidgetItem.from_standard_item(self.child(i))

    @staticmethod
    def getChildrenFromStandardItem(item: QStandardItem):
        for i in range(item.rowCount()):
            yield item.child(i)

    @classmethod
    def from_standard_item(cls, item: QStandardItem):
        for name, value in cls.__dict__.items():
            if callable(value) and name != '__init__':
                bound = value.__get__(item)
                setattr(item, name, bound)
        return item

    def get_duration_ms(self):
        return sum(song.get_duration_ms() for song in self.getChildren())

    def before_render(self):
        self.data(CustomDataRole.ITEMDATA).set_value("fileOutput", os.path.join(self.get("fileOutputDirAlbum"), self.get("fileOutputNameAlbum")))

    def before_upload(self):
        # generate timestamps
        timestamp = 0
        timestamp_str = ""
        for song in self.getChildren():
            timestamp_str += "{} {}\n".format(datetime.timedelta(seconds=int(timestamp)), song.get("videoTitle"))
            timestamp += float(song.get("realVideoLength"))
        data = self.data(CustomDataRole.ITEMDATA)
        data.set_value("timestamps", timestamp_str)
        data.update_fields()

