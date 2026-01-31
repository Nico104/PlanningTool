from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QWidget
from PySide6.QtGui import QAction

from src.services.dataService import DataService
from src.ui.planner.planner_workspace import PlannerWorkspace


from .docks import TermineDock, LVADock, RoomDock, SemesterDock, PlannerDock
from .dialog import LVADialog, RaumDialog, SemesterDialog, SettingsDialog



class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path):
        super().__init__()
        self.setWindowTitle("Planungstool")
        self.ds = DataService(data_dir)

        self.setCentralWidget(QWidget())    

        self._build_menu_and_toolbar()

        self.setDockOptions(
            QMainWindow.AllowTabbedDocks |
            QMainWindow.AllowNestedDocks |
            QMainWindow.AnimatedDocks |
            QMainWindow.GroupedDragging
        )

        # Docks
        self.planner = PlannerDock(self, self.ds, on_data_changed=self.refresh_docks)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.planner)
        


        self.lva_dock = LVADock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.lva_dock)

        self.termine_dock = TermineDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.termine_dock)
        self.tabifyDockWidget(self.lva_dock, self.termine_dock)

        self.room_dock = RoomDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.room_dock)
        self.tabifyDockWidget(self.lva_dock, self.room_dock)

        self.sem_dock = SemesterDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.sem_dock)
        self.tabifyDockWidget(self.lva_dock, self.sem_dock)
        
        # Wire dock signals
        self.termine_dock.termin_double_clicked.connect(self._edit_termin_by_id)

        self.lva_dock.add_clicked.connect(self.add_lva)
        self.lva_dock.edit_clicked.connect(self.edit_lva)
        self.lva_dock.delete_clicked.connect(self.del_lva)

        self.room_dock.add_clicked.connect(self.add_room)
        self.room_dock.edit_clicked.connect(self.edit_room)
        self.room_dock.delete_clicked.connect(self.del_room)

        self.sem_dock.add_clicked.connect(self.add_semester)
        self.sem_dock.edit_clicked.connect(self.edit_semester)
        self.sem_dock.delete_clicked.connect(self.del_semester)


        # initial
        self.refresh_docks()
        self.planner.refresh(emit=True)

    # ---------- refresh

    def refresh_docks(self):
        # Termine aus dem Planner-State (refactor-kompatibel)
        sem, room, q = self.planner.current_filters()
        terms = self.planner.state.filtered_termine(semester_id=sem, raum_id=room, q=q)

        self.termine_dock.set_rows(terms, self.planner.state.lva_map, self.planner.state.raum_map)
        self.lva_dock.set_rows(self.ds.load_lvas())
        self.room_dock.set_rows(self.ds.load_raeume())
        self.sem_dock.set_rows(self.ds.load_semester())


    # ---------- termine edit (delegiert an planner)

    def _edit_termin_by_id(self, tid: str):
        # nutzt vorhandene Planner-Methode
        if hasattr(self.planner, "_edit_termin_by_id"):
            self.planner._edit_termin_by_id(tid)
        else:
            # fallback, falls du sie mal umbenennst
            if self.planner.actions.edit_termin_by_id(tid):
                self.planner.refresh()

    # ---------- CRUD LVAs

    def add_lva(self):
        dlg = LVADialog(self, None)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        lvas = self.ds.load_lvas()
        if any(l.id == dlg.result.id for l in lvas):
            QMessageBox.warning(self, "Fehler", "Diese LVA-ID existiert bereits.")
            return
        lvas.append(dlg.result)
        self.ds.save_lvas(lvas)
        self.planner.refresh()

    def edit_lva(self):
        cid = self.lva_dock.selected_id()
        if not cid:
            return
        lvas = self.ds.load_lvas()
        cur = next((l for l in lvas if l.id == cid), None)
        if not cur:
            return
        dlg = LVADialog(self, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        if dlg.result.id != cid and any(l.id == dlg.result.id for l in lvas):
            QMessageBox.warning(self, "Fehler", "Neue LVA-ID existiert bereits.")
            return
        lvas = [dlg.result if l.id == cid else l for l in lvas]
        self.ds.save_lvas(lvas)
        if dlg.result.id != cid:
            terms = self.ds.load_termine()
            terms = [replace(t, lva_id=dlg.result.id) if t.lva_id == cid else t for t in terms]
            self.ds.save_termine(terms)
        self.planner.refresh()

    def del_lva(self):
        cid = self.lva_dock.selected_id()
        if not cid:
            return
        if QMessageBox.question(self, "Löschen", f"LVA {cid} wirklich löschen? (Termine werden auch gelöscht)") != QMessageBox.Yes:
            return
        lvas = [l for l in self.ds.load_lvas() if l.id != cid]
        terms = [t for t in self.ds.load_termine() if t.lva_id != cid]
        self.ds.save_lvas(lvas)
        self.ds.save_termine(terms)
        self.planner.refresh()

    # ---------- CRUD Rooms

    def add_room(self):
        dlg = RaumDialog(self, None)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        rooms = self.ds.load_raeume()
        if any(r.id == dlg.result.id for r in rooms):
            QMessageBox.warning(self, "Fehler", "Diese Raum-ID existiert bereits.")
            return
        rooms.append(dlg.result)
        self.ds.save_raeume(rooms)
        self.planner.refresh()

    def edit_room(self):
        rid = self.room_dock.selected_id()
        if not rid:
            return
        rooms = self.ds.load_raeume()
        cur = next((r for r in rooms if r.id == rid), None)
        if not cur:
            return
        dlg = RaumDialog(self, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        if dlg.result.id != rid and any(r.id == dlg.result.id for r in rooms):
            QMessageBox.warning(self, "Fehler", "Neue Raum-ID existiert bereits.")
            return
        rooms = [dlg.result if r.id == rid else r for r in rooms]
        self.ds.save_raeume(rooms)
        if dlg.result.id != rid:
            terms = self.ds.load_termine()
            terms = [replace(t, raum_id=dlg.result.id) if t.raum_id == rid else t for t in terms]
            self.ds.save_termine(terms)
        self.planner.refresh()

    def del_room(self):
        rid = self.room_dock.selected_id()
        if not rid:
            return
        if QMessageBox.question(self, "Löschen", f"Raum {rid} wirklich löschen? (Termine werden auch gelöscht)") != QMessageBox.Yes:
            return
        rooms = [r for r in self.ds.load_raeume() if r.id != rid]
        terms = [t for t in self.ds.load_termine() if t.raum_id != rid]
        self.ds.save_raeume(rooms)
        self.ds.save_termine(terms)
        self.planner.refresh()

    # ---------- CRUD Semester

    def add_semester(self):
        dlg = SemesterDialog(self, None)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        sems = self.ds.load_semester()
        if any(s.id == dlg.result.id for s in sems):
            QMessageBox.warning(self, "Fehler", "Diese Semester-ID existiert bereits.")
            return
        sems.append(dlg.result)
        self.ds.save_semester(sems)
        self.planner.refresh()

    def edit_semester(self):
        sid = self.sem_dock.selected_id()
        if not sid:
            return
        sems = self.ds.load_semester()
        cur = next((s for s in sems if s.id == sid), None)
        if not cur:
            return
        dlg = SemesterDialog(self, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return
        if dlg.result.id != sid and any(s.id == dlg.result.id for s in sems):
            QMessageBox.warning(self, "Fehler", "Neue Semester-ID existiert bereits.")
            return
        sems = [dlg.result if s.id == sid else s for s in sems]
        self.ds.save_semester(sems)
        if dlg.result.id != sid:
            terms = self.ds.load_termine()
            terms = [replace(t, semester_id=dlg.result.id) if t.semester_id == sid else t for t in terms]
            self.ds.save_termine(terms)
        self.planner.refresh()

    def del_semester(self):
        sid = self.sem_dock.selected_id()
        if not sid:
            return
        if QMessageBox.question(self, "Löschen", f"Semester {sid} wirklich löschen? (Termine werden auch gelöscht)") != QMessageBox.Yes:
            return
        sems = [s for s in self.ds.load_semester() if s.id != sid]
        terms = [t for t in self.ds.load_termine() if t.semester_id != sid]
        self.ds.save_semester(sems)
        self.ds.save_termine(terms)
        self.planner.refresh()
        
    def _build_menu_and_toolbar(self):
        # ---- Menüleiste
        mb = self.menuBar()

        file_menu = mb.addMenu("Datei")
        view_menu = mb.addMenu("Ansicht")
        tools_menu = mb.addMenu("Tools")

        # Actions
        self.act_settings = QAction("Settings…", self)
        self.act_settings.triggered.connect(self.open_settings)

        self.act_refresh = QAction("Aktualisieren", self)
        self.act_refresh.triggered.connect(lambda: self.planner.refresh())

        tools_menu.addAction(self.act_settings)
        file_menu.addAction(self.act_refresh)
        
    def open_settings(self):
        cur = self.ds.load_settings()
        dlg = SettingsDialog(self, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result_settings:
            return

        s = cur
        s.update(dlg.result_settings)
        self.ds.save_settings(s)
        QMessageBox.information(self, "Settings", "Gespeichert.")
        self.planner.refresh()




def run_gui():
    app = QApplication([])
    w = MainWindow(Path("data"))
    w.resize(1500, 900)
    w.show()
    app.exec()
