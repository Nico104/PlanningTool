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
    
    def get_end_time(self, duration_minutes: int) -> time:
        """Calculate end time from start time and duration in minutes."""
        from datetime import datetime, date as _date, timedelta
        dummy_date = _date(2000, 1, 1)
        dt_von = datetime.combine(dummy_date, self.von)
        dt_bis = dt_von + timedelta(minutes=duration_minutes)
        return dt_bis.time()

    def overlaps(self, other: "Zeitfenster", duration: int, other_duration: int) -> bool:
        """Check if two time windows overlap given their durations in minutes."""
        bis = self.get_end_time(duration)
        other_bis = other.get_end_time(other_duration)
        # [von, bis) overlap
        return (self.von < other_bis) and (other.von < bis)


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
    start_zeit: Optional[time]
    raum_id: str
    gruppe: Optional[Gruppe]
    anwesenheitspflicht: bool
    notiz: str = ""
    duration: int = 0  # duration in minutes

    def get_duration_minutes(self) -> int:
        """
        Get the effective duration in minutes.
        Returns the stored duration value.
        """
        return self.duration
    
    def get_end_time(self) -> Optional[time]:
        """Get the calculated end time based on start time and duration."""
        if self.start_zeit and self.duration > 0:
            from datetime import datetime, date as _date, timedelta
            dummy_date = _date(2000, 1, 1)
            dt_von = datetime.combine(dummy_date, self.start_zeit)
            dt_bis = dt_von + timedelta(minutes=self.duration)
            return dt_bis.time()
        return None
    
    def has_time_assigned(self) -> bool:
        """Check if this Termin has a date and time assigned."""
        return self.datum is not None and self.start_zeit is not None

@dataclass(frozen=True)
class Konflikt:
    """Represents a room conflict between two Termine."""
    raum_id: str
    datum: date
    termin_a: Termin
    termin_b: Termin
    grund: str


@dataclass
class ConflictIssue:
    """Represents a conflict or warning issue with scheduling."""
    severity: str  # "conflict" or "warning"
    category: str  # "Raum", "Gruppe", "Vortragende", "Unvollständig", "Zeitraum"
    termin_ids: List[str]  # one or two termin IDs involved
    message: str
    datum: Optional[date]
    zeit_von: Optional[time]
    zeit_bis: Optional[time]
    raum: str
    lva: str
    gruppe: str