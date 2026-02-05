from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import MainWindow


def load_global_style(app: QApplication) -> None:
    """
    Lädt globalen QSS-Style.
    Erwartet: src/ui/styles/light.qss (so wie du es in deinem Code wolltest).
    """
    app.setStyle("Fusion")
    
    pal = QPalette()

    # Light UI base
    pal.setColor(QPalette.Window, QColor("#f8f8f8"))
    pal.setColor(QPalette.Base, QColor("#ffffff"))
    # pal.setColor(QPalette.Window, QColor("green"))
    # pal.setColor(QPalette.Base, QColor("red"))
    pal.setColor(QPalette.Text, QColor("#111111"))
    pal.setColor(QPalette.WindowText, QColor("#111111"))

    # Selection (IMPORTANT: removes brown highlight)
    pal.setColor(QPalette.Highlight, QColor("#01659b"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    # app_bootstrap.py is at: src/ui/windows/main_window/
    # styles is at:           src/ui/styles/
    qss_path = Path(__file__).resolve().parents[2] / "styles" / "light.qss"
    print("QSS:", qss_path)

    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # Optional Debug
    print("Style:", app.style().objectName())
    print("App QSS length:", len(app.styleSheet()))
    print("Palette Window:", app.palette().color(QPalette.Window).name())
    print("Palette Base:", app.palette().color(QPalette.Base).name())
    print("Palette Text:", app.palette().color(QPalette.Text).name())


def run_gui() -> None:
    app = QApplication([])
    load_global_style(app)

    w = MainWindow(Path("data"))
    w.resize(1500, 900)
    w.show()

    app.exec()
