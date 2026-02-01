# src/ui/docks/termine_dock.py  (oder eigenes file)
from PySide6.QtCore import Qt, QMimeData, QPoint
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QTableWidget

MIME_TERMIN_ID = "application/x-planningtool-termin-id"


class DraggableTerminTable(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._drag_start_pos: QPoint | None = None

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)

        # wichtig:
        self.setDragEnabled(True)
        self.setDragDropMode(QTableWidget.DragOnly)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_start_pos = e.pos()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if not (e.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(e)
        if self._drag_start_pos is None:
            return super().mouseMoveEvent(e)

        if (e.pos() - self._drag_start_pos).manhattanLength() < 8:
            return super().mouseMoveEvent(e)

        row = self.currentRow()
        if row < 0:
            return

        it = self.item(row, 0)  # ID-spalte
        if not it:
            return
        termin_id = it.text().strip()
        if not termin_id:
            return

        mime = QMimeData()
        mime.setData(MIME_TERMIN_ID, termin_id.encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mime)

        # optional nicer: drag text preview
        drag.exec(Qt.MoveAction)
