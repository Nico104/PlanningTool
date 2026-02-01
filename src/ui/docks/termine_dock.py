from __future__ import annotations

from typing import List, Dict, Optional

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QDockWidget, QTableWidget, QTableWidgetItem, QMenu

from ...ui.utils.datetime_utils import fmt_date, fmt_time
from ...models.models import Termin, Lehrveranstaltung, Raum
from ..widgets.draggableTerminTable import DraggableTerminTable


class TermineDock(QDockWidget):
    termin_double_clicked = Signal(str)  # termin_id
    termin_delete_clicked = Signal(str)  # termin_id  (NEU)

    def __init__(self, parent=None):
        super().__init__("Termine (Liste)", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.table = DraggableTerminTable(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "Datum", "Von", "Bis", "Typ", "LVA", "Raum", "AP"])
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.table.cellDoubleClicked.connect(self._on_double_click)

        # Kontextmenü (NEU)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)

        self.setWidget(self.table)

    def set_rows(
        self,
        termine: List[Termin],
        lva_map: Dict[str, Lehrveranstaltung],
        raum_map: Dict[str, Raum],
    ) -> None:
        t = self.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for term in termine:
            row = t.rowCount()
            t.insertRow(row)

            lva = lva_map.get(term.lva_id)
            raum = raum_map.get(term.raum_id)

            vals = [
                term.id,
                fmt_date(term.datum),
                fmt_time(term.zeit.von),
                fmt_time(term.zeit.bis),
                term.typ,
                f"{term.lva_id} – {(lva.name if lva else '')}".strip(" –"),
                f"{term.raum_id} – {(raum.name if raum else '')}".strip(" –"),
                "ja" if term.anwesenheitspflicht else "nein",
            ]

            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                t.setItem(row, c, it)

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def selected_termin_id(self) -> Optional[str]:
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 0)
        return it.text().strip() if it else None

    def _on_double_click(self, row: int, col: int) -> None:
        it = self.table.item(row, 0)
        if not it:
            return
        tid = it.text().strip()
        if tid:
            self.termin_double_clicked.emit(tid)

    def _open_context_menu(self, pos: QPoint) -> None:
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return

        self.table.selectRow(idx.row())
        tid = self.selected_termin_id()
        if not tid:
            return

        menu = QMenu(self)
        act_edit = menu.addAction("Bearbeiten")
        act_del = menu.addAction("Löschen")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_edit:
            self.termin_double_clicked.emit(tid)
        elif chosen == act_del:
            self.termin_delete_clicked.emit(tid)
