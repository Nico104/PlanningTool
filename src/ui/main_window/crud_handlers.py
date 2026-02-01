from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QDialog, QMessageBox

from ..dialog import LVADialog, RaumDialog, SemesterDialog


class CrudHandlers:
    def __init__(self, mw):
        self.mw = mw

    # ---------- termine edit (delegiert an planner)
    def edit_termin_by_id(self, tid: str) -> None:
        if hasattr(self.mw.planner, "_edit_termin_by_id"):
            self.mw.planner._edit_termin_by_id(tid)
        else:
            if self.mw.planner.actions.edit_termin_by_id(tid):
                self.mw.planner.refresh()

    # ---------- CRUD LVAs
    def add_lva(self) -> None:
        dlg = LVADialog(self.mw, None)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return

        lvas = self.mw.ds.load_lvas()
        if any(l.id == dlg.result.id for l in lvas):
            QMessageBox.warning(self.mw, "Fehler", "Diese LVA-ID existiert bereits.")
            return

        lvas.append(dlg.result)
        self.mw.ds.save_lvas(lvas)
        self.mw.planner.refresh()

    def edit_lva(self) -> None:
        cid = self.mw.lva_dock.selected_id()
        if not cid:
            return

        lvas = self.mw.ds.load_lvas()
        cur = next((l for l in lvas if l.id == cid), None)
        if not cur:
            return

        dlg = LVADialog(self.mw, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return

        if dlg.result.id != cid and any(l.id == dlg.result.id for l in lvas):
            QMessageBox.warning(self.mw, "Fehler", "Neue LVA-ID existiert bereits.")
            return

        lvas = [dlg.result if l.id == cid else l for l in lvas]
        self.mw.ds.save_lvas(lvas)

        if dlg.result.id != cid:
            terms = self.mw.ds.load_termine()
            terms = [replace(t, lva_id=dlg.result.id) if t.lva_id == cid else t for t in terms]
            self.mw.ds.save_termine(terms)

        self.mw.planner.refresh()

    def del_lva(self) -> None:
        cid = self.mw.lva_dock.selected_id()
        if not cid:
            return

        if QMessageBox.question(
            self.mw,
            "Löschen",
            f"LVA {cid} wirklich löschen? (Termine werden auch gelöscht)"
        ) != QMessageBox.Yes:
            return

        lvas = [l for l in self.mw.ds.load_lvas() if l.id != cid]
        terms = [t for t in self.mw.ds.load_termine() if t.lva_id != cid]
        self.mw.ds.save_lvas(lvas)
        self.mw.ds.save_termine(terms)
        self.mw.planner.refresh()

    # ---------- CRUD Rooms
    def add_room(self) -> None:
        dlg = RaumDialog(self.mw, None)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return

        rooms = self.mw.ds.load_raeume()
        if any(r.id == dlg.result.id for r in rooms):
            QMessageBox.warning(self.mw, "Fehler", "Diese Raum-ID existiert bereits.")
            return

        rooms.append(dlg.result)
        self.mw.ds.save_raeume(rooms)
        self.mw.planner.refresh()

    def edit_room(self) -> None:
        rid = self.mw.room_dock.selected_id()
        if not rid:
            return

        rooms = self.mw.ds.load_raeume()
        cur = next((r for r in rooms if r.id == rid), None)
        if not cur:
            return

        dlg = RaumDialog(self.mw, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return

        if dlg.result.id != rid and any(r.id == dlg.result.id for r in rooms):
            QMessageBox.warning(self.mw, "Fehler", "Neue Raum-ID existiert bereits.")
            return

        rooms = [dlg.result if r.id == rid else r for r in rooms]
        self.mw.ds.save_raeume(rooms)

        if dlg.result.id != rid:
            terms = self.mw.ds.load_termine()
            terms = [replace(t, raum_id=dlg.result.id) if t.raum_id == rid else t for t in terms]
            self.mw.ds.save_termine(terms)

        self.mw.planner.refresh()

    def del_room(self) -> None:
        rid = self.mw.room_dock.selected_id()
        if not rid:
            return

        if QMessageBox.question(
            self.mw,
            "Löschen",
            f"Raum {rid} wirklich löschen? (Termine werden auch gelöscht)"
        ) != QMessageBox.Yes:
            return

        rooms = [r for r in self.mw.ds.load_raeume() if r.id != rid]
        terms = [t for t in self.mw.ds.load_termine() if t.raum_id != rid]
        self.mw.ds.save_raeume(rooms)
        self.mw.ds.save_termine(terms)
        self.mw.planner.refresh()

    # ---------- CRUD Semester
    def add_semester(self) -> None:
        dlg = SemesterDialog(self.mw, None)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return

        sems = self.mw.ds.load_semester()
        if any(s.id == dlg.result.id for s in sems):
            QMessageBox.warning(self.mw, "Fehler", "Diese Semester-ID existiert bereits.")
            return

        sems.append(dlg.result)
        self.mw.ds.save_semester(sems)
        self.mw.planner.refresh()

    def edit_semester(self) -> None:
        sid = self.mw.sem_dock.selected_id()
        if not sid:
            return

        sems = self.mw.ds.load_semester()
        cur = next((s for s in sems if s.id == sid), None)
        if not cur:
            return

        dlg = SemesterDialog(self.mw, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return

        if dlg.result.id != sid and any(s.id == dlg.result.id for s in sems):
            QMessageBox.warning(self.mw, "Fehler", "Neue Semester-ID existiert bereits.")
            return

        sems = [dlg.result if s.id == sid else s for s in sems]
        self.mw.ds.save_semester(sems)

        if dlg.result.id != sid:
            terms = self.mw.ds.load_termine()
            terms = [replace(t, semester_id=dlg.result.id) if t.semester_id == sid else t for t in terms]
            self.mw.ds.save_termine(terms)

        self.mw.planner.refresh()

    def del_semester(self) -> None:
        sid = self.mw.sem_dock.selected_id()
        if not sid:
            return

        if QMessageBox.question(
            self.mw,
            "Löschen",
            f"Semester {sid} wirklich löschen? (Termine werden auch gelöscht)"
        ) != QMessageBox.Yes:
            return

        sems = [s for s in self.mw.ds.load_semester() if s.id != sid]
        terms = [t for t in self.mw.ds.load_termine() if t.semester_id != sid]
        self.mw.ds.save_semester(sems)
        self.mw.ds.save_termine(terms)
        self.mw.planner.refresh()
