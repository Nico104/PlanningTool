from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDockWidget

from ..widgets.dock_table import DockTable
from ...models.models import Raum


class RoomDock(QDockWidget):
    add_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Räume", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.tab = DockTable(["ID", "Name", "Kapazität"])
        self.setWidget(self.tab)

        self.tab.add_btn.clicked.connect(self.add_clicked.emit)
        self.tab.edit_btn.clicked.connect(self.edit_clicked.emit)
        self.tab.del_btn.clicked.connect(self.delete_clicked.emit)

    def set_rows(self, rooms: List[Raum]) -> None:
        t = self.tab.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for r in rooms:
            row = t.rowCount()
            t.insertRow(row)
            vals = [r.id, r.name, str(r.kapazitaet)]
            for c, v in enumerate(vals):
                from PySide6.QtWidgets import QTableWidgetItem
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                t.setItem(row, c, it)

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def selected_id(self) -> Optional[str]:
        return self.tab.selected_id()
