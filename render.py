# This Python file uses the following encoding: utf-8

from PySide6.QtCore import QThread, Signal, QObject

import subprocess
import logging
import time
import traceback
import atexit
from threading import Thread
from queue import Queue

from song_tree_widget_item import *
from const import QRC_TO_FILE_PATH

PROCESSES = []

# make sure to stop all the ffmpeg processes from running
# if we close the application
def clean_up():
    for p in PROCESSES:
        p.kill()

atexit.register(clean_up)

class FFmpeg_Handler(QObject):

    progress = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()

    def read_pipe(self, pipe, queue):
        try:
            with pipe:
                for line in iter(pipe.readline, b''):
                    queue.put((pipe, line.decode('utf-8')))
        finally:
            queue.put((None, None))

    def run_ffmpeg(self, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        PROCESSES.append(p)
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
                self.error.emit(line)
        return errors

class RenderSongWorker(QObject):
    finished = Signal(bool)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, song: SongTreeWidgetItem):
        super().__init__()
        self.song = song

    def __str__(self):
        return "RenderSongWorker<{}>".format(self.song.get('file_path'))

    def run(self):
        try:
            command_str = ("ffmpeg -loglevel error -progress pipe:1 -y -loop 1 -i \"{coverArt}\" -i \"{file_path}\" "
            "-vf \"scale='min({videoWidth}, iw)':'min({videoHeight}, ih)':force_original_aspect_ratio=decrease,"
            "pad={videoWidth}:{videoHeight}:-1:-1:color=black\" "
            '-c:a aac -ab {audioBitrate} -c:v libx264 -pix_fmt yuv420p -shortest -strict -2 "{file_path}.mp4"').format(**self.song.to_dict())
            handler = FFmpeg_Handler()
            handler.error.connect(self.error.emit)
            handler.progress.connect(self.progress.emit)
            errors = handler.run_ffmpeg(command_str)
            self.finished.emit(not errors)
        except Exception as e:
            self.error.emit(traceback.format_exc())
            self.finished.emit(False)

    def __str__(self):
        return self.song.get('file_path') + '.mp4'


class Renderer(QObject):

    # emit true on success, false on failure
    finished = Signal(bool)

    # worker name, worker progress
    worker_progress = Signal(str, str)

    # worker name, worker error
    worker_error = Signal(str, str)

    # worker name
    worker_done = Signal(str)

    def __init__(self):
        self.success = True
        self.threads = []
        super().__init__()

    def worker_finished(self, worker, thread, success):
        self.worker_done.emit(str(worker))
        thread.quit()
        worker.deleteLater()
        self.success = self.success and success
        logging.debug("{} finished, success: {}".format(str(worker), success))

    def thread_finished(self, thread):
        thread.deleteLater()
        self.threads.remove(thread)
        if len(self.threads) == 0:
            self.finished.emit(self.success)
            self.deleteLater()
        # find first unstarted thread and start it
        for thread in self.threads:
            if not thread.isRunning():
                thread.start()
                break

    def add_render_album_job(self, album: AlbumTreeWidgetItem):
        if album.childCount() == 0:
            return
        if album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.SINGLE:
            pass
        elif album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.add_render_song_job(song)

    def add_render_song_job(self, song: SongTreeWidgetItem):
        thread = QThread()
        self.threads.append(thread)
        worker = RenderSongWorker(song)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda success, worker=worker, thread=thread: self.worker_finished(worker, thread, success))
        thread.finished.connect(lambda thread=thread: self.thread_finished(thread))
        worker.error.connect(lambda error, worker=worker: self.worker_error.emit(str(worker), error))
        worker.progress.connect(lambda progress, worker=worker: self.worker_progress.emit(str(worker), progress))

    def render(self):
        if len(self.threads) == 0:
            self.finished.emit(True)
        for i in range(min(int(get_setting("maxProcesses")), len(self.threads))):
            self.threads[i].start()
