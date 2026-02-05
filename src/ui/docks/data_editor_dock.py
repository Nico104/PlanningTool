import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QTableWidget, QTableWidgetItem, QMenu, QMessageBox
)

from ...core.models import Lehrveranstaltung, Raum, Semester, Termin
from ..dialogs.lva_dialog import LVADialog
from ..dialogs.raum_dialog import RaumDialog
from ..dialogs.semester_dialog import SemesterDialog
from ..dialogs.freie_tage_dialog import FreieTageDialog
from ..utils.datetime_utils import fmt_date, fmt_time

from ..dialogs.termin_dialog import TerminDialog


# --------- kleine Helpers ---------

def _it(text: str) -> QTableWidgetItem:
    it = QTableWidgetItem(text)
    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
    return it


def _selected_id(table: QTableWidget) -> Optional[str]:
    row = table.currentRow()
    if row < 0:
        return None
    it = table.item(row, 0)
    return it.text().strip() if it else None


# --------- Freie Tage IO (direkt, ohne DataService-Abhängigkeit) ---------

def _read_freie_tage(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        lst = obj.get("freie_tage", [])
        return lst if isinstance(lst, list) else []
    except Exception:
        return []


def _write_freie_tage(path: Path, freie_tage: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"freie_tage": freie_tage}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# --------- Tab Basis ---------

class _EditorTab(QWidget):
    add_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, title: str, columns: List[str], parent: QWidget):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Button row
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_edit = QPushButton("Edit")
        self.btn_del = QPushButton("Delete")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        # Table
        self.table = QTableWidget(0, len(columns), self)
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.cellDoubleClicked.connect(lambda r, c: self._emit_edit_if_selected())

        root.addWidget(self.table, 1)

        # wire buttons
        self.btn_add.clicked.connect(self.add_clicked.emit)
        self.btn_edit.clicked.connect(self.edit_clicked.emit)
        self.btn_del.clicked.connect(self.delete_clicked.emit)

        self.setObjectName(f"EditorTab_{title}")

    def _open_context_menu(self, pos: QPoint) -> None:
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        self.table.selectRow(idx.row())

        menu = QMenu(self)
        act_edit = menu.addAction("Bearbeiten")
        act_del = menu.addAction("Löschen")
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))

        if chosen == act_edit:
            self.edit_clicked.emit()
        elif chosen == act_del:
            self.delete_clicked.emit()

    def _emit_edit_if_selected(self) -> None:
        if _selected_id(self.table):
            self.edit_clicked.emit()


# --------- DataEditorDock ---------

class DataEditorDock(QDockWidget):
    """
    Ein Dock für "Stammdaten": LVA, Räume, Semester, Freie Tage.
    Keine Inline-Edits – alles über Dialoge wie bei deinen aktuellen Docks. 
    """

    def __init__(self, parent, ds, data_dir: Path, on_data_changed=None):
        super().__init__("Data Editor", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.ds = ds
        self.data_dir = data_dir
        self.on_data_changed = on_data_changed

        wrap = QWidget(self)
        root = QVBoxLayout(wrap)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        self.tabs = QTabWidget(wrap)
        root.addWidget(self.tabs, 1)

        # Tabs
        self.tab_lva = _EditorTab("LVA", ["ID", "Name", "Vortragende", "E-Mail", "Typen"], self.tabs)
        self.tab_rooms = _EditorTab("Räume", ["ID", "Name", "Kapazität"], self.tabs)
        self.tab_sem = _EditorTab("Semester", ["ID", "Name", "Start", "Ende"], self.tabs)
        self.tab_free = _EditorTab("Freie Tage", ["Art", "Datum", "Von", "Bis", "Beschreibung"], self.tabs)
        self.tab_termine = _EditorTab(
            "Termine",
            ["ID", "Datum", "Von", "Bis", "Typ", "LVA", "Raum", "Semester", "Gruppe"],
            self.tabs
        )
        
        self.tabs.addTab(self.tab_termine, "Termine")

        self.tabs.addTab(self.tab_lva, "LVAs")
        self.tabs.addTab(self.tab_rooms, "Räume")
        self.tabs.addTab(self.tab_sem, "Semester")
        self.tabs.addTab(self.tab_free, "Freie Tage")

        self.setWidget(wrap)

        # wire actions
        self.tab_lva.add_clicked.connect(self._add_lva)
        self.tab_lva.edit_clicked.connect(self._edit_lva)
        self.tab_lva.delete_clicked.connect(self._del_lva)

        self.tab_rooms.add_clicked.connect(self._add_room)
        self.tab_rooms.edit_clicked.connect(self._edit_room)
        self.tab_rooms.delete_clicked.connect(self._del_room)

        self.tab_sem.add_clicked.connect(self._add_sem)
        self.tab_sem.edit_clicked.connect(self._edit_sem)
        self.tab_sem.delete_clicked.connect(self._del_sem)

        self.tab_free.add_clicked.connect(self._add_free)
        self.tab_free.edit_clicked.connect(self._edit_free)
        self.tab_free.delete_clicked.connect(self._del_free)
        
        self.tab_termine.add_clicked.connect(self._add_termin)
        self.tab_termine.edit_clicked.connect(self._edit_termin)
        self.tab_termine.delete_clicked.connect(self._del_termin)


    # ---------- Public API ----------
    def refresh_all(self) -> None:
        self._refresh_lvas()
        self._refresh_rooms()
        self._refresh_semester()
        self._refresh_freie_tage()
        self._refresh_termine()

    # ---------- Refresh tables ----------
    def _refresh_lvas(self) -> None:
        lvas: List[Lehrveranstaltung] = self.ds.load_lvas()
        t = self.tab_lva.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for l in lvas:
            row = t.rowCount()
            t.insertRow(row)
            vals = [
                l.id,
                l.name,
                getattr(l.vortragende, "name", ""),
                getattr(l.vortragende, "email", ""),
                ", ".join(getattr(l, "typ", []) or []),
            ]
            for c, v in enumerate(vals):
                t.setItem(row, c, _it(str(v)))

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def _refresh_rooms(self) -> None:
        rooms: List[Raum] = self.ds.load_raeume()
        t = self.tab_rooms.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for r in rooms:
            row = t.rowCount()
            t.insertRow(row)
            vals = [r.id, r.name, str(r.kapazitaet)]
            for c, v in enumerate(vals):
                t.setItem(row, c, _it(str(v)))

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def _refresh_semester(self) -> None:
        from ..utils.datetime_utils import fmt_date

        sems: List[Semester] = self.ds.load_semester()
        t = self.tab_sem.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for s in sems:
            row = t.rowCount()
            t.insertRow(row)
            vals = [s.id, s.name, fmt_date(s.start), fmt_date(s.end)]
            for c, v in enumerate(vals):
                t.setItem(row, c, _it(str(v)))

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()

    def _refresh_freie_tage(self) -> None:
        ft_path = self.data_dir / "freie_tage.json"
        freie = _read_freie_tage(ft_path)

        t = self.tab_free.table
        t.setSortingEnabled(False)
        t.setRowCount(0)

        for it in freie:
            row = t.rowCount()
            t.insertRow(row)

            if "datum" in it and it.get("datum"):
                art = "single"
                datum = str(it.get("datum", ""))
                von = ""
                bis = ""
            else:
                art = "range"
                datum = ""
                von = str(it.get("von_datum", ""))
                bis = str(it.get("bis_datum", ""))

            beschr = str(it.get("beschreibung", ""))

            vals = [art, datum, von, bis, beschr]
            for c, v in enumerate(vals):
                t.setItem(row, c, _it(str(v)))

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()
        
    def _refresh_termine(self) -> None:
        # local imports so we don't depend on file-level imports
        from ..utils.datetime_utils import fmt_date, fmt_time

        def safe_date(d) -> str:
            try:
                return fmt_date(d) if d else ""
            except Exception:
                return str(d) if d is not None else ""

        def safe_time(t) -> str:
            try:
                return fmt_time(t) if t else ""
            except Exception:
                return str(t) if t is not None else ""

        termine: List[Termin] = self.ds.load_termine()
        t = self.tab_termine.table

        t.setSortingEnabled(False)
        t.setRowCount(0)

        for tm in termine:
            row = t.rowCount()
            t.insertRow(row)

            start_zeit = getattr(tm, "start_zeit", None)
            end_zeit = tm.get_end_time() if hasattr(tm, 'get_end_time') else None

            vals = [
                getattr(tm, "id", ""),
                safe_date(getattr(tm, "datum", None)),
                safe_time(start_zeit),
                safe_time(end_zeit),
                getattr(tm, "typ", ""),
                getattr(tm, "lva_id", ""),
                getattr(tm, "raum_id", ""),
                getattr(tm, "semester_id", ""),
                getattr(tm, "gruppe", "") or "",
            ]

            for c, v in enumerate(vals):
                t.setItem(row, c, _it(str(v)))

        t.setSortingEnabled(True)
        t.resizeColumnsToContents()



    # ---------- CRUD: LVA ----------
    def _add_lva(self) -> None:
        dlg = LVADialog(self, None)  # :contentReference[oaicite:3]{index=3}
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return
        lvas = self.ds.load_lvas()
        if any(x.id == dlg.result.id for x in lvas):
            QMessageBox.warning(self, "Fehler", f"LVA-ID '{dlg.result.id}' existiert bereits.")
            return
        lvas.append(dlg.result)
        self.ds.save_lvas(lvas)
        self._after_change()

    def _edit_lva(self) -> None:
        lid = _selected_id(self.tab_lva.table)
        if not lid:
            return
        lvas = self.ds.load_lvas()
        cur = next((x for x in lvas if x.id == lid), None)
        if not cur:
            return
        dlg = LVADialog(self, cur)
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return

        # replace
        out = [dlg.result if x.id == lid else x for x in lvas]
        self.ds.save_lvas(out)
        self._after_change()

    def _del_lva(self) -> None:
        lid = _selected_id(self.tab_lva.table)
        if not lid:
            return
        if QMessageBox.question(self, "Löschen", f"LVA '{lid}' wirklich löschen?") != QMessageBox.Yes:
            return
        lvas = [x for x in self.ds.load_lvas() if x.id != lid]
        self.ds.save_lvas(lvas)
        self._after_change()

    # ---------- CRUD: Room ----------
    def _add_room(self) -> None:
        dlg = RaumDialog(self, None)  # :contentReference[oaicite:4]{index=4}
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return
        rooms = self.ds.load_raeume()
        if any(x.id == dlg.result.id for x in rooms):
            QMessageBox.warning(self, "Fehler", f"Raum-ID '{dlg.result.id}' existiert bereits.")
            return
        rooms.append(dlg.result)
        self.ds.save_raeume(rooms)
        self._after_change()

    def _edit_room(self) -> None:
        rid = _selected_id(self.tab_rooms.table)
        if not rid:
            return
        rooms = self.ds.load_raeume()
        cur = next((x for x in rooms if x.id == rid), None)
        if not cur:
            return
        dlg = RaumDialog(self, cur)
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return
        out = [dlg.result if x.id == rid else x for x in rooms]
        self.ds.save_raeume(out)
        self._after_change()

    def _del_room(self) -> None:
        rid = _selected_id(self.tab_rooms.table)
        if not rid:
            return
        if QMessageBox.question(self, "Löschen", f"Raum '{rid}' wirklich löschen?") != QMessageBox.Yes:
            return
        rooms = [x for x in self.ds.load_raeume() if x.id != rid]
        self.ds.save_raeume(rooms)
        self._after_change()

    # ---------- CRUD: Semester ----------
    def _add_sem(self) -> None:
        dlg = SemesterDialog(self, None)  # :contentReference[oaicite:5]{index=5}
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return
        sems = self.ds.load_semester()
        if any(x.id == dlg.result.id for x in sems):
            QMessageBox.warning(self, "Fehler", f"Semester-ID '{dlg.result.id}' existiert bereits.")
            return
        sems.append(dlg.result)
        self.ds.save_semester(sems)
        self._after_change()

    def _edit_sem(self) -> None:
        sid = _selected_id(self.tab_sem.table)
        if not sid:
            return
        sems = self.ds.load_semester()
        cur = next((x for x in sems if x.id == sid), None)
        if not cur:
            return
        dlg = SemesterDialog(self, cur)
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return
        out = [dlg.result if x.id == sid else x for x in sems]
        self.ds.save_semester(out)
        self._after_change()

    def _del_sem(self) -> None:
        sid = _selected_id(self.tab_sem.table)
        if not sid:
            return
        if QMessageBox.question(self, "Löschen", f"Semester '{sid}' wirklich löschen?") != QMessageBox.Yes:
            return
        sems = [x for x in self.ds.load_semester() if x.id != sid]
        self.ds.save_semester(sems)
        self._after_change()

    # ---------- CRUD: Freie Tage ----------
    def _add_free(self) -> None:
        ft_path = self.data_dir / "freie_tage.json"
        freie = _read_freie_tage(ft_path)

        dlg = FreieTageDialog(self, None)
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return
        freie.append(dlg.result)
        _write_freie_tage(ft_path, freie)
        self._after_change()

    def _edit_free(self) -> None:
        t = self.tab_free.table
        row = t.currentRow()
        if row < 0:
            return

        ft_path = self.data_dir / "freie_tage.json"
        freie = _read_freie_tage(ft_path)
        if row >= len(freie):
            return

        cur = freie[row]
        dlg = FreieTageDialog(self, cur)
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return

        freie[row] = dlg.result
        _write_freie_tage(ft_path, freie)
        self._after_change()

    def _del_free(self) -> None:
        t = self.tab_free.table
        row = t.currentRow()
        if row < 0:
            return

        if QMessageBox.question(self, "Löschen", "Eintrag wirklich löschen?") != QMessageBox.Yes:
            return

        ft_path = self.data_dir / "freie_tage.json"
        freie = _read_freie_tage(ft_path)
        if row >= len(freie):
            return

        freie.pop(row)
        _write_freie_tage(ft_path, freie)
        self._after_change()

    # ---------- after change ----------
    def _after_change(self) -> None:
        self.refresh_all()
        if self.on_data_changed:
            self.on_data_changed()

    def _add_termin(self) -> None:
        dlg = TerminDialog(
            self,
            lvas=self.ds.load_lvas(),
            semester=self.ds.load_semester(),
            raeume=self.ds.load_raeume(),
            termin=None,
            settings=self.ds.load_settings()
        )
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return

        termine = self.ds.load_termine()
        if any(t.id == dlg.result.id for t in termine):
            QMessageBox.warning(self, "Fehler", f"Termin-ID '{dlg.result.id}' existiert bereits.")
            return

        termine.append(dlg.result)
        self.ds.save_termine(termine)
        self._after_change()

    def _edit_termin(self) -> None:
        tid = _selected_id(self.tab_termine.table)
        if not tid:
            return

        termine = self.ds.load_termine()
        cur = next((t for t in termine if t.id == tid), None)
        if not cur:
            return

        dlg = TerminDialog(
            self,
            lvas=self.ds.load_lvas(),
            semester=self.ds.load_semester(),
            raeume=self.ds.load_raeume(),
            termin=cur,
            settings=self.ds.load_settings()
        )
        if dlg.exec() != dlg.Accepted or not dlg.result:
            return

        out = [dlg.result if t.id == tid else t for t in termine]
        self.ds.save_termine(out)
        self._after_change()

    def _del_termin(self) -> None:
        tid = _selected_id(self.tab_termine.table)
        if not tid:
            return

        if QMessageBox.question(self, "Löschen", f"Termin '{tid}' wirklich löschen?") != QMessageBox.Yes:
            return

        termine = [t for t in self.ds.load_termine() if t.id != tid]
        self.ds.save_termine(termine)
        self._after_change()


