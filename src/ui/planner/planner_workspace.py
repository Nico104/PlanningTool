from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit, QLabel,
    QPushButton, QStackedWidget, QTableWidget
)

from ...services.dataService import DataService
from ..utils.datetime_utils import date_to_qdate
from .planner_state import PlannerState
from .planner_day_view import PlannerDayView
from .planner_week_view import PlannerWeekView
from .planner_actions import PlannerActions

from ..dragdrop.week_drop_table import WeekDropTable

from ..utils.widgets.tight_combobox import TightComboBox


class PlannerWorkspace(QWidget):
    def __init__(self, parent: QWidget, ds: DataService, on_data_changed, global_filter_dock=None):
        super().__init__(parent)
        self._emit_enabled = False
        self.on_data_changed = on_data_changed    # set via set_on_data_changed

        self.ds = ds  # NEW: behalten (falls du später direkt brauchst)

        self.state = PlannerState(ds)
        self.state.reload()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ─────────────────────────────────────────────────────────────
        # Header / Controls bar (clean, modern)
        # ─────────────────────────────────────────────────────────────
        # header = QWidget(self)
        # header.setObjectName("HeaderBar")
        # header_lay = QHBoxLayout(header)
        # header_lay.setContentsMargins(12, 10, 12, 10)
        # header_lay.setSpacing(10)
        # root.addWidget(header)

        # Left: view selector, navigation and date inputs are provided by
        # the GlobalFilterDock. If a global dock is passed, use its widgets
        # here so the planner behaves as if they were local.
    
        self.view_cb = global_filter_dock.view_cb
        self.prev_btn = global_filter_dock.prev_btn
        self.next_btn = global_filter_dock.next_btn
        self.day_date = global_filter_dock.day_date
        self.week_from = global_filter_dock.week_from
        

        # Note: global filters (Semester, LVA, Raum, Typ) are owned by MainWindow
        # and exposed via the GlobalFilterDock. PlannerWorkspace reads them via
        # `set_global_filter_state` / `current_filters` and does not own local
        # dropdowns for those filters.

        # Right: actions
        # self.refresh_btn = QPushButton("Refresh")
        # self.refresh_btn.setToolTip("Daten neu laden und Ansicht aktualisieren")
        # header_lay.addWidget(self.refresh_btn)

        # self.add_term_btn = QPushButton("Termin hinzufügen")
        # self.add_term_btn.setObjectName("PrimaryButton")
        # self.add_term_btn.setToolTip("Neuen Termin anlegen")
        # header_lay.addWidget(self.add_term_btn)

        # ─────────────────────────────────────────────────────────────
        # Views
        # ─────────────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.day_table = QTableWidget(0, 0)
        self.week_table = WeekDropTable(0, 0)
        self.day_table.setSortingEnabled(False)
        self.week_table.setSortingEnabled(False)
        self.day_table.setAlternatingRowColors(False)
        self.week_table.setAlternatingRowColors(False)
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
            friday_lbl=self.friday_lbl,
            conflict_lbl=self.conflict_lbl,
            edit_by_id_cb=self._edit_termin_by_id,
            current_filters_cb=self.current_filters,
        )
        self.week_view = PlannerWeekView(
            state=self.state,
            week_table=self.week_table,
            week_from=self.week_from,
            edit_by_id_cb=self._edit_termin_by_id,
            on_drop_cb=self._on_week_drop,
        )

        # ─────────────────────────────────────────────────────────────
        # Signals + small UX improvements
        # ─────────────────────────────────────────────────────────────
        # self.refresh_btn.clicked.connect(self.refresh)
        self.view_cb.currentIndexChanged.connect(self._on_view_changed)

        # NEW: nav buttons
        self.prev_btn.clicked.connect(lambda: self._shift_period(-1))
        self.next_btn.clicked.connect(lambda: self._shift_period(+1))

        # NOTE:
        # Planner-Filter/Navigation soll *nur* den Planner selbst beeinflussen.
        # Das Updaten der Docks/Terminliste (on_data_changed) passiert nur bei echten
        # Datenänderungen (Drop/Edit/Create/Delete) über reload_and_refresh_everything().
        self.day_date.dateChanged.connect(lambda *_: self.refresh(emit=False))
        self.week_from.dateChanged.connect(lambda *_: self.refresh(emit=False))

        # self.add_term_btn.clicked.connect(self.add_termin)

        # ---- Init
        self._init_default_dates()
        # filter boxes are provided globally; planner no longer builds local ones
        self._on_view_changed()  # also applies enabled/visible state
        self.refresh(emit=False)
        self._emit_enabled = True
        
        # --- give QSS hooks ---
        self.day_date.setObjectName("DateEdit")
        self.week_from.setObjectName("DateEdit")

        self.view_cb.setObjectName("HeaderCombo")

        # self.refresh_btn.setObjectName("SecondaryButton")

    # ─────────────────────────────────────────────────────────────
    # NEW: single place to force full update
    # ─────────────────────────────────────────────────────────────
    def reload_and_refresh_everything(self) -> None:
        """
        Use after any data change (drop/edit/create/delete).
        Reloads state (so names/LVA/room changes show up),
        refreshes current view, and notifies main window to refresh docks.
        """
        self.refresh(emit=True)

    # ─────────────────────────────────────────────────────────────
    # navigation logic
    # ─────────────────────────────────────────────────────────────
    def _qdate_to_pydate(self, qd: QDate) -> date:
        return date(qd.year(), qd.month(), qd.day())

    def _align_to_monday(self, d: date) -> date:
        return d - timedelta(days=d.weekday())

    def _shift_period(self, direction: int):
        view = str(self.view_cb.currentData())
        if view == "day":
            d = self._qdate_to_pydate(self.day_date.date()) + timedelta(days=direction)
            self.day_date.setDate(date_to_qdate(d))
        else:
            wf = self._qdate_to_pydate(self.week_from.date())
            wf = self._align_to_monday(wf) + timedelta(days=7 * direction)
            self.week_from.setDate(date_to_qdate(wf))

        # navigation should not refresh external docks/terminliste
        self.refresh(emit=False)

    def _init_default_dates(self):
        if not self.state.termine:
            return

        # only Termine that actually have a date
        dated = [t.datum for t in self.state.termine if t.datum is not None]
        if not dated:
            # fallback: today (or keep whatever is already set)
            self.day_date.setDate(QDate.currentDate())
            self.week_from.setDate(date_to_qdate(self._align_to_monday(date.today())))
            return

        min_d = min(dated)
        self.day_date.setDate(date_to_qdate(min_d))
        self.week_from.setDate(date_to_qdate(self._align_to_monday(min_d)))


    def _rebuild_filter_boxes(self):
        # Planner no longer owns local filter comboboxes; global dock provides
        # filter dropdowns. Keep this method lightweight so refresh() can call
        # it to ensure state is loaded.
        return

    def current_filters(self) -> Tuple[Optional[str], Optional[str], str, Optional[str]]:
        # Prefer an internal cached global filter if available, otherwise
        # return defaults (no filters).
        gf = getattr(self, "_global_filter", None)
        if gf is None:
            return None, None, "", None
        return gf.semester_id, gf.raum_id, (str(gf.lva_id).strip().lower() if gf.lva_id else ""), gf.typ

    def refresh(self, emit: bool = True):
        # Reload EVERYTHING every refresh so UI always matches saved JSON state
        self.state.reload()
        self._rebuild_filter_boxes()

        sem, room, q, typ = self.current_filters()
        filtered = self.state.filtered_termine(semester_id=sem, raum_id=room, q=q)
        if typ:
            filtered = [t for t in filtered if getattr(t, "typ", None) == typ]

        view = str(self.view_cb.currentData())
        if view == "day":
            self.stack.setCurrentWidget(self.day_table)
            self.day_view.refresh(filtered)
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

        self.day_date.setVisible(is_day)
        self.week_from.setVisible(not is_day)

        if not is_day:
            wf = self._qdate_to_pydate(self.week_from.date())
            self.week_from.setDate(date_to_qdate(self._align_to_monday(wf)))

        # view switching should not refresh external docks/terminliste
        self.refresh(emit=False)

    def add_termin(self):
        if self.actions.add_termin(default_qdate=self.day_date.date()):
            self.reload_and_refresh_everything()  # NEW

    def _edit_termin_by_id(self, tid: str):
        if self.actions.edit_termin_by_id(tid):
            self.reload_and_refresh_everything()  # NEW

    def set_on_data_changed(self, cb):
        self.on_data_changed = cb

    def set_global_filter_state(self, fs) -> None:
        """Apply a read-only sync from global FilterState to this workspace's filter controls.

        This updates the UI controls to reflect the global filters but does NOT
        modify the central FilterState (MainWindow owns it) and does not emit
        data-changed events to other docks.
        """
        # cache the global filter for read-only use by this workspace and
        # refresh the view. Planner does not mutate central filter state.
        if fs is None:
            self._global_filter = None
        else:
            self._global_filter = fs

        self.refresh(emit=False)

    def _on_week_drop(self, termin_id, new_date, new_start):
        # IMPORTANT: move_termin MUST persist changes.
        if self.actions.move_termin(termin_id, new_date=new_date, new_start=new_start):
            self.reload_and_refresh_everything()  # NEW
