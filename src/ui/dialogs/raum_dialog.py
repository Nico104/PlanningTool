from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDialog, QDialogButtonBox, QMessageBox, QSpinBox
)

from ...core.models import Semester, Raum, Lehrveranstaltung, Vortragende, Termin, Zeitfenster, Gruppe


class RaumDialog(QDialog):
    def __init__(self, parent: QWidget, raum: Optional[Raum] = None):
        super().__init__(parent)
        self.setWindowTitle("Raum bearbeiten" if raum else "Raum hinzufügen")
        self._result: Optional[Raum] = None

        lay = QVBoxLayout(self)
        form = QFormLayout()
        lay.addLayout(form)

        self.id_le = QLineEdit(raum.id if raum else "")
        self.name_le = QLineEdit(raum.name if raum else "")
        self.cap_sb = QSpinBox()
        self.cap_sb.setRange(1, 2000)
        self.cap_sb.setValue(raum.kapazitaet if raum else 30)

        form.addRow("ID:", self.id_le)
        form.addRow("Name:", self.name_le)
        form.addRow("Kapazität:", self.cap_sb)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _accept(self):
        rid = self.id_le.text().strip()
        name = self.name_le.text().strip()
        if not rid or not name:
            QMessageBox.warning(self, "Fehler", "ID und Name sind Pflicht.")
            return
        self._result = Raum(id=rid, name=name, kapazitaet=int(self.cap_sb.value()))
        self.accept()

    @property
    def result(self) -> Optional[Raum]:
        return self._result