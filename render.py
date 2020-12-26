# This Python file uses the following encoding: utf-8

from PySide6.QtCore import QThread, Signal, QObject

import subprocess
import logging
import time
import traceback

from song_tree_widget_item import *
from const import QRC_TO_FILE_PATH

class RenderSongWorker(QObject):
    finished = Signal(bool)
    progress = Signal(int)

    def __init__(self, song: SongTreeWidgetItem):
        super().__init__()
        self.song = song

    def __str__(self):
        return "RenderSongWorker<{}>".format(self.song.get('file_path'))

    def run(self):
        try:
            cover_art = self.song.get('coverArt')
            if cover_art in QRC_TO_FILE_PATH:
                cover_art = QRC_TO_FILE_PATH[cover_art]
            command_str = ('ffmpeg -loglevel error -y -loop 1 -i "{cover_art}" -i "{audio_path}" '
            '-vf "pad=width={videoWidth}:height={videoHeight}:x=(out_w-in_w)/2:y=(out_h-in_h)/2:color=black" '
            '-c:a aac -ab {audioBitrate} -c:v libx264 -pix_fmt yuv420p -shortest -strict -2 "{out_path}"').format(
                cover_art = cover_art,
                audio_path = self.song.get('file_path'),
                audioBitrate = self.song.get('audioBitrate'),
                videoWidth = self.song.get('videoWidth'),
                videoHeight = self.song.get('videoHeight'),
                out_path = self.song.get('file_path') + '.mp4')
            logging.debug(command_str)

            # ffmpeg only outputs to stderr
            p = subprocess.Popen(command_str, stderr=subprocess.PIPE)
            errors = False
            while True:
                time.sleep(0.01)
                line = p.stderr.readline()
                if line.decode() == '' and p.poll() is not None:
                    break
                if line.decode() != '':
                    logging.error(line.decode())
                    errors = True
            self.finished.emit(not errors)
        except Exception as e:
            logging.error(traceback.format_exc())
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

    def render_album(self, album: AlbumTreeWidgetItem):
        if album.childCount() == 0:
            return
        if album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.SINGLE:
            pass
        elif album.get('albumPlaylist') == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.render_song(song)

    def render_song(self, song: SongTreeWidgetItem):
        thread = QThread()
        self.threads.append(thread)
        worker = RenderSongWorker(song)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(lambda success, worker=worker, thread=thread: self.worker_finished(worker, thread, success))
        thread.finished.connect(lambda thread=thread: self.thread_finished(thread))
        thread.start()
