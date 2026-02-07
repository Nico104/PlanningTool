from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QDialog, QMainWindow, QMessageBox

from src.services.data_service import DataService

from src.ui.docks.termine_dock import TermineDock
from src.ui.docks.data_editor_dock import DataEditorDock
from src.ui.docks.conflicts_dock import ConflictsDock
from src.ui.docks.global_filter_dock import GlobalFilterDock
from src.core.states import FilterState
from ...utils.crud_handlers import CrudHandlers
from .layout_manager import LayoutManager
from src.ui.planner.workspace import PlannerWorkspace


class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path):
        super().__init__()
        self.setWindowTitle("Planungstool")
        self.data_dir = data_dir
        self.ds = DataService(data_dir)
        

        # self.setCentralWidget(QWidget())

        # Menüs + Settings Handler
        self._build_menus()

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
        self.refresh_everything()
        self.layout_mgr.init_default()

    # ---------- Setup

    def open_settings(self) -> None:
        from ...dialogs import SettingsDialog  # local import to avoid cycles

        cur = self.ds.load_settings()
        dlg = SettingsDialog(self, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result_settings:
            return

        s = cur
        s.update(dlg.result_settings)
        self.ds.save_settings(s)

        QMessageBox.information(self, "Settings", "Gespeichert.")
        self.refresh_everything()

    def _build_menus(self) -> None:
        mb = self.menuBar()

        file_menu = mb.addMenu("Datei")
        self.view_menu = mb.addMenu("Ansicht")
        tools_menu = mb.addMenu("Tools")

        self.act_settings = QAction("Settings…", self)
        self.act_settings.triggered.connect(self.open_settings)

        self.act_refresh = QAction("Aktualisieren", self)
        self.act_refresh.triggered.connect(self.refresh_everything)

        tools_menu.addAction(self.act_settings)
        file_menu.addAction(self.act_refresh)

        self.layout_menu = self.view_menu.addMenu("Layout")

        self.layout_group = QActionGroup(self)
        self.layout_group.setExclusive(True)

        self.act_save_layout = QAction("Aktuelles Layout speichern…", self)
        self.act_reset_layouts = QAction("Layouts zurücksetzen", self)

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

        # Conflicts dock (right side)
        self.conflicts_dock = ConflictsDock(self)
        self.conflicts_dock.setObjectName("dock_conflicts")
        self.addDockWidget(Qt.RightDockWidgetArea, self.conflicts_dock)

    def _wire_signals(self) -> None:
        # Termine
        self.termine_dock.termin_double_clicked.connect(self.crud.edit_termin_by_id)
        self.termine_dock.termin_delete_clicked.connect(self.crud.del_termin_by_id)
        
        self.termine_dock.termin_unassign_requested.connect(self._on_unassign_termin)

        # Conflicts
        self.conflicts_dock.conflict_items_highlight.connect(self.planner.highlight_termine)

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
        self.global_filter_dock.navPrev.connect(self._on_nav_prev)
        self.global_filter_dock.navNext.connect(self._on_nav_next)
        self.global_filter_dock.viewChanged.connect(self._on_view_changed)
        self.global_filter_dock.dayDateChanged.connect(self._on_day_date_changed)
        self.global_filter_dock.weekFromChanged.connect(self._on_week_from_changed)

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

        terms = self._compute_filtered_termine(fs)

        self.termine_dock.set_rows(terms, self.planner.state.lva_map, self.planner.state.raum_map)

    # ---------- refresh
    
    def _on_unassign_termin(self, tid: str):
        if self.planner.crud.unassign_termin(tid):
            self.refresh_everything()

    def _on_nav_prev(self) -> None:
        self.planner._shift_period(-1)

    def _on_nav_next(self) -> None:
        self.planner._shift_period(+1)

    def _on_view_changed(self, _view: str) -> None:
        self.planner._on_view_changed()

    def _on_day_date_changed(self, _date) -> None:
        self.planner.refresh(emit=False)

    def _on_week_from_changed(self, _date) -> None:
        self.planner.refresh(emit=False)

    def refresh_everything(self) -> None:
        self.planner.refresh(emit=True)

    def refresh_conflicts(self) -> None:
        """Refresh the conflicts dock with current Termine."""
        # Initialize detector if not already done
        self.conflicts_dock.initialize_detector(
            self.planner.state.lva_map,
            self.planner.state.raum_map,
            self.planner.state.semester
        )
        
        # Check all termine for conflicts (not filtered)
        self.conflicts_dock.refresh_conflicts(self.planner.state.termine)

        
    def refresh_docks(self) -> None:
        # prefer central filter_state if present, otherwise fall back to planner's local filters
        fs = getattr(self, "filter_state", None)
        terms = self._compute_filtered_termine(fs)

        # keep global filter dock in sync with available data
        try:
            lva_list = getattr(self.planner.state, "lvas", None) or []
            typ_list = [t.typ for t in getattr(self.planner.state, "termine", []) if getattr(t, "typ", None)]
            self.global_filter_dock.refresh_filter_options(
                self.planner.state.semester,
                lva_list,
                self.planner.state.raeume,
                typ_list=typ_list,
                current=self.filter_state,
            )
        except Exception:
            pass

        self.termine_dock.set_rows(terms, self.planner.state.lva_map, self.planner.state.raum_map)

        # Data editor dock refresh
        self.data_editor_dock.refresh_all()

        # Refresh conflicts (use all termine, not filtered)
        self.refresh_conflicts()

    def _compute_filtered_termine(self, fs: FilterState | None):
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
        return terms

