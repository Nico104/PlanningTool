from datetime import date, timedelta
from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QDateEdit, QHeaderView

from ...models.models import Termin
from ..utils.datetime_utils import qdate_to_date, monday_of, fmt_time
from .planner_state import PlannerState
from ..utils.datetime_utils import date_to_qdate


class PlannerWeekView:
    def __init__(self, state: PlannerState, week_table: QTableWidget, week_from: QDateEdit, edit_by_id_cb):
        self.state = state
        self.week_table = week_table
        self.week_table.terminDropped.connect(self._on_termin_dropped)
        self.week_from = week_from
        self.edit_by_id_cb = edit_by_id_cb

        self._setup_table()
        self.week_table.cellDoubleClicked.connect(self._on_double_click)

    def _setup_table(self) -> None:
        t = self.week_table
        t.setWordWrap(True)
        t.setTextElideMode(Qt.ElideRight)

        # optional: cleaner look
        t.setShowGrid(True)
        t.verticalHeader().setVisible(False)
        t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Make it expand nicely in layouts
        t.setSizeAdjustPolicy(QTableWidget.AdjustToContentsOnFirstShow)

        # IMPORTANT: stretch behavior (fills all space)
        h = t.horizontalHeader()
        v = t.verticalHeader()

        h.setStretchLastSection(False)
        v.setSectionResizeMode(QHeaderView.Stretch)   # row takes full height

    def refresh(self, filtered_termine: List[Termin]) -> None:
        start = monday_of(qdate_to_date(self.week_from.date()))
        end = start + timedelta(days=6)

        terms = [
            t for t in filtered_termine
            if start <= t.datum <= end and t.datum.weekday() <= 5
        ]

        self._build_week_table(start, terms)

    def _build_week_table(self, week_mo: date, terms: List[Termin]) -> None:
        if hasattr(self.week_table, "week_monday_qdate"):
            self.week_table.week_monday_qdate = date_to_qdate(week_mo)
        
        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]

        self.week_table.setRowCount(1)
        self.week_table.setColumnCount(1 + len(days))
        self.week_table.setHorizontalHeaderLabels(["KW"] + days)

        # --- Stretch columns to fill full width ---
        h = self.week_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)   # KW compact
        for c in range(1, 1 + len(days)):
            h.setSectionResizeMode(c, QHeaderView.Stretch)        # days fill remaining space

        # group terms by day
        by_day: Dict[date, List[Termin]] = {}
        for t in terms:
            by_day.setdefault(t.datum, []).append(t)
        for d in by_day:
            by_day[d].sort(key=lambda x: (x.zeit.von, x.zeit.bis))

        _, iso_week, _ = week_mo.isocalendar()
        kw_item = QTableWidgetItem(f"KW {iso_week}\n{week_mo.strftime('%d.%m')}")
        kw_item.setFlags(kw_item.flags() ^ Qt.ItemIsEditable)
        kw_item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.week_table.setItem(0, 0, kw_item)

        for col in range(6):
            d0 = week_mo + timedelta(days=col)
            items = by_day.get(d0, [])

            lines: List[str] = []
            for t in items:
                lva = self.state.lva_map.get(t.lva_id)
                lva_short = f"{t.lva_id}" + ("" if not lva else f" {lva.name}")
                room_s = f"{t.raum_id}"
                grp = "" if t.gruppe.name in ("", "-", None) else f" Gr.{t.gruppe.name}"
                ap = " AP" if t.anwesenheitspflicht else ""
                lines.append(
                    f"{fmt_time(t.zeit.von)}–{fmt_time(t.zeit.bis)} "
                    f"{t.typ} | {room_s} | {lva_short}{grp}{ap}"
                )

            cell = QTableWidgetItem("\n".join(lines))
            cell.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            cell.setFlags(cell.flags() ^ Qt.ItemIsEditable)

            if items:
                cell.setData(Qt.UserRole, items[0].id)

            self.week_table.setItem(0, 1 + col, cell)

        # ❌ REMOVE THESE: they shrink everything
        # self.week_table.resizeColumnsToContents()
        # self.week_table.resizeRowsToContents()

    def _on_double_click(self, row: int, col: int):
        if col <= 0:
            return
        it = self.week_table.item(row, col)
        if not it:
            return
        tid = it.data(Qt.UserRole)
        if tid:
            self.edit_by_id_cb(str(tid))

    def _on_termin_dropped(self, termin_id: str, target_qdate):
        target_date = qdate_to_date(target_qdate)

        # hier musst du an deine App anbinden:
        # 1) Termin holen
        t = self.state.termin_map.get(termin_id)  # falls du sowas hast
        if not t:
            return

        # 2) update (Datum ändern) + speichern
        # Beispiel: state/actions pattern
        self.state.actions.move_termin(termin_id, new_date=target_date)
