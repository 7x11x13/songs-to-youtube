from PySide6.QtCore import QPersistentModelIndex
from PySide6.QtWidgets import *

from songs_to_youtube.const import *
from songs_to_youtube.field import *
from songs_to_youtube.settings import *
from songs_to_youtube.song_tree_widget_item import *
from songs_to_youtube.utils import *

logger = logging.getLogger(APPLICATION)


class SongSettingsWidget(QWidget):
    SONG_ONLY_WIDGETS = ((QGroupBox, "ffmpegSettings"), (QGroupBox, "youtubeSettings"))
    ALBUM_ONLY_WIDGETS = (
        (QComboBox, "albumPlaylist"),
        (QLabel, "albumPlaylistLabel"),
        (QGroupBox, "ffmpegSettingsAlbum"),
        (QGroupBox, "youtubeSettingsAlbum"),
    )

    def __init__(self, *args):
        # which items are currently selected by the song tree widget
        self.tree_indexes = set()

        # which fields have been updated since we loaded data
        # this gets reset when we save the field data
        # and every time we load new data
        self.fields_updated = set()

        # values of each field when the window is loaded
        self.field_original_values = {}

        self.item_type = TreeWidgetType.ALBUM

        super().__init__(*args)
        load_ui(
            "songsettingswindow.ui",
            (SettingCheckBox, CoverArtDisplay, SettingsScrollArea, FileComboBox),
            self,
        )
        SettingsWindow.init_combo_boxes(self)
        self.setVisible(False)
        self.connect_actions()

    def resizeEvent(self, event):
        # resize UI when widget is resized
        self.findChild(QWidget, "songSettingsWindow").resize(event.size())

    def connect_actions(self):
        cover_art_button = self.findChild(QPushButton, "coverArtButton")
        cover_art_button.clicked.connect(self.change_cover_art)
        button_box = self.findChild(QDialogButtonBox)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.load_settings)
        for field in get_all_fields(self):
            field.on_update(
                lambda text, field_name=field.name: self.on_field_updated(
                    field_name, text
                )
            )
            if field.name == "albumPlaylist":
                # disable album settings whenever album mode is set to multiple values
                field.on_update(
                    lambda data: self.set_album_enabled(
                        data != SETTINGS_VALUES.AlbumPlaylist.MULTIPLE
                    )
                )
            elif field.name == "uploadYouTube":
                # disable youtube settings whenever 'upload to youtube' is unchecked
                field.on_update(
                    lambda text: self.set_youtube_enabled(
                        text != SETTINGS_VALUES.CheckBox.UNCHECKED
                    )
                )

    def change_cover_art(self):
        dir_setting = (
            "song_dir" if self.item_type == TreeWidgetType.SONG else "album_dir"
        )
        for e in self.tree_indexes:
            dir = e.data(CustomDataRole.ITEMDATA).get_value(dir_setting)
            break
        file = QFileDialog.getOpenFileName(
            self, "Import album artwork", dir, SUPPORTED_IMAGE_FILTER
        )[0]
        self.findChild(CoverArtDisplay).set(file)

    def set_youtube_enabled(self, enabled):
        if self.item_type == TreeWidgetType.SONG:
            self.findChild(QGroupBox, "youtubeSettings").setEnabled(enabled)
        else:
            # if album settings are disabled, we can't enable youtube settings
            enabled = (
                enabled and self.findChild(QGroupBox, "ffmpegSettingsAlbum").isEnabled()
            )
            self.findChild(QGroupBox, "youtubeSettingsAlbum").setEnabled(enabled)

    def set_button_box_enabled(self, enabled):
        self.findChild(QDialogButtonBox).setEnabled(enabled)

    def set_album_enabled(self, enabled):
        self.findChild(QGroupBox, "ffmpegSettingsAlbum").setEnabled(enabled)
        self.findChild(SettingCheckBox, "uploadYouTube").setEnabled(enabled)
        # if youtube settings are disabled, we can't enable them
        enabled = enabled and (
            get_field(self, "uploadYouTube").get() != SETTINGS_VALUES.CheckBox.UNCHECKED
        )
        self.findChild(QGroupBox, "youtubeSettingsAlbum").setEnabled(enabled)

    def on_field_updated(self, field, current_value):
        if field not in self.field_original_values:
            # just loaded field, set original value to loaded value
            self.field_original_values[field] = current_value
            return

        original_value = self.field_original_values[field]
        if original_value == current_value:
            self.fields_updated.discard(field)
        else:
            self.fields_updated.add(field)

        if len(self.fields_updated) == 0:
            self.set_button_box_enabled(False)
        else:
            self.set_button_box_enabled(True)

    def save_settings(self):
        self.fields_updated = set()
        self.field_original_values = {}
        self.set_button_box_enabled(False)
        for data in {i.data(CustomDataRole.ITEMDATA) for i in self.tree_indexes}:
            for field in get_all_visible_fields(self):
                value = field.get()
                if value != SETTINGS_VALUES.MULTIPLE_VALUES:
                    try:
                        data.set_value(field.name, value)
                    except:
                        logger.error(
                            f"Error while setting {field.name} with value {value}"
                        )
                self.field_original_values[field.name] = value
        self.load_settings()

    def load_settings(self):
        # update UI to show/hide appropriate elements
        # based on the type of items we are editing
        for widget in self.SONG_ONLY_WIDGETS:
            self.findChild(*widget).setVisible(self.item_type == TreeWidgetType.SONG)
        for widget in self.ALBUM_ONLY_WIDGETS:
            self.findChild(*widget).setVisible(self.item_type == TreeWidgetType.ALBUM)

        if self.item_type == TreeWidgetType.SONG:
            self.findChild(SettingCheckBox, "uploadYouTube").setEnabled(True)

        self.fields_updated = set()
        self.field_original_values = {}
        self.set_button_box_enabled(False)
        items = [i.data(CustomDataRole.ITEMDATA).to_dict() for i in self.tree_indexes]
        # set settings based on selected items
        for field in get_all_visible_fields(self):
            values = {dict(i)[field.name] for i in items if field.name in i}
            if len(values) == 0:
                continue
            has_multiple_values = len(values) > 1
            value = (
                values.pop()
                if not has_multiple_values
                else SETTINGS_VALUES.MULTIPLE_VALUES
            )
            if field.name == "albumPlaylist":
                # show album settings when at least one single video album is selected
                self.set_album_enabled(value != SETTINGS_VALUES.AlbumPlaylist.MULTIPLE)
            elif field.name == "uploadYouTube":
                # show youtube settings when at least one song is to be uploaded is unchecked
                self.set_youtube_enabled(value != SETTINGS_VALUES.CheckBox.UNCHECKED)
            if field.class_name == "QComboBox" or field.class_name == "FileComboBox":
                if field.class_name == "FileComboBox":
                    field.widget.reload()
                # add <<Multiple values>> to combobox as necessary
                multiple_values_index = field.widget.findData(
                    SETTINGS_VALUES.MULTIPLE_VALUES
                )
                if not has_multiple_values and multiple_values_index != -1:
                    field.set(value)
                    field.widget.removeItem(multiple_values_index)
                elif has_multiple_values and multiple_values_index == -1:
                    field.widget.addItem(
                        SETTINGS_VALUES.MULTIPLE_VALUES, SETTINGS_VALUES.MULTIPLE_VALUES
                    )
                    field.set(value)
                else:
                    field.set(value)
            else:
                field.set(value)
            self.field_original_values[field.name] = value

    def song_tree_selection_changed(self, selected, deselected):
        selected = [QPersistentModelIndex(i) for i in selected.indexes()]
        deselected = [QPersistentModelIndex(i) for i in deselected.indexes()]
        self.tree_indexes |= set(selected)  # add new selected indexes
        self.tree_indexes -= set(deselected)  # remove deselected indexes
        self.setVisible(
            len(self.tree_indexes) > 0
        )  # hide window if nothing is selected
        if len(self.tree_indexes) > 0:
            for index in self.tree_indexes:
                # all indexes will have the same item type
                # guaranteed by our selection model
                self.item_type = index.data(CustomDataRole.ITEMTYPE)
                break
            self.load_settings()
