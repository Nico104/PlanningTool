from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget

from src.services.dataService import DataService

from ..docks import TermineDock, DataEditorDock
from ..docks.global_filter_dock import GlobalFilterDock
from ...models.filter_state import FilterState
from .actions import build_menus, attach_settings_handler
from .crud_handlers import CrudHandlers
from .layout_manager import LayoutManager
from src.ui.planner.planner_workspace import PlannerWorkspace


class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path):
        super().__init__()
        self.setWindowTitle("Planungstool")
        self.data_dir = data_dir
        self.ds = DataService(data_dir)
        

        # self.setCentralWidget(QWidget())

        # Menüs + Settings Handler
        attach_settings_handler(self)  # setzt self.open_settings
        build_menus(self)

        # initial (shared) filter state owned by MainWindow
        self.filter_state = FilterState()

        # Dock options
        self._setup_dock_options()

        # Docks
        self._setup_docks()

        # Handler/Manager
        self.crud = CrudHandlers(self)
        self.layout_mgr = LayoutManager(self)

        # Signals
        self._wire_signals()

        # initial refresh
        self.refresh_docks()
        self.planner.refresh(emit=True)
        self.layout_mgr.init_default()

    # ---------- Setup

    def _setup_dock_options(self) -> None:
        self.setDockOptions(
            QMainWindow.AllowTabbedDocks |
            QMainWindow.AllowNestedDocks |
            QMainWindow.AnimatedDocks |
            QMainWindow.GroupedDragging
        )


        
    def _setup_docks(self) -> None:
        # Global filters dock (shared) — create first so planner can use its widgets
        self.global_filter_dock = GlobalFilterDock(self)
        self.global_filter_dock.setObjectName("dock_global_filters")
        self.addDockWidget(Qt.TopDockWidgetArea, self.global_filter_dock)

        # Planner (uses widgets from global_filter_dock)
        self.planner = PlannerWorkspace(self, self.ds, on_data_changed=self.refresh_docks, global_filter_dock=self.global_filter_dock)
        self.setCentralWidget(self.planner)
        self.centralWidget().setMinimumWidth(self.width() * 0.75)

        # Termine (bleibt)
        self.termine_dock = TermineDock(self)
        self.termine_dock.setObjectName("dock_termine")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.termine_dock)
        self.termine_dock.setMinimumWidth(self.width() * 0.35)
        self.resizeDocks([self.termine_dock], [self.width() * 0.75], Qt.Horizontal)

        # Data Editor (LVA+Räume+Semester+Freie Tage)
        self.data_editor_dock = DataEditorDock(self, ds=self.ds, data_dir=self.data_dir, on_data_changed=self.refresh_docks)
        self.data_editor_dock.setObjectName("dock_data_editor")
        # self.addDockWidget(Qt.DockWidgetArea, self.data_editor_dock)

        self.tabifyDockWidget(self.termine_dock, self.data_editor_dock)
        self.termine_dock.raise_()

    def _wire_signals(self) -> None:
        # Termine
        self.termine_dock.termin_double_clicked.connect(self.crud.edit_termin_by_id)
        
        self.termine_dock.termin_unassign_requested.connect(self._on_unassign_termin)

        # LVA dock (nur Kontextmenü)
        # self.lva_dock.edit_clicked.connect(self.crud.edit_lva)
        # self.lva_dock.delete_clicked.connect(self.crud.del_lva)

        # Room dock
        # self.room_dock.edit_clicked.connect(self.crud.edit_room)
        # self.room_dock.delete_clicked.connect(self.crud.del_room)

        # Semester dock
        # self.sem_dock.edit_clicked.connect(self.crud.edit_semester)
        # self.sem_dock.delete_clicked.connect(self.crud.del_semester)
        # Global filters
        self.global_filter_dock.filtersChanged.connect(self._on_global_filters_changed)

        # Wire view/navigation/date widgets to planner behavior
        # Planner connects to these widgets internally, but ensure navigation
        # buttons call planner navigation as well.
        try:
            self.global_filter_dock.prev_btn.clicked.connect(lambda: self.planner._shift_period(-1))
            self.global_filter_dock.next_btn.clicked.connect(lambda: self.planner._shift_period(+1))
            self.global_filter_dock.view_cb.currentIndexChanged.connect(lambda *_: self.planner._on_view_changed())
            self.global_filter_dock.day_date.dateChanged.connect(lambda *_: self.planner.refresh(emit=False))
            self.global_filter_dock.week_from.dateChanged.connect(lambda *_: self.planner.refresh(emit=False))
        except Exception:
            pass

    def _on_global_filters_changed(self, fs: FilterState) -> None:
        """Update the shared FilterState and refresh views that depend on it.

        This method owns updating the central FilterState (MainWindow-owned)
        and then triggers refreshes on PlannerWorkspace and TermineDock.
        """
        # update central state
        self.filter_state = fs

        # Let planner reflect the UI state (read-only sync) and refresh
        try:
            self.planner.set_global_filter_state(fs)
        except Exception:
            # planner may not implement the sync method yet; ignore
            pass

        # Recompute terms using global filters and update TermineDock
        sem = fs.semester_id
        room = fs.raum_id
        q = (str(fs.lva_id).strip().lower() if fs.lva_id else "")
        terms = self.planner.state.filtered_termine(semester_id=sem, raum_id=room, q=q)
        # apply typ filtering centrally as well
        if fs.typ:
            terms = [t for t in terms if getattr(t, "typ", None) == fs.typ]

        # let the TermineDock know about global filters (sync its UI) if it supports it
        try:
            self.termine_dock.set_global_filter_state(fs)
        except Exception:
            pass

        self.termine_dock.set_rows(terms, self.planner.state.lva_map, self.planner.state.raum_map)

    # ---------- refresh
    
    def _on_unassign_termin(self, tid: str):
        if self.planner.actions.unassign_termin(tid):
            self.refresh_docks()
            self.planner.refresh()

        
    def refresh_docks(self) -> None:
        # prefer central filter_state if present, otherwise fall back to planner's local filters
        fs = getattr(self, "filter_state", None)
        if fs:
            sem = fs.semester_id
            room = fs.raum_id
            q = (str(fs.lva_id).strip().lower() if fs.lva_id else "")
            typ = fs.typ
        else:
            sem, room, q, typ = self.planner.current_filters()

        terms = self.planner.state.filtered_termine(semester_id=sem, raum_id=room, q=q)
        if typ:
            terms = [t for t in terms if getattr(t, "typ", None) == typ]

        # keep global filter dock in sync with available data
        try:
            lva_list = getattr(self.planner.state, "lvas", None) or []
            typ_list = [t.typ for t in getattr(self.planner.state, "termine", []) if getattr(t, "typ", None)]
            self.global_filter_dock.rebuild(self.planner.state.semester, lva_list, self.planner.state.raeume, typ_list=typ_list, current=self.filter_state)
        except Exception:
            pass

        # apply central typ filter if present
        if fs and getattr(fs, "typ", None):
            terms = [t for t in terms if getattr(t, "typ", None) == fs.typ]

        self.termine_dock.set_rows(terms, self.planner.state.lva_map, self.planner.state.raum_map)

        # Data editor dock refresh
        self.data_editor_dock.refresh_all()

