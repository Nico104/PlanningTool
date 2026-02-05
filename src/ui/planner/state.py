from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ...core.models import Semester, Raum, Lehrveranstaltung, Termin
from ...services.data_service import DataService
from ...services.filter_service import filter_termine
from ...services.termin_service import TerminService


@dataclass
class PlannerState:
    ds: DataService

    semester: List[Semester] = field(default_factory=list)
    raeume: List[Raum] = field(default_factory=list)
    lvas: List[Lehrveranstaltung] = field(default_factory=list)
    termine: List[Termin] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)

    ts: Optional[TerminService] = None
    lva_map: Dict[str, Lehrveranstaltung] = field(default_factory=dict)
    raum_map: Dict[str, Raum] = field(default_factory=dict)

    termin_map: Dict[str, "Termin"] = field(default_factory=dict)

    def reload(self) -> None:
        self.semester = self.ds.load_semester()
        self.raeume = self.ds.load_raeume()
        self.lvas = self.ds.load_lvas()
        self.termine = self.ds.load_termine()
        self.settings = self.ds.load_settings()
        self.ts = TerminService(self.settings)
        self.lva_map = {l.id: l for l in self.lvas}
        self.raum_map = {r.id: r for r in self.raeume}
        self.termin_map = {t.id: t for t in self.termine}

    def filtered_termine(self, semester_id: Optional[str], raum_id: Optional[str], q: str) -> List[Termin]:
        out = filter_termine(self.termine, semester_id=semester_id, raum_id=raum_id)
        q = (q or "").strip().lower()
        if q:
            def match(t: Termin) -> bool:
                lva = self.lva_map.get(t.lva_id)
                hay = " ".join([
                    t.lva_id,
                    lva.name if lva else "",
                    lva.vortragende.name if lva else "",
                ]).lower()
                return q in hay
            out = [t for t in out if match(t)]
        return out
