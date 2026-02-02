

# from __future__ import annotations

# from typing import List, Dict, Optional

# from PySide6.QtCore import Qt, Signal, QPoint
# from PySide6.QtWidgets import (
#     QDockWidget, QTableWidget, QTableWidgetItem, QMenu,
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
# )

# from ...ui.utils.datetime_utils import fmt_date, fmt_time
# from ...models.models import Termin, Lehrveranstaltung, Raum

# # Drag source table (must exist at: src/ui/dragdrop/termin_drag_table.py)
# from ..dragdrop.termin_drag_table import TerminDragTable


# class TermineDock(QDockWidget):
#     termin_double_clicked = Signal(str)  # termin_id
#     termin_delete_clicked = Signal(str)  # termin_id

#     def __init_old__(self, parent=None):
#         super().__init__("Termine (Liste)", parent)
#         self.setAllowedAreas(Qt.AllDockWidgetAreas)

#         # Draggable table
#         self.table = TerminDragTable()
#         self.table.setColumnCount(8)
#         self.table.setHorizontalHeaderLabels(["ID", "Datum", "Von", "Bis", "Typ", "LVA", "Raum", "AP"])

#         # UX / behavior (same as your file)
#         self.table.setSortingEnabled(True)
#         self.table.horizontalHeader().setStretchLastSection(True)
#         self.table.setSelectionBehavior(QTableWidget.SelectRows)
#         self.table.setSelectionMode(QTableWidget.SingleSelection)
#         self.table.setEditTriggers(QTableWidget.NoEditTriggers)

#         # double click -> edit
#         self.table.cellDoubleClicked.connect(self._on_double_click)

#         # context menu (edit/delete)
#         self.table.setContextMenuPolicy(Qt.CustomContextMenu)
#         self.table.customContextMenuRequested.connect(self._open_context_menu)

#         self.setWidget(self.table)
        
#     def __init__(self, parent=None):
#         super().__init__("Termine (Liste)", parent)
#         self.setAllowedAreas(Qt.AllDockWidgetAreas)

#         self._all_termine: List[Termin] = []
#         self._lva_map: Dict[str, Lehrveranstaltung] = {}
#         self._raum_map: Dict[str, Raum] = {}

#         wrap = QWidget(self)
#         root = QVBoxLayout(wrap)
#         root.setContentsMargins(6, 6, 6, 6)
#         root.setSpacing(6)

#         # ---- Header: Text + Filter (LVA) ----
#         header = QHBoxLayout()
#         self.lbl_lva = QLabel("Lehrveranstaltung:", wrap)

#         self.cb_lva = QComboBox(wrap)
#         self.cb_lva.setMinimumWidth(260)
#         self.cb_lva.currentIndexChanged.connect(self._apply_filter)

#         header.addWidget(self.lbl_lva)
#         header.addWidget(self.cb_lva, 1)
#         root.addLayout(header)

#         # ---- Table ----
#         self.table = TerminDragTable()
#         self.table.setColumnCount(8)
#         self.table.setHorizontalHeaderLabels(["ID", "Datum", "Von", "Bis", "Typ", "LVA", "Raum", "AP"])
#         self.table.setSortingEnabled(False)  # wir sortieren selbst
#         self.table.horizontalHeader().setStretchLastSection(True)
#         self.table.setSelectionBehavior(QTableWidget.SelectRows)
#         self.table.setSelectionMode(QTableWidget.SingleSelection)
#         self.table.setEditTriggers(QTableWidget.NoEditTriggers)

#         self.table.cellDoubleClicked.connect(self._on_double_click)
#         self.table.setContextMenuPolicy(Qt.CustomContextMenu)
#         self.table.customContextMenuRequested.connect(self._open_context_menu)

#         root.addWidget(self.table, 1)
#         self.setWidget(wrap)

#     def set_rows(
#         self,
#         termine: List[Termin],
#         lva_map: Dict[str, Lehrveranstaltung],
#         raum_map: Dict[str, Raum],
#     ) -> None:
#         # Cache
#         self._all_termine = list(termine)
#         self._lva_map = dict(lva_map)
#         self._raum_map = dict(raum_map)

#         # Combo füllen (All + jede LVA die in termine vorkommt)
#         cur = self.cb_lva.currentData()
#         self.cb_lva.blockSignals(True)
#         self.cb_lva.clear()

#         self.cb_lva.addItem("Alle Lehrveranstaltungen", None)

#         lva_ids = sorted({t.lva_id for t in self._all_termine if t.lva_id})
#         for lid in lva_ids:
#             lva = self._lva_map.get(lid)
#             name = lva.name if lva else ""
#             text = f"{lid} – {name}".strip(" –")
#             self.cb_lva.addItem(text, lid)

#         # Auswahl wiederherstellen falls möglich
#         if cur is not None:
#             idx = self.cb_lva.findData(cur)
#             if idx >= 0:
#                 self.cb_lva.setCurrentIndex(idx)
#         self.cb_lva.blockSignals(False)

#         # Tabelle füllen
#         self._apply_filter()

#     def _apply_filter(self) -> None:
#         lid = self.cb_lva.currentData()

#         if lid:
#             filtered = [t for t in self._all_termine if t.lva_id == lid]
#             lva = self._lva_map.get(lid)
#             title = f"Lehrveranstaltung: {lid}"
#             if lva and lva.name:
#                 title += f" – {lva.name}"
#             self.lbl_lva.setText(title)
#         else:
#             filtered = list(self._all_termine)
#             self.lbl_lva.setText("Lehrveranstaltung: Alle")

#         # sort by date asc + time
#         filtered.sort(key=lambda x: (x.datum, x.zeit.von, x.id))

#         t = self.table
#         t.setRowCount(0)

#         for term in filtered:
#             row = t.rowCount()
#             t.insertRow(row)

#             lva = self._lva_map.get(term.lva_id)
#             raum = self._raum_map.get(term.raum_id)

#             vals = [
#                 term.id,
#                 fmt_date(term.datum),
#                 fmt_time(term.zeit.von),
#                 fmt_time(term.zeit.bis),
#                 term.typ,
#                 f"{term.lva_id} – {(lva.name if lva else '')}".strip(" –"),
#                 f"{term.raum_id} – {(raum.name if raum else '')}".strip(" –"),
#                 "ja" if term.anwesenheitspflicht else "nein",
#             ]

#             for c, v in enumerate(vals):
#                 it = QTableWidgetItem(str(v))
#                 it.setFlags(it.flags() & ~Qt.ItemIsEditable)
#                 t.setItem(row, c, it)

#         t.resizeColumnsToContents()


#     def set_rows_old(
#         self,
#         termine: List[Termin],
#         lva_map: Dict[str, Lehrveranstaltung],
#         raum_map: Dict[str, Raum],
#     ) -> None:
#         t = self.table
#         t.setSortingEnabled(False)
#         t.setRowCount(0)

#         for term in termine:
#             row = t.rowCount()
#             t.insertRow(row)

#             lva = lva_map.get(term.lva_id)
#             raum = raum_map.get(term.raum_id)

#             vals = [
#                 term.id,  # IMPORTANT: drag uses column 0 (termin id)
#                 fmt_date(term.datum),
#                 fmt_time(term.zeit.von),
#                 fmt_time(term.zeit.bis),
#                 term.typ,
#                 f"{term.lva_id} – {(lva.name if lva else '')}".strip(" –"),
#                 f"{term.raum_id} – {(raum.name if raum else '')}".strip(" –"),
#                 "ja" if term.anwesenheitspflicht else "nein",
#             ]

#             for c, v in enumerate(vals):
#                 it = QTableWidgetItem(str(v))
#                 it.setFlags(it.flags() & ~Qt.ItemIsEditable)
#                 t.setItem(row, c, it)

#         t.setSortingEnabled(True)
#         t.resizeColumnsToContents()

#         # optional: hide ID column if you don’t want to see it
#         # (drag still works)
#         # t.setColumnHidden(0, True)

#     def selected_termin_id(self) -> Optional[str]:
#         row = self.table.currentRow()
#         if row < 0:
#             return None
#         it = self.table.item(row, 0)
#         return it.text().strip() if it else None

#     def _on_double_click(self, row: int, col: int) -> None:
#         it = self.table.item(row, 0)
#         if not it:
#             return
#         tid = it.text().strip()

#         # Header rows haben leere ID -> ignorieren
#         if not tid:
#             return

#         self.termin_double_clicked.emit(tid)

#     def _open_context_menu(self, pos: QPoint) -> None:
#         idx = self.table.indexAt(pos)
#         if not idx.isValid():
#             return

#         self.table.selectRow(idx.row())
#         tid = self.selected_termin_id()

#         # Header row -> kein Menü
#         if not tid:
#             return


#     def _open_context_menu_old(self, pos: QPoint) -> None:
#         idx = self.table.indexAt(pos)
#         if not idx.isValid():
#             return

#         self.table.selectRow(idx.row())
#         tid = self.selected_termin_id()
#         if not tid:
#             return

#         menu = QMenu(self)
#         act_edit = menu.addAction("Bearbeiten")
#         act_del = menu.addAction("Löschen")

#         chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
#         if chosen == act_edit:
#             self.termin_double_clicked.emit(tid)
#         elif chosen == act_del:
#             self.termin_delete_clicked.emit(tid)
from __future__ import annotations

from typing import List, Dict, Optional, Set

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QComboBox, QLabel, QMenu
)

from ...ui.utils.datetime_utils import fmt_date, fmt_time
from ...models.models import Termin, Lehrveranstaltung, Raum
from ..termine.termin_card import TerminCard


class TermineDock(QDockWidget):
    termin_double_clicked = Signal(str)
    termin_delete_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Termine", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self._all_termine: List[Termin] = []
        self._lva_map: Dict[str, Lehrveranstaltung] = {}
        self._raum_map: Dict[str, Raum] = {}

        wrap = QWidget(self)
        root = QVBoxLayout(wrap)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ---- Filter bar ----
        bar = QHBoxLayout()
        bar.setSpacing(8)

        bar.addWidget(QLabel("LVA:"))
        self.cb_lva = QComboBox()
        self.cb_lva.setMinimumWidth(240)
        self.cb_lva.currentIndexChanged.connect(self._render)
        bar.addWidget(self.cb_lva, 1)

        bar.addWidget(QLabel("Typ:"))
        self.cb_typ = QComboBox()
        self.cb_typ.setMinimumWidth(120)
        self.cb_typ.currentIndexChanged.connect(self._render)
        bar.addWidget(self.cb_typ, 0)

        root.addLayout(bar)

        # ---- Scroll area with cards ----
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(2, 2, 2, 2)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

        self.setWidget(wrap)

    # ---------- public ----------
    def set_rows(
        self,
        termine: List[Termin],
        lva_map: Dict[str, Lehrveranstaltung],
        raum_map: Dict[str, Raum],
    ) -> None:
        self._all_termine = list(termine)
        self._lva_map = dict(lva_map)
        self._raum_map = dict(raum_map)

        self._rebuild_filters()
        self._render()

    # ---------- filters ----------
    def _rebuild_filters(self) -> None:
        # keep selections
        cur_lva = self.cb_lva.currentData()
        cur_typ = self.cb_typ.currentData()

        self.cb_lva.blockSignals(True)
        self.cb_typ.blockSignals(True)

        self.cb_lva.clear()
        self.cb_typ.clear()

        # LVA
        self.cb_lva.addItem("Alle", None)
        lva_ids = sorted({t.lva_id for t in self._all_termine if t.lva_id})
        for lid in lva_ids:
            lva = self._lva_map.get(lid)
            name = lva.name if lva else ""
            text = f"{lid} – {name}".strip(" –")
            self.cb_lva.addItem(text, lid)

        # Typ
        self.cb_typ.addItem("Alle", None)
        typs = sorted({t.typ for t in self._all_termine if t.typ})
        for tp in typs:
            self.cb_typ.addItem(tp, tp)

        # restore selection
        if cur_lva is not None:
            i = self.cb_lva.findData(cur_lva)
            if i >= 0:
                self.cb_lva.setCurrentIndex(i)

        if cur_typ is not None:
            i = self.cb_typ.findData(cur_typ)
            if i >= 0:
                self.cb_typ.setCurrentIndex(i)

        self.cb_lva.blockSignals(False)
        self.cb_typ.blockSignals(False)

    # ---------- rendering ----------
    def _render(self) -> None:
        # clear old cards (leave last stretch)
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        sel_lva = self.cb_lva.currentData()
        sel_typ = self.cb_typ.currentData()

        # filter
        terms = self._all_termine
        if sel_lva:
            terms = [t for t in terms if t.lva_id == sel_lva]
        if sel_typ:
            terms = [t for t in terms if t.typ == sel_typ]

        # sort by date asc + start time
        # terms = sorted(terms, key=lambda t: (t.datum, t.zeit.von, t.id))
        from datetime import date as _date, time as _time

        def _sort_key(t):
            unassigned = (t.datum is None)

            d = t.datum or _date.min
            von = (t.zeit.von if t.zeit and t.zeit.von else _time.min)

            return (not unassigned, d, von, t.id)

        terms = sorted(terms, key=_sort_key)


        for t in terms:
            lva = self._lva_map.get(t.lva_id)
            raum = self._raum_map.get(t.raum_id)

            title = f"{t.lva_id} – {(lva.name if lva else '')}".strip(" –")
            raum_txt = f"{t.raum_id} – {(raum.name if raum else '')}".strip(" –")

            card = TerminCard(
                termin_id=t.id,
                title=title,
                date=fmt_date(t.datum),
                # time=f"{fmt_time(t.zeit.von)} – {fmt_time(t.zeit.bis)}",
                time=(
                    f"{fmt_time(t.zeit.von)} – {fmt_time(t.zeit.bis)}"
                    if t.zeit and (t.zeit.von or t.zeit.bis)
                    else ""
                ),
                typ=t.typ,
                raum=raum_txt,
                ap=t.anwesenheitspflicht,
                parent=self.container,
            )

            card.double_clicked.connect(self.termin_double_clicked.emit)
            card.right_clicked.connect(self._open_menu)

            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

    def _open_menu(self, termin_id: str) -> None:
        menu = QMenu(self)
        act_edit = menu.addAction("Bearbeiten")
        act_del = menu.addAction("Löschen")

        chosen = menu.exec(self.cursor().pos())
        if chosen == act_edit:
            self.termin_double_clicked.emit(termin_id)
        elif chosen == act_del:
            self.termin_delete_clicked.emit(termin_id)
