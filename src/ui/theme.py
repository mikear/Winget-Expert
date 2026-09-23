"""
Temas visuales de la aplicación (estilo Fusion con paletas clara y oscura).
"""
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

_ACCENT = QColor(0x0078D4)  # Azul de Windows


def _build_palette(dark: bool) -> QPalette:
    palette = QPalette()

    if dark:
        window = QColor(0x20, 0x20, 0x20)
        window_alt = QColor(0x2B, 0x2B, 0x2B)
        base = QColor(0x25, 0x25, 0x25)
        base_alt = QColor(0x30, 0x30, 0x30)
        text = QColor(0xF0, 0xF0, 0xF0)
        text_disabled = QColor(0x90, 0x90, 0x90)
        button = QColor(0x33, 0x33, 0x33)
        highlight_text = QColor(0xFF, 0xFF, 0xFF)
        link = QColor(0x5C, 0xB6, 0xFF)
    else:
        window = QColor(0xF3, 0xF3, 0xF3)
        window_alt = QColor(0xE9, 0xE9, 0xE9)
        base = QColor(0xFF, 0xFF, 0xFF)
        base_alt = QColor(0xF5, 0xF5, 0xF5)
        text = QColor(0x1A, 0x1A, 0x1A)
        text_disabled = QColor(0x9E, 0x9E, 0x9E)
        button = QColor(0xFB, 0xFB, 0xFB)
        highlight_text = QColor(0xFF, 0xFF, 0xFF)
        link = QColor(0x00, 0x5F, 0xB8)

    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, base_alt)
    palette.setColor(QPalette.ColorRole.ToolTipBase, base)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, button)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(0xFF, 0x66, 0x66))
    palette.setColor(QPalette.ColorRole.Link, link)
    palette.setColor(QPalette.ColorRole.Highlight, _ACCENT)
    palette.setColor(QPalette.ColorRole.HighlightedText, highlight_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, text_disabled)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, text_disabled)
    return palette


_LIGHT_STYLESHEET = """
QTableView, QTableWidget, QTreeView, QListView { border: 1px solid #D9D9D9; }
"""

_DARK_STYLESHEET = """
QTableView, QTableWidget, QTreeView, QListView { border: 1px solid #3D3D3D; }
QToolTip { color: #F0F0F0; background-color: #2B2B2B; border: 1px solid #555555; }
"""


def apply_theme(app: QApplication, dark: bool):
    """Aplica tema claro u oscuro sobre el estilo Fusion."""
    app.setStyle('Fusion')
    app.setPalette(_build_palette(dark))
    app.setStyleSheet(_DARK_STYLESHEET if dark else _LIGHT_STYLESHEET)
