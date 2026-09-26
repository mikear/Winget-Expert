"""
Regenera las imágenes del README (banner + capturas) con datos reales.

Debe ejecutarse con el plataforma nativa de Windows (NO offscreen: las
fuentes se renderizan mal sin pantalla real). Uso, desde la raíz del repo:

    python tools/actualizar_imagenes_readme.py

Genera:
- docs/banner.png (render exacto del splash, 1280x720)
- docs/screenshots/01-tabla.png      (1600x1000)
- docs/screenshots/02-arbol.png      (1600x1000)
- docs/screenshots/03-actualizando.png (900x600)
- docs/screenshots/04-detalles.png   (800x650)

La captura 03 usa un StreamWorker con salida simulada (no toca WinGet).
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


def _esperar(app, cond, timeout_s, etiqueta):
    limite = time.monotonic() + timeout_s
    while not cond():
        if time.monotonic() > limite:
            raise TimeoutError(f'Tiempo de espera agotado: {etiqueta}')
        app.processEvents()
        time.sleep(0.03)


def _normalizar(ruta, ancho, alto):
    img = Image.open(ruta)
    if img.size != (ancho, alto):
        img = img.resize((ancho, alto), Image.LANCZOS)
        img.save(ruta)
    print(f'[OK] {ruta} {Image.open(ruta).size}')


def main():
    os.chdir(BASE)

    app = QApplication(sys.argv)
    app.setApplicationName('WinGet Expert')

    from src.core.settings import AppSettings
    from src.ui.theme import apply_theme
    from src.ui.main_window import MainWindow
    from src.ui.dialogs import PackageDetailsDialog, OperationDialog, StreamWorker
    from src.ui.splash import SplashScreen

    # Banner: render exacto del splash (el splash dibuja su pixmap a 2x)
    splash = SplashScreen()
    splash._pixmap.save('docs/banner.png')
    splash.deleteLater()
    app.processEvents()
    print('[OK] docs/banner.png (desde el diseno del splash)')

    settings = AppSettings()
    settings.theme = 'light'
    settings.auto_check_updates = False
    settings.save = lambda *a, **k: None  # no tocar el settings.json real
    apply_theme(app, False)

    window = MainWindow(app, splash=None)
    window.setGeometry(120, 80, 1600, 1000)
    window.show()

    # Esperar la carga real de paquetes (winget list + fechas)
    _esperar(app, lambda: (not window._busy and window.packages
                           and not window.progress_bar.isVisible()), 120, 'carga de paquetes')
    # Incluir paquetes del sistema (como en el uso real) y repoblar
    window.show_system.setChecked(True)
    app.processEvents()
    time.sleep(0.4)

    # 01: vista tabla
    window.grab().save('docs/screenshots/01-tabla.png')

    # 02: vista arbol (grupos expandidos)
    window.view_combo.setCurrentText('Árbol')
    app.processEvents()
    time.sleep(0.3)
    window.tree.expandAll()
    app.processEvents()
    time.sleep(0.2)
    window.grab().save('docs/screenshots/02-arbol.png')
    window.view_combo.setCurrentText('Tabla')
    app.processEvents()

    # 03: dialogo de operacion con log en vivo (worker simulado).
    # Preferir un paquete con actualización real para el subtítulo.
    pkg = next((p for p in window.filtered_packages if p.has_update), None) \
        or window.filtered_packages[0]
    version_destino = pkg.available_version or '2.46.0'

    def flujo_simulado(on_line=None, cancel_event=None):
        lineas = [
            'WinGet, versión 1.29.0',
            f'Buscando actualizaciones para: {pkg.id}',
            f'Encontrado {pkg.name} [{pkg.id}]',
            'Descargando instalador...',
            f'{version_destino} [============================] 100%',
            'Instalando el paquete...',
            'Se instaló correctamente el paquete',
        ]
        for linea in lineas:
            if cancel_event is not None and cancel_event.is_set():
                return False, 'Operación cancelada por el usuario'
            if on_line is not None:
                on_line(linea)
            time.sleep(0.35)
        return True, f'{pkg.name} se actualizó correctamente'

    worker = StreamWorker(flujo_simulado)
    op_dlg = OperationDialog(
        f'Actualizar {pkg.name}',
        f'{pkg.version} → {version_destino} (salida de WinGet en vivo)', worker)
    op_dlg.resize(900, 600)
    op_dlg.show()
    _esperar(app, lambda: len(op_dlg.log_view.toPlainText().splitlines()) >= 5,
             30, 'lineas del log simulado')
    time.sleep(0.3)
    op_dlg.grab().save('docs/screenshots/03-actualizando.png')
    _esperar(app, lambda: op_dlg._done, 30, 'fin del worker simulado')
    op_dlg.close()

    # 04: detalles + historial (datos reales del paquete via winget show)
    info, error = window.client.show_package_info(pkg.id)
    det_dlg = PackageDetailsDialog(pkg, info if not error else {},
                                   window.settings.history_for(pkg.id))
    det_dlg.resize(800, 650)
    det_dlg.show()
    app.processEvents()
    time.sleep(0.4)
    det_dlg.grab().save('docs/screenshots/04-detalles.png')
    det_dlg.close()

    window.close()
    app.processEvents()

    # Normalizar a los tamaños que usa el README
    _normalizar('docs/banner.png', 1280, 720)
    _normalizar('docs/screenshots/01-tabla.png', 1600, 1000)
    _normalizar('docs/screenshots/02-arbol.png', 1600, 1000)
    _normalizar('docs/screenshots/03-actualizando.png', 900, 600)
    _normalizar('docs/screenshots/04-detalles.png', 800, 650)
    print('[OK] Imagenes del README actualizadas')


if __name__ == '__main__':
    main()
