# This Python file uses the following encoding: utf-8

from PySide6.QtCore import QObject, Signal, QThread

import logging
import traceback

from youtube_uploader_selenium import YouTubeUploader
from song_tree_widget_item import *
from settings import get_setting
from const import *

logger = logging.getLogger(APPLICATION)

class UploadWorker(QObject):

    upload_finished = Signal(str, bool) # file_path, success
    log_message = Signal(str, int) # message, loglevel
    on_progress = Signal(str, int) # job name, percent done
    finished = Signal()

    def __init__(self, username, jobs):
        super().__init__()
        self.jobs = jobs
        self.username = username

    def run(self):
        try:
            self.uploader = YouTubeUploader(self.username, self.jobs)
            self.uploader.upload_finished.connect(lambda file_path, success: self.upload_finished.emit(file_path, success))
            self.uploader.log_message.connect(lambda message, level: self.log_message.emit(message, level))
            self.uploader.on_progress.connect(lambda job_name, progress: self.on_progress.emit(job_name, progress))
            self.uploader.upload_all()
        except Exception:
            self.log_message.emit(traceback.format_exc(), logging.ERROR)
        finally:
            self.finished.emit()


class Uploader(QObject):

    # dict of worker name and worker success
    finished = Signal(dict)
    
    # worker name, worker progress (percentage)
    worker_progress = Signal(str, int)

    # not used
    worker_error = Signal(str, str)

    # worker name
    worker_done = Signal(str, bool)

    def __init__(self, render_results, *args):
        super().__init__()
        self.uploading = False
        self.jobs = []
        self.results = {}
        self.render_results = render_results
        self.cancelled = False
        self.worker = None
        self.thread = None

    def upload_finished(self, file_path, success):
        self.results[file_path] = success
        self.worker_done.emit(file_path, success)

    def on_done_uploading(self, file_path, success):
        if not self.cancelled:
            self.uploading = False
            self.results[file_path] = success

    def cancel(self):
        self.cancelled = True
        for job in self.jobs:
            if job['file_path'] not in self.results:
                self.results[job['file_path']] = False
        self.finished.emit(self.results)
        self.worker.uploader.browser.quit()
            

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
                                'visibility': album.get('videoVisibilityAlbum'),
                                'notify_subs': album.get('notifySubsAlbum') == SETTINGS_VALUES.CheckBox.CHECKED}
                    metadata['file_path'] = file
                    self.jobs.append(metadata)
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
                            'visibility': song.get('videoVisibility'),
                            'notify_subs': song.get('notifySubs') == SETTINGS_VALUES.CheckBox.CHECKED}
                metadata['file_path'] = file
                if any(job['file_path'] == file for job in self.jobs):
                    logger.error(f"Ignoring duplicate job {file}")
                else:
                    self.jobs.append(metadata)

    def is_uploading(self):
        return self.uploading

    def worker_finished(self):
        self.worker.deleteLater()
        self.thread.quit()
        self.finished.emit(self.results)
        
    def log(self, message, level):
        if not self.cancelled:
            logger.log(level, message)

    def upload(self):
        self.results = {job['file_path']: False for job in self.jobs}
        if len(self.jobs) == 0:
            self.finished.emit(self.results)
            return
        self.thread = QThread()
        username = get_setting('username')
        if not username:
            raise ValueError("No user selected to upload to. Add a user at File > Settings > Add new user")
        self.worker = UploadWorker(username, self.jobs)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda: self.worker_finished())
        self.thread.finished.connect(lambda: self.thread.deleteLater())
        self.worker.log_message.connect(self.log)
        self.worker.on_progress.connect(lambda worker_name, progress: self.worker_progress.emit(worker_name, progress))
        self.worker.upload_finished.connect(self.upload_finished)
        self.thread.start()