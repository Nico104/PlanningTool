from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QDrag, QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import QMimeData


MIME_TERMIN_ID = "application/x-termin-id"


class TerminCard(QFrame):
    double_clicked = Signal(str)
    right_clicked = Signal(str)

    def __init__(
        self,
        termin_id: str,
        title: str,
        date: str,
        time: str,
        typ: str,
        raum: str,
        ap: bool,
        parent=None,
    ):
        super().__init__(parent)
        self.termin_id = termin_id
        self._press_pos: QPoint | None = None

        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("TerminCard")
        self.setCursor(Qt.PointingHandCursor)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(6)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("CardTitle")
        root.addWidget(lbl_title)

        lbl_dt = QLabel(f"{date} · {time}")
        lbl_dt.setObjectName("CardSub")
        root.addWidget(lbl_dt)

        chips = QHBoxLayout()
        chips.setSpacing(6)

        def chip(text, name):
            l = QLabel(text)
            l.setObjectName(name)
            l.setAlignment(Qt.AlignCenter)
            return l

        chips.addWidget(chip(typ, "ChipType"))
        chips.addWidget(chip(raum, "ChipRoom"))
        if ap:
            chips.addWidget(chip("AP", "ChipAP"))

        chips.addStretch(1)
        root.addLayout(chips)

    # ---------- DnD ----------
    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.LeftButton:
            self._press_pos = e.pos()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if not (e.buttons() & Qt.LeftButton):
            return
        if self._press_pos is None:
            return

        # Qt Drag threshold
        if (e.pos() - self._press_pos).manhattanLength() < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()

        # 1) universell
        mime.setText(self.termin_id)
        # 2) spezifisch
        mime.setData(MIME_TERMIN_ID, self.termin_id.encode("utf-8"))

        drag.setMimeData(mime)

        # optional: kleines Drag-Bild (sieht nicer aus)
        pm = QPixmap(self.size())
        self.render(pm)
        drag.setPixmap(pm)
        drag.setHotSpot(self._press_pos)

        drag.exec(Qt.CopyAction)

    # ---------- interactions ----------
    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        self.double_clicked.emit(self.termin_id)
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e) -> None:
        self.right_clicked.emit(self.termin_id)
        e.accept()
