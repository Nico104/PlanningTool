# from __future__ import annotations

# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import QDockWidget

# from ...services.dataService import DataService
# from ..planner.planner_workspace import PlannerWorkspace


# class PlannerDock(QDockWidget):
#     def __init__(self, parent, ds, on_data_changed=None):
#         super().__init__("Kalender / Planung", parent)
#         self.workspace = PlannerWorkspace(parent, ds, on_data_changed=on_data_changed)
#         self.setWidget(self.workspace)

#     # ---- Forwarder / API nach außen ----
#     def current_filters(self):
#         return self.workspace.current_filters()

#     @property
#     def state(self):
#         return self.workspace.state

#     @property
#     def actions(self):
#         return self.workspace.actions

#     def refresh(self, emit: bool = False):
#         return self.workspace.refresh(emit=emit)

#     def _edit_termin_by_id(self, tid: str):
#         return self.workspace._edit_termin_by_id(tid)
