from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtWidgets import QTableWidget

MIME_TERMIN_ID = "application/x-planningtool-termin-id"


class DroppableWeekTable(QTableWidget):
    terminDropped = Signal(str, QDate)  # termin_id, target_date

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableWidget.DropOnly)

        # wird vom WeekView gesetzt
        self.week_monday_qdate: QDate | None = None

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat(MIME_TERMIN_ID):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat(MIME_TERMIN_ID):
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        if not e.mimeData().hasFormat(MIME_TERMIN_ID):
            e.ignore()
            return
        if self.week_monday_qdate is None:
            e.ignore()
            return

        pos = e.position().toPoint()  # Qt6
        idx = self.indexAt(pos)
        if not idx.isValid():
            e.ignore()
            return

        col = idx.column()
        if col <= 0:  # KW-Spalte
            e.ignore()
            return

        day_offset = col - 1  # Mo=0 .. Sa=5
        target_date = self.week_monday_qdate.addDays(day_offset)

        termin_id = bytes(e.mimeData().data(MIME_TERMIN_ID)).decode("utf-8").strip()
        if termin_id:
            self.terminDropped.emit(termin_id, target_date)
            e.acceptProposedAction()
        else:
            e.ignore()
