from dataclasses import dataclass
from typing import Optional


@dataclass
class FilterState:
    semester_id: Optional[str] = None
    lva_id: Optional[str] = None
    raum_id: Optional[str] = None
    typ: Optional[str] = None
