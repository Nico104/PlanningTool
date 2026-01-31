from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDockWidget

from ..widgets.dock_table import DockTable
from ...models.models import Lehrveranstaltung


class LVADock(QDockWidget):
    add_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("LVAs", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.tab = DockTable(["ID", "Name", "Vortragende", "E-Mail", "Typen"])
        self.setWidget(self.tab)

        self.tab.add_btn.clicked.connect(self.add_clicked.emit)
        self.tab.edit_btn.clicked.connect(self.edit_clicked.emit)
        self.tab.del_btn.clicked.connect(self.delete_clicked.emit)

    def set_rows(self, lvas: List[Lehrveranstaltung]) -> None:
        t = self.tab.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for l in lvas:
            row = t.rowCount()
            t.insertRow(row)
            vals = [l.id, l.name, l.vortragende.name, l.vortragende.email, ", ".join(l.typ)]
            for c, v in enumerate(vals):
                from PySide6.QtWidgets import QTableWidgetItem
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                t.setItem(row, c, it)

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def selected_id(self) -> Optional[str]:
        return self.tab.selected_id()
