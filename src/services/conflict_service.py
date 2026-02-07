"""
Conflict detection service for schedule conflicts and warnings.

Detects:
- Room conflicts (same room, date, overlapping time)
- Group conflicts (same LVA + group, date, overlapping time)
- Lecturer conflicts (same lecturer, date, overlapping time)
- Warnings for incomplete/unassigned Termine
- Warnings for dates outside planning period

EXTENDING WITH NEW CONFLICT TYPES:
====================================
To add a new conflict detection rule, simply add a method to the ConflictDetector class
with one of these naming patterns:

1. For hard conflicts: `def detect_<name>_conflicts(self, termine: List[Termin]) -> List[ConflictIssue]:`
2. For warnings: `def detect_<name>_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:`

The method will be automatically discovered and called by detect_all()!

Example:
    def detect_capacity_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:
        '''Detect when group size exceeds room capacity.'''
        warnings = []
        for t in termine:
            raum = self.raum_map.get(t.raum_id)
            if raum and t.gruppe and t.gruppe.groesse > raum.kapazitaet:
                warnings.append(ConflictIssue(...))
        return warnings

That's it! No need to modify detect_all() or register anything.
"""

from datetime import date, time
from typing import List, Dict, Optional, Tuple, Callable
from ..core.models import Termin, Lehrveranstaltung, Raum, Semester, ConflictIssue


# Sentinel date for unassigned Termine
UNASSIGNED_DATE = date(2000, 1, 1)


class ConflictDetector:
    """Detects scheduling conflicts and warnings."""
    
    def __init__(self, 
                 lva_map: Dict[str, Lehrveranstaltung],
                 raum_map: Dict[str, Raum],
                 semester_list: List[Semester]):
        self.lva_map = lva_map
        self.raum_map = raum_map
        self.semester_list = semester_list
    
    def is_assigned(self, termin: Termin) -> bool:
        """Check if a Termin has a real assigned date (not sentinel/None)."""
        return (termin.datum is not None and 
                termin.datum != UNASSIGNED_DATE and
                termin.start_zeit is not None)
    
    def times_overlap(self, t1: Termin, t2: Termin) -> bool:
        """Check if two Termine overlap in time.
        
        Requires both to have start_zeit and duration.
        Treats back-to-back (end == start) as NOT overlapping.
        """
        if not t1.start_zeit or not t2.start_zeit:
            return False
        if t1.duration <= 0 or t2.duration <= 0:
            return False
        
        end1 = t1.get_end_time()
        end2 = t2.get_end_time()
        
        if not end1 or not end2:
            return False
        
        # startA < endB AND startB < endA
        return (t1.start_zeit < end2) and (t2.start_zeit < end1)
    
    def get_planning_period(self, semester_id: str) -> Optional[Tuple[date, date]]:
        """Get planning start/end dates for a semester."""
        for sem in self.semester_list:
            if sem.id == semester_id:
                return (sem.start, sem.end)
        return None
    
    def detect_all(self, termine: List[Termin]) -> List[ConflictIssue]:
        """Detect all conflicts and warnings in the given Termine list.
        
        Automatically discovers and calls all detection methods that follow
        the naming convention: detect_*_conflicts() or detect_*_warnings()
        """
        issues = []
        assigned = [t for t in termine if self.is_assigned(t)]
        
        # Auto-discover all detection methods
        for method_name in dir(self):
            if method_name.startswith('detect_') and (
                method_name.endswith('_conflicts') or method_name.endswith('_warnings')
            ):
                method = getattr(self, method_name)
                if callable(method):
                    # Pass appropriate termine list based on method name
                    # Warnings can check all termine, conflicts typically check assigned only
                    if '_warnings' in method_name:
                        detected = method(termine)
                    else:
                        detected = method(assigned)
                    
                    if detected:
                        issues.extend(detected)
        
        return issues
    
    # ========================================================================
    # CONFLICT DETECTORS
    # ========================================================================
    # Add new detection methods here with naming pattern:
    # - detect_<name>_conflicts(termine) for hard conflicts
    # - detect_<name>_warnings(termine) for soft warnings
    # They will be automatically discovered and called!
    # ========================================================================
    
    def detect_incomplete_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:
        """Detect warnings for incomplete or unassigned Termine."""
        warnings = []
        
        for t in termine:
            problems = []
            
            # Check for missing/unassigned date
            if t.datum is None or t.datum == UNASSIGNED_DATE:
                problems.append("kein Datum")
            
            # Check for missing time
            if t.start_zeit is None:
                problems.append("keine Startzeit")
            
            # Check for missing/invalid duration
            if t.duration <= 0:
                problems.append("keine Dauer")
            
            # Check for missing room
            if not t.raum_id or t.raum_id.strip() == "":
                problems.append("kein Raum")
            
            if problems:
                lva = self.lva_map.get(t.lva_id)
                raum = self.raum_map.get(t.raum_id)
                
                msg = f"Unvollständiger Termin: {', '.join(problems)}"
                
                warnings.append(ConflictIssue(
                    severity="warning",
                    category="incomplete",
                    termin_ids=[t.id],
                    message=msg,
                    datum=t.datum if t.datum and t.datum != UNASSIGNED_DATE else None,
                   zeit_von=t.start_zeit,
                    zeit_bis=t.get_end_time(),
                    raum=raum.name if raum else "",
                    lva=lva.name if lva else t.lva_id,
                    gruppe=t.gruppe.name if t.gruppe else ""
                ))
        
        return warnings
    
    def detect_room_conflicts(self, termine: List[Termin]) -> List[ConflictIssue]:
        """Detect room conflicts (same room, date, overlapping time)."""
        conflicts = []
        
        # Group by room and date
        by_room_date: Dict[Tuple[str, date], List[Termin]] = {}
        for t in termine:
            if not t.raum_id or not t.datum:
                continue
            key = (t.raum_id, t.datum)
            by_room_date.setdefault(key, []).append(t)
        
        # Check for overlaps within each group
        for (raum_id, datum), terms in by_room_date.items():
            for i, t1 in enumerate(terms):
                for t2 in terms[i+1:]:
                    if self.times_overlap(t1, t2):
                        # Ensure we report each pair only once
                        if t1.id < t2.id:
                            conflicts.append(self._create_conflict(
                                "room", t1, t2, "Raum-Konflikt"
                            ))
        
        return conflicts
    
    def detect_group_conflicts(self, termine: List[Termin]) -> List[ConflictIssue]:
        """Detect group conflicts (same LVA + group, date, overlapping time)."""
        conflicts = []
        
        # Group by LVA, group name, and date
        by_lva_group_date: Dict[Tuple[str, str, date], List[Termin]] = {}
        for t in termine:
            if not t.datum or not t.gruppe:
                continue
            group_key = t.gruppe.name
            key = (t.lva_id, group_key, t.datum)
            by_lva_group_date.setdefault(key, []).append(t)
        
        # Check for overlaps within each group
        for key, terms in by_lva_group_date.items():
            for i, t1 in enumerate(terms):
                for t2 in terms[i+1:]:
                    if self.times_overlap(t1, t2):
                        if t1.id < t2.id:
                            conflicts.append(self._create_conflict(
                                "group", t1, t2, "Gruppen-Konflikt"
                            ))
        
        return conflicts
    
    def detect_lecturer_conflicts(self, termine: List[Termin]) -> List[ConflictIssue]:
        """Detect lecturer conflicts (same lecturer, date, overlapping time)."""
        conflicts = []
        
        # Group by lecturer and date
        by_lecturer_date: Dict[Tuple[str, date], List[Termin]] = {}
        for t in termine:
            if not t.datum:
                continue
            lva = self.lva_map.get(t.lva_id)
            if not lva or not lva.vortragende:
                continue
            
            lecturer_key = lva.vortragende.email  # Use email as unique identifier
            key = (lecturer_key, t.datum)
            by_lecturer_date.setdefault(key, []).append(t)
        
        # Check for overlaps within each group
        for (lecturer_email, datum), terms in by_lecturer_date.items():
            for i, t1 in enumerate(terms):
                for t2 in terms[i+1:]:
                    if self.times_overlap(t1, t2):
                        if t1.id < t2.id:
                            conflicts.append(self._create_conflict(
                                "lecturer", t1, t2, "Vortragenden-Konflikt"
                            ))
        
        return conflicts
    
    def detect_outside_period_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:
        """Detect warnings for dates outside the planning period."""
        warnings = []
        
        for t in termine:
            if not t.datum or not t.semester_id:
                continue
            
            period = self.get_planning_period(t.semester_id)
            if not period:
                continue
            
            start, end = period
            if t.datum < start or t.datum > end:
                lva = self.lva_map.get(t.lva_id)
                raum = self.raum_map.get(t.raum_id)
                
                msg = f"Datum außerhalb des Planungszeitraums ({start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')})"
                
                warnings.append(ConflictIssue(
                    severity="warning",
                    category="time_period",
                    termin_ids=[t.id],
                    message=msg,
                    datum=t.datum,
                    zeit_von=t.start_zeit,
                    zeit_bis=t.get_end_time(),
                    raum=raum.name if raum else "",
                    lva=lva.name if lva else t.lva_id,
                    gruppe=t.gruppe.name if t.gruppe else ""
                ))
        
        return warnings
    
    def _create_conflict(self, category: str, t1: Termin, t2: Termin, msg_prefix: str) -> ConflictIssue:
        """Create a conflict issue for two overlapping Termine."""
        lva1 = self.lva_map.get(t1.lva_id)
        lva2 = self.lva_map.get(t2.lva_id)
        raum1 = self.raum_map.get(t1.raum_id)
        raum2 = self.raum_map.get(t2.raum_id)
        
        lva1_name = lva1.name if lva1 else t1.lva_id
        lva2_name = lva2.name if lva2 else t2.lva_id
        raum1_name = raum1.name if raum1 else ""
        raum2_name = raum2.name if raum2 else ""
        
        # Use earlier time as reference
        zeit_von = min(t1.start_zeit, t2.start_zeit) if t1.start_zeit and t2.start_zeit else None
        end1 = t1.get_end_time()
        end2 = t2.get_end_time()
        zeit_bis = max(end1, end2) if end1 and end2 else None
        
        msg = f"{msg_prefix}: {lva1_name} ({raum1_name}) ↔ {lva2_name} ({raum2_name})"
        
        return ConflictIssue(
            severity="conflict",
            category=category,
            termin_ids=[t1.id, t2.id],
            message=msg,
            datum=t1.datum,  # Both should have same date
            zeit_von=zeit_von,
            zeit_bis=zeit_bis,
            raum=raum1_name if category == "room" else f"{raum1_name}, {raum2_name}",
            lva=f"{lva1_name}, {lva2_name}" if lva1_name != lva2_name else lva1_name,
            gruppe=""  # Could be enhanced to show both groups
        )


# ============================================================================
# EXAMPLE: How to add a new conflict type
# ============================================================================
# Uncomment and customize one of these templates to add your own detector:
#
# def detect_capacity_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:
#     """Detect when group size exceeds room capacity."""
#     warnings = []
#     for t in termine:
#         if not self.is_assigned(t):
#             continue
#         raum = self.raum_map.get(t.raum_id)
#         if raum and t.gruppe and t.gruppe.groesse > raum.kapazitaet:
#             lva = self.lva_map.get(t.lva_id)
#             msg = f"Gruppe ({t.gruppe.groesse} Personen) zu groß für {raum.name} (Kapazität: {raum.kapazitaet})"
#             warnings.append(ConflictIssue(
#                 severity="warning",
#                 category="Kapazität",
#                 termin_ids=[t.id],
#                 message=msg,
#                 datum=t.datum,
#                 zeit_von=t.start_zeit,
#                 zeit_bis=t.get_end_time(),
#                 raum=raum.name,
#                 lva=lva.name if lva else t.lva_id,
#                 gruppe=t.gruppe.name
#             ))
#     return warnings
#
# def detect_duration_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:
#     """Detect unusually long or short appointments."""
#     warnings = []
#     for t in termine:
#         if not self.is_assigned(t) or t.duration <= 0:
#             continue
#         if t.duration < 30:  # Less than 30 minutes
#             msg = f"Sehr kurze Dauer: nur {t.duration} Minuten"
#         elif t.duration > 240:  # More than 4 hours
#             msg = f"Sehr lange Dauer: {t.duration} Minuten ({t.duration // 60}h {t.duration % 60}min)"
#         else:
#             continue
#         
#         lva = self.lva_map.get(t.lva_id)
#         raum = self.raum_map.get(t.raum_id)
#         warnings.append(ConflictIssue(
#             severity="warning",
#             category="Dauer",
#             termin_ids=[t.id],
#             message=msg,
#             datum=t.datum,
#             zeit_von=t.start_zeit,
#             zeit_bis=t.get_end_time(),
#             raum=raum.name if raum else "",
#             lva=lva.name if lva else t.lva_id,
#             gruppe=t.gruppe.name if t.gruppe else ""
#         ))
#     return warnings
#
# def detect_weekend_warnings(self, termine: List[Termin]) -> List[ConflictIssue]:
#     """Detect appointments scheduled on weekends."""
#     warnings = []
#     for t in termine:
#         if not self.is_assigned(t):
#             continue
#         if t.datum.weekday() >= 5:  # Saturday=5, Sunday=6
#             lva = self.lva_map.get(t.lva_id)
#             raum = self.raum_map.get(t.raum_id)
#             day_name = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][t.datum.weekday()]
#             warnings.append(ConflictIssue(
#                 severity="warning",
#                 category="Wochenende",
#                 termin_ids=[t.id],
#                 message=f"Termin am {day_name}",
#                 datum=t.datum,
#                 zeit_von=t.start_zeit,
#                 zeit_bis=t.get_end_time(),
#                 raum=raum.name if raum else "",
#                 lva=lva.name if lva else t.lva_id,
#                 gruppe=t.gruppe.name if t.gruppe else ""
#             ))
#     return warnings
# ============================================================================
