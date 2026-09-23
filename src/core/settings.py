"""
Persistencia de configuración e historial de acciones.

Guarda un JSON en %APPDATA%\\WinGet GUI Manager\\settings.json con:
- tema elegido (claro/oscuro)
- geometría de la ventana principal
- historial de instalaciones/actualizaciones/desinstalaciones
- preferencias de filtros
"""
import json
import os
from datetime import datetime
from typing import List, Optional

_APP_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'WinGet GUI Manager')
_SETTINGS_FILE = os.path.join(_APP_DIR, 'settings.json')

_MAX_HISTORY = 500


class AppSettings:
    """Gestor de configuración persistente de la aplicación"""

    def __init__(self):
        self.data = {
            'theme': 'dark',
            'window_geometry': None,
            'include_system': True,
            'auto_check_updates': False,
            'history': [],
        }
        self.load()

    # ------------------------------ carga / guardado ---------------- #

    def load(self):
        try:
            with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                stored = json.load(f)
            if isinstance(stored, dict):
                self.data.update(stored)
        except (OSError, json.JSONDecodeError):
            pass  # Primera ejecución o archivo corrupto: usar valores por defecto

    def save(self):
        try:
            os.makedirs(_APP_DIR, exist_ok=True)
            with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except OSError:
            pass  # Sin permisos de escritura: la app sigue funcionando sin persistir

    # ------------------------------ acceso tipado -------------------- #

    @property
    def theme(self) -> str:
        return self.data.get('theme', 'dark')

    @theme.setter
    def theme(self, value: str):
        self.data['theme'] = value

    @property
    def window_geometry(self) -> Optional[bytes]:
        return self.data.get('window_geometry')

    @window_geometry.setter
    def window_geometry(self, value):
        if value is None:
            self.data['window_geometry'] = None
            return
        try:
            # QByteArray -> hex str
            self.data['window_geometry'] = bytes(value.toHex()).decode('ascii')
        except AttributeError:
            # bytes / bytearray
            self.data['window_geometry'] = bytes(value).hex() if value else None

    def get_geometry(self) -> Optional[bytes]:
        from PySide6.QtCore import QByteArray
        raw = self.data.get('window_geometry')
        if not raw or not isinstance(raw, str):
            return None
        try:
            bytes.fromhex(raw)  # valida: fromHex de Qt ignora basura sin avisar
        except (ValueError, TypeError):
            return None
        try:
            return QByteArray.fromHex(raw.encode('ascii'))
        except (AttributeError, TypeError):
            return None

    @property
    def include_system(self) -> bool:
        return self.data.get('include_system', True)

    @include_system.setter
    def include_system(self, value: bool):
        self.data['include_system'] = value

    @property
    def auto_check_updates(self) -> bool:
        return self.data.get('auto_check_updates', False)

    @auto_check_updates.setter
    def auto_check_updates(self, value: bool):
        self.data['auto_check_updates'] = value

    @property
    def silent_mode(self) -> bool:
        """Instalar/actualizar sin mostrar ventanas del instalador (--silent)."""
        return self.data.get('silent_mode', True)

    @silent_mode.setter
    def silent_mode(self, value: bool):
        self.data['silent_mode'] = value

    # ------------------------------ historial ------------------------ #

    @property
    def history(self) -> List[dict]:
        return self.data.get('history', [])

    def add_history(self, package_id: str, name: str, action: str, version: str = ''):
        """Registra una acción sobre un paquete ('instalado', 'actualizado', 'desinstalado')"""
        self.data.setdefault('history', []).append({
            'id': package_id,
            'name': name,
            'action': action,
            'version': version,
            'date': datetime.now().isoformat(timespec='seconds'),
        })
        # Limitar tamaño del historial
        self.data['history'] = self.data['history'][-_MAX_HISTORY:]
        self.save()

    def history_for(self, package_id: str) -> List[dict]:
        return [h for h in self.history if h['id'] == package_id]

    def history_last(self, package_id: str, action: Optional[str] = None) -> Optional[dict]:
        """Última entrada del historial para un paquete (opcionalmente filtrada por acción)."""
        entries = [h for h in self.history
                   if h['id'] == package_id and (action is None or h.get('action') == action)]
        return entries[-1] if entries else None
