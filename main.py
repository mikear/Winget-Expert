"""
Punto de entrada de la aplicación WinGet Expert
"""
import os
import sys

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from src.core.settings import AppSettings
from src.ui.app_icon import icono_aplicacion
from src.ui.main_window import MainWindow
from src.ui.theme import apply_theme


def _asset_path(*parts: str) -> str:
    """Ruta a un recurso, válida tanto en desarrollo como en el .exe (PyInstaller)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _load_icon_font():
    """Registra Font Awesome Solid para los iconos de la ayuda (sin emojis)."""
    path = _asset_path('assets', 'fonts', 'fa-solid-900.ttf')
    if os.path.isfile(path):
        QFontDatabase.addApplicationFont(path)


def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setApplicationName("WinGet Expert")
    app.setOrganizationName("WinGet Expert")

    _load_icon_font()

    icono = icono_aplicacion()
    if not icono.isNull():
        app.setWindowIcon(icono)

    settings = AppSettings()
    apply_theme(app, settings.theme == 'dark')

    from src.ui.splash import SplashScreen
    splash = SplashScreen()
    splash.show()
    splash.show_message("Iniciando...")

    window = MainWindow(app, splash=splash)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
