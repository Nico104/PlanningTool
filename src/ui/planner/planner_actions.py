from PySide6.QtWidgets import QDialog

from ...services.idService import next_id
from ..dialog.termin_dialog import TerminDialog
from .planner_state import PlannerState

from datetime import date, datetime, time, timedelta
from dataclasses import replace

from ...models.models import Zeitfenster




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
        )
        if dlg.exec() != QDialog.Accepted or not dlg.result:
            return False

        new_t = dlg.result
        self.state.termine = [new_t if x.id == tid else x for x in self.state.termine]
        self.state.ds.save_termine(self.state.termine)
        return True
    
    def move_termin(self, termin_id: str, new_date: date, new_start: time) -> bool:
        """
        Move termin to new_date + new_start.
        - keeps duration (bis - von) if assigned
        - if unassigned -> default 30 minutes
        - persists via DataService.save_termine
        """
        t = next((x for x in self.state.termine if x.id == termin_id), None)
        if not t:
            return False

        # duration (keep if possible)
        dur = timedelta(minutes=30)
        if getattr(t, "zeit", None) and t.zeit.von and t.zeit.bis:
            try:
                dur = (
                    datetime.combine(date(2000, 1, 1), t.zeit.bis)
                    - datetime.combine(date(2000, 1, 1), t.zeit.von)
                )
                if dur.total_seconds() <= 0:
                    dur = timedelta(minutes=30)
            except Exception:
                dur = timedelta(minutes=30)

        new_end = (datetime.combine(new_date, new_start) + dur).time()

        # build new Zeitfenster (don't replace(None,...))
        new_zeit = Zeitfenster(von=new_start, bis=new_end)

        # ✅ Update termin (try dataclass replace, else mutate)
        try:
            # if Termin is a dataclass, this is clean
            new_t = replace(t, datum=new_date, zeit=new_zeit)
        except Exception:
            # fallback if Termin isn't a dataclass
            t.datum = new_date
            t.zeit = new_zeit
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
        new_t = replace(t, datum=None, zeit=None)

        # optional: raum auch leeren, falls du willst:
        # new_t = replace(new_t, raum_id="")

        self.state.termine = [new_t if x.id == termin_id else x for x in self.state.termine]

        if hasattr(self.state, "termin_map"):
            self.state.termin_map[termin_id] = new_t

        self.state.ds.save_termine(self.state.termine)
        return True

