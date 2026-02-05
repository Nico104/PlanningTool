from __future__ import annotations

from typing import Optional

from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QPushButton, QDateEdit

from ..components.widgets.tight_combobox import TightComboBox
from ...core.states import FilterState


class GlobalFilterDock(QDockWidget):
    """Dockable widget that owns global filters and emits FilterState on changes.

    Emits `filtersChanged` with a FilterState instance whenever a dropdown changes.
    The dock does not mutate application state itself; it only emits the new state.
    """

    filtersChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__("Filter", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self._widget = QWidget(self)
        headerBar = QHBoxLayout(self._widget)
        headerBar.setObjectName("HeaderBar")
        headerBar.setContentsMargins(6, 6, 6, 6)
        headerBar.setSpacing(8)

        self.sem_cb = TightComboBox()
        self.sem_cb.setToolTip("Semester filter")
        self.sem_cb.setMinimumWidth(200)
        headerBar.addWidget(self.sem_cb)

        self.lva_cb = TightComboBox()
        self.lva_cb.setToolTip("LVA filter")
        self.lva_cb.setMinimumWidth(220)
        headerBar.addWidget(self.lva_cb)

        self.typ_cb = TightComboBox()
        self.typ_cb.setToolTip("Typ filter")
        self.typ_cb.setMinimumWidth(160)
        headerBar.addWidget(self.typ_cb)

        self.room_cb = TightComboBox()
        self.room_cb.setToolTip("Raum filter")
        self.room_cb.setMinimumWidth(200)
        headerBar.addWidget(self.room_cb)
        
        
        # View selector + navigation + dates (moved from Planner header)
        self.view_cb = TightComboBox()
        self.view_cb.addItem("Wochen", "week")
        self.view_cb.addItem("Tag", "day")
        self.view_cb.setFixedWidth(120)
        headerBar.addWidget(self.view_cb)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setObjectName("NavButton")
        self.prev_btn.setFixedWidth(36)
        headerBar.addWidget(self.prev_btn)

        self.next_btn = QPushButton(">")
        self.next_btn.setObjectName("NavButton")
        self.next_btn.setFixedWidth(36)
        headerBar.addWidget(self.next_btn)

        self.day_date = QDateEdit()
        # self.day_date.setObjectName("HeaderDate")
        self.day_date.setCalendarPopup(True)
        self.day_date.setDate(QDate.currentDate())
        self.day_date.setFixedWidth(150)
        headerBar.addWidget(self.day_date)

        self.week_from = QDateEdit()
        self.week_from.setObjectName("DateEdit")
        self.week_from.setCalendarPopup(True)
        self.week_from.setFixedWidth(150)
        self.week_from.setDate(QDate.currentDate().addDays(-28))
        headerBar.addWidget(self.week_from)
        
        self.sem_cb.setObjectName("HeaderCombo")
        self.lva_cb.setObjectName("HeaderCombo")
        self.typ_cb.setObjectName("HeaderCombo")
        self.room_cb.setObjectName("HeaderCombo")
        self.view_cb.setObjectName("HeaderCombo")

        # connect signals
        self.sem_cb.currentIndexChanged.connect(self._on_change)
        self.lva_cb.currentIndexChanged.connect(self._on_change)
        self.typ_cb.currentIndexChanged.connect(self._on_change)
        self.room_cb.currentIndexChanged.connect(self._on_change)
        # view/date/navigation signals exposed; planner will connect to these
        # externally. We do not forward them via filtersChanged.

        self.setWidget(self._widget)

    def _on_change(self, *_) -> None:
        fs = FilterState(
            semester_id=self.sem_cb.currentData() or None,
            lva_id=self.lva_cb.currentData() or None,
            raum_id=self.room_cb.currentData() or None,
            typ=self.typ_cb.currentData() or None,
        )
        self.filtersChanged.emit(fs)

    def rebuild(self, semester_list, lva_list, raum_list, typ_list=None, current: Optional[FilterState] = None) -> None:
        """Populate dropdowns from provided lists and restore current selection if given.

        Each list is expected to contain objects with `id` and `name` attributes.
        """
        cur_sem = current.semester_id if current else None
        cur_lva = current.lva_id if current else None
        cur_room = current.raum_id if current else None
        cur_typ = current.typ if current else None

        # Semester
        self.sem_cb.blockSignals(True)
        self.sem_cb.clear()
        self.sem_cb.addItem("Semester: alle", "")
        for s in semester_list:
            self.sem_cb.addItem(f"{s.id} – {s.name}", s.id)
        if cur_sem:
            i = self.sem_cb.findData(cur_sem)
            if i >= 0:
                self.sem_cb.setCurrentIndex(i)
        self.sem_cb.blockSignals(False)

        # LVA
        self.lva_cb.blockSignals(True)
        self.lva_cb.clear()
        self.lva_cb.addItem("LVA: Alle", None)
        for lv in lva_list:
            self.lva_cb.addItem(f"{lv.id} – {getattr(lv, 'name', '')}", lv.id)
        if cur_lva:
            i = self.lva_cb.findData(cur_lva)
            if i >= 0:
                self.lva_cb.setCurrentIndex(i)
        self.lva_cb.blockSignals(False)

        # Typ
        self.typ_cb.blockSignals(True)
        self.typ_cb.clear()
        self.typ_cb.addItem("Typ: Alle", None)
        if typ_list:
            for tp in sorted({t for t in typ_list if t}):
                self.typ_cb.addItem(tp, tp)
        if cur_typ is not None:
            i = self.typ_cb.findData(cur_typ)
            if i >= 0:
                self.typ_cb.setCurrentIndex(i)
        self.typ_cb.blockSignals(False)

        # Räume
        self.room_cb.blockSignals(True)
        self.room_cb.clear()
        self.room_cb.addItem("Raum: alle", "")
        for r in raum_list:
            self.room_cb.addItem(f"{r.id} – {getattr(r, 'name', '')}", r.id)
        if cur_room:
            i = self.room_cb.findData(cur_room)
            if i >= 0:
                self.room_cb.setCurrentIndex(i)
        self.room_cb.blockSignals(False)
