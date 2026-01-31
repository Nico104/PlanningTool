from __future__ import annotations
from datetime import date
from typing import Dict, List, Optional

from ..models.models import Semester, Raum, Lehrveranstaltung, Termin, Zeitfenster


def fmt_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")

def fmt_time(t) -> str:
    return t.strftime("%H:%M")

def print_semester(semester: List[Semester]) -> None:
    for s in semester:
        print(f"- {s.id}: {s.name} ({fmt_date(s.start)} – {fmt_date(s.end)})")

def print_raeume(raeume: List[Raum]) -> None:
    for r in raeume:
        print(f"- {r.id}: {r.name} (Kapazität {r.kapazitaet})")

def print_lvas(lvas: List[Lehrveranstaltung]) -> None:
    for l in lvas:
        typ = ", ".join(l.typ) if l.typ else "-"
        print(f"- {l.id}: {l.name} | {l.vortragende.name} <{l.vortragende.email}> | Typ: {typ}")

def print_termine(termine: List[Termin], lva_map: Dict[str, Lehrveranstaltung], raum_map: Dict[str, Raum]) -> None:
    if not termine:
        print("(keine Termine gefunden)")
        return
    for t in termine:
        lva = lva_map.get(t.lva_id)
        raum = raum_map.get(t.raum_id)
        lva_name = lva.name if lva else t.lva_id
        raum_name = raum.name if raum else t.raum_id
        grp = "" if (t.gruppe.name in ("", "-", None)) else f" | Gruppe {t.gruppe.name} ({t.gruppe.groesse})"
        ap = " | AP" if t.anwesenheitspflicht else ""
        note = f" | {t.notiz}" if t.notiz else ""
        print(f"- {t.id}: {fmt_date(t.datum)} {fmt_time(t.zeit.von)}–{fmt_time(t.zeit.bis)} | {t.typ} | {lva_name} | {raum_name}{grp}{ap}{note}")

def print_free_slots(slots: List[Zeitfenster]) -> None:
    if not slots:
        print("(keine passenden freien Slots gefunden)")
        return
    for s in slots:
        print(f"- frei: {fmt_time(s.von)}–{fmt_time(s.bis)}")
