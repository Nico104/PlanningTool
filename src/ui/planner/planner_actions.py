from PySide6.QtWidgets import QDialog

from ...services.idService import next_id
from ..dialog.termin_dialog import TerminDialog
from .planner_state import PlannerState

from datetime import date, datetime, time, timedelta
from dataclasses import replace



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
        - keeps duration (bis - von)
        - works with frozen dataclasses (creates new instances)
        - keeps Zeitfenster values as datetime.time (DataService needs strftime())
        """
        # find termin from list (most robust)
        t = next((x for x in self.state.termine if x.id == termin_id), None)
        if not t:
            return False

        # duration
        try:
            dur = datetime.combine(date(2000, 1, 1), t.zeit.bis) - datetime.combine(date(2000, 1, 1), t.zeit.von)
            if dur.total_seconds() <= 0:
                dur = timedelta(minutes=30)
        except Exception:
            dur = timedelta(minutes=30)

        new_end_dt = datetime.combine(new_date, new_start) + dur
        new_end = new_end_dt.time()

        # create new frozen objects
        new_zeit = replace(t.zeit, von=new_start, bis=new_end)
        new_t = replace(t, datum=new_date, zeit=new_zeit)

        # replace in list
        self.state.termine = [new_t if x.id == termin_id else x for x in self.state.termine]

        # update termin_map if you have it
        if hasattr(self.state, "termin_map"):
            self.state.termin_map[termin_id] = new_t

        # persist using DataService (you DO have save_termine)
        self.state.ds.save_termine(self.state.termine)
        return True

