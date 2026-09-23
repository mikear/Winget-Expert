"""Genera el icono de la aplicación (ICO multi-tamaño + PNG)."""
import os

from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_ICO = os.path.join(BASE, 'assets', 'icon.ico')
OUT_PNG = os.path.join(BASE, 'assets', 'icon.png')

_TOP = (0, 120, 212)     # azul WinGet claro
_BOTTOM = (0, 90, 158)   # azul WinGet oscuro
_WHITE = (255, 255, 255, 255)
_BADGE = (16, 185, 129, 255)  # verde descarga


def _rounded_rect(draw, box, radius, fill):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _vertical_gradient(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    top = Image.new('RGBA', (size, size), _TOP + (255,))
    bottom = Image.new('RGBA', (size, size), _BOTTOM + (255,))
    mask = Image.new('L', (1, size))
    for y in range(size):
        mask.putpixel((0, y), int(255 * y / max(size - 1, 1)))
    grad = Image.composite(bottom, top, mask.resize((size, size)))
    corner = Image.new('L', (size, size), 0)
    ImageDraw.Draw(corner).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    img.paste(grad, (0, 0), corner)
    return img


def draw_icon(size):
    img = _vertical_gradient(size)
    d = ImageDraw.Draw(img)
    u = size / 256.0

    # Caja/paquete blanca (isométrica simple)
    cx, cy = size * 0.44, size * 0.46
    w, h = size * 0.30, size * 0.24
    # cuerpo
    _rounded_rect(d, [cx - w, cy - h * 0.4, cx + w, cy + h], int(8 * u), _WHITE)
    # tapa
    d.polygon([(cx - w, cy - h * 0.4), (cx, cy - h), (cx + w, cy - h * 0.4),
               (cx, cy + h * 0.2)], fill=(225, 238, 250, 255))
    # cinta vertical
    d.rectangle([cx - w * 0.16, cy - h * 0.62, cx + w * 0.16, cy + h],
                fill=(0, 120, 212, 255))

    # Insignia circular verde con flecha de descarga
    bx, by, br = size * 0.72, size * 0.70, size * 0.20
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=_BADGE)
    aw, ah = br * 0.55, br * 0.65
    d.rectangle([bx - aw * 0.35, by - ah, bx + aw * 0.35, by + ah * 0.25],
                fill=_WHITE)
    d.polygon([(bx - aw, by + ah * 0.1), (bx + aw, by + ah * 0.1),
               (bx, by + ah)], fill=_WHITE)
    return img


def main():
    os.makedirs(os.path.join(BASE, 'assets'), exist_ok=True)
    big = draw_icon(256)
    big.save(OUT_PNG)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48),
             (64, 64), (128, 128), (256, 256)]
    big.save(OUT_ICO, format='ICO', sizes=sizes)
    print(f'OK: {OUT_ICO} ({os.path.getsize(OUT_ICO)} bytes) + {OUT_PNG}')


if __name__ == '__main__':
    main()
