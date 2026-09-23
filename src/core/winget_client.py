"""
Cliente para interactuar con WinGet CLI.

Diseño:
- Ejecuta winget mediante subprocess sin ventana de consola (CREATE_NO_WINDOW).
- WinGet no ofrece salida JSON en versiones actuales, por lo que se parsea la
  tabla de texto de forma robusta: las posiciones de las columnas se deducen de
  la línea separadora de guiones, lo que funciona en cualquier idioma.
"""
import os
import re
import subprocess
from typing import List, Optional, Tuple

from .models import Package

# Código de salida de winget cuando no hay actualizaciones disponibles
_EXIT_NO_UPGRADE = 0x8A15002B

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


def _to_signed(code: int) -> int:
    """Convierte códigos de salida sin signo (estilo Windows) a su valor firmado."""
    if code > 0x7FFFFFFF:
        return code - 0x100000000
    return code


class WinGetClient:
    """Wrapper para ejecutar comandos de WinGet y parsear resultados"""

    def __init__(self):
        self.encoding = 'utf-8'
        # Sin ventana de consola al lanzar winget desde una app gráfica
        # (solo existe en Windows; en otros SO vale 0).
        self.creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

    @staticmethod
    def find_winget() -> Optional[str]:
        """Ruta al ejecutable de winget o None si no está en el PATH."""
        import shutil
        return shutil.which('winget')

    def is_available(self) -> bool:
        """Verifica que winget exista y responda (chequeo de arranque)."""
        if not self.find_winget():
            return False
        try:
            result = self._run_raw(['--version'], timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    # ------------------------------------------------------------------ #
    # Ejecución básica
    # ------------------------------------------------------------------ #

    def _run_raw(self, args: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ['winget'] + args,
            capture_output=True,
            text=True,
            encoding=self.encoding,
            errors='replace',
            timeout=timeout,
            creationflags=self.creationflags,
        )

    def _run(self, args: List[str], timeout: int = 120) -> dict:
        """Ejecuta winget y retorna {'rc', 'output', 'error_msg'}."""
        try:
            result = self._run_raw(args, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {'rc': -1, 'output': '', 'error_msg': f'La operación tardó demasiado (límite: {timeout} s)'}
        except FileNotFoundError:
            return {'rc': -1, 'output': '', 'error_msg': 'WinGet no está instalado o no está en el PATH del sistema'}
        except OSError as e:
            return {'rc': -1, 'output': '', 'error_msg': f'Error del sistema: {e}'}

        combined = _ANSI_RE.sub('', (result.stdout or '') + '\n' + (result.stderr or ''))
        combined = combined.replace('\r\n', '\n').replace('\r', '\n')

        error_msg = ''
        if result.returncode != 0:
            error_msg = self._humanize_error(combined, args)
        return {'rc': result.returncode, 'output': combined, 'error_msg': error_msg}

    def _humanize_error(self, output: str, args: List[str]) -> str:
        low = output.lower()
        # Si winget volcó la ayuda (flag inválido, uso incorrecto), las
        # heurísticas por palabras dan falsos positivos ("administrador"
        # aparece en la ayuda): devolver las primeras líneas con el error real.
        if ('uso: winget' in low or 'usage:' in low
                or 'disponibles las siguientes opciones' in low
                or 'available options' in low):
            lines = [ln.strip() for ln in output.strip().split('\n') if ln.strip()]
            body = [ln for ln in lines
                    if not ln.lower().startswith(('administrador de paquetes',
                                                  '©', '(c)'))]
            text = ' '.join(body[:3])
            if text:
                return f'Error de WinGet: {text[:300]}'
        # Permisos: solo señales fuertes (la ayuda menciona "administrador"
        # y antes provocaba falsos positivos).
        if ('access denied' in low or 'acceso denegado' in low
                or '0x80070005' in low or 'permission denied' in low
                or 'permiso denegado' in low or 'sin permiso' in low
                or 'elevat' in low or 'elevaci' in low):
            return 'No tienes permisos suficientes. Ejecuta la aplicación como administrador.'
        if 'network' in low or 'connection' in low or 'internet' in low or 'conexión' in low:
            return 'Error de conexión. Verifica tu conexión a internet.'
        if 'source' in low and ('open' in low or 'update' in low or 'reset' in low):
            return 'Hay un problema con las fuentes de paquetes. Prueba "winget source reset --force".'
        if 'space' in low or 'disco' in low:
            return 'No hay suficiente espacio en disco para completar la operación.'
        if 'cancel' in low or 'cancelad' in low:
            return 'La operación fue cancelada por el usuario o por el instalador.'
        text = ' '.join(line for line in output.strip().split('\n') if line.strip())
        if text:
            return f'Error de WinGet: {text[:300]}'
        cmd = 'winget ' + ' '.join(args) if args else 'winget'
        return f'WinGet falló al ejecutar "{cmd}" sin más detalles.'

    # ------------------------------------------------------------------ #
    # Parser de tabla (independiente del idioma)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _table_rows(output: str) -> Tuple[Optional[List[str]], List[List[str]]]:
        """
        Parsea la tabla de winget: localiza la línea separadora de guiones que
        sigue al encabezado, deduce el inicio de cada columna desde las
        posiciones de las etiquetas del encabezado y recorta cada fila por
        esas posiciones (los valores van alineados a esas posiciones).

        Retorna (encabezados, filas) o (None, []) si no hay tabla.
        """
        lines = output.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Separador: línea de guiones (winget la emite a veces con
            # espacios intermedios según idioma/ancho de columnas).
            if i == 0 or len(stripped) < 5 or stripped.strip('- ') != '':
                continue
            if '-' not in stripped:
                continue
            header_line = lines[i - 1]
            if not header_line.strip():
                continue

            # Inicios de columna: tokens tras el inicio de línea o 2+ espacios
            spans = []
            for m in re.finditer(r'(?:^| {2,})(\S)', header_line):
                start = m.start(1)
                if not spans or start > spans[-1]:
                    spans.append(start)
            if len(spans) < 2:
                continue

            headers = [header_line[s:spans[j + 1] if j + 1 < len(spans) else None].strip()
                       for j, s in enumerate(spans)]

            # winget ajusta el ancho de columnas al contenido: si una columna
            # queda del ancho exacto de su etiqueta (p. ej. "Disponible" vacío),
            # el encabezado siguiente queda a UN solo espacio ("Disponible Origen")
            # y el regex de 2+ espacios lo fusiona en un token. Separa esos
            # tokens cuando cada parte parece una columna conocida.
            headers, spans = WinGetClient._split_merged_headers(headers, spans)

            rows = []
            for data_line in lines[i + 1:]:
                if not data_line.strip():
                    continue
                # Líneas de resumen final (sin alineación con columnas) se descartan
                # porque su primer valor no arranca en la columna 0
                if data_line[0].isspace():
                    continue
                values = []
                for j, s in enumerate(spans):
                    end = spans[j + 1] if j + 1 < len(spans) else len(data_line)
                    values.append(data_line[s:end].strip())
                rows.append(values)
            return headers, rows
        return None, []

    @staticmethod
    def _split_merged_headers(headers: List[str], spans: List[int]
                              ) -> Tuple[List[str], List[int]]:
        """Divide tokens de encabezado fusionados por un solo espacio.

        Caso real (winget list ES): "Disponible Origen" llega como un token.
        Solo se divide si TODAS las partes contienen alguna palabra clave de
        columna conocida, para no romper etiquetas legítimas de 2 palabras.
        """
        pool = ('nombre', 'name', 'id', 'versi', 'version', 'disponib',
                'available', 'disponible', 'origen', 'source',
                'argumento', 'arg', 'url')
        new_headers: List[str] = []
        new_spans: List[int] = []
        for header, start in zip(headers, spans):
            parts = header.split(' ')
            if len(parts) > 1 and all(
                    any(k in p.lower() for k in pool) for p in parts if p):
                offset = start
                for part in parts:
                    if not part:
                        offset += 1
                        continue
                    new_headers.append(part)
                    new_spans.append(offset)
                    offset += len(part) + 1
            else:
                new_headers.append(header)
                new_spans.append(start)
        return new_headers, new_spans

    @staticmethod
    def _col_index(headers: List[str], *keywords: str) -> Optional[int]:
        for idx, header in enumerate(headers):
            low = header.lower()
            if any(k in low for k in keywords):
                return idx
        return None

    @classmethod
    def _rows_to_packages(cls, headers: List[str], rows: List[List[str]]) -> List[Package]:
        raw_name = cls._col_index(headers, 'nombre', 'name')
        idx_name = raw_name if raw_name is not None else 0
        idx_id = cls._col_index(headers, 'id')
        idx_ver = cls._col_index(headers, 'versi', 'version')
        idx_avail = cls._col_index(headers, 'disponib', 'available', 'disponible')
        idx_src = cls._col_index(headers, 'origen', 'source')

        packages = []
        for row in rows:
            def cell(i):
                return row[i] if i is not None and i < len(row) else ''

            pkg_id = cell(idx_id)
            if not pkg_id:
                continue
            packages.append(Package(
                name=cell(idx_name) or pkg_id,
                id=pkg_id,
                version=cell(idx_ver) or 'N/A',
                available_version=cell(idx_avail) or None,
                source=cell(idx_src) or 'winget',
            ))
        return packages

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #

    def list_packages(self) -> Tuple[List[Package], Optional[str]]:
        """Lista los paquetes instalados."""
        result = self._run([
            'list',
            '--accept-source-agreements',
            '--disable-interactivity',
        ], timeout=180)

        if result['rc'] != 0:
            return [], result['error_msg'] or 'Error desconocido'

        headers, rows = self._table_rows(result['output'])
        if headers is None:
            return [], 'No se pudo interpretar la salida de WinGet'
        return self._rows_to_packages(headers, rows), None

    def get_upgrades(self) -> Tuple[List[Package], Optional[str]]:
        """Lista los paquetes con actualizaciones disponibles."""
        result = self._run([
            'upgrade',
            '--include-unknown',
            '--include-pinned',
            '--accept-source-agreements',
            '--disable-interactivity',
        ], timeout=180)

        if result['rc'] != 0:
            # Sin actualizaciones disponibles no es un error real
            low = result['output'].lower()
            if 'no hay' in low or 'no upgrade' in low or 'ninguna actualización' in low:
                return [], None
            return [], result['error_msg'] or 'Error desconocido'

        headers, rows = self._table_rows(result['output'])
        if headers is None:
            return [], 'No se pudo interpretar la salida de WinGet'
        packages = self._rows_to_packages(headers, rows)
        # En algunas salidas la versión instalada va en "Versión" y la nueva en
        # "Disponible"; conservar solo las que tienen algo disponible
        packages = [p for p in packages
                    if p.available_version and p.available_version.lower() != 'unknown']
        return packages, None

    def search_packages(self, query: str) -> Tuple[List[dict], Optional[str]]:
        """Busca paquetes disponibles para instalar."""
        result = self._run([
            'search', query,
            '--accept-source-agreements',
            '--disable-interactivity',
        ], timeout=90)

        if result['rc'] != 0:
            # Sin coincidencias no es un error: lista vacía
            low = result['output'].lower()
            if ('no se encontr' in low or 'no matching' in low
                    or 'no packages found' in low or 'ningún paquete' in low):
                return [], None
            return [], result['error_msg'] or 'Error desconocido'

        headers, rows = self._table_rows(result['output'])
        if headers is None:
            return [], None  # Sin resultados

        raw_name = self._col_index(headers, 'nombre', 'name')
        idx_name = raw_name if raw_name is not None else 0
        idx_id = self._col_index(headers, 'id')
        idx_ver = self._col_index(headers, 'versi', 'version')
        idx_src = self._col_index(headers, 'origen', 'source')

        packages = []
        for row in rows:
            def cell(i):
                return row[i] if i is not None and i < len(row) else ''

            pkg_id = cell(idx_id)
            if not pkg_id:
                continue
            packages.append({
                'name': cell(idx_name) or pkg_id,
                'id': pkg_id,
                'version': cell(idx_ver),
                'source': cell(idx_src) or 'winget',
            })
        return packages, None

    def show_package_info(self, package_id: str) -> Tuple[dict, Optional[str]]:
        """Información detallada de un paquete (salida de `winget show`)."""
        # Los IDs MSIX\... y ARP\... son entradas locales (Store/sistema),
        # no existen en el catálogo: `winget show` siempre falla con ellos.
        # Se devuelven solo los datos locales sin llamar a winget.
        if package_id.upper().startswith(('MSIX\\', 'ARP\\')):
            return ({
                'Nota': 'Sin ficha remota: es una aplicación del sistema o de '
                        'Microsoft Store; se muestran únicamente los datos locales.',
            }, None)
        result = self._run([
            'show', '--id', package_id, '--exact',
            '--accept-source-agreements',
            '--disable-interactivity',
        ], timeout=60)

        if result['rc'] != 0:
            low = result['output'].lower()
            # El paquete existe localmente pero WinGet no tiene su ficha
            # (o la fuente msstore falló): mostrar datos locales en vez de error.
            if ('no se encontr' in low or 'no matching' in low
                    or 'not found' in low or 'ningún paquete coincidente' in low):
                return ({
                    'Nota': 'WinGet no devolvió ficha remota para este paquete; '
                            'se muestran únicamente los datos locales.',
                }, None)
            return {}, result['error_msg'] or 'Error desconocido'

        info: dict = {}
        last_key = None
        for line in result['output'].split('\n'):
            match = re.match(r'^\s*([^:]{1,60}):\s?(.*)$', line)
            if match and not line.startswith('  '):
                last_key = match.group(1).strip()
                info.setdefault(last_key, match.group(2).strip())
            elif last_key and line.strip():
                # Líneas de continuación (descripciones multilínea)
                if not info[last_key]:
                    info[last_key] = line.strip()
                else:
                    info[last_key] += '\n' + line.strip()
        return info, None

    # ------------------------------------------------------------------ #
    # Acciones
    # ------------------------------------------------------------------ #

    def run_streaming(self, args: List[str], timeout: int = 600,
                      on_line=None, cancel_event=None) -> dict:
        """Ejecuta winget emitiendo cada línea de salida a `on_line`.

        `on_line` se llama desde un hilo lector con cada línea de texto
        (sin salto final). Si `cancel_event` (threading.Event) se activa,
        el proceso se termina y el resultado lleva 'cancelled': True.
        Retorna {'rc', 'output', 'error_msg', 'cancelled'}.
        """
        import threading
        import time

        try:
            proc = subprocess.Popen(
                ['winget'] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=self.encoding,
                errors='replace',
                creationflags=self.creationflags,
            )
        except FileNotFoundError:
            return {'rc': -1, 'output': '',
                    'error_msg': 'WinGet no está instalado o no está en el PATH del sistema',
                    'cancelled': False}
        except OSError as e:
            return {'rc': -1, 'output': '', 'error_msg': f'Error del sistema: {e}',
                    'cancelled': False}

        chunks: List[str] = []

        def _reader():
            try:
                for raw in proc.stdout:
                    chunks.append(raw)
                    if on_line:
                        # winget reescribe el progreso con \r: mostrar cada tramo
                        for part in raw.replace('\r', '\n').split('\n'):
                            text = part.strip()
                            if text:
                                on_line(text)
            except (OSError, ValueError):
                pass

        reader = threading.Thread(target=_reader, daemon=True)
        reader.start()

        cancelled = False
        start = time.time()
        while reader.is_alive():
            if cancel_event is not None and cancel_event.is_set():
                cancelled = True
                try:
                    proc.terminate()
                except OSError:
                    pass
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    try:
                        proc.kill()
                    except OSError:
                        pass
                break
            if time.time() - start > timeout:
                try:
                    proc.kill()
                except OSError:
                    pass
                break
            time.sleep(0.1)

        try:
            rc = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            rc = -1
        reader.join(timeout=5)

        combined = _ANSI_RE.sub('', ''.join(chunks))
        combined = combined.replace('\r\n', '\n').replace('\r', '\n')

        if cancelled:
            return {'rc': rc, 'output': combined,
                    'error_msg': 'Operación cancelada por el usuario.',
                    'cancelled': True}
        if time.time() - start >= timeout and rc != 0 and not combined.strip():
            return {'rc': -1, 'output': combined,
                    'error_msg': f'La operación tardó demasiado (límite: {timeout} s)',
                    'cancelled': False}
        error_msg = ''
        if rc != 0:
            error_msg = self._humanize_error(combined, args)
        return {'rc': rc, 'output': combined, 'error_msg': error_msg,
                'cancelled': False}

    @staticmethod
    def _action_args(command: str, package_id: str, silent: bool) -> List[str]:
        # OJO: `uninstall` NO acepta --accept-package-agreements (winget lo
        # rechaza volcando la ayuda). Solo install/upgrade lo admiten.
        args = [
            command, '--id', package_id, '--exact',
            '--accept-source-agreements',
            '--disable-interactivity',
        ]
        if command in ('install', 'upgrade'):
            args.append('--accept-package-agreements')
        if silent and command in ('install', 'upgrade', 'uninstall'):
            args.append('--silent')
        return args

    def _maybe_stream(self, args: List[str], timeout: int,
                      on_line, cancel_event) -> dict:
        if on_line is None and cancel_event is None:
            result = self._run(args, timeout=timeout)
            result['cancelled'] = False
            return result
        return self.run_streaming(args, timeout=timeout,
                                  on_line=on_line, cancel_event=cancel_event)

    def install_package(self, package_id: str, silent: bool = True,
                        on_line=None, cancel_event=None) -> Tuple[bool, str]:
        result = self._maybe_stream(
            self._action_args('install', package_id, silent),
            timeout=600, on_line=on_line, cancel_event=cancel_event)
        if result.get('cancelled'):
            return False, f'Instalación de {package_id} cancelada'
        if result['rc'] != 0:
            low = result['output'].lower()
            if 'already installed' in low or 'ya está instalado' in low:
                return True, f'El paquete {package_id} ya estaba instalado'
            return False, f"No se pudo instalar {package_id}: {result['error_msg']}"
        return True, f'Paquete {package_id} instalado correctamente'

    def upgrade_package(self, package_id: str, silent: bool = True,
                        on_line=None, cancel_event=None) -> Tuple[bool, str]:
        result = self._maybe_stream(
            self._action_args('upgrade', package_id, silent),
            timeout=900, on_line=on_line, cancel_event=cancel_event)
        if result.get('cancelled'):
            return False, f'Actualización de {package_id} cancelada'
        if result['rc'] != 0:
            low = result['output'].lower()
            if 'no applicable' in low or 'ninguna actualización' in low or 'no update' in low:
                return True, f'El paquete {package_id} ya está en su versión más reciente'
            return False, f"No se pudo actualizar {package_id}: {result['error_msg']}"
        return True, f'Paquete {package_id} actualizado correctamente'

    def upgrade_all(self, silent: bool = True,
                    on_line=None, cancel_event=None) -> Tuple[bool, str]:
        args = ['upgrade', '--all', '--accept-package-agreements',
                '--accept-source-agreements', '--disable-interactivity']
        if silent:
            args.append('--silent')
        result = self._maybe_stream(args, timeout=3600,
                                    on_line=on_line, cancel_event=cancel_event)
        if result.get('cancelled'):
            return False, 'Actualización masiva cancelada'
        if result['rc'] != 0:
            if _to_signed(result['rc']) & 0xFFFFFFFF == _EXIT_NO_UPGRADE:
                return True, 'Todos los paquetes ya están actualizados'
            return False, f"No se pudieron actualizar los paquetes: {result['error_msg']}"
        return True, 'Actualización masiva completada'

    def uninstall_package(self, package_id: str, silent: bool = True,
                          on_line=None, cancel_event=None) -> Tuple[bool, str]:
        result = self._maybe_stream(
            self._action_args('uninstall', package_id, silent),
            timeout=300, on_line=on_line, cancel_event=cancel_event)
        if result.get('cancelled'):
            return False, f'Desinstalación de {package_id} cancelada'
        if result['rc'] != 0:
            return False, f"No se pudo desinstalar {package_id}: {result['error_msg']}"
        return True, f'Paquete {package_id} desinstalado correctamente'

    # ------------------------------------------------------------------ #
    # Pines (winget pin)
    # ------------------------------------------------------------------ #

    def pin_package(self, package_id: str) -> Tuple[bool, str]:
        result = self._run([
            'pin', 'add', '--id', package_id, '--exact', '--blocking',
            '--accept-source-agreements', '--disable-interactivity',
        ], timeout=60)
        if result['rc'] != 0:
            return False, f"No se pudo fijar {package_id}: {result['error_msg']}"
        return True, f'{package_id} fijado (no se actualizará con "Actualizar Todo")'

    def unpin_package(self, package_id: str) -> Tuple[bool, str]:
        result = self._run([
            'pin', 'remove', '--id', package_id, '--exact',
            '--accept-source-agreements', '--disable-interactivity',
        ], timeout=60)
        if result['rc'] != 0:
            return False, f"No se pudo quitar el fijado de {package_id}: {result['error_msg']}"
        return True, f'{package_id} vuelve a actualizarse normalmente'

    def list_pinned_ids(self) -> List[str]:
        """IDs de paquetes fijados actualmente (vacío si el comando falla)."""
        result = self._run(['pin', 'list', '--disable-interactivity'], timeout=60)
        if result['rc'] != 0:
            return []
        headers, rows = self._table_rows(result['output'])
        if headers is None:
            return []
        idx_id = self._col_index(headers, 'id')
        if idx_id is None:
            return []
        return [row[idx_id] for row in rows if idx_id < len(row) and row[idx_id].strip()]

    # ------------------------------------------------------------------ #
    # Fuentes
    # ------------------------------------------------------------------ #

    def list_sources(self) -> Tuple[List[dict], Optional[str]]:
        result = self._run(['source', 'list', '--disable-interactivity'], timeout=60)
        if result['rc'] != 0:
            return [], result['error_msg'] or 'Error desconocido'

        headers, rows = self._table_rows(result['output'])
        if headers is None:
            return [], None
        raw_name = self._col_index(headers, 'nombre', 'name')
        idx_name = raw_name if raw_name is not None else 0
        idx_arg = self._col_index(headers, 'argumento', 'arg', 'url')

        sources = []
        for row in rows:
            name = row[idx_name] if idx_name < len(row) else ''
            arg = row[idx_arg] if idx_arg is not None and idx_arg < len(row) else ''
            if name:
                sources.append({'name': name, 'arg': arg})
        return sources, None

    def add_source(self, name: str, arg: str) -> Tuple[bool, str]:
        result = self._run([
            'source', 'add', '--name', name, '--arg', arg,
            '--accept-source-agreements', '--disable-interactivity',
        ], timeout=120)
        if result['rc'] != 0:
            return False, f"No se pudo agregar la fuente: {result['error_msg']}"
        return True, f'Fuente {name} agregada correctamente'

    def remove_source(self, name: str) -> Tuple[bool, str]:
        result = self._run(['source', 'remove', '--name', name, '--disable-interactivity'], timeout=60)
        if result['rc'] != 0:
            return False, f"No se pudo eliminar la fuente: {result['error_msg']}"
        return True, f'Fuente {name} eliminada correctamente'

    # ------------------------------------------------------------------ #
    # Limpieza segura de temporales
    # ------------------------------------------------------------------ #

    def clean_temp_files(self) -> Tuple[bool, str]:
        """
        Elimina únicamente los instaladores temporales de winget en %TEMP%.
        Nunca toca los directorios de instalación ni de paquetes portables.
        """
        import glob
        import shutil

        temp_dir = os.environ.get('TEMP', '')
        if not temp_dir:
            return False, 'No se pudo localizar la carpeta temporal'

        removed = 0
        for pattern in ('winget*', 'WinGet*'):
            for path in glob.glob(os.path.join(temp_dir, pattern)):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                    removed += 1
                except OSError:
                    continue

        if removed:
            return True, f'Se eliminaron {removed} elementos temporales de WinGet'
        return True, 'No hay archivos temporales de WinGet que limpiar'
