from __future__ import annotations
from dataclasses import dataclass
from datetime import date, time
from typing import Optional, List, Dict


@dataclass(frozen=True)
class Semester:
    id: str
    name: str
    start: date
    end: date


@dataclass(frozen=True)
class Raum:
    id: str
    name: str
    kapazitaet: int


@dataclass(frozen=True)
class Vortragende:
    name: str
    email: str


@dataclass(frozen=True)
class Lehrveranstaltung:
    id: str
    name: str
    vortragende: Vortragende
    typ: List[str]  # erlaubte Termin-Typen, z.B. ["VO", "UE"]


@dataclass(frozen=True)
class Zeitfenster:
    von: time
    bis: time

    def overlaps(self, other: "Zeitfenster") -> bool:
        # [von, bis) Überlappung
        return (self.von < other.bis) and (other.von < self.bis)


@dataclass(frozen=True)
class Gruppe:
    name: str
    groesse: int


@dataclass(frozen=True)
class Termin:
    id: str
    lva_id: str
    semester_id: str
    typ: str
    datum: Optional[date]
    zeit: Optional[Zeitfenster]
    raum_id: str
    gruppe: Gruppe
    anwesenheitspflicht: bool
    notiz: str = ""
