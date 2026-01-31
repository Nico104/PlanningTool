from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Tuple

from ..models.models import Termin, Zeitfenster


@dataclass(frozen=True)
class Konflikt:
    raum_id: str
    datum: date
    termin_a: Termin
    termin_b: Termin
    grund: str


class TerminService:
    def __init__(self, settings: Dict):
        self.settings = settings

    def find_room_conflicts(self, termine: List[Termin], semester_id: Optional[str] = None) -> List[Konflikt]:
        # Gruppiere nach (raum_id, datum)
        buckets: Dict[Tuple[str, date], List[Termin]] = {}
        for t in termine:
            if semester_id and t.semester_id != semester_id:
                continue
            buckets.setdefault((t.raum_id, t.datum), []).append(t)

        conflicts: List[Konflikt] = []
        for (room, day), ts in buckets.items():
            ts_sorted = sorted(ts, key=lambda x: (x.zeit.von, x.zeit.bis))
            for i in range(len(ts_sorted)):
                for j in range(i + 1, len(ts_sorted)):
                    a, b = ts_sorted[i], ts_sorted[j]
                    # da sortiert: wenn b schon nach a endet, kann man abbrechen
                    if b.zeit.von >= a.zeit.bis:
                        break
                    if a.zeit.overlaps(b.zeit):
                        conflicts.append(Konflikt(
                            raum_id=room,
                            datum=day,
                            termin_a=a,
                            termin_b=b,
                            grund="Raum doppelt belegt (Zeit überschneidet sich)"
                        ))
        return conflicts

    @staticmethod
    def _to_dt(d: date, t: time) -> datetime:
        return datetime(d.year, d.month, d.day, t.hour, t.minute)

    def find_free_slots_in_room(
        self,
        termine: List[Termin],
        raum_id: str,
        datum: date,
        duration_minutes: int,
        semester_id: Optional[str] = None,
    ) -> List[Zeitfenster]:
        """
        Gibt freie Zeitfenster im Raum für ein Datum zurück (innerhalb day_start/day_end).
        """
        day_start = datetime.strptime(self.settings.get("day_start", "08:00"), "%H:%M").time()
        day_end = datetime.strptime(self.settings.get("day_end", "18:00"), "%H:%M").time()

        # relevante Termine
        rel = [
            t for t in termine
            if t.raum_id == raum_id and t.datum == datum and (semester_id is None or t.semester_id == semester_id)
        ]
        rel = sorted(rel, key=lambda x: (x.zeit.von, x.zeit.bis))

        start_dt = self._to_dt(datum, day_start)
        end_dt = self._to_dt(datum, day_end)
        slot = timedelta(minutes=int(self.settings.get("time_slot_minutes", 15)))
        want = timedelta(minutes=duration_minutes)

        # belegte Intervalle als dt
        busy: List[Tuple[datetime, datetime]] = [
            (self._to_dt(datum, t.zeit.von), self._to_dt(datum, t.zeit.bis)) for t in rel
        ]

        # Merge busy
        merged: List[Tuple[datetime, datetime]] = []
        for b in busy:
            if not merged or b[0] > merged[-1][1]:
                merged.append(list(b))  # type: ignore
            else:
                merged[-1][1] = max(merged[-1][1], b[1])  # type: ignore
        merged = [(a,b) for a,b in merged]

        # Erzeuge freie Fenster
        free: List[Tuple[datetime, datetime]] = []
        cursor = start_dt
        for a, b in merged:
            if a > cursor:
                free.append((cursor, a))
            cursor = max(cursor, b)
        if cursor < end_dt:
            free.append((cursor, end_dt))

        # Rastere in Slots und filtere nach Mindestdauer
        out: List[Zeitfenster] = []
        for a, b in free:
            # runden auf Slot-Raster nach oben/unten
            def ceil_to_slot(dt: datetime) -> datetime:
                minutes = dt.hour * 60 + dt.minute
                s = int(slot.total_seconds() // 60)
                m = ((minutes + s - 1) // s) * s
                return dt.replace(hour=m // 60, minute=m % 60, second=0, microsecond=0)

            def floor_to_slot(dt: datetime) -> datetime:
                minutes = dt.hour * 60 + dt.minute
                s = int(slot.total_seconds() // 60)
                m = (minutes // s) * s
                return dt.replace(hour=m // 60, minute=m % 60, second=0, microsecond=0)

            a2 = ceil_to_slot(a)
            b2 = floor_to_slot(b)
            if b2 - a2 >= want:
                out.append(Zeitfenster(von=a2.time(), bis=b2.time()))
        return out
