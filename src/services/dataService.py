from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, date, time
from typing import Dict, List, Any

from ..models.models import Semester, Raum, Vortragende, Lehrveranstaltung, Zeitfenster, Gruppe, Termin


class DataService:
    """
    Minimaler JSON-Speicher: lädt/schreibt die Projekt-JSON-Dateien aus dem data/-Ordner.
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    def _read(self, filename: str) -> Dict[str, Any]:
        path = self.data_dir / filename
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, filename: str, obj: Dict[str, Any]) -> None:
        path = self.data_dir / filename
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _parse_date(s: str) -> date:
        return datetime.strptime(s, "%Y-%m-%d").date()

    @staticmethod
    def _parse_time(s: str) -> time:
        return datetime.strptime(s, "%H:%M").time()

    @staticmethod
    def _fmt_date(d: date) -> str:
        return d.isoformat()

    @staticmethod
    def _fmt_time(t: time) -> str:
        return t.strftime("%H:%M")

    # ---------- LOAD ----------
    def load_semester(self) -> List[Semester]:
        raw = self._read("semester.json")["semester"]
        return [Semester(
            id=x["id"],
            name=x["name"],
            start=self._parse_date(x["start"]),
            end=self._parse_date(x["end"]),
        ) for x in raw]

    def load_raeume(self) -> List[Raum]:
        raw = self._read("raeume.json")["raeume"]
        return [Raum(id=x["id"], name=x["name"], kapazitaet=int(x["kapazitaet"])) for x in raw]

    def load_lvas(self) -> List[Lehrveranstaltung]:
        raw = self._read("lehrveranstaltungen.json")["lehrveranstaltungen"]
        out: List[Lehrveranstaltung] = []
        for x in raw:
            v = x["vortragende"]
            out.append(Lehrveranstaltung(
                id=x["id"],
                name=x["name"],
                vortragende=Vortragende(name=v["name"], email=v.get("email", "")),
                typ=list(x.get("typ", [])),
            ))
        return out

    def load_termine(self) -> List[Termin]:
        raw = self._read("termine.json")["termine"]
        out: List[Termin] = []

        for x in raw:
            # optional fields
            z = x.get("zeit")          # may be missing or None
            g = x.get("gruppe") or {}  # may be missing

            # datum optional
            d_raw = x.get("datum")
            datum = self._parse_date(d_raw) if d_raw else None

            # zeit optional
            zeit = None
            if isinstance(z, dict):
                von_raw = z.get("von")
                bis_raw = z.get("bis")

                # if one is missing, keep it None (works with your saving)
                von = self._parse_time(von_raw) if von_raw else None
                bis = self._parse_time(bis_raw) if bis_raw else None

                # if both missing -> treat as None (unassigned)
                if von is not None or bis is not None:
                    zeit = Zeitfenster(von=von, bis=bis)

            out.append(Termin(
                id=x["id"],
                lva_id=x["lva_id"],
                semester_id=x["semester_id"],
                typ=x["typ"],
                datum=datum,
                zeit=zeit,
                raum_id=x.get("raum_id", ""),
                gruppe=Gruppe(name=g.get("name", "-"), groesse=int(g.get("groesse", 0) or 0)),
                anwesenheitspflicht=bool(x.get("anwesenheitspflicht", False)),
                notiz=x.get("notiz", ""),
            ))

        return out


    def load_settings(self) -> Dict[str, Any]:
        return self._read("settings.json")

    # ---------- SAVE ----------
    def save_semester(self, semester: List[Semester]) -> None:
        self._write("semester.json", {
            "semester": [{
                "id": s.id, "name": s.name,
                "start": self._fmt_date(s.start),
                "end": self._fmt_date(s.end)
            } for s in semester]
        })

    def save_raeume(self, raeume: List[Raum]) -> None:
        self._write("raeume.json", {
            "raeume": [{"id": r.id, "name": r.name, "kapazitaet": r.kapazitaet} for r in raeume]
        })

    def save_lvas(self, lvas: List[Lehrveranstaltung]) -> None:
        self._write("lehrveranstaltungen.json", {
            "lehrveranstaltungen": [{
                "id": l.id,
                "name": l.name,
                "vortragende": {"name": l.vortragende.name, "email": l.vortragende.email},
                "typ": list(l.typ)
            } for l in lvas]
        })

    def save_termine(self, termine: List[Termin]) -> None:
        self._write("termine.json", {
            "termine": [{
                "id": t.id,
                "lva_id": t.lva_id,
                "semester_id": t.semester_id,
                "typ": t.typ,
                "datum": self._fmt_date(t.datum) if t.datum is not None else None,
                "zeit": {"von": self._fmt_time(t.zeit.von) if t.zeit and t.zeit.von else None, "bis": self._fmt_time(t.zeit.bis) if t.zeit and t.zeit.bis else None} if t.zeit else None,
                "raum_id": t.raum_id,
                "gruppe": {"name": t.gruppe.name, "groesse": t.gruppe.groesse},
                "anwesenheitspflicht": t.anwesenheitspflicht,
                "notiz": t.notiz
            } for t in termine]
        })

    def save_settings(self, settings: Dict[str, Any]) -> None:
        # minimal guard
        self._write("settings.json", settings)