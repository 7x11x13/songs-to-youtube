from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from songs_to_youtube.song_tree_widget_item import TreeWidgetItemData


class MetadataTableWidget(QTableWidget):
    def __init__(self, *args):
        super().__init__(*args)

    def from_data(self, data: TreeWidgetItemData):
        for key, value in data.to_dict().items():
            self.insertRow(self.rowCount())
            key_item = QTableWidgetItem(key)
            key_item.setFlags(Qt.ItemIsEnabled | Qt.ItemNeverHasChildren)
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(Qt.ItemIsEnabled | Qt.ItemNeverHasChildren)
            self.setItem(self.rowCount() - 1, 0, key_item)
            self.setItem(self.rowCount() - 1, 1, value_item)

    def resizeEvent(self, event):
        for c in range(self.columnCount()):
            self.setColumnWidth(c, event.size().width() // self.columnCount())
