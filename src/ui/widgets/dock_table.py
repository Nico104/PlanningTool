from __future__ import annotations

from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget
)

class DockTable(QWidget):
    def __init__(self, columns: List[str]):
        super().__init__()
        lay = QVBoxLayout(self)
        btns = QHBoxLayout()
        lay.addLayout(btns)
        self.add_btn = QPushButton("Hinzufügen")
        self.edit_btn = QPushButton("Bearbeiten")
        self.del_btn = QPushButton("Löschen")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        btns.addStretch(1)

        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table, 1)

    def selected_id(self) -> Optional[str]:
        row = self.table.currentRow()
        if row < 0:
            return None
        it = self.table.item(row, 0)
        return it.text().strip() if it else None