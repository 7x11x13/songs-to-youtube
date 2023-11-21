import os

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from songs_to_youtube.field import SETTINGS_VALUES
from songs_to_youtube.metadata_table_widget import MetadataTableWidget
from songs_to_youtube.render import Renderer
from songs_to_youtube.settings import *
from songs_to_youtube.song_tree_widget_item import *
from songs_to_youtube.upload import Uploader
from songs_to_youtube.utils import *


class SongTreeModel(QStandardItemModel):
    def __init__(self, *args):
        super().__init__(*args)

    def dropMimeData(self, data, action, row, column, parent):
        # If album dropped onto another album, don't insert
        if parent.isValid():
            dummy_model = QStandardItemModel()
            dummy_model.dropMimeData(data, action, 0, 0, QModelIndex())
            indexes = []
            for r in range(dummy_model.rowCount()):
                for c in range(dummy_model.columnCount()):
                    index = dummy_model.index(r, c)
                    # QStandardItemModel doesn't recognize our items as our custom classes
                    # so we have to treat them as QStandardItems
                    item = dummy_model.item(r, c)
                    if item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                        pass
                    elif item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                        indexes.append(index)
            data = dummy_model.mimeData(indexes)
        ret = super().dropMimeData(data, action, row, column, parent)
        return ret


class SongTreeSelectionModel(QItemSelectionModel):
    def __init__(self, *args):
        super().__init__(*args)

    def _going_to_select_item(self, index, command):
        if command & QItemSelectionModel.Select:
            return True
        if command & QItemSelectionModel.Toggle and not self.isSelected(index):
            return True
        return False

    def select(self, selected, command):
        # If one of the selected items is an album,
        # deselect all song items to make sure
        # we only edit items of the same type
        # at the same time
        if isinstance(selected, QModelIndex):
            # turn single selected index into a QItemSelection
            # so we only have to deal with one type
            selected = QItemSelection(selected, selected)

        # check if after this selection action
        # we would have an album selected
        # this will emit selectionChanged
        super().select(selected, command)
        album_selected = False
        for index in self.selection().indexes():
            if index.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                album_selected = True
                break

        if album_selected:
            deselect = None
            if album_selected:
                # deselect all song items
                for index in self.selection().indexes():
                    if index.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                        if deselect:
                            deselect.append(QItemSelection(index, index))
                        else:
                            deselect = QItemSelection(index, index)
            if deselect:
                super().select(deselect, QItemSelectionModel.Deselect)


class SongTreeWidget(QTreeView):
    def __init__(self, *args):
        super().__init__(*args)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.setModel(SongTreeModel())
        self.setSelectionModel(SongTreeSelectionModel(self.model()))
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        self.init_shortcuts()

    def init_shortcuts(self):
        self.del_shortcut = QShortcut(QKeySequence(QKeySequence.Delete), self)
        self.del_shortcut.activated.connect(self.remove_selected_items)

    def _create_album_item(self, dir_path, songs):
        return AlbumTreeWidgetItem(dir_path, songs)

    def _create_song_item(self, file_path):
        return SongTreeWidgetItem(file_path)

    def _get_all_items(self):
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                item = AlbumTreeWidgetItem.from_standard_item(item)
                yield item
            elif item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                item = SongTreeWidgetItem.from_standard_item(item)
                yield item

    def _get_all_items_flat(self):
        for item in self._get_all_items():
            yield item
            if item.item_type() == TreeWidgetType.ALBUM:
                yield from item.getChildren()

    def remove_by_file_paths(self, paths, uploaded=True):
        """Remove items from widget with output paths given by paths;
        if uploaded is False, only remove items which are not going
        to be uploaded (render-only)"""
        for item in list(self._get_all_items_flat())[::-1]:
            if item.get("fileOutput") in paths:
                if (
                    uploaded
                    or item.get("uploadYouTube") == SETTINGS_VALUES.CheckBox.UNCHECKED
                ):
                    self.model().removeRow(item.row(), item.index().parent())

        # if all children of an album are removed,
        # remove the album as well
        for item in list(self._get_all_items())[::-1]:
            if item.item_type() == TreeWidgetType.ALBUM:
                if item.childCount() == 0:
                    self.model().removeRow(item.row(), item.index().parent())

    def remove_all(self):
        if self.model().hasChildren():
            self.model().removeRows(0, self.model().rowCount())

    def addTopLevelItem(self, item):
        self.model().appendRow(item)

    def remove_selected_items(self):
        while len(self.selectedIndexes()) > 0:
            index = self.selectedIndexes()[0]
            index.model().removeRow(index.row(), index.parent())

    def show_metadata_menu(self, index):
        self.metadata_dialog = load_ui("metadata.ui", (MetadataTableWidget,))
        self.metadata_dialog.tableWidget.from_data(index.data(CustomDataRole.ITEMDATA))
        self.metadata_dialog.show()

    def on_context_menu(self, pos: QPoint):
        index = self.indexAt(pos)
        menu = QMenu(self)

        meta_action = menu.addAction("View metadata")
        meta_action.triggered.connect(
            lambda chk=False, index=index: self.show_metadata_menu(index)
        )

        remove_action = menu.addAction("Remove")
        remove_action.setShortcut(QKeySequence(QKeySequence.Delete))
        remove_action.triggered.connect(self.remove_selected_items)

        menu.popup(self.viewport().mapToGlobal(pos))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.source() is self:
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.source() is self:
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.source():
            super().dropEvent(event)
        else:
            for url in event.mimeData().urls():
                info = QFileInfo(url.toLocalFile())
                if not info.isReadable():
                    logger.warning("File {} is not readable".format(info.filePath()))
                    continue
                if info.isDir():
                    if (
                        get_setting("dragAndDropBehavior")
                        == SETTINGS_VALUES.DragAndDrop.ALBUM_MODE
                    ):
                        self.addAlbum(url.toLocalFile())
                    else:
                        for file_path in files_in_directory_and_subdirectories(
                            info.filePath()
                        ):
                            self.addSong(file_path)
                else:
                    self.addSong(info.filePath())

    def addAlbum(self, dir_path: str):
        songs = []
        for file_path in files_in_directory(dir_path):
            if os.name == "nt" and len(file_path) > 255:
                file_path = get_short_path_name(file_path)
            info = QFileInfo(file_path)
            if not info.isReadable():
                logger.warning("File {} is not readable".format(file_path))
                continue
            if info.isDir():
                self.addAlbum(file_path)
            elif file_is_audio(file_path):
                item = self._create_song_item(file_path)
                item.setText(info.fileName())
                songs.append(item)
        if len(songs) > 0:
            album_item = self._create_album_item(dir_path, songs)
            album_item.setText(dir_path)
            self.addTopLevelItem(album_item)

    def addSong(self, path: str):
        if os.name == "nt" and len(path) > 255:
            path = get_short_path_name(path)
        if not file_is_audio(path):
            logger.info("File {} is not audio".format(path))
            return
        item = self._create_song_item(path)
        item.setText(QFileInfo(path).fileName())
        self.addTopLevelItem(item)

    def get_renderer(self):
        renderer = Renderer()
        for item in self._get_all_items():
            if item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                renderer.add_render_album_job(item)
            elif item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                renderer.add_render_song_job(item)
        return renderer

    def get_uploader(self, render_results):
        uploader = Uploader(render_results)
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.ALBUM:
                item = AlbumTreeWidgetItem.from_standard_item(item)
                uploader.add_upload_album_job(item)
            elif item.data(CustomDataRole.ITEMTYPE) == TreeWidgetType.SONG:
                item = SongTreeWidgetItem.from_standard_item(item)
                uploader.add_upload_song_job(item)
        return uploader
