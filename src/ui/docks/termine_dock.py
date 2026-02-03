

from __future__ import annotations

from typing import List, Dict, Optional

from PySide6.QtCore import Qt, Signal,QDate
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QComboBox, QLabel, QMenu, QPushButton, QFrame
)

from ...ui.utils.datetime_utils import fmt_date, fmt_time
from ...models.models import Termin, Lehrveranstaltung, Raum
from ..termine.termin_card import TerminCard


from ..utils.widgets.tight_combobox import TightComboBox
from ..planner.planner_actions import PlannerActions


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

        header = QWidget(self)
        header.setObjectName("HeaderBar")
        root = QVBoxLayout(header)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ---- Header bar ----
        bar = QHBoxLayout()
        bar.setSpacing(8)
        root.addLayout(bar)

        # ---- Scroll area with cards ----
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setLineWidth(0)


        # IMPORTANT: droppable container (drop anywhere to unassign)
        self.container = _TerminDropContainer()
        self.container.terminDroppedToList.connect(self._on_drop_to_list)

        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(8, 2, 8, 2)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

        self.setWidget(header)

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

        # Global filtering is applied by MainWindow before calling set_rows.
        # Just render the provided rows.
        self._render()

    def set_global_filter_state(self, fs) -> None:
        """Sync the dock's filter UI from a central FilterState (read-only).

        This updates local comboboxes to reflect global selections but does not
        emit signals back to the application (blockSignals used).
        """
        # TermineDock no longer shows local filter widgets; MainWindow applies
        # global filters and passes the filtered rows to set_rows().
        return

    # ---------- filters ----------
    def _rebuild_filters(self) -> None:
        # No local filters to rebuild; global dock owns filter widgets.
        return

    # ---------- rendering ----------
    def _render(self) -> None:
        # clear old cards (leave last stretch)
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # MainWindow supplies already-filtered termine to set_rows(); render them.
        terms = self._all_termine

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
            