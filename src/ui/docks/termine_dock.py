from typing import List, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QMenu, QFrame
)

from ..utils.datetime_utils import fmt_date, fmt_time
from ...core.models import Termin, Lehrveranstaltung, Raum
from ..components.cards.termin_card import TerminCard
from ..components.dragdrop.termin_drop_area import TerminDropArea
from datetime import date as date, time as time

class TermineDock(QDockWidget):
    termin_double_clicked = Signal(str)
    termin_delete_clicked = Signal(str)
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

        #Header bar
        bar = QHBoxLayout()
        bar.setSpacing(8)
        root.addLayout(bar)

        #Scroll area with cards
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setLineWidth(0)


        self.container = TerminDropArea()
        self.container.terminDroppedToList.connect(self._on_drop_to_list)

        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(8, 2, 8, 2)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)

        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

        self.setWidget(header)


    def set_rows(
        self,
        termine: List[Termin],
        lva_map: Dict[str, Lehrveranstaltung],
        raum_map: Dict[str, Raum],
    ) -> None:
        self._all_termine = list(termine)
        self._lva_map = dict(lva_map)
        self._raum_map = dict(raum_map)

        # Global filtering is applied by MainWindow before calling set_rows
        self._build_cards()

    def _build_cards(self) -> None:
        # clear old cards (leave last stretch)
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # MainWindow supplies already-filtered termine to set_rows()
        terms = self._all_termine

        def _sort_key(t: Termin):
            unassigned = (t.datum is None) or (t.start_zeit is None)
            d = t.datum or date.min
            von = (t.start_zeit if t.start_zeit else time.min)
            return (not unassigned, d, von, t.id)

        terms = sorted(terms, key=_sort_key)

        for t in terms:
            lva = self._lva_map.get(t.lva_id)
            raum = self._raum_map.get(t.raum_id)

            title = f"{t.lva_id} – {(lva.name if lva else '')}".strip(" –")
            raum_txt = f"{t.raum_id} – {(raum.name if raum else '')}".strip(" –")

            # date/time display (safe for None)
            date_text = fmt_date(t.datum)
            end_time = t.get_end_time()
            time_text = (
                f"{fmt_time(t.start_zeit)} – {fmt_time(end_time)} ({t.duration} min)"
                if t.start_zeit and end_time
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
                duration=t.get_duration_minutes(),
                parent=self.container,
            )

            card.double_clicked.connect(self.termin_double_clicked.emit)
            card.right_clicked.connect(self._open_menu)

            self.list_layout.insertWidget(self.list_layout.count() - 1, card)


    def _on_drop_to_list(self, termin_id: str) -> None:
        """
        Dropping a termin back into the list means: unassign it
        """
        self.termin_unassign_requested.emit(termin_id)

    def _open_menu(self, termin_id: str) -> None:
        menu = QMenu(self)
        act_edit = menu.addAction("Bearbeiten")
        act_del = menu.addAction("Löschen")

        chosen = menu.exec(self.cursor().pos())
        if chosen == act_edit:
            self.termin_double_clicked.emit(termin_id)
        elif chosen == act_del:
            self.termin_delete_clicked.emit(termin_id)
            