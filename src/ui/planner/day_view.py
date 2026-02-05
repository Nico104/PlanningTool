from datetime import date, time, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QLabel, QComboBox, QDateEdit

from ...core.models import Raum, Termin
from ..utils.datetime_utils import qdate_to_date, fmt_time, fmt_date
from .state import PlannerState


class PlannerDayView:
    def __init__(
        self,
        state: PlannerState,
        day_table: QTableWidget,
        day_date: QDateEdit,
        friday_lbl: QLabel,
        conflict_lbl: QLabel,
        edit_by_id_cb,
        current_filters_cb,
    ):
        self.state = state
        self.day_table = day_table
        self.day_date = day_date
        self.friday_lbl = friday_lbl
        self.conflict_lbl = conflict_lbl
        self.edit_by_id_cb = edit_by_id_cb
        self.current_filters_cb = current_filters_cb

        self.day_table.cellDoubleClicked.connect(self._on_double_click)

    def _day_bounds(self) -> Tuple[time, time, int]:
        s = self.state.settings
        day_start = datetime.strptime(s.get("day_start", "08:00"), "%H:%M").time()
        day_end = datetime.strptime(s.get("day_end", "18:00"), "%H:%M").time()
        slot = int(s.get("time_slot_minutes", 30))
        return day_start, day_end, slot

    def refresh(self, filtered_termine: List[Termin]) -> None:
        assert self.state.ts is not None

        d = qdate_to_date(self.day_date.date())
        sem, room_filter, _q, _typ = self.current_filters_cb()
        self.friday_lbl.setText("⭐ Freitag" if d.weekday() == 4 else "")

        rooms = self.state.raeume
        if room_filter:
            rooms = [r for r in rooms if r.id == room_filter]

        terms_day = [t for t in filtered_termine if t.datum == d]
        self._build_day_grid(rooms, terms_day, d, sem, room_filter)

    def _build_day_grid(self, rooms: List[Raum], terms: List[Termin], d: date, sem: Optional[str], room_filter: Optional[str]) -> None:
        assert self.state.ts is not None

        day_start, day_end, slot_min = self._day_bounds()
        start_dt = datetime(d.year, d.month, d.day, day_start.hour, day_start.minute)
        end_dt = datetime(d.year, d.month, d.day, day_end.hour, day_end.minute)
        slot = timedelta(minutes=slot_min)

        times: List[datetime] = []
        cur = start_dt
        while cur < end_dt:
            times.append(cur)
            cur += slot

        self.day_table.clearSpans()
        self.day_table.setRowCount(len(times))
        self.day_table.setColumnCount(1 + len(rooms))
        headers = ["Zeit"] + [f"{r.id}\n{r.name}" for r in rooms]
        self.day_table.setHorizontalHeaderLabels(headers)

        for r, dt0 in enumerate(times):
            it = QTableWidgetItem(dt0.strftime("%H:%M"))
            it.setFlags(it.flags() ^ Qt.ItemIsEditable)
            self.day_table.setItem(r, 0, it)

        room_index = {r.id: idx for idx, r in enumerate(rooms)}

        for r in range(len(times)):
            for c in range(1, 1 + len(rooms)):
                it = QTableWidgetItem("")
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                self.day_table.setItem(r, c, it)

        def row_for(t0: time) -> int:
            dt_t = datetime(d.year, d.month, d.day, t0.hour, t0.minute)
            return int((dt_t - start_dt) / slot)

        occupied = [[False] * (1 + len(rooms)) for _ in range(len(times))]

        for t in terms:
            if t.raum_id not in room_index:
                continue
            c = 1 + room_index[t.raum_id]
            r0 = max(0, min(row_for(t.start_zeit), len(times) - 1))
            # Calculate end time from duration
            end_time = t.get_end_time()
            if end_time is None:
                end_time = t.start_zeit  # fallback if no duration
            r1 = max(r0 + 1, min(row_for(end_time), len(times)))
            span = max(1, r1 - r0)

            # Konflikt (UI-Span vermeiden)
            if any(occupied[rr][c] for rr in range(r0, min(len(times), r0 + span))):
                base = self.day_table.item(r0, c)
                old = base.text() if base else ""
                lva = self.state.lva_map.get(t.lva_id)
                lva_name = lva.name if lva else t.lva_id
                end_time_display = t.get_end_time() or t.start_zeit
                conflict_line = f"⚠ KONFLIKT: {fmt_time(t.start_zeit)}–{fmt_time(end_time_display)} {t.typ} {t.lva_id} {lva_name}"
                new_txt = (old + "\n\n" + conflict_line).strip() if old else conflict_line
                it = QTableWidgetItem(new_txt)
                it.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
                it.setFlags(it.flags() ^ Qt.ItemIsEditable)
                it.setData(Qt.UserRole, t.id)
                self.day_table.setItem(r0, c, it)
                continue

            for rr in range(r0, min(len(times), r0 + span)):
                occupied[rr][c] = True

            self.day_table.setSpan(r0, c, span, 1)

            lva = self.state.lva_map.get(t.lva_id)
            lva_name = lva.name if lva else t.lva_id
            grp = "" if t.gruppe.name in ("", "-", None) else f"\nGruppe {t.gruppe.name} ({t.gruppe.groesse})"
            ap = "\nAP" if t.anwesenheitspflicht else ""
            note = f"\n{t.notiz}" if t.notiz else ""
            txt = f"{t.typ} {t.lva_id}\n{lva_name}{grp}{ap}{note}"

            it = QTableWidgetItem(txt)
            it.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
            it.setFlags(it.flags() ^ Qt.ItemIsEditable)
            it.setData(Qt.UserRole, t.id)
            self.day_table.setItem(r0, c, it)

            for rr in range(r0 + 1, r0 + span):
                ph = QTableWidgetItem("")
                ph.setFlags(ph.flags() ^ Qt.ItemIsEditable)
                ph.setData(Qt.UserRole, t.id)
                self.day_table.setItem(rr, c, ph)

        # Konflikte unten (TerminService)
        conflicts = self.state.ts.find_room_conflicts(self.state.termine, semester_id=sem)
        conflicts = [c for c in conflicts if c.datum == d]
        if room_filter:
            conflicts = [c for c in conflicts if c.raum_id == room_filter]

        if not conflicts:
            self.conflict_lbl.setText("Konflikte: keine ✅")
        else:
            first = conflicts[0]
            more = "" if len(conflicts) == 1 else f" (+{len(conflicts)-1} weitere)"
            self.conflict_lbl.setText(
                f"Konflikte: Raum {first.raum_id} {fmt_date(first.datum)}: {first.termin_a.id} ↔ {first.termin_b.id}{more}"
            )

        self.day_table.resizeColumnsToContents()
        self.day_table.resizeRowsToContents()

    def _on_double_click(self, row: int, col: int):
        if col <= 0:
            return
        it = self.day_table.item(row, col)
        if not it:
            return
        tid = it.data(Qt.UserRole)
        if tid:
            self.edit_by_id_cb(str(tid))
