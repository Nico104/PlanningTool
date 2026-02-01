from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget

from src.services.dataService import DataService

from ..docks import TermineDock, LVADock, RoomDock, SemesterDock
from .actions import build_menus, attach_settings_handler
from .crud_handlers import CrudHandlers
from .layout_manager import LayoutManager
from src.ui.planner.planner_workspace import PlannerWorkspace


class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path):
        super().__init__()
        self.setWindowTitle("Planungstool")
        self.ds = DataService(data_dir)

        # self.setCentralWidget(QWidget())

        # Menüs + Settings Handler
        attach_settings_handler(self)  # setzt self.open_settings
        build_menus(self)

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
        # Planner
        # self.planner = PlannerDock(self, self.ds, on_data_changed=self.refresh_docks)
        # self.planner.setObjectName("dock_planner")
        # self.addDockWidget(Qt.RightDockWidgetArea, self.planner)
        self.planner = PlannerWorkspace(self, self.ds, on_data_changed=self.refresh_docks)
        self.setCentralWidget(self.planner)

        # Left side tabbed docks
        self.lva_dock = LVADock(self)
        self.lva_dock.setObjectName("dock_lvas")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.lva_dock)

        self.termine_dock = TermineDock(self)
        self.termine_dock.setObjectName("dock_termine")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.termine_dock)
        self.tabifyDockWidget(self.lva_dock, self.termine_dock)

        self.room_dock = RoomDock(self)
        self.room_dock.setObjectName("dock_rooms")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.room_dock)
        self.tabifyDockWidget(self.lva_dock, self.room_dock)

        self.sem_dock = SemesterDock(self)
        self.sem_dock.setObjectName("dock_semester")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sem_dock)
        self.tabifyDockWidget(self.lva_dock, self.sem_dock)

        self.lva_dock.raise_()  # default tab

    def _wire_signals(self) -> None:
        # Termine
        self.termine_dock.termin_double_clicked.connect(self.crud.edit_termin_by_id)

        # LVA dock (nur Kontextmenü)
        self.lva_dock.edit_clicked.connect(self.crud.edit_lva)
        self.lva_dock.delete_clicked.connect(self.crud.del_lva)

        # Room dock
        self.room_dock.edit_clicked.connect(self.crud.edit_room)
        self.room_dock.delete_clicked.connect(self.crud.del_room)

        # Semester dock
        self.sem_dock.edit_clicked.connect(self.crud.edit_semester)
        self.sem_dock.delete_clicked.connect(self.crud.del_semester)
    # ---------- refresh

    def refresh_docks(self) -> None:
        sem, room, q = self.planner.current_filters()
        terms = self.planner.state.filtered_termine(semester_id=sem, raum_id=room, q=q)

        self.termine_dock.set_rows(terms, self.planner.state.lva_map, self.planner.state.raum_map)
        self.lva_dock.set_rows(self.ds.load_lvas())
        self.room_dock.set_rows(self.ds.load_raeume())
        self.sem_dock.set_rows(self.ds.load_semester())
