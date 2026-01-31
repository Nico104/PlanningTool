from __future__ import annotations

from datetime import date, time
from typing import List, Optional

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QDialog, QDialogButtonBox, QMessageBox,
    QComboBox, QDateEdit, QTimeEdit, QCheckBox, QSpinBox, QTextEdit
)

from ...models.models import Termin, Zeitfenster, Gruppe, Lehrveranstaltung, Semester, Raum
from ..utils.datetime_utils import date_to_qdate, qdate_to_date



class TerminDialog(QDialog):
    def __init__(self, parent: QWidget, *,
                 lvas: List[Lehrveranstaltung],
                 semester: List[Semester],
                 raeume: List[Raum],
                 termin: Optional[Termin] = None):
        super().__init__(parent)
        self.setWindowTitle("Termin bearbeiten" if termin else "Termin hinzufügen")
        self._result: Optional[Termin] = None

        lay = QVBoxLayout(self)
        form = QFormLayout()
        lay.addLayout(form)

        self.id_le = QLineEdit(termin.id if termin else "")

        self.lva_cb = QComboBox()
        for l in lvas:
            self.lva_cb.addItem(f"{l.id} – {l.name}", l.id)

        self.sem_cb = QComboBox()
        for s in semester:
            self.sem_cb.addItem(f"{s.id} – {s.name}", s.id)

        self.typ_le = QLineEdit(termin.typ if termin else "VO")
        self.date_de = QDateEdit()
        self.date_de.setCalendarPopup(True)

        self.time_from = QTimeEdit()
        self.time_to = QTimeEdit()

        self.raum_cb = QComboBox()
        for r in raeume:
            self.raum_cb.addItem(f"{r.id} – {r.name}", r.id)

        self.grp_name = QLineEdit(termin.gruppe.name if termin else "-")
        self.grp_size = QSpinBox()
        self.grp_size.setRange(0, 2000)
        self.grp_size.setValue(termin.gruppe.groesse if termin else 0)

        self.ap_cb = QCheckBox("Anwesenheitspflicht")
        self.ap_cb.setChecked(bool(termin.anwesenheitspflicht) if termin else False)

        self.note_te = QTextEdit()
        self.note_te.setFixedHeight(60)
        self.note_te.setPlainText(termin.notiz if termin else "")

        if termin:
            self.date_de.setDate(date_to_qdate(termin.datum))
            self.time_from.setTime(QTime(termin.zeit.von.hour, termin.zeit.von.minute))
            self.time_to.setTime(QTime(termin.zeit.bis.hour, termin.zeit.bis.minute))
            self._set_cb(self.lva_cb, termin.lva_id)
            self._set_cb(self.sem_cb, termin.semester_id)
            self._set_cb(self.raum_cb, termin.raum_id)
        else:
            today = date.today()
            self.date_de.setDate(date_to_qdate(today))
            self.time_from.setTime(QTime(8, 0))
            self.time_to.setTime(QTime(9, 30))

        form.addRow("Termin-ID:", self.id_le)
        form.addRow("LVA:", self.lva_cb)
        form.addRow("Semester:", self.sem_cb)
        form.addRow("Typ:", self.typ_le)
        form.addRow("Datum:", self.date_de)
        form.addRow("Von:", self.time_from)
        form.addRow("Bis:", self.time_to)
        form.addRow("Raum:", self.raum_cb)
        form.addRow("Gruppe Name:", self.grp_name)
        form.addRow("Gruppe Größe:", self.grp_size)
        form.addRow("", self.ap_cb)
        form.addRow("Notiz:", self.note_te)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _set_cb(self, cb: QComboBox, data_value: str):
        for i in range(cb.count()):
            if cb.itemData(i) == data_value:
                cb.setCurrentIndex(i)
                return

    def _accept(self):
        tid = self.id_le.text().strip()
        if not tid:
            QMessageBox.warning(self, "Fehler", "Termin-ID ist Pflicht.")
            return

        lva_id = str(self.lva_cb.currentData())
        sem_id = str(self.sem_cb.currentData())
        raum_id = str(self.raum_cb.currentData())
        typ = self.typ_le.text().strip().upper()
        d = qdate_to_date(self.date_de.date())

        tf = self.time_from.time()
        tt = self.time_to.time()
        von = time(tf.hour(), tf.minute())
        bis = time(tt.hour(), tt.minute())
        if bis <= von:
            QMessageBox.warning(self, "Fehler", "Endzeit muss nach Startzeit liegen.")
            return

        gname = self.grp_name.text().strip() or "-"
        gsize = int(self.grp_size.value())
        if gname == "-":
            gsize = 0

        self._result = Termin(
            id=tid,
            lva_id=lva_id,
            semester_id=sem_id,
            typ=typ,
            datum=d,
            zeit=Zeitfenster(von=von, bis=bis),
            raum_id=raum_id,
            gruppe=Gruppe(name=gname, groesse=gsize),
            anwesenheitspflicht=bool(self.ap_cb.isChecked()),
            notiz=self.note_te.toPlainText().strip(),
        )
        self.accept()

    @property
    def result(self) -> Optional[Termin]:
        return self._result