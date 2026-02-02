from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QTableWidget


class WeekDropTable(QTableWidget):
    """
    Drop target for Termine.
    Emits: (termin_id, row, col) based on drop position.
    """
    terminDropped = Signal(str, int, int)
    MIME = "application/x-termin-id"

    def __init__(self, rows: int, cols: int, parent=None):
        super().__init__(rows, cols, parent)
        self.setAcceptDrops(True)
        # self.setDragDropMode(QTableWidget.DropOnly)
        # self.setDefaultDropAction(Qt.MoveAction)
        
        self.setDragEnabled(True)
        self.setDragDropMode(QTableWidget.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QTableWidget.SingleSelection)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(self.MIME):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(self.MIME):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent):
        md = e.mimeData()
        if not md.hasFormat(self.MIME):
            e.ignore()
            return

        termin_id = bytes(md.data(self.MIME)).decode("utf-8").strip()

        pos: QPoint = e.position().toPoint()  # Qt6
        r = self.rowAt(pos.y())
        c = self.columnAt(pos.x())
        if r < 0 or c < 0:
            e.ignore()
            return

        self.terminDropped.emit(termin_id, r, c)
        e.acceptProposedAction()
        
    def startDrag(self, supportedActions):
        it = self.currentItem()
        if not it:
            return
        termin_id = it.data(Qt.UserRole)
        if not termin_id:
            return  # empty cell

        from PySide6.QtGui import QDrag
        from PySide6.QtCore import QMimeData

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self.MIME, str(termin_id).encode("utf-8"))
        drag.setMimeData(mime)
        drag.exec(Qt.MoveAction)


