import atexit
import logging
import os
import subprocess
import time
import traceback
from queue import Queue
from threading import Thread

import psutil
from PySide6.QtCore import *

from songs_to_youtube.const import *
from songs_to_youtube.field import SETTINGS_VALUES
from songs_to_youtube.song_tree_widget_item import *

logger = logging.getLogger(APPLICATION)

PROCESSES = []


# make sure to stop all the ffmpeg processes from running
# if we close the application
def clean_up():
    for p in PROCESSES:
        try:
            process = psutil.Process(p.pid)
            for proc in process.children(recursive=True):
                proc.kill()
            process.kill()
        except:
            pass


atexit.register(clean_up)


class ProcessHandler(QObject):
    stdout = Signal(str)
    stderr = Signal(str)

    def __init__(self):
        super().__init__()

    def read_pipe(self, pipe, queue):
        try:
            with pipe:
                for line in iter(pipe.readline, b""):
                    queue.put((pipe, line.decode("utf-8")))
        finally:
            queue.put((None, None))

    def run(self, command):
        if os.name == "nt":
            p = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                shell=True,
            )
        else:
            p = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
            )

        PROCESSES.append(p)
        q = Queue()
        Thread(target=self.read_pipe, args=[p.stdout, q]).start()
        Thread(target=self.read_pipe, args=[p.stderr, q]).start()
        while True:
            while q.empty() or (item := q.get_nowait()) is None:
                time.sleep(0.01)
            pipe, line = item
            if pipe is None:
                break
            if pipe == p.stdout:
                self.stdout.emit(line)
            else:
                self.stderr.emit(line)
        error = p.wait() != 0
        PROCESSES.remove(p)
        return error


class WorkerSignals(QObject):
    finished = Signal(bool)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self):
        super().__init__()


class RenderSongWorker(QRunnable):
    def __init__(self, song: SongTreeWidgetItem, auto_delete):
        super().__init__()
        self.auto_delete = auto_delete
        self.song = song
        self.name = self.song.get("fileOutput")
        self.signals = WorkerSignals()
        self.setAutoDelete(False)

    def run(self):
        try:
            command_str = (self.song.get("commandString")).format(**self.song.to_dict())
            handler = ProcessHandler()
            handler.stderr.connect(self.signals.error.emit)
            handler.stdout.connect(self.signals.progress.emit)
            errors = handler.run(command_str)
            self.signals.finished.emit(not errors)
        except Exception as e:
            self.signals.error.emit(traceback.format_exc())
            self.signals.finished.emit(False)

    def get_duration_ms(self):
        return self.song.get_duration_ms()

    def __str__(self):
        return self.name


class CombineSongWorker(QRunnable):
    def __init__(self, album: AlbumTreeWidgetItem):
        super().__init__()
        self.auto_delete = True
        self.album = album
        self.name = self.album.get("fileOutput")
        self.signals = WorkerSignals()
        self.setAutoDelete(False)

    def run(self):
        try:
            song_list = QTemporaryFile()
            song_list.open(QIODevice.WriteOnly | QIODevice.Append | QIODevice.Text)
            for song in self.album.getChildren():
                song_list.write(
                    QByteArray(
                        "file 'file:{}'\n".format(
                            song.get("fileOutput").replace("'", "'\\''")
                        )
                    )
                )
            song_list.close()
            command_str = self.album.get("concatCommandString").format(
                input_file_list=song_list.fileName(),
                fileOutputPath=self.album.get("fileOutput"),
            )
            handler = ProcessHandler()
            handler.stderr.connect(self.signals.error.emit)
            handler.stdout.connect(self.signals.progress.emit)
            errors = handler.run(command_str)
            for song in self.album.getChildren():
                try:
                    os.remove(song.get("fileOutput"))
                except:
                    pass
            self.signals.finished.emit(not errors)
        except Exception as e:
            self.signals.error.emit(traceback.format_exc())
            self.signals.finished.emit(False)

    def get_duration_ms(self):
        return self.album.get_duration_ms()

    def __str__(self):
        return self.name


class AlbumRenderHelper:
    def __init__(self, album: AlbumTreeWidgetItem, *args):
        self.album = album
        self.workers = set()
        self.renderer = None
        self.combine_worker = ""
        self.error = False

    def worker_done(self, worker, success):
        if worker in self.workers:
            self.workers.discard(worker)
            if not success:
                self.error = True
                self.renderer.cancel_worker(self.combine_worker)
        if len(self.workers) == 0 and not self.error:
            # done rendering songs,
            # begin concatenation
            self.renderer.start_worker(self.combine_worker)

    def render(self, renderer):
        renderer.worker_done.connect(self.worker_done)
        for song in self.album.getChildren():
            song.before_render()
            worker = renderer.add_render_song_job(song, auto_delete=False)
            self.workers.add(worker)
        self.combine_worker = renderer.combine_songs_into_album(self.album)
        self.renderer = renderer
        return self


class Renderer(QObject):
    # emit true on success, false on failure
    finished = Signal(dict)

    # worker name, worker progress (percentage)
    worker_progress = Signal(str, int)

    # worker name, worker error
    worker_error = Signal(str, str)

    # worker name
    worker_done = Signal(str, bool)

    def __init__(self):
        super().__init__()

        QThreadPool.globalInstance().setMaxThreadCount(int(get_setting("maxProcesses")))

        # array of album helpers so they
        # don't get garbage collected
        self.helpers = []

        # worker name -> QRunnable
        self.workers = {}

        # worker name -> QRunnable
        # workers which are not in the thread pool yet
        self.queued_workers = {}

        # finished workers that still need to be held onto
        # so that resources don't go out of scope
        self.finished_workers = []

        # output file -> success
        self.results = {}

        self.cancelled = False

    def _worker_progress(self, worker, progress):
        try:
            key, value = progress.strip().split("=")
            if key == "out_time_us":
                current_time_ms = int(value) // 1000
                total_time_ms = worker.get_duration_ms()
                progress = max(
                    0, min(int((current_time_ms / total_time_ms) * 100), 100)
                )
                self.worker_progress.emit(str(worker), progress)
        except:
            logger.warning("Could not parse worker_progress line: {}".format(progress))

    def worker_finished(self, worker, success):
        self.results[str(worker)] = success
        self.workers.pop(str(worker), None)
        if not self.cancelled:
            if not worker.auto_delete:
                self.finished_workers.append(worker)
            self.worker_done.emit(str(worker), success)
            logger.debug("{} finished, success: {}".format(str(worker), success))
            if len(self.workers) == 0:
                if len(self.queued_workers) == 0:
                    # finished all jobs, send results
                    self.finished.emit(self.results)
                else:
                    # still have combine jobs, move them to thread pool
                    for worker_name, worker in self.queued_workers.items():
                        self.add_worker(worker)
                    self.queued_workers = {}

    def start_worker(self, worker_name):
        # manually start a worker that wasn't created
        # with auto_start=True
        if worker_name in self.queued_workers:
            worker = self.queued_workers.pop(worker_name)
            self.workers[worker_name] = worker
            QThreadPool.globalInstance().start(worker)

    def cancel_worker(self, worker_name):
        # cancel a worker which is not in the thread pool yet
        self.queued_workers.pop(worker_name, None)

    def add_worker(self, worker, auto_start=True):
        worker.signals.finished.connect(
            lambda success, worker=worker: self.worker_finished(worker, success)
        )
        worker.signals.error.connect(
            lambda error, worker=worker: self.worker_error.emit(str(worker), error)
        )
        worker.signals.progress.connect(
            lambda progress, worker=worker: self._worker_progress(worker, progress)
        )
        if auto_start:
            self.workers[str(worker)] = worker
            QThreadPool.globalInstance().start(worker)
        else:
            self.queued_workers[str(worker)] = worker

        return worker

    def add_render_album_job(self, album: AlbumTreeWidgetItem):
        album.before_render()
        if album.childCount() == 0:
            return
        if album.get("albumPlaylist") == SETTINGS_VALUES.AlbumPlaylist.SINGLE:
            self.helpers.append(AlbumRenderHelper(album).render(self))
        elif album.get("albumPlaylist") == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.add_render_song_job(song)

    def add_render_song_job(self, song: SongTreeWidgetItem, auto_delete=True):
        song.before_render()
        worker = RenderSongWorker(song, auto_delete)
        self.add_worker(worker)
        return str(worker)

    def combine_songs_into_album(self, album: AlbumTreeWidgetItem):
        worker = CombineSongWorker(album)
        self.add_worker(worker, False)
        return str(worker)

    def render(self):
        if len(self.workers) == 0 and len(self.finished_workers) == 0:
            self.finished.emit(self.results)

    def cancel(self):
        clean_up()
        self.cancelled = True
        for worker in self.workers:
            if str(worker) not in self.results:
                self.results[str(worker)] = False
        self.finished_workers = []
        self.finished.emit(self.results)
