from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QDialog, QInputDialog, QMessageBox


def build_menus(mw) -> None:
    """
    Baut die Menüleiste und hängt Actions an mw.
    Erwartet, dass mw.open_settings existiert (wird unten via attach_settings_handler gesetzt).
    """
    mb = mw.menuBar()

    file_menu = mb.addMenu("Datei")
    mw.view_menu = mb.addMenu("Ansicht")
    tools_menu = mb.addMenu("Tools")

    # Actions
    mw.act_settings = QAction("Settings…", mw)
    mw.act_settings.triggered.connect(mw.open_settings)

    mw.act_refresh = QAction("Aktualisieren", mw)
    mw.act_refresh.triggered.connect(lambda: mw.planner.refresh())

    tools_menu.addAction(mw.act_settings)
    file_menu.addAction(mw.act_refresh)

    # Layout Submenu (LayoutManager hängt die dynamischen Layout-Items an)
    mw.layout_menu = mw.view_menu.addMenu("Layout")

    # ActionGroup für Layout Auswahl
    mw.layout_group = QActionGroup(mw)
    mw.layout_group.setExclusive(True)

    # Layout-Verwaltung Actions (werden vom LayoutManager genutzt)
    mw.act_save_layout = QAction("Aktuelles Layout speichern…", mw)
    mw.act_reset_layouts = QAction("Layouts zurücksetzen", mw)


def attach_settings_handler(mw) -> None:
    """
    Implementiert mw.open_settings, damit actions.py nicht direkt DataService/Dialogs importen muss.
    """
    from ...dialogs import SettingsDialog  # lokal import: vermeidet Import-Zyklen

    def open_settings():
        cur = mw.ds.load_settings()
        dlg = SettingsDialog(mw, cur)
        if dlg.exec() != QDialog.Accepted or not dlg.result_settings:
            return

        s = cur
        s.update(dlg.result_settings)
        mw.ds.save_settings(s)

        QMessageBox.information(mw, "Settings", "Gespeichert.")
        mw.planner.refresh()

    mw.open_settings = open_settings
