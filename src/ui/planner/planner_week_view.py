from datetime import date, timedelta
from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QDateEdit

from ...models.models import Termin
from ..utils.datetime_utils import qdate_to_date, monday_of, fmt_time
from .planner_state import PlannerState


class PlannerWeekView:
    def __init__(self, state: PlannerState, week_table: QTableWidget, week_from: QDateEdit, week_to: QDateEdit, edit_by_id_cb):
        self.state = state
        self.week_table = week_table
        self.week_from = week_from
        self.week_to = week_to
        self.edit_by_id_cb = edit_by_id_cb

        self.week_table.cellDoubleClicked.connect(self._on_double_click)

    def refresh(self, filtered_termine: List[Termin]) -> None:
        start = qdate_to_date(self.week_from.date())
        end = qdate_to_date(self.week_to.date())
        if end < start:
            start, end = end, start

        terms = [t for t in filtered_termine if start <= t.datum <= end and t.datum.weekday() <= 5]
        self._build_week_table(start, end, terms)

    def _build_week_table(self, start: date, end: date, terms: List[Termin]) -> None:
        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]
        self.week_table.setColumnCount(1 + len(days))
        self.week_table.setHorizontalHeaderLabels(["KW"] + days)

        cur = monday_of(start)
        weeks: List[date] = []
        while cur <= end:
            weeks.append(cur)
            cur += timedelta(days=7)

        self.week_table.setRowCount(len(weeks))

        by_day: Dict[date, List[Termin]] = {}
        for t in terms:
            by_day.setdefault(t.datum, []).append(t)
        for d0 in by_day:
            by_day[d0].sort(key=lambda x: (x.zeit.von, x.zeit.bis))

        for row, week_mo in enumerate(weeks):
            _, iso_week, _ = week_mo.isocalendar()
            kw_item = QTableWidgetItem(f"KW {iso_week}\n{week_mo.strftime('%d.%m')}")
            kw_item.setFlags(kw_item.flags() ^ Qt.ItemIsEditable)
            self.week_table.setItem(row, 0, kw_item)

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
                    lines.append(f"{fmt_time(t.zeit.von)}–{fmt_time(t.zeit.bis)} {t.typ} | {room_s} | {lva_short}{grp}{ap}")
                cell = QTableWidgetItem("\n".join(lines))
                cell.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                cell.setFlags(cell.flags() ^ Qt.ItemIsEditable)
                if items:
                    cell.setData(Qt.UserRole, items[0].id)  # Hinweis: editiert immer den 1. Termin des Tages
                self.week_table.setItem(row, 1 + col, cell)

        self.week_table.resizeColumnsToContents()
        self.week_table.resizeRowsToContents()

    def _on_double_click(self, row: int, col: int):
        if col <= 0:
            return
        it = self.week_table.item(row, col)
        if not it:
            return
        tid = it.data(Qt.UserRole)
        if tid:
            self.edit_by_id_cb(str(tid))
