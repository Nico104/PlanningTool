from __future__ import annotations
from typing import List, Optional

from ..models.models import Termin


def filter_termine(
    termine: List[Termin],
    semester_id: Optional[str] = None,
    raum_id: Optional[str] = None,
    lva_id: Optional[str] = None,
    datum: Optional[str] = None,  # YYYY-MM-DD
) -> List[Termin]:
    out = termine
    if semester_id:
        out = [t for t in out if t.semester_id == semester_id]
    if raum_id:
        out = [t for t in out if t.raum_id == raum_id]
    if lva_id:
        out = [t for t in out if t.lva_id == lva_id]
    if datum:
        out = [t for t in out if t.datum.isoformat() == datum]
    return sorted(out, key=lambda t: (t.datum, t.zeit.von, t.zeit.bis))
