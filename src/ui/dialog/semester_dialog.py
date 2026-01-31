from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDialog, QDialogButtonBox, QMessageBox, QDateEdit
)

from ...models.models import Semester
from ..utils.datetime_utils import date_to_qdate, qdate_to_date



class SemesterDialog(QDialog):
    def __init__(self, parent: QWidget, sem: Optional[Semester] = None):
        super().__init__(parent)
        self.setWindowTitle("Semester bearbeiten" if sem else "Semester hinzufügen")
        self._result: Optional[Semester] = None

        lay = QVBoxLayout(self)
        form = QFormLayout()
        lay.addLayout(form)

        self.id_le = QLineEdit(sem.id if sem else "")
        self.name_le = QLineEdit(sem.name if sem else "")
        self.start_de = QDateEdit()
        self.start_de.setCalendarPopup(True)
        self.end_de = QDateEdit()
        self.end_de.setCalendarPopup(True)

        if sem:
            self.start_de.setDate(date_to_qdate(sem.start))
            self.end_de.setDate(date_to_qdate(sem.end))
        else:
            today = date.today()
            self.start_de.setDate(date_to_qdate(today))
            self.end_de.setDate(date_to_qdate(today))

        form.addRow("ID:", self.id_le)
        form.addRow("Name:", self.name_le)
        form.addRow("Start:", self.start_de)
        form.addRow("Ende:", self.end_de)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _accept(self):
        sid = self.id_le.text().strip()
        name = self.name_le.text().strip()
        if not sid or not name:
            QMessageBox.warning(self, "Fehler", "ID und Name sind Pflicht.")
            return
        s = Semester(
            id=sid,
            name=name,
            start=qdate_to_date(self.start_de.date()),
            end=qdate_to_date(self.end_de.date()),
        )
        self._result = s
        self.accept()

    @property
    def result(self) -> Optional[Semester]:
        return self._result