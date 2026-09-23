"""
Fechas de instalación desde el propio Windows (sin WinGet).

Fuentes (de más a menos precisa):
1. Entradas MSIX\\... / ARP\\...: correlación directa con Appx y el registro.
2. Registro de desinstalación (DisplayName + InstallDate) por nombre.
3. Historial de esta app (lo consulta el llamador, no este módulo).

Todo es de solo lectura. El resultado se cachea hasta `refresh_install_dates()`.
"""
import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

_cache: Optional[Dict[str, Dict[str, str]]] = None


def _norm(text: str) -> str:
    return ' '.join((text or '').lower().split())


def _to_iso(raw: str) -> Optional[str]:
    raw = (raw or '').strip()
    if len(raw) == 8 and raw.isdigit():  # formato típico del registro: AAAAMMDD
        return f'{raw[:4]}-{raw[4:6]}-{raw[6:8]}'
    if len(raw) >= 10 and raw[4:5] == '-' and raw[7:8] == '-':
        return raw[:10]
    return None


def _filetime_to_iso(filetime: int) -> Optional[str]:
    try:
        dt = datetime(1601, 1, 1) + timedelta(microseconds=filetime // 10)
        return dt.strftime('%Y-%m-%d')
    except (OverflowError, OSError, ValueError):
        return None


def _folder_date(path: str) -> Optional[str]:
    try:
        return datetime.fromtimestamp(os.path.getctime(path)).strftime('%Y-%m-%d')
    except OSError:
        return None


def _read_registry() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Retorna (por_nombre, por_subclave).

    por_nombre: {DisplayName normalizado: 'YYYY-MM-DD'} (solo InstallDate).
    por_subclave: {subclave en minúsculas: fecha} con InstallDate o, como
    respaldo, la última modificación de la clave (instalación/actualización).
    """
    try:
        import winreg
    except ImportError:
        return {}, {}
    by_name: Dict[str, str] = {}
    by_sub: Dict[str, str] = {}
    targets = [
        (winreg.HKEY_LOCAL_MACHINE,
         r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_LOCAL_MACHINE,
         r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_CURRENT_USER,
         r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
    ]
    for hive, path in targets:
        try:
            root = winreg.OpenKey(hive, path)
        except OSError:
            continue
        try:
            index = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(root, index)
                except OSError:
                    break
                index += 1
                try:
                    sub = winreg.OpenKey(root, sub_name)
                except OSError:
                    continue
                try:
                    try:
                        display, _ = winreg.QueryValueEx(sub, 'DisplayName')
                    except OSError:
                        continue
                    iso = None
                    try:
                        raw_date, _ = winreg.QueryValueEx(sub, 'InstallDate')
                        iso = _to_iso(str(raw_date))
                    except OSError:
                        pass
                    if iso is None:
                        # Respaldo: última escritura de la clave
                        try:
                            iso = _filetime_to_iso(winreg.QueryInfoKey(sub)[2])
                        except OSError:
                            pass
                    if not iso:
                        continue
                    name = _norm(str(display))
                    if name:
                        by_name.setdefault(name, iso)
                    by_sub.setdefault(sub_name.lower(), iso)
                finally:
                    winreg.CloseKey(sub)
        finally:
            winreg.CloseKey(root)
    return by_name, by_sub


def _read_appx() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Retorna (fechas, ubicaciones): {nombre Appx en minúsculas: ...}.

    InstallDate suele venir vacío en Windows; la ubicación permite usar la
    fecha de la carpeta como respaldo (ver `get_install_date`).
    """
    cmd = ("Get-AppxPackage | Select-Object Name, InstallLocation, "
           "@{Name='InstallDate';Expression={$_.InstallDate.ToString('yyyy-MM-dd')}} "
           "| ConvertTo-Json -Compress")
    try:
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', cmd],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=90,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}, {}
    if proc.returncode != 0:
        return {}, {}
    try:
        data = json.loads(proc.stdout or '')
    except (json.JSONDecodeError, ValueError):
        return {}, {}
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return {}, {}
    dates: Dict[str, str] = {}
    locs: Dict[str, str] = {}
    for entry in data:
        if not isinstance(entry, dict):
            continue
        name = _norm(str(entry.get('Name', '')))
        if not name:
            continue
        iso = _to_iso(str(entry.get('InstallDate', '')))
        if iso:
            dates.setdefault(name, iso)
        loc = str(entry.get('InstallLocation', '') or '').strip()
        if loc:
            locs.setdefault(name, loc)
    return dates, locs


def refresh_install_dates() -> Dict[str, Dict[str, str]]:
    """Reconstruye la caché (llamar en un worker: Appx tarda unos segundos)."""
    global _cache
    reg_names, reg_subs = _read_registry()
    appx_dates, appx_locs = _read_appx()
    _cache = {'reg_names': reg_names, 'reg_subs': reg_subs,
              'appx_dates': appx_dates, 'appx_locs': appx_locs}
    return _cache


def get_install_date(package_id: str, package_name: str) -> Optional[str]:
    """Fecha de instalación 'YYYY-MM-DD' o None si no se pudo determinar.

    Para MSIX sin InstallDate se usa la fecha de su carpeta (equivale a la
    instalación de la versión actual); para ARP sin InstallDate, la última
    modificación de su clave de registro.
    """
    global _cache
    if _cache is None:
        refresh_install_dates()
    assert _cache is not None
    upper = (package_id or '').upper()

    if upper.startswith('MSIX\\'):
        # MSIX\<FullName>: el nombre Appx es el primer segmento
        token = package_id[5:].split('_')[0].lower()
        hit = _cache['appx_dates'].get(token)
        if hit:
            return hit
        loc = _cache['appx_locs'].get(token)
        if loc:
            folder = _folder_date(loc)
            if folder:
                return folder
    elif upper.startswith('ARP\\'):
        # ARP\...\<subclave del registro>
        sub = package_id.split('\\')[-1].lower()
        hit = _cache['reg_subs'].get(sub)
        if hit:
            return hit

    # Reserva: coincidencia por nombre visible
    want = _norm(package_name)
    reg_names = _cache['reg_names']
    if want in reg_names:
        return reg_names[want]
    for name, iso in reg_names.items():
        if want and (want in name or name in want):
            return iso
    return None
