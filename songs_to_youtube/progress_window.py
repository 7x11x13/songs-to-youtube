import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from songs_to_youtube.const import *
from songs_to_youtube.utils import *

logger = logging.getLogger(APPLICATION)


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
        self.progress.setValue(0)


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
        find_ancestor(self, "QScrollArea").setVisible(True)
        if worker_name not in self.workers:
            self.init_worker_progress(worker_name)
        worker = self.workers[worker_name]
        logger.debug(f"{worker_name} - {progress}% done")
        worker.progress.setValue(progress)

    def worker_error(self, worker_name, error):
        if worker_name not in self.workers:
            self.init_worker_progress(worker_name)
        logger.error("{} - {}".format(worker_name, error))

    def worker_done(self, worker_name, success, obj_type):
        if success:
            logger.success(f"{worker_name} - Done {obj_type}")
        else:
            logger.error(f"{worker_name} - Error while {obj_type}")
        worker = self.workers.pop(worker_name, None)
        if worker:
            worker.setVisible(False)
            self.layout().removeWidget(worker)

    def connect_workers(self, obj, obj_type):
        obj.worker_progress.connect(self.worker_progress)
        obj.worker_error.connect(self.worker_error)
        obj.worker_done.connect(
            lambda worker_name, success, obj_type=obj_type: self.worker_done(
                worker_name, success, obj_type
            )
        )
        obj.finished.connect(
            lambda success: find_ancestor(self, "QScrollArea").setVisible(False)
        )

    def on_render_start(self, renderer):
        self.connect_workers(renderer, "rendering")

    def on_upload_start(self, uploader):
        self.connect_workers(uploader, "uploading")
