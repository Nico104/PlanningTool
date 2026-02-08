from pathlib import Path

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .main_window import MainWindow


def load_global_style(app: QApplication) -> None:
    app.setStyle("Fusion")
    
    pal = QPalette()

    # Light UI base
    pal.setColor(QPalette.Window, QColor("#f8f8f8"))
    pal.setColor(QPalette.Base, QColor("#ffffff"))
    pal.setColor(QPalette.Text, QColor("#111111"))
    pal.setColor(QPalette.WindowText, QColor("#111111"))
    pal.setColor(QPalette.Highlight, QColor("#01659b"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)
    
    
    qss_path = Path(__file__).resolve().parents[2] / "styles" / "light.qss"

    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

def run_gui() -> None:
    app = QApplication([])
    load_global_style(app)

    w = MainWindow(Path("data"))
    w.resize(1500, 900)
    w.show()

    app.exec()
