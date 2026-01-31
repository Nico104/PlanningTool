from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional

from ..models.models import Termin, Zeitfenster, Gruppe


@dataclass(frozen=True)
class WeeklyTemplate:
    """
    Erstellt wöchentliche Termine zwischen start/end (inklusive), an einem Wochentag (0=Mo..6=So).
    """
    weekday: int
    start_date: date
    end_date: date
    time_from: time
    time_to: time
    semester_id: str
    raum_id: str
    lva_id: str
    typ: str
    group_names: List[str]            # z.B. ["A","B"]
    group_size: int
    attendance_required: bool
    note: str = ""


def generate_weekly_terms(tpl: WeeklyTemplate, id_factory) -> List[Termin]:
    d = tpl.start_date
    # jump to first weekday
    while d.weekday() != tpl.weekday:
        d += timedelta(days=1)

    terms: List[Termin] = []
    while d <= tpl.end_date:
        for gname in (tpl.group_names or ["-"]):
            tid = id_factory()
            terms.append(Termin(
                id=tid,
                lva_id=tpl.lva_id,
                semester_id=tpl.semester_id,
                typ=tpl.typ,
                datum=d,
                zeit=Zeitfenster(von=tpl.time_from, bis=tpl.time_to),
                raum_id=tpl.raum_id,
                gruppe=Gruppe(name=gname, groesse=(tpl.group_size if gname != "-" else 0)),
                anwesenheitspflicht=tpl.attendance_required,
                notiz=tpl.note
            ))
        d += timedelta(days=7)
    return terms
