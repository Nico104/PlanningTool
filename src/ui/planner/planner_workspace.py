# from __future__ import annotations

# from datetime import date, timedelta
# from typing import Optional, Tuple

# from PySide6.QtCore import Qt, QDate
# from PySide6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit, QLabel, QLineEdit,
#     QPushButton, QStackedWidget, QTableWidget
# )

# from ...services.dataService import DataService
# from ..utils.datetime_utils import date_to_qdate
# from .planner_state import PlannerState
# from .planner_day_view import PlannerDayView
# from .planner_week_view import PlannerWeekView
# from .planner_actions import PlannerActions


# class PlannerWorkspace(QWidget):
#     def __init__(self, parent: QWidget, ds: DataService, on_data_changed):
#         super().__init__(parent)
#         self._emit_enabled = False
#         # self.on_data_changed = on_data_changed
#         self.on_data_changed = None

#         self.state = PlannerState(ds)
#         self.state.reload()

#         lay = QVBoxLayout(self)

#         # ---- Controls
#         ctrl = QHBoxLayout()
#         lay.addLayout(ctrl)

#         ctrl.addWidget(QLabel("Ansicht:"))
#         self.view_cb = QComboBox()
#         self.view_cb.addItem("Tag (Zeit×Räume)", "day")
#         self.view_cb.addItem("Wochen (KW, Mo–Sa)", "week")
#         ctrl.addWidget(self.view_cb)

#         ctrl.addWidget(QLabel("Datum (Tag):"))
#         self.day_date = QDateEdit()
#         self.day_date.setCalendarPopup(True)
#         self.day_date.setDate(QDate.currentDate())
#         ctrl.addWidget(self.day_date)

#         ctrl.addWidget(QLabel("Wochenbereich:"))
#         self.week_from = QDateEdit()
#         self.week_from.setCalendarPopup(True)
#         self.week_to = QDateEdit()
#         self.week_to.setCalendarPopup(True)
#         today = date.today()
#         self.week_from.setDate(date_to_qdate(today - timedelta(days=28)))
#         self.week_to.setDate(date_to_qdate(today + timedelta(days=28)))
#         ctrl.addWidget(self.week_from)
#         ctrl.addWidget(self.week_to)

#         ctrl.addWidget(QLabel("Semester:"))
#         self.sem_cb = QComboBox()
#         ctrl.addWidget(self.sem_cb)

#         ctrl.addWidget(QLabel("Raum:"))
#         self.room_cb = QComboBox()
#         ctrl.addWidget(self.room_cb)

#         ctrl.addWidget(QLabel("Suche:"))
#         self.search_le = QLineEdit()
#         self.search_le.setPlaceholderText("LVA-ID oder Text…")
#         ctrl.addWidget(self.search_le, 1)

#         self.add_term_btn = QPushButton("Termin hinzufügen")
#         self.refresh_btn = QPushButton("Aktualisieren")
#         ctrl.addWidget(self.add_term_btn)
#         ctrl.addWidget(self.refresh_btn)

#         # ---- Tables
#         self.stack = QStackedWidget()
#         lay.addWidget(self.stack, 1)

#         self.day_table = QTableWidget(0, 0)
#         self.week_table = QTableWidget(0, 0)
#         self.day_table.setSortingEnabled(False)
#         self.week_table.setSortingEnabled(False)
#         self.stack.addWidget(self.day_table)
#         self.stack.addWidget(self.week_table)

#         # ---- Info line
#         info = QHBoxLayout()
#         lay.addLayout(info)
#         self.friday_lbl = QLabel("")
#         self.conflict_lbl = QLabel("Konflikte: –")
#         self.conflict_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
#         info.addWidget(self.friday_lbl)
#         info.addStretch(1)
#         info.addWidget(self.conflict_lbl)

#         # ---- Helpers
#         self.actions = PlannerActions(self.state, self)

#         self.day_view = PlannerDayView(
#             state=self.state,
#             day_table=self.day_table,
#             day_date=self.day_date,
#             room_cb=self.room_cb,
#             sem_cb=self.sem_cb,
#             friday_lbl=self.friday_lbl,
#             conflict_lbl=self.conflict_lbl,
#             edit_by_id_cb=self._edit_termin_by_id,
#             current_filters_cb=self.current_filters,
#         )
#         self.week_view = PlannerWeekView(
#             state=self.state,
#             week_table=self.week_table,
#             week_from=self.week_from,
#             week_to=self.week_to,
#             edit_by_id_cb=self._edit_termin_by_id,
#         )

#         # ---- Signals
#         self.refresh_btn.clicked.connect(self.refresh)
#         self.view_cb.currentIndexChanged.connect(self._on_view_changed)
#         self.day_date.dateChanged.connect(self.refresh)
#         self.week_from.dateChanged.connect(self.refresh)
#         self.week_to.dateChanged.connect(self.refresh)
#         self.sem_cb.currentIndexChanged.connect(self.refresh)
#         self.room_cb.currentIndexChanged.connect(self.refresh)
#         self.search_le.textChanged.connect(self.refresh)
#         self.add_term_btn.clicked.connect(self.add_termin)

#         # ---- Init
#         self._init_default_dates()
#         self._rebuild_filter_boxes()
#         self.refresh(emit=False)
#         self._emit_enabled = True

#     def _init_default_dates(self):
#         if not self.state.termine:
#             return
#         min_d = min(t.datum for t in self.state.termine)
#         max_d = max(t.datum for t in self.state.termine)
#         self.day_date.setDate(date_to_qdate(min_d))
#         self.week_from.setDate(date_to_qdate(min_d))
#         self.week_to.setDate(date_to_qdate(max_d))

#     def _rebuild_filter_boxes(self):
#         current_sem = self.sem_cb.currentData() if self.sem_cb.count() else ""
#         self.sem_cb.blockSignals(True)
#         self.sem_cb.clear()
#         self.sem_cb.addItem("(alle)", "")
#         for s in self.state.semester:
#             self.sem_cb.addItem(f"{s.id} – {s.name}", s.id)
#         if current_sem:
#             for i in range(self.sem_cb.count()):
#                 if self.sem_cb.itemData(i) == current_sem:
#                     self.sem_cb.setCurrentIndex(i)
#                     break
#         self.sem_cb.blockSignals(False)

#         current_room = self.room_cb.currentData() if self.room_cb.count() else ""
#         self.room_cb.blockSignals(True)
#         self.room_cb.clear()
#         self.room_cb.addItem("(alle)", "")
#         for r in self.state.raeume:
#             self.room_cb.addItem(f"{r.id} – {r.name}", r.id)
#         if current_room:
#             for i in range(self.room_cb.count()):
#                 if self.room_cb.itemData(i) == current_room:
#                     self.room_cb.setCurrentIndex(i)
#                     break
#         self.room_cb.blockSignals(False)

#     def current_filters(self) -> Tuple[Optional[str], Optional[str], str]:
#         sem = self.sem_cb.currentData() or None
#         room = self.room_cb.currentData() or None
#         q = (self.search_le.text() or "").strip().lower()
#         return sem, room, q

#     def refresh(self, emit: bool = True):
#         self.state.reload()
#         self._rebuild_filter_boxes()

#         sem, room, q = self.current_filters()
#         filtered = self.state.filtered_termine(semester_id=sem, raum_id=room, q=q)

#         view = str(self.view_cb.currentData())
#         if view == "day":
#             self.stack.setCurrentWidget(self.day_table)
#             self.day_view.refresh(filtered)
#         else:
#             self.stack.setCurrentWidget(self.week_table)
#             self.friday_lbl.setText("")
#             self.conflict_lbl.setText("Konflikte: –")
#             self.week_view.refresh(filtered)

#         if emit and self._emit_enabled and callable(self.on_data_changed):
#             self.on_data_changed()

#     def _on_view_changed(self):
#         view = str(self.view_cb.currentData())
#         is_day = (view == "day")
#         self.day_date.setEnabled(is_day)
#         self.week_from.setEnabled(not is_day)
#         self.week_to.setEnabled(not is_day)
#         self.refresh()

#     def add_termin(self):
#         if self.actions.add_termin(default_qdate=self.day_date.date()):
#             self.refresh()

#     def _edit_termin_by_id(self, tid: str):
#         if self.actions.edit_termin_by_id(tid):
#             self.refresh()
            
#     def set_on_data_changed(self, cb):
#         self.on_data_changed = cb


from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QTableWidget, QSizePolicy
)

from ...services.dataService import DataService
from ..utils.datetime_utils import date_to_qdate
from .planner_state import PlannerState
from .planner_day_view import PlannerDayView
from .planner_week_view import PlannerWeekView
from .planner_actions import PlannerActions



class PlannerWorkspace(QWidget):
    def __init__(self, parent: QWidget, ds: DataService, on_data_changed):
        super().__init__(parent)
        self._emit_enabled = False
        self.on_data_changed = None  # set via set_on_data_changed

        self.state = PlannerState(ds)
        self.state.reload()


        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ─────────────────────────────────────────────────────────────
        # Header / Controls bar (clean, modern)
        # ─────────────────────────────────────────────────────────────
        header = QWidget(self)
        header.setObjectName("HeaderBar")
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(12, 10, 12, 10)
        header_lay.setSpacing(10)
        root.addWidget(header)

        # Left: filters
        self.view_cb = QComboBox()
        self.view_cb.addItem("Tag", "day")
        self.view_cb.addItem("Wochen", "week")
        self.view_cb.setToolTip("Ansicht wechseln (Tag / Wochen)")
        self.view_cb.setFixedWidth(120)
        header_lay.addWidget(self.view_cb)

        self.day_date = QDateEdit()
        self.day_date.setCalendarPopup(True)
        self.day_date.setDate(QDate.currentDate())
        self.day_date.setToolTip("Datum für Tagansicht")
        self.day_date.setFixedWidth(150)
        header_lay.addWidget(self.day_date)

        self.week_from = QDateEdit()
        self.week_from.setCalendarPopup(True)
        self.week_from.setToolTip("Wochenbereich: Von")
        self.week_from.setFixedWidth(150)

        self.week_to = QDateEdit()
        self.week_to.setCalendarPopup(True)
        self.week_to.setToolTip("Wochenbereich: Bis")
        self.week_to.setFixedWidth(150)

        today = date.today()
        self.week_from.setDate(date_to_qdate(today - timedelta(days=28)))
        self.week_to.setDate(date_to_qdate(today + timedelta(days=28)))
        header_lay.addWidget(self.week_from)
        header_lay.addWidget(self.week_to)

        self.sem_cb = QComboBox()
        self.sem_cb.setToolTip("Semester filter")
        self.sem_cb.setMinimumWidth(220)
        header_lay.addWidget(self.sem_cb)

        self.room_cb = QComboBox()
        self.room_cb.setToolTip("Raum filter")
        self.room_cb.setMinimumWidth(220)
        header_lay.addWidget(self.room_cb)

        self.search_le = QLineEdit()
        self.search_le.setPlaceholderText("Suchen (LVA-ID / Text)…")
        self.search_le.setToolTip("Filtert Termine nach LVA-ID oder Text")
        self.search_le.setClearButtonEnabled(True)
        self.search_le.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_lay.addWidget(self.search_le, 1)

        # Right: actions
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Daten neu laden und Ansicht aktualisieren")
        header_lay.addWidget(self.refresh_btn)

        self.add_term_btn = QPushButton("Termin hinzufügen")
        self.add_term_btn.setObjectName("PrimaryButton")
        self.add_term_btn.setToolTip("Neuen Termin anlegen")
        header_lay.addWidget(self.add_term_btn)

        # ─────────────────────────────────────────────────────────────
        # Views
        # ─────────────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.day_table = QTableWidget(0, 0)
        self.week_table = QTableWidget(0, 0)
        self.day_table.setSortingEnabled(False)
        self.week_table.setSortingEnabled(False)
        self.day_table.setAlternatingRowColors(True)
        self.week_table.setAlternatingRowColors(True)
        self.stack.addWidget(self.day_table)
        self.stack.addWidget(self.week_table)

        # ─────────────────────────────────────────────────────────────
        # Info line (chip style)
        # ─────────────────────────────────────────────────────────────
        info = QHBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(8)
        root.addLayout(info)

        self.friday_lbl = QLabel("")
        self.friday_lbl.setObjectName("Chip")
        self.friday_lbl.setVisible(False)
        info.addWidget(self.friday_lbl)

        info.addStretch(1)

        self.conflict_lbl = QLabel("Konflikte: –")
        self.conflict_lbl.setObjectName("Chip")
        self.conflict_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info.addWidget(self.conflict_lbl)

        # ─────────────────────────────────────────────────────────────
        # Helpers
        # ─────────────────────────────────────────────────────────────
        self.actions = PlannerActions(self.state, self)

        self.day_view = PlannerDayView(
            state=self.state,
            day_table=self.day_table,
            day_date=self.day_date,
            room_cb=self.room_cb,
            sem_cb=self.sem_cb,
            friday_lbl=self.friday_lbl,
            conflict_lbl=self.conflict_lbl,
            edit_by_id_cb=self._edit_termin_by_id,
            current_filters_cb=self.current_filters,
        )
        self.week_view = PlannerWeekView(
            state=self.state,
            week_table=self.week_table,
            week_from=self.week_from,
            week_to=self.week_to,
            edit_by_id_cb=self._edit_termin_by_id,
        )

        # ─────────────────────────────────────────────────────────────
        # Signals + small UX improvements
        # ─────────────────────────────────────────────────────────────
        self.refresh_btn.clicked.connect(self.refresh)
        self.view_cb.currentIndexChanged.connect(self._on_view_changed)

        self.day_date.dateChanged.connect(lambda *_: self.refresh())
        self.week_from.dateChanged.connect(lambda *_: self.refresh())
        self.week_to.dateChanged.connect(lambda *_: self.refresh())
        self.sem_cb.currentIndexChanged.connect(lambda *_: self.refresh())
        self.room_cb.currentIndexChanged.connect(lambda *_: self.refresh())

        # Debounced search (feels much smoother on big datasets)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(180)
        self._search_timer.timeout.connect(self.refresh)
        self.search_le.textChanged.connect(lambda *_: self._search_timer.start())

        self.add_term_btn.clicked.connect(self.add_termin)

        # ---- Init
        self._init_default_dates()
        self._rebuild_filter_boxes()
        self._on_view_changed()  # also applies enabled/visible state
        self.refresh(emit=False)
        self._emit_enabled = True

    def _init_default_dates(self):
        if not self.state.termine:
            return
        min_d = min(t.datum for t in self.state.termine)
        max_d = max(t.datum for t in self.state.termine)
        self.day_date.setDate(date_to_qdate(min_d))
        self.week_from.setDate(date_to_qdate(min_d))
        self.week_to.setDate(date_to_qdate(max_d))

    def _rebuild_filter_boxes(self):
        current_sem = self.sem_cb.currentData() if self.sem_cb.count() else ""
        self.sem_cb.blockSignals(True)
        self.sem_cb.clear()
        self.sem_cb.addItem("Semester: alle", "")
        for s in self.state.semester:
            self.sem_cb.addItem(f"{s.id} – {s.name}", s.id)
        if current_sem:
            for i in range(self.sem_cb.count()):
                if self.sem_cb.itemData(i) == current_sem:
                    self.sem_cb.setCurrentIndex(i)
                    break
        self.sem_cb.blockSignals(False)

        current_room = self.room_cb.currentData() if self.room_cb.count() else ""
        self.room_cb.blockSignals(True)
        self.room_cb.clear()
        self.room_cb.addItem("Raum: alle", "")
        for r in self.state.raeume:
            self.room_cb.addItem(f"{r.id} – {r.name}", r.id)
        if current_room:
            for i in range(self.room_cb.count()):
                if self.room_cb.itemData(i) == current_room:
                    self.room_cb.setCurrentIndex(i)
                    break
        self.room_cb.blockSignals(False)

    def current_filters(self) -> Tuple[Optional[str], Optional[str], str]:
        sem = self.sem_cb.currentData() or None
        room = self.room_cb.currentData() or None
        q = (self.search_le.text() or "").strip().lower()
        return sem, room, q

    def refresh(self, emit: bool = True):
        self.state.reload()
        self._rebuild_filter_boxes()

        sem, room, q = self.current_filters()
        filtered = self.state.filtered_termine(semester_id=sem, raum_id=room, q=q)

        view = str(self.view_cb.currentData())
        if view == "day":
            self.stack.setCurrentWidget(self.day_table)
            self.day_view.refresh(filtered)
            # show friday chip if day_view sets it
            self.friday_lbl.setVisible(bool(self.friday_lbl.text()))
        else:
            self.stack.setCurrentWidget(self.week_table)
            self.friday_lbl.setText("")
            self.friday_lbl.setVisible(False)
            self.conflict_lbl.setText("Konflikte: –")
            self.week_view.refresh(filtered)

        if emit and self._emit_enabled and callable(self.on_data_changed):
            self.on_data_changed()

    def _on_view_changed(self):
        view = str(self.view_cb.currentData())
        is_day = (view == "day")

        # Modern UX: hide irrelevant date inputs
        self.day_date.setVisible(is_day)
        self.week_from.setVisible(not is_day)
        self.week_to.setVisible(not is_day)

        self.refresh()

    def add_termin(self):
        if self.actions.add_termin(default_qdate=self.day_date.date()):
            self.refresh()

    def _edit_termin_by_id(self, tid: str):
        if self.actions.edit_termin_by_id(tid):
            self.refresh()

    def set_on_data_changed(self, cb):
        self.on_data_changed = cb
