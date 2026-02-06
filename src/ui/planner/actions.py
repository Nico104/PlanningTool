from PySide6.QtWidgets import QDialog

from ...services.id_service import next_id
from ..dialogs.termin_dialog import TerminDialog
from .state import PlannerState

from datetime import date, datetime, time, timedelta
from dataclasses import replace

from ...core.models import Termin




class PlannerActions:
    def __init__(self, state: PlannerState, parent_widget):
        self.state = state
        self.parent = parent_widget

    def new_termin_id(self) -> str:
        return next_id("T", [t.id for t in self.state.termine], width=3)

    def add_termin(self, default_qdate) -> bool:
        dlg = TerminDialog(
            self.parent,
            lvas=self.state.lvas,
            semester=self.state.semester,
            raeume=self.state.raeume,
            termin=None,
            settings=self.state.settings,
        )
        dlg.id_le.setText(self.new_termin_id())
        dlg.date_de.setDate(default_qdate)

        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return False

        self.state.termine.append(dlg.result)
        self.state.ds.save_termine(self.state.termine)
        return True

    def edit_termin_by_id(self, tid: str) -> bool:
        t = next((x for x in self.state.termine if x.id == tid), None)
        if not t:
            return False

        dlg = TerminDialog(
            self.parent,
            lvas=self.state.lvas,
            semester=self.state.semester,
            raeume=self.state.raeume,
            termin=t,
            settings=self.state.settings,
        )
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return False

        new_t = dlg.result
        self.state.termine = [new_t if x.id == tid else x for x in self.state.termine]
        self.state.ds.save_termine(self.state.termine)
        return True
    
    def move_termin(self, termin_id: str, new_date: date, new_start: time, new_room_id: str = None) -> bool:
        """
        Move termin to new_date + new_start (and optionally new_room_id).
        - keeps duration in minutes
        - if unassigned duration -> default 30 minutes
        - persists via DataService.save_termine
        """
        t = next((x for x in self.state.termine if x.id == termin_id), None)
        if not t:
            return False

        # Keep existing duration or use default
        duration_minutes = t.duration if t.duration > 0 else 30

        # ✅ Update termin (try dataclass replace, else mutate)
        try:
            # if Termin is a dataclass, this is clean
            updates = {'datum': new_date, 'start_zeit': new_start, 'duration': duration_minutes}
            if new_room_id is not None:
                updates['raum_id'] = new_room_id
            new_t = replace(t, **updates)
        except Exception:
            # fallback if Termin isn't a dataclass
            t.datum = new_date
            t.start_zeit = new_start
            t.duration = duration_minutes
            if new_room_id is not None:
                t.raum_id = new_room_id
            new_t = t

        # replace in list
        self.state.termine = [new_t if x.id == termin_id else x for x in self.state.termine]

        # update map if present
        if hasattr(self.state, "termin_map"):
            self.state.termin_map[termin_id] = new_t

        self.state.ds.save_termine(self.state.termine)
        return True

    def unassign_termin(self, termin_id: str) -> bool:
        t = next((x for x in self.state.termine if x.id == termin_id), None)
        if not t:
            return False

        # Termin ist frozen -> wir erstellen eine neue Instanz
        new_t = replace(t, datum=None, start_zeit=None)

        # optional: raum auch leeren, falls du willst:
        # new_t = replace(new_t, raum_id="")

        self.state.termine = [new_t if x.id == termin_id else x for x in self.state.termine]

        if hasattr(self.state, "termin_map"):
            self.state.termin_map[termin_id] = new_t

        self.state.ds.save_termine(self.state.termine)
        return True

