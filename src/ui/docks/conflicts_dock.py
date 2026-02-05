"""
Konflikte Dock Widget - displays schedule conflicts and warnings.
"""

from typing import List, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QScrollArea, QFrame
)

from ...core.models import Termin, Lehrveranstaltung, Raum, Semester, ConflictIssue
from ...services.conflict_service import ConflictDetector
from ..components.cards.conflict_card import ConflictCard
from ..utils.datetime_utils import fmt_date, fmt_time


class ConflictsDock(QDockWidget):
    """Dock widget for displaying schedule conflicts and warnings."""
    
    # Signal emitted when user double-clicks an issue - passes termin_id
    conflict_item_activated = Signal(str)
    # Signal emitted to highlight all related termine
    conflict_items_highlight = Signal(list)

    _CATEGORY_KINDS = {
        "raum": "raum",
        "vortragende": "vortragende",
        "zeitraum": "zeitraum",
        "gruppe": "gruppe",
        "semester": "semester",
        "unvollständig": "unvollstaendig",
        "unvollstaendig": "unvollstaendig",
    }
    
    def __init__(self, parent=None):
        super().__init__("Konflikte", parent)
        self.setObjectName("dock_conflicts")
        self.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        self._issues: List[ConflictIssue] = []
        self._detector: Optional[ConflictDetector] = None
        
        # Filter state
        self._filter_severity = "Alle"  # "Alle", "Konflikt", "Warnung"
        self._filter_category = "Alle"   # "Alle" or specific category name
        
        # Main widget
        main_widget = QWidget(self)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)
        
        filter_layout.addWidget(QLabel("Typ:"))
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["Alle", "Konflikt", "Warnung"])
        self.severity_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.severity_filter)
        
        filter_layout.addWidget(QLabel("Kategorie:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Alle")
        self.category_filter.currentTextChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.category_filter)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Header with summary and refresh button
        header = QHBoxLayout()
        header.setSpacing(8)
        
        self.summary_label = QLabel("Keine Konflikte")
        self.summary_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self.summary_label)
        
        header.addStretch()
        
        self.refresh_btn = QPushButton("Aktualisieren")
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Scrollable card list
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.cards_container = QWidget(self.scroll)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch(1)

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)
        
        self.setWidget(main_widget)
    
    def initialize_detector(self, 
                          lva_map: Dict[str, Lehrveranstaltung],
                          raum_map: Dict[str, Raum],
                          semester_list: List[Semester]) -> None:
        """Initialize the conflict detector with current data."""
        self._detector = ConflictDetector(lva_map, raum_map, semester_list)
    
    def refresh_conflicts(self, termine: List[Termin]) -> None:
        """Detect and display conflicts for the given Termine."""
        if not self._detector:
            return
        
        # Detect all issues
        self._issues = self._detector.detect_all(termine)
        
        # Update category filter with unique categories
        self._update_category_filter()
        
        # Update summary (using all issues, not filtered)
        conflicts = [i for i in self._issues if i.severity == "conflict"]
        warnings = [i for i in self._issues if i.severity == "warning"]
        
        if not self._issues:
            summary = "✓ Keine Konflikte"
            self.summary_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            summary = f"⚠ {len(conflicts)} Konflikt(e), {len(warnings)} Warnung(en)"
            if conflicts:
                self.summary_label.setStyleSheet("font-weight: bold; color: #d32f2f;")
            else:
                self.summary_label.setStyleSheet("font-weight: bold; color: #f57c00;")
        
        self.summary_label.setText(summary)
        
        # Update cards with filtered results
        self._populate_cards()
    def _populate_cards(self) -> None:
        """Populate the card list with detected issues (applying filters)."""
        self._clear_cards()

        filtered_issues = self._apply_filters()

        for issue in filtered_issues:
            type_text = "Konflikt" if issue.severity == "conflict" else "Warnung"
            zeit_str = ""
            if issue.zeit_von and issue.zeit_bis:
                zeit_str = f"{fmt_time(issue.zeit_von)} - {fmt_time(issue.zeit_bis)}"
            elif issue.zeit_von:
                zeit_str = fmt_time(issue.zeit_von)

            subtitle = f"{fmt_date(issue.datum)} · {zeit_str}".strip(" ·")
            title = f"{type_text} · {issue.category}"

            conflict_kind = self._get_conflict_kind(issue.category)
            termin_ids = [str(tid) for tid in issue.termin_ids] if issue.termin_ids else []

            card = ConflictCard(
                termin_ids=termin_ids,
                title=title,
                subtitle=subtitle,
                typ=type_text,
                raum=issue.raum,
                lva=issue.lva,
                gruppe=issue.gruppe,
                message=issue.message,
                conflict_kind=conflict_kind,
                severity=issue.severity,
                parent=self.cards_container,
            )
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_clicked)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _clear_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.cards_layout.addStretch(1)

    def _on_card_clicked(self, termin_ids: list[str]) -> None:
        if termin_ids:
            self.conflict_items_highlight.emit(termin_ids)

    def _get_conflict_kind(self, category: str) -> str:
        cat = category.lower()
        for key, kind in self._CATEGORY_KINDS.items():
            if key in cat:
                return kind
        return "default"
    
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click - emit signal or trigger parent refresh."""
        # This will be connected to the main window's refresh method
        parent = self.parent()
        if parent and hasattr(parent, 'refresh_conflicts'):
            parent.refresh_conflicts()
    
    def _on_filter_changed(self) -> None:
        """Handle filter dropdown changes."""
        self._filter_severity = self.severity_filter.currentText()
        self._filter_category = self.category_filter.currentText()
        self._populate_cards()
    
    def _apply_filters(self) -> List[ConflictIssue]:
        """Apply current filters to issues list."""
        filtered = self._issues
        
        # Filter by severity
        if self._filter_severity == "Konflikt":
            filtered = [i for i in filtered if i.severity == "conflict"]
        elif self._filter_severity == "Warnung":
            filtered = [i for i in filtered if i.severity == "warning"]
        # "Alle" shows everything
        
        # Filter by category
        if self._filter_category != "Alle":
            filtered = [i for i in filtered if i.category == self._filter_category]
        
        return filtered
    
    def _update_category_filter(self) -> None:
        """Update category filter dropdown with unique categories from current issues."""
        # Store current selection
        current = self.category_filter.currentText()
        
        # Get unique categories
        categories = sorted(set(issue.category for issue in self._issues))
        
        # Update dropdown
        self.category_filter.blockSignals(True)  # Prevent triggering filter change
        self.category_filter.clear()
        self.category_filter.addItem("Alle")
        self.category_filter.addItems(categories)
        
        # Restore selection if still valid
        idx = self.category_filter.findText(current)
        if idx >= 0:
            self.category_filter.setCurrentIndex(idx)
        else:
            self.category_filter.setCurrentIndex(0)  # "Alle"
        
        self.category_filter.blockSignals(False)
