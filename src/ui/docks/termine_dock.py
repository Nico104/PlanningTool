# from __future__ import annotations

# from typing import List, Dict, Optional, Set

# from PySide6.QtCore import Qt, Signal
# from PySide6.QtWidgets import (
#     QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
#     QScrollArea, QComboBox, QLabel, QMenu
# )

# from ...ui.utils.datetime_utils import fmt_date, fmt_time
# from ...models.models import Termin, Lehrveranstaltung, Raum
# from ..termine.termin_card import TerminCard


# class TermineDock(QDockWidget):
#     termin_double_clicked = Signal(str)
#     termin_delete_clicked = Signal(str)

#     def __init__(self, parent=None):
#         super().__init__("Termine", parent)
#         self.setAllowedAreas(Qt.AllDockWidgetAreas)

#         self._all_termine: List[Termin] = []
#         self._lva_map: Dict[str, Lehrveranstaltung] = {}
#         self._raum_map: Dict[str, Raum] = {}

#         wrap = QWidget(self)
#         root = QVBoxLayout(wrap)
#         root.setContentsMargins(6, 6, 6, 6)
#         root.setSpacing(6)

#         # ---- Filter bar ----
#         bar = QHBoxLayout()
#         bar.setSpacing(8)

#         bar.addWidget(QLabel("LVA:"))
#         self.cb_lva = QComboBox()
#         self.cb_lva.setMinimumWidth(240)
#         self.cb_lva.currentIndexChanged.connect(self._render)
#         bar.addWidget(self.cb_lva, 1)

#         bar.addWidget(QLabel("Typ:"))
#         self.cb_typ = QComboBox()
#         self.cb_typ.setMinimumWidth(120)
#         self.cb_typ.currentIndexChanged.connect(self._render)
#         bar.addWidget(self.cb_typ, 0)

#         root.addLayout(bar)

#         # ---- Scroll area with cards ----
#         self.scroll = QScrollArea(self)
#         self.scroll.setWidgetResizable(True)

#         self.container = QWidget()
#         self.list_layout = QVBoxLayout(self.container)
#         self.list_layout.setContentsMargins(2, 2, 2, 2)
#         self.list_layout.setSpacing(8)
#         self.list_layout.addStretch(1)

#         self.scroll.setWidget(self.container)
#         root.addWidget(self.scroll, 1)

#         self.setWidget(wrap)

#     # ---------- public ----------
#     def set_rows(
#         self,
#         termine: List[Termin],
#         lva_map: Dict[str, Lehrveranstaltung],
#         raum_map: Dict[str, Raum],
#     ) -> None:
#         self._all_termine = list(termine)
#         self._lva_map = dict(lva_map)
#         self._raum_map = dict(raum_map)

#         self._rebuild_filters()
#         self._render()

#     # ---------- filters ----------
#     def _rebuild_filters(self) -> None:
#         # keep selections
#         cur_lva = self.cb_lva.currentData()
#         cur_typ = self.cb_typ.currentData()

#         self.cb_lva.blockSignals(True)
#         self.cb_typ.blockSignals(True)

#         self.cb_lva.clear()
#         self.cb_typ.clear()

#         # LVA
#         self.cb_lva.addItem("Alle", None)
#         lva_ids = sorted({t.lva_id for t in self._all_termine if t.lva_id})
#         for lid in lva_ids:
#             lva = self._lva_map.get(lid)
#             name = lva.name if lva else ""
#             text = f"{lid} – {name}".strip(" –")
#             self.cb_lva.addItem(text, lid)

#         # Typ
#         self.cb_typ.addItem("Alle", None)
#         typs = sorted({t.typ for t in self._all_termine if t.typ})
#         for tp in typs:
#             self.cb_typ.addItem(tp, tp)

#         # restore selection
#         if cur_lva is not None:
#             i = self.cb_lva.findData(cur_lva)
#             if i >= 0:
#                 self.cb_lva.setCurrentIndex(i)

#         if cur_typ is not None:
#             i = self.cb_typ.findData(cur_typ)
#             if i >= 0:
#                 self.cb_typ.setCurrentIndex(i)

#         self.cb_lva.blockSignals(False)
#         self.cb_typ.blockSignals(False)

#     # ---------- rendering ----------
#     def _render(self) -> None:
#         # clear old cards (leave last stretch)
#         while self.list_layout.count() > 1:
#             item = self.list_layout.takeAt(0)
#             w = item.widget()
#             if w:
#                 w.deleteLater()

#         sel_lva = self.cb_lva.currentData()
#         sel_typ = self.cb_typ.currentData()

#         # filter
#         terms = self._all_termine
#         if sel_lva:
#             terms = [t for t in terms if t.lva_id == sel_lva]
#         if sel_typ:
#             terms = [t for t in terms if t.typ == sel_typ]

#         # sort by date asc + start time
#         # terms = sorted(terms, key=lambda t: (t.datum, t.zeit.von, t.id))
#         from datetime import date as _date, time as _time

#         def _sort_key(t):
#             unassigned = (t.datum is None)

#             d = t.datum or _date.min
#             von = (t.zeit.von if t.zeit and t.zeit.von else _time.min)

#             return (not unassigned, d, von, t.id)

#         terms = sorted(terms, key=_sort_key)


#         for t in terms:
#             lva = self._lva_map.get(t.lva_id)
#             raum = self._raum_map.get(t.raum_id)

#             title = f"{t.lva_id} – {(lva.name if lva else '')}".strip(" –")
#             raum_txt = f"{t.raum_id} – {(raum.name if raum else '')}".strip(" –")

#             card = TerminCard(
#                 termin_id=t.id,
#                 title=title,
#                 date=fmt_date(t.datum),
#                 # time=f"{fmt_time(t.zeit.von)} – {fmt_time(t.zeit.bis)}",
#                 time=(
#                     f"{fmt_time(t.zeit.von)} – {fmt_time(t.zeit.bis)}"
#                     if t.zeit and (t.zeit.von or t.zeit.bis)
#                     else ""
#                 ),
#                 typ=t.typ,
#                 raum=raum_txt,
#                 ap=t.anwesenheitspflicht,
#                 parent=self.container,
#             )

#             card.double_clicked.connect(self.termin_double_clicked.emit)
#             card.right_clicked.connect(self._open_menu)

#             self.list_layout.insertWidget(self.list_layout.count() - 1, card)

#     def _open_menu(self, termin_id: str) -> None:
#         menu = QMenu(self)
#         act_edit = menu.addAction("Bearbeiten")
#         act_del = menu.addAction("Löschen")

#         chosen = menu.exec(self.cursor().pos())
#         if chosen == act_edit:
#             self.termin_double_clicked.emit(termin_id)
#         elif chosen == act_del:
#             self.termin_delete_clicked.emit(termin_id)


from __future__ import annotations

from typing import List, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QComboBox, QLabel, QMenu
)

from ...ui.utils.datetime_utils import fmt_date, fmt_time
from ...models.models import Termin, Lehrveranstaltung, Raum
from ..termine.termin_card import TerminCard


class _TerminDropContainer(QWidget):
    """
    Drop target for Termine list.
    Drop anywhere inside this container -> emit termin_id (unassign request).
    """
    terminDroppedToList = Signal(str)
    MIME = "application/x-termin-id"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(self.MIME):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(self.MIME):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent):
        md = e.mimeData()
        if not md.hasFormat(self.MIME):
            e.ignore()
            return

        tid = bytes(md.data(self.MIME)).decode("utf-8").strip()
        if tid:
            self.terminDroppedToList.emit(tid)
            e.acceptProposedAction()
        else:
            e.ignore()


class TermineDock(QDockWidget):
    termin_double_clicked = Signal(str)
    termin_delete_clicked = Signal(str)

    # NEW: when dropped back into list (unassign)
    termin_unassign_requested = Signal(str)

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

        # IMPORTANT: droppable container (drop anywhere to unassign)
        self.container = _TerminDropContainer()
        self.container.terminDroppedToList.connect(self._on_drop_to_list)

        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(8, 2, 8, 2)
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

        # sort: unassigned first, then date/time
        from datetime import date as _date, time as _time

        def _sort_key(t: Termin):
            unassigned = (t.datum is None) or (t.zeit is None)
            d = t.datum or _date.min
            von = (t.zeit.von if t.zeit and t.zeit.von else _time.min)
            return (not unassigned, d, von, t.id)

        terms = sorted(terms, key=_sort_key)

        for t in terms:
            lva = self._lva_map.get(t.lva_id)
            raum = self._raum_map.get(t.raum_id)

            title = f"{t.lva_id} – {(lva.name if lva else '')}".strip(" –")
            raum_txt = f"{t.raum_id} – {(raum.name if raum else '')}".strip(" –")

            # date/time display (safe for None)
            date_text = fmt_date(t.datum)
            time_text = (
                f"{fmt_time(t.zeit.von)} – {fmt_time(t.zeit.bis)}"
                if t.zeit and (t.zeit.von or t.zeit.bis)
                else ""
            )

            card = TerminCard(
                termin_id=t.id,
                title=title,
                date=date_text,
                time=time_text,
                typ=t.typ,
                raum=raum_txt,
                ap=t.anwesenheitspflicht,
                parent=self.container,
            )

            card.double_clicked.connect(self.termin_double_clicked.emit)
            card.right_clicked.connect(self._open_menu)

            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

    # ---------- drop handling ----------
    def _on_drop_to_list(self, termin_id: str) -> None:
        """
        Dropping a termin back into the list means: unassign it.
        We don't change data here; we emit a signal so MainWindow/Handlers can persist.
        """
        self.termin_unassign_requested.emit(termin_id)

    # ---------- context menu ----------
    def _open_menu(self, termin_id: str) -> None:
        menu = QMenu(self)
        act_edit = menu.addAction("Bearbeiten")
        act_del = menu.addAction("Löschen")

        chosen = menu.exec(self.cursor().pos())
        if chosen == act_edit:
            self.termin_double_clicked.emit(termin_id)
        elif chosen == act_del:
            self.termin_delete_clicked.emit(termin_id)
