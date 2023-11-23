import glob
import json
import logging
import time
import traceback
from http.cookiejar import Cookie, FileCookieJar, MozillaCookieJar
from typing import List, Tuple

from PySide6.QtCore import *
from youtube_up import Metadata as YTMetadata
from youtube_up import Playlist as YTPlaylist
from youtube_up import YTUploaderSession

from songs_to_youtube.const import *
from songs_to_youtube.field import SETTINGS_VALUES
from songs_to_youtube.settings import get_setting
from songs_to_youtube.song_tree_widget_item import *

logger = logging.getLogger(APPLICATION)


def make_metadata_safe(metadata: YTMetadata):
    metadata.title = metadata.title[:100]
    metadata.description = metadata.description[:5000]
    metadata.title = metadata.title.replace("<", "＜").replace(">", "＞")
    metadata.description = metadata.description.replace("<", "＜").replace(">", "＞")
    return metadata


class JSONFileCookieJar(FileCookieJar):
    def _really_load(self, f, filename, ignore_discard, ignore_expires):
        now = time.time()
        cookies = json.load(f)
        for cookie in cookies:
            rest = {}
            if cookie.get("httpOnly"):
                rest["HTTPOnly"] = ""
            c = Cookie(
                0,
                cookie["name"],
                cookie["value"],
                None,
                False,
                cookie["domain"],
                True,
                cookie["domain"].startswith("."),
                cookie["path"],
                True,
                cookie["secure"],
                cookie["expires"] or None,
                False,
                None,
                None,
                rest,
            )
            if not ignore_discard and c.discard:
                continue
            if not ignore_expires and c.is_expired(now):
                continue
            self.set_cookie(c)

    def save(self, filename=None, ignore_discard=False, ignore_expires=False):
        now = time.time()
        cookies = []
        for cookie in self:
            domain = cookie.domain
            if not ignore_discard and cookie.discard:
                continue
            if not ignore_expires and cookie.is_expired(now):
                continue
            if cookie.secure:
                secure = "TRUE"
            else:
                secure = "FALSE"
            if domain.startswith("."):
                initial_dot = "TRUE"
            else:
                initial_dot = "FALSE"
            if cookie.expires is not None:
                expires = str(cookie.expires)
            else:
                expires = ""
            if cookie.value is None:
                name = ""
                value = cookie.name
            else:
                name = cookie.name
                value = cookie.value
            httpOnly = False
            if cookie.has_nonstandard_attr("HTTPOnly"):
                httpOnly = True
            cookies.append(
                {
                    "name": name,
                    "value": value,
                    "domain": domain,
                    "path": cookie.path,
                    "expires": expires,
                    "httpOnly": httpOnly,
                    "secure": secure,
                }
            )

        if filename is None:
            if self.filename is not None:
                filename = self.filename

        with open(filename, "w") as f:
            json.dump(cookies, f)


def get_cookie_jar_for_username(username: str) -> FileCookieJar:
    cookie_dir = YouTubeLogin.get_cookie_path_from_username(username)
    txt_cookie_paths = glob.glob(posixpath.join(cookie_dir, "*.txt"))
    json_cookie_paths = glob.glob(posixpath.join(cookie_dir, "*.json"))
    if txt_cookie_paths:
        return MozillaCookieJar(txt_cookie_paths[0])
    elif json_cookie_paths:
        return JSONFileCookieJar(json_cookie_paths[0])
    else:
        raise FileNotFoundError(
            f"No cookie files matching *.txt or *.json found in {cookie_dir}"
        )


class UploadWorker(QObject):
    upload_finished = Signal(str, bool)  # file_path, success
    log_message = Signal(str, int)  # message, loglevel
    on_progress = Signal(str, int)  # job name, percent done
    finished = Signal()

    def __init__(self, username, jobs):
        super().__init__()
        self.jobs = jobs
        self.username = username

    def run(self):
        try:
            cj = get_cookie_jar_for_username(self.username)
            self.uploader = YTUploaderSession(cj)
            for file, metadata in self.jobs:

                def callback(step, progress):
                    self.on_progress.emit(file, progress)
                    # self.log_message.emit(step, logging.DEBUG)

                try:
                    self.uploader.upload(file, metadata, callback)
                    self.upload_finished.emit(file, True)
                except Exception:
                    self.log_message.emit(traceback.format_exc(), logging.ERROR)
                    self.upload_finished.emit(file, False)

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
        self.jobs: List[Tuple[str, YTMetadata]] = []  # file path and metadata
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
        for file, _ in self.jobs:
            if file not in self.results:
                self.results[file] = False
        self.finished.emit(self.results)

    def add_upload_album_job(self, album: AlbumTreeWidgetItem):
        if album.childCount() == 0:
            return
        if album.get("albumPlaylist") == SETTINGS_VALUES.AlbumPlaylist.SINGLE:
            if album.get("uploadYouTube") == SETTINGS_VALUES.CheckBox.CHECKED:
                file = album.get("fileOutput")
                if file in self.render_results and self.render_results[file]:
                    album.before_upload()
                    privacy = album.get("videoVisibilityAlbum")
                    notify_subs = (
                        album.get("notifySubsAlbum") == SETTINGS_VALUES.CheckBox.CHECKED
                    )
                    tags = (
                        album.get("videoTagsAlbum").split(",")
                        if album.get("videoTagsAlbum")
                        else []
                    )
                    metadata = make_metadata_safe(
                        YTMetadata(
                            album.get("videoTitleAlbum"),
                            album.get("videoDescriptionAlbum"),
                            privacy,
                            False,
                            tags,
                            publish_to_feed=notify_subs,
                        )
                    )
                    self.jobs.append((file, metadata))
        elif album.get("albumPlaylist") == SETTINGS_VALUES.AlbumPlaylist.MULTIPLE:
            for song in album.getChildren():
                self.add_upload_song_job(song)

    def add_upload_song_job(self, song: SongTreeWidgetItem):
        if song.get("uploadYouTube") == SETTINGS_VALUES.CheckBox.CHECKED:
            file = song.get("fileOutput")
            if file in self.render_results and self.render_results[file]:
                song.before_upload()
                privacy = song.get("videoVisibility")
                notify_subs = song.get("notifySubs") == SETTINGS_VALUES.CheckBox.CHECKED
                tags = song.get("videoTags").split(",") if song.get("videoTags") else []
                playlist_names = song.get("playlistName").split("\n")
                playlists = [
                    YTPlaylist(
                        name,
                        privacy=privacy,
                        create_if_title_exists=False,
                        create_if_title_doesnt_exist=True,
                    )
                    for name in playlist_names
                ]
                metadata = make_metadata_safe(
                    YTMetadata(
                        song.get("videoTitle"),
                        song.get("videoDescription"),
                        privacy,
                        False,
                        tags,
                        playlists=playlists,
                        publish_to_feed=notify_subs,
                    )
                )
                if any(job_file == file for job_file, _ in self.jobs):
                    logger.error(f"Ignoring duplicate job {file}")
                else:
                    self.jobs.append((file, metadata))

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
        self.results = {file: False for file, _ in self.jobs}
        if len(self.jobs) == 0:
            self.finished.emit(self.results)
            return
        self.thread = QThread()
        username = get_setting("username")
        if not username:
            raise ValueError(
                "No user selected to upload to. Add a user at File > Settings > Add new user"
            )
        self.worker = UploadWorker(username, self.jobs)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda: self.worker_finished())
        self.thread.finished.connect(lambda: self.thread.deleteLater())
        self.worker.log_message.connect(self.log)
        self.worker.on_progress.connect(
            lambda worker_name, progress: self.worker_progress.emit(
                worker_name, progress
            )
        )
        self.worker.upload_finished.connect(self.upload_finished)
        self.thread.start()
