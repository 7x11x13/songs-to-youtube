# This Python file uses the following encoding: utf-8

from PySide6.QtCore import QThread, Signal, QObject

import subprocess
import logging
import time
import traceback
from threading import Thread
from queue import Queue

from song_tree_widget_item import *
from const import QRC_TO_FILE_PATH


class FFmpeg_Handler(QObject):

    progress = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()

    def read_pipe(self, pipe, queue):
        try:
            with pipe:
                for line in iter(pipe.readline, b''):
                    queue.put((pipe, line.decode()))
        finally:
            queue.put((None, None))

    def run_ffmpeg(self, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        q = Queue()
        Thread(target=self.read_pipe, args=[p.stdout, q]).start()
        Thread(target=self.read_pipe, args=[p.stderr, q]).start()
        errors = False
        while True:
            while q.empty() or (item := q.get_nowait()) is None:
                time.sleep(0.01)
            pipe, line = item
            if pipe is None:
                break
            if pipe == p.stdout:
                self.progress.emit(line)
            else:
                errors = True
                self.error(line)
        return errors

class RenderSongWorker(QObject):
    finished = Signal(bool)
    progress = Signal(str)

    def __init__(self, song: SongTreeWidgetItem, logger):
        super().__init__()
        self.song = song
        self.logger = logger

    def __str__(self):
        return "RenderSongWorker<{}>".format(self.song.get('file_path'))

    def run(self):
        try:
            cover_art = self.song.get('coverArt')
            if cover_art in QRC_TO_FILE_PATH:
                cover_art = QRC_TO_FILE_PATH[cover_art]
            command_str = ('ffmpeg -loglevel error -progress pipe:1 -y -loop 1 -i "{cover_art}" -i "{audio_path}" '
            '-vf "pad=width={videoWidth}:height={videoHeight}:x=(out_w-in_w)/2:y=(out_h-in_h)/2:color=black" '
            '-c:a aac -ab {audioBitrate} -c:v libx264 -pix_fmt yuv420p -shortest -strict -2 "{out_path}"').format(
                cover_art = cover_art,
                audio_path = self.song.get('file_path'),
                audioBitrate = self.song.get('audioBitrate'),
                videoWidth = self.song.get('videoWidth'),
                videoHeight = self.song.get('videoHeight'),
                out_path = self.song.get('file_path') + '.mp4')
            self.logger.debug(command_str)
            handler = FFmpeg_Handler()
            handler.error.connect(self.logger.error)
            handler.progress.connect(self.logger.info)
            errors = handler.run_ffmpeg(command_str)
            self.finished.emit(not errors)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            self.finished.emit(False)


class Renderer(QObject):

    # emit true on success, false on failure
    finished = Signal(bool)

    def __init__(self):
        self.success = True
        self.threads = []
        super().__init__()

    def worker_finished(self, worker, thread, success):
        thread.quit()
        worker.deleteLater()
        self.success = self.success and success
        logging.info("{} finished, success: {}".format(str(worker), success))

    def thread_finished(self, thread):
        thread.deleteLater()
        self.threads.remove(thread)
        if len(self.threads) == 0:
            self.finished.emit(self.success)

    def render_album(self, album: AlbumTreeWidgetItem, logger):
        if album.childCount() == 0:
            return
        if album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.SINGLE:
            pass
        elif album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.render_song(song, logger)

    def render_song(self, song: SongTreeWidgetItem, logger):
        thread = QThread()
        self.threads.append(thread)
        worker = RenderSongWorker(song, logger)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda success, worker=worker, thread=thread: self.worker_finished(worker, thread, success))
        thread.finished.connect(lambda thread=thread: self.thread_finished(thread))
        thread.start()
