# This Python file uses the following encoding: utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout, QSizePolicy

import logging

from render import Renderer
from utils import find_ancestor


class WorkerProgress(QWidget):
    def __init__(self, worker_name, *args):
        super().__init__(*args)
        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        self.label = QLabel(self)
        self.label.setText(worker_name.replace("\\", "/").split("/")[-1] + ":")
        self.progress = QProgressBar(self)
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.progress)
        self.progress.setMaximum(100000)

    def set_progress(self, us):
        ms = us // 1000
        ms = min(ms, self.progress.maximum())
        if 0 < ms < 0xffffffff:
            self.progress.setValue(ms)


class ProgressWindow(QWidget):
    def __init__(self, *args):

        self.workers = {}

        super().__init__(*args)

        self.setLayout(QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)
        find_ancestor(self, "QScrollArea").setVisible(False)

    def init_worker_progress(self, worker_name):
        progress = WorkerProgress(worker_name, self)
        self.workers[worker_name] = progress
        self.layout().addWidget(progress)

    def worker_progress(self, worker_name, progress):
        if worker_name not in self.workers:
            self.init_worker_progress(worker_name)
        key, value = progress.strip().split("=")
        if key == "out_time_us":
            worker = self.workers[worker_name]
            worker.set_progress(int(value))
            logging.debug("{} - {}".format(worker_name, progress))

    def worker_error(self, worker_name, error):
        if worker_name not in self.workers:
            self.init_worker_progress(worker_name)
        logging.error("{} - {}".format(worker_name, error))

    def worker_done(self, worker_name):
        logging.info("{} - Done".format(worker_name))
        worker = self.workers.pop(worker_name, None)
        if worker:
            worker.setVisible(False)
            self.layout().removeWidget(worker)

    def on_render_start(self, renderer: Renderer):
        find_ancestor(self, "QScrollArea").setVisible(True)
        renderer.worker_progress.connect(self.worker_progress)
        renderer.worker_error.connect(self.worker_error)
        renderer.worker_done.connect(self.worker_done)
        renderer.finished.connect(lambda success: find_ancestor(self, "QScrollArea").setVisible(False))
