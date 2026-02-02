from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QDockWidget, QTableWidget, QTableWidgetItem, QMenu

from ...models.models import Lehrveranstaltung


class LVADock(QDockWidget):
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("LVAs", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Vortragende", "E-Mail", "Typen"])
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Kontextmenü (Rechtsklick)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

        # Optional: Doppelklick = Bearbeiten
        self.table.cellDoubleClicked.connect(lambda r, c: self._emit_edit_if_selected())

        self.setWidget(self.table)

    # ---------------- Context menu ----------------

    def _open_context_menu(self, pos: QPoint) -> None:
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return

        # Sicherstellen, dass die rechtsgeklickte Zeile ausgewählt ist
        self.table.selectRow(idx.row())

        menu = QMenu(self)
        act_edit = menu.addAction("Bearbeiten")
        act_del = menu.addAction("Löschen")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_edit:
            self.edit_clicked.emit()
        elif chosen == act_del:
            self.delete_clicked.emit()

    def _emit_edit_if_selected(self) -> None:
        if self.selected_id():
            self.edit_clicked.emit()

    # ---------------- Data ----------------

    def set_rows(self, lvas: List[Lehrveranstaltung]) -> None:
        t = self.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for l in lvas:
            row = t.rowCount()
            t.insertRow(row)

            vals = [
                l.id,
                l.name,
                getattr(l.vortragende, "name", ""),
                getattr(l.vortragende, "email", ""),
                ", ".join(getattr(l, "typ", []) or []),
            ]

            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                t.setItem(row, c, it)

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def selected_id(self) -> Optional[str]:
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 0)
        return it.text().strip() if it else None
