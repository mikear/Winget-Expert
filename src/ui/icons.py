"""
Iconos de la interfaz: Font Awesome Solid (fuente local, sin emojis).

La fuente se registra en `main.py` al arrancar; `ensure_loaded()` es idempotente
por si algún diálogo se usa en otro contexto. Los iconos se dibujan como QPixmap
con el color de texto de la paleta activa, así se adaptan al tema claro/oscuro.
"""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPixmap, QPalette

_font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'assets', 'fonts', 'fa-solid-900.ttf')

_family: str = ''

# Glifos usados por la aplicación (nombres FA6 Solid)
REFRESH = 'f021'        # arrows-rotate
UPDATES = 'f019'        # cloud-arrow-down
UPGRADE_ALL = 'f135'    # rocket
UPGRADE_ONE = 'f062'    # arrow-up
INSTALL = 'f49e'        # box-open
UNINSTALL = 'f1f8'      # trash
DETAILS = 'f05a'        # circle-info
PIN = 'f08d'            # thumbtack (fijar y quitar fijado: cambia el texto)
BACKUP = 'f0c7'         # floppy-disk
RESTORE = 'f0e2'        # arrow-rotate-left
EXPORT = 'f56e'         # file-export
OPTIONS = 'f013'        # gear
COPY = 'f0c5'           # copy
SOURCES = 'f1c0'        # database
CLEAN = 'f51a'          # broom
MANUAL = 'f02d'         # book
SEARCH = 'f002'         # magnifying-glass
CLOSE = 'f00d'           # xmark
STORE = 'f290'           # bag-shopping


def ensure_loaded() -> str:
    """Registra la fuente (una vez) y retorna el nombre de la familia."""
    global _family
    if _family:
        return _family
    path = _font_path
    if not os.path.isfile(path):
        # Empaquetado con PyInstaller: resolver desde _MEIPASS
        base = getattr(sys, '_MEIPASS', None)
        if base:
            path = os.path.join(base, 'assets', 'fonts', 'fa-solid-900.ttf')
    if os.path.isfile(path):
        font_id = QFontDatabase.addApplicationFont(path)
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
        if families:
            _family = families[0]
    return _family


def icon(code_hex: str, size_px: int = 64, color: QColor = None) -> QIcon:
    """Genera un QIcon con el glifo FA dado (ej. 'f021')."""
    family = ensure_loaded()
    pixmap = QPixmap(size_px, size_px)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    if color is None:
        from PySide6.QtWidgets import QApplication
        color = QColor(0xF0, 0xF0, 0xF0)
        if QApplication.instance():
            color = QApplication.instance().palette().color(QPalette.ColorRole.WindowText)
    painter.setPen(color)
    font = QFont(family)
    font.setPixelSize(int(size_px * 0.8))
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, chr(int(code_hex, 16)))
    painter.end()
    return QIcon(pixmap)
