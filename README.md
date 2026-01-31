# Planungstool – Workspace (PySide6, JSON-only)

Features:
- **Workspace wie VSCode**: DockWidgets (drag & drop, tabbed docks)
- **Kalenderansicht umschaltbar**:
  - Tag: Zeit × Räume (Blöcke)
  - Woche: KW-Zeilen, Mo–Sa-Spalten
- **Termine-Liste** zusätzlich (Dock): immer sichtbar, Doppelklick -> bearbeiten
- CRUD (Docks): LVAs, Räume, Semester
- Settings (Dock): Raster, Tag-Start/Ende
- Vorlagen: wöchentliche Termine erzeugen
- Alles speichert direkt in `data/*.json`

## Installation
Python 3.10+:
```bash
pip install -r requirements.txt
```

## Start
```bash
python main.py
```

## Bedienung
- Kalenderansicht oben links umschalten (Tag/Woche)
- **Tag-Ansicht**: Datum wählen
- **Wochen-Ansicht**: Datumsbereich wählen (von/bis)
- Docks kannst du per Drag&Drop nach links/rechts/unten/oben ziehen oder zu Tabs zusammenfassen (wie VSCode)
- Termine-Liste: Doppelklick auf Termin-ID öffnet Editor
