from __future__ import annotations

from datetime import date, time, timedelta
from typing import Dict, List, Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QDateEdit, QHeaderView

from ...models.models import Termin
from ..utils.datetime_utils import qdate_to_date, monday_of, fmt_time
from .planner_state import PlannerState
from ..utils.datetime_utils import date_to_qdate


# --- grid config (adjust later if you want) ---
GRID_MIN = 30
DAY_START_H = 8
DAY_END_H = 20  # exclusive


def _time_slots() -> List[time]:
    slots: List[time] = []
    start = DAY_START_H * 60
    end = DAY_END_H * 60
    for m in range(start, end, GRID_MIN):
        slots.append(time(hour=m // 60, minute=m % 60))
    return slots


def _mins(t: time) -> int:
    return t.hour * 60 + t.minute


# --- Option A: simple color mapping by type (background + foreground) ---
TYPE_COLORS: Dict[str, QColor] = {
    "VO": QColor("#E3F2FD"),  # light blue
    "UE": QColor("#E8F5E9"),  # light green
    "LU": QColor("#FFF3E0"),  # light orange
    "SE": QColor("#F3E5F5"),  # light purple
}
DEFAULT_BG = QColor("#F7F7F7")
DEFAULT_FG = QColor("#111111")


class PlannerWeekView:
    """
    Shows a week grid (Mo–Sa) with time slots as rows.
    Supports dropping a Termin (by id) onto a cell -> calls on_drop_cb(id, target_date, target_time).
    Renders Termine as blocks spanning multiple rows based on duration (GRID_MIN).
    """

    def __init__(
        self,
        state: PlannerState,
        week_table: QTableWidget,
        week_from: QDateEdit,
        edit_by_id_cb: Callable[[str], None],
        on_drop_cb: Callable[[str, date, time], None],
    ):
        self.state = state
        self.week_table = week_table
        self.week_from = week_from
        self.edit_by_id_cb = edit_by_id_cb
        self.on_drop_cb = on_drop_cb

        # if using WeekDropTable, it has terminDropped(str,int,int)
        if hasattr(self.week_table, "terminDropped"):
            self.week_table.terminDropped.connect(self._on_termin_dropped)

        self._setup_table()
        self.week_table.cellDoubleClicked.connect(self._on_double_click)

    def _setup_table(self) -> None:
        t = self.week_table
        t.setWordWrap(True)
        t.setTextElideMode(Qt.ElideRight)

        t.setShowGrid(True)
        t.verticalHeader().setVisible(False)
        t.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        t.setSizeAdjustPolicy(QTableWidget.AdjustToContentsOnFirstShow)

        h = t.horizontalHeader()
        v = t.verticalHeader()

        h.setStretchLastSection(False)
        v.setSectionResizeMode(QHeaderView.Stretch)
        
        self.week_table.verticalHeader().setDefaultSectionSize(26)


    def refresh(self, filtered_termine: List[Termin]) -> None:
        week_mo = monday_of(qdate_to_date(self.week_from.date()))
        week_su = week_mo + timedelta(days=6)

        # keep Mo–Sa only
        terms = [
            t for t in filtered_termine
            if t.datum is not None
            and week_mo <= t.datum <= week_su
            and t.datum.weekday() <= 5
        ]

        self._build_week_table(week_mo, terms)

    def _build_week_table(self, week_mo: date, terms: List[Termin]) -> None:
        # store current week monday on table (handy in other places)
        if hasattr(self.week_table, "week_monday_qdate"):
            self.week_table.week_monday_qdate = date_to_qdate(week_mo)

        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]
        slots = _time_slots()

        self.week_table.setRowCount(len(slots))
        self.week_table.setColumnCount(1 + len(days))
        self.week_table.setHorizontalHeaderLabels(["Zeit"] + days)

        # header sizing: time column compact, days stretch
        h = self.week_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for c in range(1, 1 + len(days)):
            h.setSectionResizeMode(c, QHeaderView.Stretch)

        # time column
        for r, tt in enumerate(slots):
            it = QTableWidgetItem(f"{tt.hour:02d}:{tt.minute:02d}")
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)

            # IMPORTANT: grid-line style (Option 2)
            it.setTextAlignment(Qt.AlignRight | Qt.AlignTop)

            self.week_table.setItem(r, 0, it)

        # clear all spans first (important when refreshing)
        for r in range(len(slots)):
            for c in range(1, 1 + len(days)):
                self.week_table.setSpan(r, c, 1, 1)

        # prepare empty cells
        for col in range(6):
            d0 = week_mo + timedelta(days=col)
            for r in range(len(slots)):
                cell = QTableWidgetItem("")
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
                cell.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                cell.setData(Qt.UserRole, None)  # termin id
                cell.setData(Qt.UserRole + 1, d0.isoformat())  # target date

                # reset styling for empty cells
                cell.setBackground(QBrush(Qt.transparent))
                cell.setForeground(QBrush(DEFAULT_FG))
                f = cell.font()
                f.setBold(False)
                cell.setFont(f)

                self.week_table.setItem(r, 1 + col, cell)

        # render existing Termine into grid as blocks (span rows by duration)
        by_day: Dict[date, List[Termin]] = {}
        for t in terms:
            by_day.setdefault(t.datum, []).append(t)
        for d in by_day:
            by_day[d].sort(key=lambda x: (x.zeit.von, x.zeit.bis))

        for col in range(6):
            d0 = week_mo + timedelta(days=col)
            items = by_day.get(d0, [])

            for t in items:
                start_raw = t.zeit.von
                end_raw = t.zeit.bis
                if not isinstance(start_raw, time) or not isinstance(end_raw, time):
                    continue

                start_min = _mins(start_raw)
                end_min = _mins(end_raw)
                if end_min <= start_min:
                    continue

                start_t = time(hour=start_min // 60, minute=start_min % 60)
                if start_t not in slots:
                    continue

                row = slots.index(start_t)

                # duration -> number of rows (ceil to GRID_MIN)
                dur_min = end_min - start_min
                span_rows = max(1, (dur_min + GRID_MIN - 1) // GRID_MIN)

                # clamp so we don't run past the end of the table
                span_rows = min(span_rows, len(slots) - row)

                col_idx = 1 + col

                # clear existing span at start cell (safety)
                self.week_table.setSpan(row, col_idx, 1, 1)

                # clear items in covered rows so text doesn't appear below
                for rr in range(row, row + span_rows):
                    it = self.week_table.item(rr, col_idx)
                    if it is None:
                        it = QTableWidgetItem("")
                        it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                        it.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                        it.setData(Qt.UserRole + 1, d0.isoformat())
                        self.week_table.setItem(rr, col_idx, it)

                    it.setText("")
                    it.setData(Qt.UserRole, None)

                    # also reset styling
                    it.setBackground(QBrush(Qt.transparent))
                    it.setForeground(QBrush(DEFAULT_FG))
                    f = it.font()
                    f.setBold(False)
                    it.setFont(f)

                # apply span
                self.week_table.setSpan(row, col_idx, span_rows, 1)

                cell = self.week_table.item(row, col_idx)
                if not cell:
                    continue

                lva = self.state.lva_map.get(t.lva_id)
                lva_short = f"{t.lva_id}" + ("" if not lva else f" {lva.name}")
                room_s = f"{t.raum_id}"
                gname = (t.gruppe.name if t.gruppe else "")
                grp = "" if (not gname or gname == "-") else f" Gr.{gname}"
                ap = " AP" if t.anwesenheitspflicht else ""

                cell.setText(
                    f"{fmt_time(t.zeit.von)}–{fmt_time(t.zeit.bis)} "
                    f"{t.typ} | {room_s} | {lva_short}{grp}{ap}"
                )
                cell.setData(Qt.UserRole, t.id)

                # ---- color by type (Option A) ----
                typ = (t.typ or "").strip().upper()
                bg = TYPE_COLORS.get(typ, DEFAULT_BG)
                cell.setBackground(QBrush(bg))
                cell.setForeground(QBrush(DEFAULT_FG))

                f = cell.font()
                f.setBold(False)
                cell.setFont(f)

    def _on_double_click(self, row: int, col: int):
        if col <= 0:
            return
        it = self.week_table.item(row, col)
        if not it:
            return
        tid = it.data(Qt.UserRole)
        if tid:
            self.edit_by_id_cb(str(tid))

    def _on_termin_dropped(self, termin_id: str, row: int, col: int) -> None:
        # col 0 ist Zeit-Spalte
        if col <= 0:
            return

        week_mo = monday_of(qdate_to_date(self.week_from.date()))
        day_offset = col - 1  # Mo..Sa
        target_date = week_mo + timedelta(days=day_offset)

        slots = _time_slots()
        if row < 0 or row >= len(slots):
            return
        target_start = slots[row]

        # View macht NUR callback (Workspace entscheidet Speichern + Reload + Refresh)
        self.on_drop_cb(str(termin_id), target_date, target_start)
