from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDialog, QDialogButtonBox, QMessageBox
)

from ...core.models import Semester, Raum, Lehrveranstaltung, Vortragende, Termin, Zeitfenster, Gruppe


class LVADialog(QDialog):
    def __init__(self, parent: QWidget, lva: Optional[Lehrveranstaltung] = None):
        super().__init__(parent)
        self.setWindowTitle("LVA bearbeiten" if lva else "LVA hinzufügen")
        self._result: Optional[Lehrveranstaltung] = None

        lay = QVBoxLayout(self)
        form = QFormLayout()
        lay.addLayout(form)

        self.id_le = QLineEdit(lva.id if lva else "")
        self.name_le = QLineEdit(lva.name if lva else "")
        self.vname_le = QLineEdit(lva.vortragende.name if lva else "")
        self.vmail_le = QLineEdit(lva.vortragende.email if lva else "")
        self.typ_le = QLineEdit(", ".join(lva.typ) if lva else "VO")

        form.addRow("LVA-ID:", self.id_le)
        form.addRow("Name:", self.name_le)
        form.addRow("Vortragende Name:", self.vname_le)
        form.addRow("Vortragende E-Mail:", self.vmail_le)
        form.addRow("Erlaubte Typen (Komma):", self.typ_le)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _accept(self):
        cid = self.id_le.text().strip()
        name = self.name_le.text().strip()
        vname = self.vname_le.text().strip()
        if not cid or not name or not vname:
            QMessageBox.warning(self, "Fehler", "LVA-ID, Name und Vortragende Name sind Pflicht.")
            return
        typ = [t.strip().upper() for t in self.typ_le.text().split(",") if t.strip()]
        self._result = Lehrveranstaltung(
            id=cid,
            name=name,
            vortragende=Vortragende(name=vname, email=self.vmail_le.text().strip()),
            typ=typ
        )
        self.accept()

    @property
    def result(self) -> Optional[Lehrveranstaltung]:
        return self._result