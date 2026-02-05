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

from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QRect
from PySide6.QtGui import QDropEvent, QDragMoveEvent, QPainter, QPen, QColor
from PySide6.QtWidgets import QTableWidget, QAbstractItemView, QTableWidgetSelectionRange
import math


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
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)

        # Qt's default drop indicator is often too subtle; we do our own.
        self.setDropIndicatorShown(False)

        # Track current hover target during drag
        self._hover_row = -1
        self._hover_col = -1
        self._hover_span = 1
        self._hover_termin_id = None

        # Duration preview config
        self._duration_provider = None
        self._color_provider = None
        self._text_provider = None
        self._slot_minutes = 30

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

        termin_id = bytes(e.mimeData().data(self.MIME)).decode("utf-8").strip()
        self._hover_termin_id = termin_id
        duration = 0
        if self._duration_provider:
            try:
                duration = int(self._duration_provider(termin_id) or 0)
            except Exception:
                duration = 0
        if duration <= 0:
            duration = self._slot_minutes
        span = max(1, int(math.ceil(duration / max(1, self._slot_minutes))))

        pos = e.position().toPoint()  # viewport coords (Qt6)
        self._last_drag_pos = pos

        r = self.rowAt(pos.y())
        c = self.columnAt(pos.x())
        if r < 0 or c < 0:
            self._set_hover(-1, -1)
            e.ignore()
            return

        # SNAP: update hover target + selection highlight
        self._set_hover(r, c, span)
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
        self._set_hover(-1, -1, 1)

        self.terminDropped.emit(termin_id, r, c)
        e.acceptProposedAction()

    # ---------- Snap hover helpers ----------
    def _set_hover(self, r: int, c: int, span: int = 1):
        if r == self._hover_row and c == self._hover_col and span == self._hover_span:
            return
        self._hover_row, self._hover_col, self._hover_span = r, c, span

        if r >= 0 and c >= 0:
            self.clearSelection()
            r_end = min(self.rowCount() - 1, r + max(1, span) - 1)
            self.setRangeSelected(QTableWidgetSelectionRange(r, c, r_end, c), True)
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

    def set_duration_preview_provider(self, provider, slot_minutes: int) -> None:
        """Set provider to resolve duration minutes for a termin_id."""
        self._duration_provider = provider
        self._slot_minutes = max(1, int(slot_minutes))

    def set_color_provider(self, provider) -> None:
        """Set provider to resolve background color for a termin_id."""
        self._color_provider = provider

    def set_text_provider(self, provider) -> None:
        """Set provider to resolve display text for a termin_id."""
        self._text_provider = provider

    # ---------- Nice visible drop preview ----------
    def paintEvent(self, e):
        super().paintEvent(e)

        if self._hover_row < 0 or self._hover_col < 0:
            return

        x = self.columnViewportPosition(self._hover_col)
        y = self.rowViewportPosition(self._hover_row)
        w = self.columnWidth(self._hover_col)
        h = self.rowHeight(self._hover_row)
        rect = QRect(x, y, w, h)

        # Expand rect to cover span rows for preview
        end_row = min(self.rowCount() - 1, self._hover_row + max(1, self._hover_span) - 1)
        if end_row != self._hover_row:
            bottom_y = self.rowViewportPosition(end_row)
            bottom_h = self.rowHeight(end_row)
            bottom_rect = QRect(x, bottom_y, w, bottom_h)
            rect = rect.united(bottom_rect)

        # draw a filled preview block + crisp border around hovered span
        p = QPainter(self.viewport())
        p.setRenderHint(QPainter.Antialiasing, False)

        fill_color = QColor("#111111")
        if self._color_provider and self._hover_termin_id:
            try:
                fill_color = self._color_provider(self._hover_termin_id)
            except Exception:
                pass
        
        p.setBrush(fill_color)
        p.setPen(Qt.NoPen)
        p.drawRect(rect.adjusted(1, 1, -1, -1))

        # Draw text if provider available
        if self._text_provider and self._hover_termin_id:
            try:
                text = self._text_provider(self._hover_termin_id)
                if text:
                    p.setPen(QColor("#111111"))
                    p.drawText(rect.adjusted(5, 3, -5, -3), Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop, text)
            except Exception:
                pass

        pen = QPen(Qt.black)
        pen.setWidth(2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRect(rect.adjusted(1, 1, -1, -1))
        p.end()

    def startDrag(self, supportedActions):
        # Try to get the widget at current cell position
        current_row = self.currentRow()
        current_col = self.currentColumn()
        
        if current_row < 0 or current_col < 0:
            return

        # Check if this is a cell widget (new TerminCard approach)
        cell_widget = self.cellWidget(current_row, current_col)
        if cell_widget:
            # Try to extract termin_id from the widget
            # If it's a TimeSlotCell, get the first termin card
            if hasattr(cell_widget, 'get_termin_ids'):
                termin_ids = cell_widget.get_termin_ids()
                if termin_ids:
                    termin_id = termin_ids[0]
                else:
                    return
            elif hasattr(cell_widget, 'termin_id'):
                # If it's a TerminCard directly
                termin_id = cell_widget.termin_id
            else:
                return
        else:
            # Fallback to item-based approach for backwards compatibility
            it = self.item(current_row, current_col)
            if not it:
                return

            # Try to get termin id from item data
            termin_id = it.data(self.Qt.UserRole) if hasattr(self, 'Qt') else it.data(0x0100)

            # fallback (if you used text)
            if not termin_id:
                termin_id = (it.text() or "").strip()

            if not termin_id:
                return

        from PySide6.QtGui import QDrag
        from PySide6.QtCore import QMimeData

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(self.MIME, str(termin_id).encode("utf-8"))
        drag.setMimeData(mime)

        drag.exec(Qt.MoveAction)
