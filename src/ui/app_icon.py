"""
Icono de la aplicación: cuadrado redondeado azul con caja blanca y badge
verde de descarga — el mismo diseño que dibuja el splash de arranque.

`pintar_icono_app()` es la fuente única del diseño: la usa el splash y
también `create_icon.py` para generar `assets/icon.ico` / `assets/icon.png`.
`icono_aplicacion()` carga ese .ico para ventana, splash y barra de tareas.
"""
import os
import sys

from PySide6.QtCore import QPoint, QRect, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient,
                           QPainter, QPainterPath, QPixmap)

from src.ui import icons

_BASE = 132  # tamaño de referencia del diseño (como en el splash)


def icono_aplicacion() -> QIcon:
    """QIcon desde assets/icon.ico (válido en desarrollo y empaquetado)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    path = os.path.join(base, 'assets', 'icon.ico')
    return QIcon(path) if os.path.isfile(path) else QIcon()


def _rounded_rect_path(rect: QRect, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), radius, radius)
    return path


def pintar_icono_app(painter: QPainter, x: int, y: int, size: int):
    """Dibuja el icono de la app en el rectángulo (x, y, size, size)."""
    s = size / _BASE
    rect = QRect(x, y, size, size)

    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor(0x1E, 0x88, 0xE5))
    gradient.setColorAt(1.0, QColor(0x15, 0x65, 0xC0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(gradient))
    painter.drawPath(_rounded_rect_path(rect, 26 * s))

    family = icons.ensure_loaded()
    if family:
        font = QFont(family)
        font.setPixelSize(int(64 * s))
        painter.setFont(font)
        painter.setPen(QColor(0xFF, 0xFF, 0xFF))
        painter.drawText(rect.adjusted(0, int(-8 * s), 0, int(-8 * s)),
                         Qt.AlignmentFlag.AlignCenter, chr(0xF49E))  # box-open

    # Badge verde con flecha de descarga (esquina inferior derecha)
    badge_r = int(34 * s)
    badge_center = QPoint(rect.right() - badge_r + int(10 * s),
                          rect.bottom() - badge_r + int(10 * s))
    painter.setPen(QColor(0x0A, 0x22, 0x40))
    painter.setBrush(QColor(0x22, 0xC5, 0x5E))
    painter.drawEllipse(badge_center, badge_r, badge_r)
    if family:
        font = QFont(family)
        font.setPixelSize(int(30 * s))
        painter.setFont(font)
        painter.setPen(QColor(0xFF, 0xFF, 0xFF))
        badge_rect = QRect(badge_center.x() - badge_r, badge_center.y() - badge_r,
                           badge_r * 2, badge_r * 2)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, chr(0xF019))  # download


def render_icono(size_px: int) -> QPixmap:
    """Icono como QPixmap (fondo transparente), renderizado a 4x y reducido."""
    scale = 4
    big = QPixmap(size_px * scale, size_px * scale)
    big.fill(Qt.GlobalColor.transparent)
    painter = QPainter(big)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    pintar_icono_app(painter, 0, 0, big.width())
    painter.end()
    return big.scaled(size_px, size_px,
                      Qt.AspectRatioMode.IgnoreAspectRatio,
                      Qt.TransformationMode.SmoothTransformation)
