from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QComboBox, QDateEdit
)

from ..utils.datetime_utils import date_to_qdate, qdate_to_date


class FreieTageDialog(QDialog):
    """
    Editiert 1 Eintrag aus freie_tage.json:
      - single: {"datum": "YYYY-MM-DD", "beschreibung": "..."}
      - range:  {"von_datum": "...", "bis_datum": "...", "beschreibung": "..."}
    """

    def __init__(self, parent: QWidget, item: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.setWindowTitle("Freier Tag bearbeiten" if item else "Freien Tag hinzufügen")
        self._result: Optional[Dict[str, Any]] = None

        lay = QVBoxLayout(self)
        form = QFormLayout()
        lay.addLayout(form)

        self.art_cb = QComboBox()
        self.art_cb.addItems(["single", "range"])

        self.datum_de = QDateEdit()
        self.datum_de.setCalendarPopup(True)

        self.von_de = QDateEdit()
        self.von_de.setCalendarPopup(True)

        self.bis_de = QDateEdit()
        self.bis_de.setCalendarPopup(True)

        self.beschr_le = QLineEdit()

        today = date.today()
        self.datum_de.setDate(date_to_qdate(today))
        self.von_de.setDate(date_to_qdate(today))
        self.bis_de.setDate(date_to_qdate(today))

        # load existing
        if item:
            self.beschr_le.setText(str(item.get("beschreibung", "")))

            if "datum" in item and item.get("datum"):
                self.art_cb.setCurrentText("single")
                # datum
                try:
                    y, m, d = map(int, str(item.get("datum")).split("-"))
                    self.datum_de.setDate(date_to_qdate(date(y, m, d)))
                except Exception:
                    pass
            else:
                self.art_cb.setCurrentText("range")
                # von/bis
                for key, widget in [("von_datum", self.von_de), ("bis_datum", self.bis_de)]:
                    try:
                        y, m, d = map(int, str(item.get(key, "")).split("-"))
                        widget.setDate(date_to_qdate(date(y, m, d)))
                    except Exception:
                        pass

        form.addRow("Art:", self.art_cb)
        form.addRow("Datum (single):", self.datum_de)
        form.addRow("Von (range):", self.von_de)
        form.addRow("Bis (range):", self.bis_de)
        form.addRow("Beschreibung:", self.beschr_le)

        self.art_cb.currentTextChanged.connect(self._update_visibility)
        self._update_visibility(self.art_cb.currentText())

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _update_visibility(self, art: str) -> None:
        is_single = (art == "single")
        self.datum_de.setEnabled(is_single)
        self.von_de.setEnabled(not is_single)
        self.bis_de.setEnabled(not is_single)

    def _accept(self) -> None:
        beschr = self.beschr_le.text().strip()
        if not beschr:
            QMessageBox.warning(self, "Fehler", "Beschreibung ist Pflicht.")
            return

        art = self.art_cb.currentText().strip().lower()
        if art == "single":
            d = qdate_to_date(self.datum_de.date())
            self._result = {"datum": d.isoformat(), "beschreibung": beschr}
        else:
            v = qdate_to_date(self.von_de.date())
            b = qdate_to_date(self.bis_de.date())
            if b < v:
                QMessageBox.warning(self, "Fehler", "Bis-Datum muss >= Von-Datum sein.")
                return
            self._result = {"von_datum": v.isoformat(), "bis_datum": b.isoformat(), "beschreibung": beschr}

        self.accept()

    @property
    def result(self) -> Optional[Dict[str, Any]]:
        return self._result
