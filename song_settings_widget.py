# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QCheckBox, QDialogButtonBox, QGroupBox

from song_tree_widget import CustomDataRole
from settings import SETTINGS_VALUES
from utils import load_ui, get_all_fields


class SettingCheckBox(QCheckBox):
    def __init__(self, *args):
        super().__init__(*args)
        self.setTristate()

    def nextCheckState(self):
        # don't let user select inbetween state
        if self.checkState() == Qt.PartiallyChecked:
            self.setCheckState(Qt.Checked)
        else:
            self.setChecked(not self.isChecked())
        self.stateChanged.emit(self.checkState())


class SongSettingsWidget(QWidget):
    def __init__(self, *args):
        # which items are currently selected by the song tree widget
        self.tree_indexes = set()

        # which fields have been updated since we loaded data
        # this gets reset when we save the field data
        # and every time we load new data
        self.fields_updated = set()

        # values of each field when the window is loaded
        self.field_original_values = {}

        super().__init__(*args)
        load_ui("songsettingswindow.ui", [SettingCheckBox], self)
        self.setVisible(False)
        self.connect_actions()

    def resizeEvent(self, event):
        # resize UI when widget is resized
        self.findChild(QWidget, "songSettingsWindow").resize(event.size())

    def connect_actions(self):
        button_box = self.findChild(QDialogButtonBox)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.load_settings)
        for field in get_all_fields(self):
            field.on_update(lambda text, field_name=field.name: self.on_field_updated(field_name, text))
            if field.name == "uploadYouTube":
                # disable youtube settings whenever 'upload to youtube' is unchecked
                field.on_update(lambda text: self.set_youtube_enabled(text != SETTINGS_VALUES.CheckBox.UNCHECKED))

    def set_youtube_enabled(self, enabled):
        self.findChild(QGroupBox, "youtubeSettings").setEnabled(enabled)

    def set_button_box_enabled(self, enabled):
        self.findChild(QDialogButtonBox).setEnabled(enabled)

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
            for field in get_all_fields(self):
                value = field.get()
                if value != SETTINGS_VALUES.MULTIPLE_VALUES:
                    data.set_value(field.name, value)
                self.field_original_values[field.name] = value

    def load_settings(self):
        self.fields_updated = set()
        self.field_original_values = {}
        self.set_button_box_enabled(False)
        items = [i.data(CustomDataRole.ITEMDATA).to_dict() for i in self.tree_indexes]
        # set settings based on selected items
        for field in get_all_fields(self):
            values = {dict(i)[field.name] for i in items if field.name in i}
            if len(values) == 0:
                continue
            has_multiple_values = (len(values) > 1)
            value = values.pop() if not has_multiple_values else SETTINGS_VALUES.MULTIPLE_VALUES
            if field.class_name == "QComboBox":
                # add <<Multiple values>> to combobox as necessary
                multiple_values_index = field.widget.findText(SETTINGS_VALUES.MULTIPLE_VALUES)
                if not has_multiple_values and multiple_values_index != -1:
                    field.widget.removeItem(multiple_values_index)
                if has_multiple_values and multiple_values_index == -1:
                    field.widget.addItem(SETTINGS_VALUES.MULTIPLE_VALUES)
            field.set(value)
            self.field_original_values[field.name] = value

    def song_tree_selection_changed(self, selected, deselected):
        self.tree_indexes |= set(selected.indexes())   # add new selected indexes
        self.tree_indexes -= set(deselected.indexes()) # remove deselected indexes
        self.setVisible(len(self.tree_indexes) > 0) # hide window if nothing is selected
        self.load_settings()
