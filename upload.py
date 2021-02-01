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

    def __init__(self, uploader, file_path, metadata, callback=lambda: None):
        super().__init__(daemon=True)
        self.uploader = uploader
        self.file_path = file_path
        self.metadata = metadata
        self.callback = callback

    def run(self):
        try:
            success, video_id = self.uploader.upload(self.file_path, self.metadata)
            if success:
                logging.success("Successfully uploaded {}, link at: https://youtube.com/watch?v={}".format(self.file_path, video_id))
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
        self.uploader = None
        self.uploading = False
        self.threads = []
        self.results = {}
        self.render_results = render_results

    def on_done_uploading(self, success, thread):
        self.uploading = False
        self.threads.remove(thread)
        self.results[thread.file_path] = success
        if len(self.threads) == 0:
            self.uploader.quit()
            self.finished.emit(self.results)
        else:
            self.uploading = True
            self.threads[0].start()

    def _upload(self, file_path, metadata):
        if self.uploader is None:
            self.uploader = YouTubeUploader(get_setting('username'))
        if self.uploader.username == "":
            raise Exception("No user selected to upload to")
        thread = UploadThread(self.uploader, file_path, metadata, self.on_done_uploading)
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
                if file in self.render_results and self.render_results[file]:
                    album.before_upload()
                    metadata = {'title': album.get('videoTitleAlbum'),
                                'description': album.get('videoDescriptionAlbum'),
                                'tags': album.get('videoTagsAlbum'),
                                'visibility': album.get('videoVisibilityAlbum')}
                    self._upload(file, metadata)
        elif album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.add_upload_song_job(song)

    def add_upload_song_job(self, song: SongTreeWidgetItem):
        if song.get('uploadYouTube') == SETTINGS_VALUES.CheckBox.CHECKED:
            file = song.get("fileOutput")
            if file in self.render_results and self.render_results[file]:
                song.before_upload()
                metadata = {'title': song.get('videoTitle'),
                            'description': song.get('videoDescription'),
                            'tags': song.get('videoTags'),
                            'playlist': song.get('playlistName'),
                            'visibility': song.get('videoVisibility')}
                self._upload(file, metadata)

    def is_uploading(self):
        return self.uploading
