from PySide6.QtWidgets import QDialog

from ...services.idService import next_id
from ..dialog.termin_dialog import TerminDialog
from .planner_state import PlannerState


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
