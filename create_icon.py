"""
Genera assets/icon.ico y assets/icon.png con el diseño del icono del splash
(cuadrado redondeado azul, caja blanca y badge verde de descarga).

Uso (solo desarrollo; requiere PySide6 + Pillow):
    python create_icon.py
"""
import os

from PySide6.QtWidgets import QApplication

from src.ui.app_icon import render_icono

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_ICO = os.path.join(BASE, 'assets', 'icon.ico')
OUT_PNG = os.path.join(BASE, 'assets', 'icon.png')

ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48),
             (64, 64), (128, 128), (256, 256)]


def main():
    app = QApplication([])  # QPainter sobre QPixmap necesita una instancia de Qt
    os.makedirs(os.path.join(BASE, 'assets'), exist_ok=True)

    # PNG en 256 px
    render_icono(256).save(OUT_PNG)

    # ICO multi-tamaño: se renderiza grande y Pillow genera cada tamaño
    tmp = os.path.join(BASE, 'assets', 'icon_tmp_1024.png')
    render_icono(1024).save(tmp)
    from PIL import Image
    Image.open(tmp).save(OUT_ICO, format='ICO', sizes=ICO_SIZES)
    os.remove(tmp)

    print(f'OK: {OUT_ICO} ({os.path.getsize(OUT_ICO)} bytes) + {OUT_PNG}')


if __name__ == '__main__':
    main()
