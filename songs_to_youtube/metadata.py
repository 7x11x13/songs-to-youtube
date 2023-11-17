import logging
import posixpath

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from PySide6.QtCore import *

from songs_to_youtube.const import *
from songs_to_youtube.utils import *

# can expand these if wanted
EasyMP4.RegisterTextKey("url", "purl")

logger = logging.getLogger(APPLICATION)


class Metadata:
    def __init__(self, song_path):
        self.pictures = []
        self.path = song_path
        self.tags = {}
        try:
            self.load_song(song_path)
        except Exception as err:
            logger.error(
                f"Could not load metadata for {song_path}: {err.__class__}: {err}"
            )

    def load_song(self, path):
        f = mutagen.File(path, easy=True)
        if f.info:
            for key, value in vars(f.info).items():
                self.tags[key] = make_value_qt_safe(value)
        if f.tags:
            logger.debug(f"Tags: {f.keys()}")
            for key, value in f.tags.items():
                self.tags[key] = make_value_qt_safe(value)

            if isinstance(f.tags, mutagen.easyid3.EasyID3) or isinstance(
                f.tags, mutagen.id3.ID3
            ):
                if isinstance(f.tags, mutagen.easyid3.EasyID3):
                    f = mutagen.File(path)
                for key in f:
                    if key.startswith("COM"):
                        # load comment data here since comment frame keys have
                        # language suffix we can't just register text key COMM
                        self.tags["comment"] = make_value_qt_safe(f[key])
                    if key.startswith("APIC") or key.startswith("PIC"):
                        # get cover art
                        self.pictures.append(f[key].data)
                if isinstance(f.tags, mutagen.id3.ID3):
                    for key, getter in EasyID3.Get.items():
                        try:
                            value = getter(f.tags, key)
                            self.tags[key] = make_value_qt_safe(value)
                        except:
                            pass
            elif isinstance(f.tags, mutagen.easymp4.EasyMP4Tags):
                f = mutagen.File(path)
                if "covr" in f:
                    for art in f["covr"]:
                        self.pictures.append(bytes(art))
            elif isinstance(f, mutagen.flac.FLAC):
                for picture in f.pictures:
                    self.pictures.append(picture.data)

    def get_cover_art(self):
        # extract cover art if it exists
        if len(self.pictures) > 0:
            bytes = QByteArray(self.pictures[0])
            cover = QTemporaryFile(
                posixpath.join(QDir().tempPath(), APPLICATION, "XXXXXX.cover")
            )
            cover.setAutoRemove(False)
            cover.open(QIODevice.WriteOnly)
            cover.write(bytes)
            cover.close()
            return cover.fileName()
        return None

    def get_tags(self):
        return self.tags
