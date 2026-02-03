# from __future__ import annotations

# from PySide6.QtCore import Qt, Signal, QPoint
# from PySide6.QtGui import QDropEvent
# from PySide6.QtWidgets import QTableWidget


# class WeekDropTable(QTableWidget):
#     """
#     Drop target for Termine.
#     Emits: (termin_id, row, col) based on drop position.
#     """
#     terminDropped = Signal(str, int, int)
#     MIME = "application/x-termin-id"

#     def __init__(self, rows: int, cols: int, parent=None):
#         super().__init__(rows, cols, parent)
#         self.setAcceptDrops(True)
#         # self.setDragDropMode(QTableWidget.DropOnly)
#         # self.setDefaultDropAction(Qt.MoveAction)
        
#         self.setDragEnabled(True)
#         self.setDragDropMode(QTableWidget.DragDrop)
#         self.setDefaultDropAction(Qt.MoveAction)
#         self.setSelectionMode(QTableWidget.SingleSelection)

#     def dragEnterEvent(self, e):
#         if e.mimeData().hasFormat(self.MIME):
#             e.acceptProposedAction()
#         else:
#             e.ignore()

#     def dragMoveEvent(self, e):
#         if e.mimeData().hasFormat(self.MIME):
#             e.acceptProposedAction()
#         else:
#             e.ignore()

#     def dropEvent(self, e: QDropEvent):
#         md = e.mimeData()
#         if not md.hasFormat(self.MIME):
#             e.ignore()
#             return

#         termin_id = bytes(md.data(self.MIME)).decode("utf-8").strip()

#         pos: QPoint = e.position().toPoint()  # Qt6
#         r = self.rowAt(pos.y())
#         c = self.columnAt(pos.x())
#         if r < 0 or c < 0:
#             e.ignore()
#             return

#         self.terminDropped.emit(termin_id, r, c)
#         e.acceptProposedAction()
        
#     def startDrag(self, supportedActions):
#         it = self.currentItem()
#         if not it:
#             return
#         termin_id = it.data(Qt.UserRole)
#         if not termin_id:
#             return  # empty cell

#         from PySide6.QtGui import QDrag
#         from PySide6.QtCore import QMimeData

#         drag = QDrag(self)
#         mime = QMimeData()
#         mime.setData(self.MIME, str(termin_id).encode("utf-8"))
#         drag.setMimeData(mime)
#         drag.exec(Qt.MoveAction)


from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QDropEvent, QDragMoveEvent, QPainter, QPen
from PySide6.QtWidgets import QTableWidget, QAbstractItemView


class WeekDropTable(QTableWidget):
    """
    Drop target for Termine.
    Snaps hover to nearest (row, col) and shows a drop preview.
    Emits: (termin_id, row, col) based on drop position.
    """
    terminDropped = Signal(str, int, int)
    MIME = "application/x-termin-id"

    def __init__(self, rows: int, cols: int, parent=None):
        super().__init__(rows, cols, parent)

        self.setAcceptDrops(True)

        # If this table is ONLY a drop target, you can turn dragging off.
        # But if you also want to drag from the calendar, keep it enabled.
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

        # Needed so current-cell highlight can be used as "snap preview"
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)

        # Qt's default drop indicator is often too subtle; we do our own.
        self.setDropIndicatorShown(False)

        # Track current hover target during drag
        self._hover_row = -1
        self._hover_col = -1

        # Small edge auto-scroll while dragging
        self._auto_scroll_timer = QTimer(self)
        self._auto_scroll_timer.setInterval(25)
        self._auto_scroll_timer.timeout.connect(self._auto_scroll_tick)
        self._last_drag_pos: QPoint | None = None

    # ---------- DnD ----------
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(self.MIME):
            e.acceptProposedAction()
            self._auto_scroll_timer.start()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        self._auto_scroll_timer.stop()
        self._set_hover(-1, -1)
        super().dragLeaveEvent(e)

    def dragMoveEvent(self, e: QDragMoveEvent):
        if not e.mimeData().hasFormat(self.MIME):
            e.ignore()
            return

        pos = e.position().toPoint()  # viewport coords (Qt6)
        self._last_drag_pos = pos

        r = self.rowAt(pos.y())
        c = self.columnAt(pos.x())
        if r < 0 or c < 0:
            self._set_hover(-1, -1)
            e.ignore()
            return

        # SNAP: update hover target + selection highlight
        self._set_hover(r, c)
        e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        md = e.mimeData()
        if not md.hasFormat(self.MIME):
            e.ignore()
            return

        termin_id = bytes(md.data(self.MIME)).decode("utf-8").strip()

        pos: QPoint = e.position().toPoint()
        r = self.rowAt(pos.y())
        c = self.columnAt(pos.x())
        if r < 0 or c < 0:
            e.ignore()
            return

        self._auto_scroll_timer.stop()
        self._set_hover(-1, -1)

        self.terminDropped.emit(termin_id, r, c)
        e.acceptProposedAction()

    # ---------- Snap hover helpers ----------
    def _set_hover(self, r: int, c: int):
        if r == self._hover_row and c == self._hover_col:
            return
        self._hover_row, self._hover_col = r, c

        if r >= 0 and c >= 0:
            # This is the "snap": current cell becomes the drop target
            self.setCurrentCell(r, c)
        else:
            self.clearSelection()
            self.setCurrentCell(-1, -1)

        # trigger repaint so we can draw preview border
        self.viewport().update()

    def _auto_scroll_tick(self):
        if self._last_drag_pos is None:
            return

        # Scroll when dragging near edges of the viewport
        margin = 20
        dy = 0
        dx = 0
        vp = self.viewport().rect()
        p = self._last_drag_pos

        if p.y() < vp.top() + margin:
            dy = -1
        elif p.y() > vp.bottom() - margin:
            dy = 1

        if p.x() < vp.left() + margin:
            dx = -1
        elif p.x() > vp.right() - margin:
            dx = 1

        if dy:
            sb = self.verticalScrollBar()
            sb.setValue(sb.value() + dy * 2)
        if dx:
            sb = self.horizontalScrollBar()
            sb.setValue(sb.value() + dx * 6)

    # ---------- Nice visible drop preview ----------
    def paintEvent(self, e):
        super().paintEvent(e)

        if self._hover_row < 0 or self._hover_col < 0:
            return

        it = self.item(self._hover_row, self._hover_col)
        if it is None:
            # even if cell empty, visualRect still works via model index:
            idx = self.model().index(self._hover_row, self._hover_col)
            rect = self.visualRect(idx)
        else:
            rect = self.visualItemRect(it)

        if rect.isNull():
            return

        # draw a crisp border around hovered cell
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.Antialiasing, False)
        pen = QPen(Qt.black)
        pen.setWidth(2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRect(rect.adjusted(1, 1, -1, -1))
        p.end()

    def startDrag(self, supportedActions):
        it = self.currentItem()
        if not it:
            return

        # You must have stored the termin id somewhere on the cell item
        # Recommended: item.setData(Qt.UserRole, termin_id)
        termin_id = it.data(Qt.UserRole)

        # fallback (if you used text)
        if not termin_id:
            termin_id = (it.text() or "").strip()

        if not termin_id:
            return  # empty cell / no termin here

        from PySide6.QtGui import QDrag
        from PySide6.QtCore import QMimeData

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self.MIME, str(termin_id).encode("utf-8"))
        drag.setMimeData(mime)

        drag.exec(Qt.MoveAction)
