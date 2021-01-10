# This Python file uses the following encoding: utf-8

from PySide6.QtCore import QObject, Signal

from queue import Queue
from threading import Thread
import logging
import traceback
import time

from youtube_uploader_selenium import YouTubeUploader
from song_tree_widget_item import *
from settings import get_setting

class UploadThread(Thread):

    def __init__(self, file_path, metadata, username, callback=lambda: None):
        super().__init__(daemon=True)
        self.file_path = file_path
        self.metadata = metadata
        self.callback = callback
        self.username = username

    def run(self):
        try:
            if self.username == "":
                raise Exception("No user selected to upload to")
            self.uploader = YouTubeUploader(self.file_path, self.metadata, self.username)
            time.sleep(5)
            success, video_id = self.uploader.upload()
            if success:
                logging.info("Successfully uploaded {}, link at: https://youtube.com/watch?v={}".format(self.file_path, video_id))
            else:
                logging.error("Could not upload {}".format(self.file_path))
            self.callback(success, self)
        except Exception as e:
            logging.error("Error while uploading {}".format(self.file_path))
            logging.error(traceback.format_exc())
            logging.error(e)
            self.callback(False, self)


class Uploader(QObject):
    finished = Signal(dict)

    def __init__(self, render_results, *args):
        super().__init__()
        self.uploading = False
        self.threads = []
        self.results = {}
        self.render_results = render_results

    def on_done_uploading(self, success, thread):
        self.uploading = False
        self.threads.remove(thread)
        self.results[thread.file_path] = success
        if len(self.threads) == 0:
            self.finished.emit(self.results)
        else:
            self.uploading = True
            self.threads[0].start()

    def _upload(self, file_path, metadata):
        thread = UploadThread(file_path, metadata, get_setting('username'), self.on_done_uploading)
        self.threads.append(thread)
        if not self.uploading:
            self.uploading = True
            thread.start()

    def add_upload_album_job(self, album: AlbumTreeWidgetItem):
        if album.childCount() == 0:
            return
        if album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.SINGLE:
            if album.get('uploadYouTube') == SETTINGS_VALUES.CheckBox.CHECKED:
                file = album.get("fileOutput")
                if self.render_results[file]:
                    metadata = {'title': album.get('videoTitleAlbum'),
                                'description': album.get('videoDescriptionAlbum'),
                                'tags': album.get('videoTagsAlbum'),
                                'visibility': album.get('videoVisibility')}
                    self._upload(file, metadata)
        elif album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.add_upload_song_job(song)

    def add_upload_song_job(self, song: SongTreeWidgetItem):
        if song.get('uploadYouTube') == SETTINGS_VALUES.CheckBox.CHECKED:
            file = song.get("fileOutput")
            if self.render_results[file]:
                metadata = {'title': song.get('videoTitle'),
                            'description': song.get('videoDescription'),
                            'tags': song.get('videoTags'),
                            'playlist': song.get('playlistName'),
                            'visibility': song.get('videoVisibility')}
                self._upload(file, metadata)

    def is_uploading(self):
        return self.uploading
