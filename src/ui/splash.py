"""
Splash screen de arranque, con el estilo del banner del README:
fondo azul marino con degradado, icono de paquete con badge de descarga,
título blanco, subtítulo gris-azulado y franja azul inferior.
"""
import time

from PySide6.QtCore import QPointF, QPoint, QRect, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
                           QPainterPath, QPixmap, QRadialGradient)
from PySide6.QtWidgets import QSplashScreen, QApplication

from src.ui.app_icon import icono_aplicacion, pintar_icono_app

_WIDTH = 640
_HEIGHT = 360
_SCALE = 2  # renderizar a 2x para nitidez en pantallas HiDPI

_APP_TITLE = "WinGet Expert"
_APP_SUBTITLE = "Gestor gráfico para Windows Package Manager"
_APP_AUTHOR = "Diego A. Rábalo"
_APP_VERSION = "3.0"


def _rounded_rect_path(rect: QRect, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), radius, radius)
    return path


class SplashScreen(QSplashScreen):
    """Splash con el estilo del banner de GitHub y mensajes de progreso."""

    # Tiempo mínimo en pantalla para que se aprecie aunque la carga sea rápida
    min_display_ms = 3000

    def __init__(self):
        self._pixmap = self._build_pixmap()
        self._message = ''
        self._shown_at = time.monotonic()
        super().__init__(self._pixmap)
        self.setWindowIcon(icono_aplicacion())
        # Zona de mensajes sobre la franja azul inferior
        self._message_rect = QRect(24, _HEIGHT - 66, _WIDTH - 48, 22)

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self._shown_at) * 1000)

    def remaining_ms(self) -> int:
        """Milisegundos que faltan para alcanzar el tiempo mínimo de visualización."""
        return max(0, self.min_display_ms - self.elapsed_ms())

    def show_message(self, message: str):
        """Muestra un mensaje de progreso en la zona inferior."""
        self._message = message
        self.update()
        QApplication.processEvents()

    def drawContents(self, painter: QPainter):
        """Dibuja el mensaje actual en la zona reservada (en vez del centro)."""
        if not self._message:
            return
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPixelSize(15)
        painter.setFont(font)
        painter.setPen(QColor(0xE6, 0xEF, 0xF7))
        painter.drawText(self._message_rect, Qt.AlignmentFlag.AlignLeft, self._message)

    # ------------------------------------------------------------------ #

    def _build_pixmap(self) -> QPixmap:
        pixmap = QPixmap(_WIDTH * _SCALE, _HEIGHT * _SCALE)
        pixmap.setDevicePixelRatio(_SCALE)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        body = QRect(0, 0, _WIDTH, _HEIGHT)

        # Fondo: degradado diagonal azul marino (como el banner)
        gradient = QLinearGradient(body.topLeft(), body.bottomRight())
        gradient.setColorAt(0.0, QColor(0x12, 0x3A, 0x5E))
        gradient.setColorAt(1.0, QColor(0x0A, 0x22, 0x40))
        painter.fillPath(_rounded_rect_path(body, 10), QBrush(gradient))

        # Círculo tenue decorativo (arriba a la derecha, como el banner)
        painter.setPen(QColor(0x2A, 0x55, 0x80, 90))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPoint(_WIDTH - 70, 56), 110, 110)
        painter.drawEllipse(QPoint(_WIDTH - 70, 56), 78, 78)

        # Forma curva sutil detrás del icono (arriba a la izquierda)
        soft = QRadialGradient(QPointF(120, 60), 240)
        soft.setColorAt(0.0, QColor(0x1E, 0x50, 0x7C, 110))
        soft.setColorAt(1.0, QColor(0x1E, 0x50, 0x7C, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(soft))
        painter.drawEllipse(QPoint(120, 60), 240, 200)

        self._draw_app_icon(painter, 48, 84)
        self._draw_texts(painter)

        # Franja azul inferior (identidad del banner), recortada al radio
        painter.save()
        painter.setClipPath(_rounded_rect_path(body, 10))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0x1E, 0x90, 0xFF))
        painter.drawRect(QRect(0, _HEIGHT - 6, _WIDTH, 6))
        painter.restore()

        painter.end()
        return pixmap

    def _draw_app_icon(self, painter: QPainter, x: int, y: int):
        """Icono de la app (diseño compartido con assets/icon.ico)."""
        pintar_icono_app(painter, x, y, 132)

    def _draw_texts(self, painter: QPainter):
        left = 216
        # Título
        title = QFont()
        title.setFamily("Segoe UI")
        title.setBold(True)
        title.setPixelSize(42)
        painter.setFont(title)
        painter.setPen(QColor(0xFF, 0xFF, 0xFF))
        painter.drawText(QPoint(left, 148), _APP_TITLE)

        # Subtítulo
        subtitle = QFont()
        subtitle.setFamily("Segoe UI")
        subtitle.setPixelSize(15)
        painter.setFont(subtitle)
        painter.setPen(QColor(0xAA, 0xB8, 0xC8))
        painter.drawText(QPoint(left, 180), _APP_SUBTITLE)

        # Autor
        author = QFont()
        author.setFamily("Segoe UI")
        author.setItalic(True)
        author.setPixelSize(14)
        painter.setFont(author)
        painter.setPen(QColor(0x8F, 0xB8, 0xDE))
        painter.drawText(QPoint(left, 212), f"por {_APP_AUTHOR}")

        # Versión (esquina inferior izquierda, sobre la franja)
        version = QFont()
        version.setFamily("Segoe UI")
        version.setPixelSize(13)
        painter.setFont(version)
        painter.setPen(QColor(0x7A, 0x93, 0xA8))
        painter.drawText(QPoint(24, _HEIGHT - 38), f"v{_APP_VERSION}")
