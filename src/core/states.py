"""Application and filter state classes."""

from dataclasses import dataclass
from typing import Optional



@dataclass
class FilterState:
    """Represents filter/query parameters for filtering Termine."""
    lva_id: Optional[str] = None
    raum_id: Optional[str] = None
    typ: Optional[str] = None
    dozent: Optional[str] = None
