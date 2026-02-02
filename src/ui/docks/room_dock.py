# # from __future__ import annotations

# # from typing import List, Optional

# # from PySide6.QtCore import Qt, Signal
# # from PySide6.QtWidgets import QDockWidget

# # from ..widgets.dock_table import DockTable
# # from ...models.models import Raum


# # class RoomDock(QDockWidget):
# #     add_clicked = Signal()
# #     edit_clicked = Signal()
# #     delete_clicked = Signal()

# #     def __init__(self, parent=None):
# #         super().__init__("Räume", parent)
# #         self.setAllowedAreas(Qt.AllDockWidgetAreas)

# #         self.tab = DockTable(["ID", "Name", "Kapazität"])
# #         self.setWidget(self.tab)

# #         self.tab.add_btn.clicked.connect(self.add_clicked.emit)
# #         self.tab.edit_btn.clicked.connect(self.edit_clicked.emit)
# #         self.tab.del_btn.clicked.connect(self.delete_clicked.emit)

# #     def set_rows(self, rooms: List[Raum]) -> None:
# #         t = self.tab.table
# #         t.setSortingEnabled(False)
# #         t.setRowCount(0)

# #         for r in rooms:
# #             row = t.rowCount()
# #             t.insertRow(row)
# #             vals = [r.id, r.name, str(r.kapazitaet)]
# #             for c, v in enumerate(vals):
# #                 from PySide6.QtWidgets import QTableWidgetItem
# #                 it = QTableWidgetItem(str(v))
# #                 it.setFlags(it.flags() ^ Qt.ItemIsEditable)
# #                 t.setItem(row, c, it)

# #         t.setSortingEnabled(True)
# #         t.resizeColumnsToContents()

# #     def selected_id(self) -> Optional[str]:
# #         return self.tab.selected_id()

# from __future__ import annotations

# from typing import List, Optional

# from PySide6.QtCore import Qt, Signal, QPoint
# from PySide6.QtWidgets import QDockWidget, QTableWidget, QTableWidgetItem, QMenu

# from ...models.models import Raum


# class RoomDock(QDockWidget):
#     edit_clicked = Signal()
#     delete_clicked = Signal()

#     def __init__(self, parent=None):
#         super().__init__("Räume", parent)
#         self.setAllowedAreas(Qt.AllDockWidgetAreas)

#         self.table = QTableWidget(0, 3, self)
#         self.table.setHorizontalHeaderLabels(["ID", "Name", "Kapazität"])
#         self.table.setSortingEnabled(True)
#         self.table.horizontalHeader().setStretchLastSection(True)
#         self.table.setSelectionBehavior(QTableWidget.SelectRows)
#         self.table.setSelectionMode(QTableWidget.SingleSelection)
#         self.table.setEditTriggers(QTableWidget.NoEditTriggers)

#         self.table.setContextMenuPolicy(Qt.CustomContextMenu)
#         self.table.customContextMenuRequested.connect(self._open_context_menu)

#         self.table.cellDoubleClicked.connect(lambda r, c: self._emit_edit_if_selected())

#         self.setWidget(self.table)

#     def _open_context_menu(self, pos: QPoint) -> None:
#         idx = self.table.indexAt(pos)
#         if not idx.isValid():
#             return

#         self.table.selectRow(idx.row())

#         menu = QMenu(self)
#         act_edit = menu.addAction("Bearbeiten")
#         act_del = menu.addAction("Löschen")

#         chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
#         if chosen == act_edit:
#             self.edit_clicked.emit()
#         elif chosen == act_del:
#             self.delete_clicked.emit()

#     def _emit_edit_if_selected(self) -> None:
#         if self.selected_id():
#             self.edit_clicked.emit()

#     def set_rows(self, rooms: List[Raum]) -> None:
#         t = self.table
#         t.setSortingEnabled(False)
#         t.setRowCount(0)

#         for r in rooms:
#             row = t.rowCount()
#             t.insertRow(row)

#             vals = [r.id, r.name, str(r.kapazitaet)]
#             for c, v in enumerate(vals):
#                 it = QTableWidgetItem(str(v))
#                 it.setFlags(it.flags() & ~Qt.ItemIsEditable)
#                 t.setItem(row, c, it)

#         t.setSortingEnabled(True)
#         t.resizeColumnsToContents()

#     def selected_id(self) -> Optional[str]:
#         row = self.table.currentRow()
#         if row < 0:
#             return None
#         it = self.table.item(row, 0)
#         return it.text().strip() if it else None
