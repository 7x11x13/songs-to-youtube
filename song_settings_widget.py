# This Python file uses the following encoding: utf-8
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QGroupBox, QCheckBox, QDialogButtonBox

from song_tree_widget import CustomDataRole, TreeWidgetItemData
from settings import WIDGET_FUNCTIONS
from utils import find_ancestor, get_all_children, load_ui


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


class SongSettingsWidget(QWidget):
    def __init__(self, *args):
        self.tree_indexes = set()
        super().__init__(*args)
        self.setVisible(False)
        load_ui("songsettingswindow.ui", [SettingCheckBox], self)
        self.connect_actions()

    def resizeEvent(self, event):
        # resize UI when widget is resized
        self.findChild(QWidget, "songSettingsWindow").resize(event.size())

    def connect_actions(self):
        button_box = self.findChild(QDialogButtonBox)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.load_settings)

    def save_settings(self):
        for data in {i.data(CustomDataRole.ITEMDATA) for i in self.tree_indexes}:
            for widget in get_all_children(self):
                class_name = widget.metaObject().className()
                if class_name in WIDGET_FUNCTIONS:
                    setting = widget.objectName()
                    value = WIDGET_FUNCTIONS[class_name]["getter"](widget)
                    if value != "<<Multiple values>>":
                        data.set_value(setting, value)

    def load_settings(self):
        items = [i.data(CustomDataRole.ITEMDATA).to_dict() for i in self.tree_indexes]
        # set settings based on selected items
        for widget in get_all_children(self):
            class_name = widget.metaObject().className()
            if class_name in WIDGET_FUNCTIONS:
                field = widget.objectName()
                values = {dict(i)[field] for i in items if field in dict(i)}
                if len(values) == 0:
                    continue
                has_multiple_values = (len(values) > 1)
                value = values.pop() if not has_multiple_values else "<<Multiple values>>"
                if class_name == "QComboBox":
                    # add <<Multiple values>> to combobox as necessary
                    multiple_values_index = widget.findText("<<Multiple values>>")
                    if not has_multiple_values and multiple_values_index != -1:
                        widget.removeItem(multiple_values_index)
                    if has_multiple_values and multiple_values_index == -1:
                        widget.addItem("<<Multiple values>>")
                WIDGET_FUNCTIONS[class_name]["setter"](widget, value)

    def song_tree_selection_changed(self, selected, deselected):
        self.tree_indexes |= set(selected.indexes())   # add new selected indexes
        self.tree_indexes -= set(deselected.indexes()) # remove deselected indexes
        self.setVisible(len(self.tree_indexes) > 0) # hide window if nothing is selected
        self.load_settings()
