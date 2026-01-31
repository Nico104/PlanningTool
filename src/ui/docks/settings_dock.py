from __future__ import annotations

from datetime import datetime
from typing import Dict

from PySide6.QtCore import Qt, Signal, QTime
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout, QSpinBox, QTimeEdit, QPushButton
)


class SettingsDock(QDockWidget):
    save_clicked = Signal(dict)

    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        self.root = QWidget()
        self.setWidget(self.root)

        lay = QVBoxLayout(self.root)
        form = QFormLayout()
        lay.addLayout(form)

        self.slot_sb = QSpinBox()
        self.slot_sb.setRange(5, 120)
        self.slot_sb.setSingleStep(5)

        self.day_start_te = QTimeEdit()
        self.day_end_te = QTimeEdit()

        self.save_btn = QPushButton("Settings speichern")
        self.save_btn.clicked.connect(self._on_save)

        form.addRow("Zeit-Raster (Minuten):", self.slot_sb)
        form.addRow("Tag Start:", self.day_start_te)
        form.addRow("Tag Ende:", self.day_end_te)

        lay.addWidget(self.save_btn)
        lay.addStretch(1)

    def load(self, s: Dict) -> None:
        self.slot_sb.setValue(int(s.get("time_slot_minutes", 30)))

        ds = datetime.strptime(s.get("day_start", "08:00"), "%H:%M").time()
        de = datetime.strptime(s.get("day_end", "18:00"), "%H:%M").time()
        self.day_start_te.setTime(QTime(ds.hour, ds.minute))
        self.day_end_te.setTime(QTime(de.hour, de.minute))

    def extract(self) -> Dict:
        return {
            "time_slot_minutes": int(self.slot_sb.value()),
            "day_start": self.day_start_te.time().toString("HH:mm"),
            "day_end": self.day_end_te.time().toString("HH:mm"),
        }

    def _on_save(self) -> None:
        self.save_clicked.emit(self.extract())
