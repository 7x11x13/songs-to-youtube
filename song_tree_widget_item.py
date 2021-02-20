# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QByteArray, QTemporaryFile, QIODevice, QFileInfo, QDir
from PySide6.QtGui import QStandardItem

from enum import IntEnum
import audio_metadata
import logging
import os
import datetime
import subprocess
from string import Template

from const import *
from settings import get_setting
from utils import flatten_metadata

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
        # can be any type
        self.metadata = {}

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
                metadata = audio_metadata.load(self.dict['song_path'])

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
                logging.warning(self.dict['song_path'])
        else:
            # album gets metadata from children
            # song metadata is stored as song.<key>
            # e.g. song.tags.album would be the album name
            #
            # we will only get metadata from one song
            # because the album shouldn't care about
            # the varying metadata values for the songs
            # such as title or track number
            for song in songs:
                if song.has_metadata():
                    for key, value in song.to_dict().items():
                        key = "song.{}".format(key)
                        self.metadata[key] = value
                    break

        self.update_fields()

    def update_fields(self):
        for field, value in self.dict.items():
            self.set_value(field, value)

    def to_dict(self):
        dict = {**self.dict, **self.metadata}
        return dict

    def get_value(self, field):
        return self.dict[field]

    def get_metadata_value(self, key):
        if key in self.metadata:
            return self.metadata[key]
        return None

    def set_value(self, field, value):
        # replace {variable} with value from metadata
        value = SettingTemplate(value).safe_substitute(**self.to_dict())

        if field in ("videoDescription", "videoDescriptionAlbum",
                     "videoTitle", "videoTitleAlbum"):
            # youtube does not allow < and > symbols in title/description
            # replace with fullwidth version
            value = value.replace("<", "＜").replace(">", "＞")

        self.dict[field] = value

    def get_duration_ms(self):
        if 'streaminfo.duration' in self.metadata:
            return self.metadata['streaminfo.duration'] * 1000
        else:
            logging.error("Could not find duration of file {}".format(self.dict['song_path']))
            logging.debug(self.metadata)
            return 180 * 1000

    def get_track_number(self):
        if 'tags.tracknumber' in self.metadata:
            try:
                tracknumber = self.metadata['tags.tracknumber']
                if "/" in tracknumber:
                    # sometimes track number is represented as a fraction
                    tracknumber = tracknumber[:tracknumber.index("/")]
                return int(tracknumber)
            except:
                logging.warning("Could not convert {} to int".format(self.metadata['tags.tracknumber']))
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

    def has_metadata(self):
        return len(self.data(CustomDataRole.ITEMDATA).metadata) > 0

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
        # create temporary file name guaranteed to be unique
        temp_file = QTemporaryFile(os.path.join(QDir().tempPath(), APPLICATION, "XXXXXX.{}".format(self.get("fileOutputName"))))
        temp_file.setAutoRemove(False)
        temp_file.open(QIODevice.WriteOnly)
        temp_file.close()
        self.set("tempFileOutput", temp_file.fileName())
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

