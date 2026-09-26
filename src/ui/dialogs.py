"""
Diálogos principales: instalar, detalles, restaurar backup y fuentes.
"""
import threading
import time
from datetime import datetime

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from src.ui import icons
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QMessageBox, QProgressBar, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)


class WorkerThread(QThread):
    """Thread para operaciones de búsqueda e instalación sin bloquear la UI"""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.finished.emit(self.func(*self.args, **self.kwargs))
        except Exception as e:  # noqa: BLE001 - se reporta a la UI tal cual
            self.error.emit(str(e))


class InstallDialog(QDialog):
    """Diálogo para instalar nuevos paquetes"""

    def __init__(self, client, settings, parent=None):
        super().__init__(parent)
        self.client = client
        self.settings = settings
        self.search_results = []
        self.installed_any = False
        self._worker = None
        self._busy = False

        self.setWindowTitle("Instalar Paquetes")
        self.resize(820, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar paquetes (nombre, id, moniker)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.returnPressed.connect(self.search_packages)
        search_layout.addWidget(QLabel("Buscar:"), 0)
        search_layout.addWidget(self.search_input, 1)

        self.search_btn = QPushButton(icons.icon(icons.SEARCH), "Buscar")
        self.search_btn.clicked.connect(self.search_packages)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        layout.addWidget(self.progress_bar)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Nombre", "ID", "Versión", "Fuente", "Instalar"])
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)

        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 90)
        layout.addWidget(self.results_table, 1)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _set_busy(self, busy: bool, message: str = ""):
        self._busy = busy
        self.progress_bar.setVisible(busy)
        self.search_btn.setEnabled(not busy)
        self.status_label.setText(message)

    def search_packages(self):
        query = self.search_input.text().strip()
        if not query or self._busy:
            return

        self._set_busy(True, "Buscando...")
        self._worker = WorkerThread(self.client.search_packages, query)
        self._worker.finished.connect(self.on_search_finished)
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_search_finished(self, result):
        packages, error = result
        if error:
            self._set_busy(False)
            QMessageBox.warning(self, "Error", f"Error en búsqueda: {error}")
            return
        self._set_busy(False, f"{len(packages)} resultados")
        self.search_results = packages
        self.populate_results(packages)

    def on_error(self, error_msg):
        self._set_busy(False)
        QMessageBox.critical(self, "Error", f"Error: {error_msg}")

    def populate_results(self, packages):
        self.results_table.setRowCount(0)
        self.results_table.setRowCount(len(packages))
        for row, pkg in enumerate(packages):
            name_item = QTableWidgetItem(pkg['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, pkg['id'])
            self.results_table.setItem(row, 0, name_item)
            self.results_table.setItem(row, 1, QTableWidgetItem(pkg['id']))
            self.results_table.setItem(row, 2, QTableWidgetItem(pkg['version']))
            self.results_table.setItem(row, 3, QTableWidgetItem(pkg['source']))

            install_btn = QPushButton("Instalar")
            install_btn.clicked.connect(lambda checked, p=pkg: self.install_package(p))
            self.results_table.setCellWidget(row, 4, install_btn)

    def install_package(self, package):
        if self._busy:
            return
        reply = QMessageBox.question(
            self, "Confirmar instalación",
            f"¿Instalar {package['name']} v{package['version']}?\n\nID: {package['id']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True, f"Instalando {package['name']}...")
        self._worker = WorkerThread(self.client.install_package, package['id'],
                                    silent=self.settings.silent_mode)
        self._worker.finished.connect(lambda r: self.on_install_finished(r, package))
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_install_finished(self, result, package):
        success, message = result
        if success:
            self.installed_any = True
            self.settings.add_history(package['id'], package['name'],
                                      'instalado', package.get('version', ''))
            self._set_busy(False, message)
        else:
            self._set_busy(False)
            QMessageBox.warning(self, "Error", message)

    def done(self, result):
        # Aceptar el diálogo si se instaló algo, para que la lista principal se refresque
        if self.installed_any:
            super().done(QDialog.DialogCode.Accepted)
        else:
            super().done(result)


class PackageDetailsDialog(QDialog):
    """Diálogo con detalles e historial de acciones de un paquete"""

    def __init__(self, package, info, history, parent=None):
        super().__init__(parent)
        self.package = package
        self.info = info or {}
        self.history = history or []

        self.setWindowTitle(f"Detalles - {package.name}")
        self.resize(640, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(f"<h2>{self.package.name}</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        tabs = QTabWidget()

        # Pestaña de información
        info_table = QTableWidget()
        info_table.setColumnCount(2)
        info_table.setHorizontalHeaderLabels(["Propiedad", "Valor"])
        info_table.verticalHeader().setVisible(False)
        info_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        data = [
            ("ID", self.package.id),
            ("Versión Instalada", self.package.version),
            ("Versión Disponible", self.package.available_version or "-"),
            ("Fuente", self.package.source),
            ("Estado", self.package.status),
            ("Fijado (pin)", "Sí" if self.package.pinned else "No"),
            ("Fecha de instalación",
             getattr(self.package, 'install_date', None) or "-"),
            ("Última actualización",
             getattr(self.package, 'updated_date', None) or "-"),
        ]
        skip = {"Versión", "Encontrado"}
        for key, value in self.info.items():
            if key not in skip and value:
                data.append((key, str(value)))

        info_table.setRowCount(len(data))
        for row, (key, value) in enumerate(data):
            info_table.setItem(row, 0, QTableWidgetItem(key))
            value_item = QTableWidgetItem(str(value))
            value_item.setToolTip(str(value))
            info_table.setItem(row, 1, value_item)

        header = info_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tabs.addTab(info_table, "Información")

        # Pestaña de historial de acciones
        history_text = QTextEdit()
        history_text.setReadOnly(True)
        if self.history:
            lines = []
            for entry in reversed(self.history):  # Más reciente primero
                lines.append(f"{entry['date']} — {entry['action'].title()} "
                             f"(versión {entry.get('version') or 'n/d'})")
            history_text.setPlainText("Historial de acciones en esta aplicación:\n\n" +
                                      "\n".join(lines))
        else:
            history_text.setPlainText("Todavía no hay acciones registradas para este paquete.")
        tabs.addTab(history_text, "Historial")

        layout.addWidget(tabs, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)


class RestoreDialog(QDialog):
    """Diálogo para restaurar paquetes desde un backup"""

    def __init__(self, packages, client, settings, parent=None):
        super().__init__(parent)
        self.client = client
        self.settings = settings
        self.selected_packages = []
        self.results = []
        self._worker = None
        self._index = 0
        self._queue = []

        self.setWindowTitle("Restaurar Paquetes")
        self.resize(720, 520)
        self._packages = packages
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Se encontraron {len(self._packages)} paquetes en el backup."))

        self.package_list = QListWidget()
        self.package_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        from PySide6.QtWidgets import QListWidgetItem
        for pkg in self._packages:
            if not isinstance(pkg, dict) or not pkg.get('id'):
                continue
            item_text = f"{pkg.get('name', pkg['id'])} - v{pkg.get('version', '?')} ({pkg.get('source', '?')})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, pkg)
            self.package_list.addItem(item)
        layout.addWidget(self.package_list, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Seleccionar Todos")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)

        restore_btn = QPushButton("Restaurar Seleccionados")
        restore_btn.clicked.connect(self.restore_packages)
        button_layout.addWidget(restore_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        dialog_buttons.rejected.connect(self.accept)
        layout.addWidget(dialog_buttons)

    def select_all(self):
        self.package_list.selectAll()

    def restore_packages(self):
        selected = self.package_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Selecciona paquetes para restaurar")
            return

        self._queue = [i.data(Qt.ItemDataRole.UserRole) for i in selected]
        # Filtrar entradas corruptas (sin id) que no se pueden instalar
        self._queue = [p for p in self._queue if isinstance(p, dict) and p.get('id')]
        if not self._queue:
            QMessageBox.warning(self, "Advertencia",
                                "Los elementos seleccionados no contienen IDs válidos")
            return
        reply = QMessageBox.question(
            self, "Confirmar restauración",
            f"¿Restaurar {len(self._queue)} paquetes?\n\nEsta operación puede tardar varios minutos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.results = []
        self._index = 0
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self._queue))
        self.progress_bar.setValue(0)
        self._restore_next()

    def _restore_next(self):
        if self._index >= len(self._queue):
            self.progress_bar.setVisible(False)
            self._show_summary()
            self.accept()
            return

        pkg = self._queue[self._index]
        self.progress_bar.setValue(self._index)
        self._worker = WorkerThread(self.client.install_package, pkg['id'],
                                    silent=self.settings.silent_mode)
        self._worker.finished.connect(self.on_package_restored)
        self._worker.error.connect(self.on_restore_error)
        self._worker.start()

    def on_package_restored(self, result):
        success, message = result
        pkg = self._queue[self._index]
        self.results.append((pkg['name'], success, message))
        if success:
            self.settings.add_history(pkg['id'], pkg['name'], 'instalado',
                                      pkg.get('version', ''))
        self._index += 1
        self._restore_next()

    def on_restore_error(self, error_msg):
        pkg = self._queue[self._index]
        self.results.append((pkg['name'], False, error_msg))
        self._index += 1
        self._restore_next()

    def _show_summary(self):
        ok = sum(1 for _, success, _ in self.results if success)
        fail = len(self.results) - ok
        lines = [f"Instalados correctamente: {ok}"]
        if fail:
            lines.append(f"Fallidos: {fail}\n")
            lines.extend(f"- No instalado {name}: {msg}" for name, success, msg in self.results if not success)
        QMessageBox.information(self, "Restauración completada", "\n".join(lines))


class SourcesDialog(QDialog):
    """Diálogo para gestionar fuentes de WinGet"""

    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.sources = []
        self._worker = None
        self._busy = False

        self.setWindowTitle("Gestionar Fuentes")
        self.resize(640, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(3)
        self.sources_table.setHorizontalHeaderLabels(["Nombre", "URL", "Acciones"])
        self.sources_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sources_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sources_table.verticalHeader().setVisible(False)

        header = self.sources_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.sources_table, 1)

        add_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre de la fuente")
        add_layout.addWidget(QLabel("Nombre:"))
        add_layout.addWidget(self.name_input)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("URL de la fuente")
        add_layout.addWidget(QLabel("URL:"))
        add_layout.addWidget(self.url_input)
        self.add_btn = QPushButton("Agregar")
        self.add_btn.clicked.connect(self.add_source)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

        self.refresh_sources()

    def _set_busy(self, busy: bool, message: str = ""):
        self._busy = busy
        self.add_btn.setEnabled(not busy)
        self.status_label.setText(message)

    def refresh_sources(self):
        if self._busy:
            return
        self._set_busy(True, "Cargando fuentes...")
        self._worker = WorkerThread(self.client.list_sources)
        self._worker.finished.connect(self.on_sources_loaded)
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_sources_loaded(self, result):
        sources, error = result
        if error:
            self._set_busy(False)
            QMessageBox.warning(self, "Error", f"Error cargando fuentes: {error}")
            return
        self._set_busy(False)
        self.sources = sources
        self.populate_table(sources)

    def populate_table(self, sources):
        self.sources_table.setRowCount(0)
        self.sources_table.setRowCount(len(sources))
        for row, source in enumerate(sources):
            self.sources_table.setItem(row, 0, QTableWidgetItem(source['name']))
            self.sources_table.setItem(row, 1, QTableWidgetItem(source.get('arg', '')))

            remove_btn = QPushButton("Eliminar")
            remove_btn.clicked.connect(lambda checked, s=source['name']: self.remove_source(s))
            self.sources_table.setCellWidget(row, 2, remove_btn)

    def on_error(self, error_msg):
        self._set_busy(False)
        QMessageBox.critical(self, "Error", f"Error: {error_msg}")

    def add_source(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        if not name or not url:
            QMessageBox.warning(self, "Advertencia", "Ingresa nombre y URL")
            return
        self._set_busy(True, f"Agregando fuente {name}...")
        self._worker = WorkerThread(self.client.add_source, name, url)
        self._worker.finished.connect(lambda r: self.on_source_added(r, name))
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_source_added(self, result, name):
        success, message = result
        if success:
            self.name_input.clear()
            self.url_input.clear()
            self.refresh_sources()
        else:
            self._set_busy(False)
            QMessageBox.warning(self, "Error", message)

    def remove_source(self, name):
        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar la fuente '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._set_busy(True, f"Eliminando fuente {name}...")
        self._worker = WorkerThread(self.client.remove_source, name)
        self._worker.finished.connect(lambda r: self.on_source_removed(r, name))
        self._worker.error.connect(self.on_error)
        self._worker.start()

    def on_source_removed(self, result, name):
        success, message = result
        if success:
            self.refresh_sources()
        else:
            self._set_busy(False)
            QMessageBox.warning(self, "Error", message)


class StreamWorker(QThread):
    """Thread que ejecuta una acción de WinGet reenviando su salida línea a línea.

    La función debe aceptar `on_line` y `cancel_event` como kwargs
    (ver WinGetClient.install_package / upgrade_package / ...).
    """
    line = Signal(str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.cancel_event = threading.Event()

    def _on_line(self, text: str):
        self.line.emit(text)

    def run(self):
        try:
            kwargs = dict(self.kwargs)
            kwargs['on_line'] = self._on_line
            kwargs['cancel_event'] = self.cancel_event
            self.finished.emit(self.func(*self.args, **kwargs))
        except Exception as e:  # noqa: BLE001 - se reporta a la UI tal cual
            self.error.emit(str(e))

    def cancel(self):
        self.cancel_event.set()


class OperationDialog(QDialog):
    """Diálogo de operación larga con log en vivo y botón Cancelar.

    Uso:
        worker = StreamWorker(client.upgrade_package, pkg_id, silent=True)
        dialog = OperationDialog("Actualizar X", "Descargando e instalando...", worker, self)
        dialog.exec()
        result = dialog.result  # (success, message) o None si se cerró con error
    """

    def __init__(self, title: str, subtitle: str, worker: StreamWorker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.result = None
        self._done = False
        self._start = time.time()

        self.setWindowTitle(title)
        self.resize(720, 480)
        self.setModal(True)
        self._init_ui(subtitle)

        self.worker.line.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        self._timer.start(500)

    def _init_ui(self, subtitle: str):
        layout = QVBoxLayout(self)

        self.subtitle_label = QLabel(subtitle)
        layout.addWidget(self.subtitle_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setPlaceholderText("Esperando salida de WinGet...")
        layout.addWidget(self.log_view, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminado mientras trabaja
        layout.addWidget(self.progress_bar)

        bottom = QHBoxLayout()
        self.status_label = QLabel("Iniciando... (0 s)")
        bottom.addWidget(self.status_label, 1)

        self.cancel_btn = QPushButton(icons.icon(icons.CLOSE), "Cancelar")
        self.cancel_btn.clicked.connect(self.cancel_operation)
        bottom.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.setEnabled(False)
        self.close_btn.setDefault(True)
        self.close_btn.clicked.connect(self.accept)
        bottom.addWidget(self.close_btn)
        layout.addLayout(bottom)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed)

    def append_log(self, text: str):
        self.log_view.append(text)
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _elapsed(self) -> int:
        return int(time.time() - self._start)

    def _update_elapsed(self):
        if not self._done:
            self.status_label.setText(f"Trabajando... ({self._elapsed()} s)")

    def _finish(self, message: str):
        self._done = True
        self._timer.stop()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)
        self.close_btn.setFocus()
        self.status_label.setText(f"{message} ({self._elapsed()} s)")

    def on_finished(self, result):
        self.result = result
        try:
            success, message = result
        except (TypeError, ValueError):
            success, message = False, str(result)
        self.append_log(f"── {message} ──")
        self._finish("Completado" if success else "Terminado con errores")

    def on_error(self, error_msg: str):
        self.result = (False, error_msg)
        self.append_log(f"── Error: {error_msg} ──")
        self._finish("Terminado con errores")

    def cancel_operation(self):
        if self._done:
            return
        self.worker.cancel()
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Cancelando... (terminando el proceso de WinGet)")
        self.append_log("── Cancelación solicitada, esperando a WinGet... ──")

    def closeEvent(self, event):
        if not self._done and self.worker.isRunning():
            # Cerrar con la X equivale a cancelar: no dejar huerfanos
            self.worker.cancel()
            self.worker.wait(15000)
        super().closeEvent(event)


class WinGetMissingDialog(QDialog):
    """Aviso cuando WinGet no está instalado, con solución y reintento.

    Códigos: Accepted = reintentar, Rejected = salir, OPEN_STORE = abrir
    la ficha de "Instalador de aplicación" en Microsoft Store.
    """
    OPEN_STORE = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("WinGet no encontrado")
        self.setMinimumWidth(540)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>No se encontró WinGet</h2>"))

        info = QLabel(
            "Esta aplicación necesita <b>Windows Package Manager (WinGet)</b> "
            "y no está instalado o no está en el PATH del sistema.<br><br>"
            "<b>Para solucionarlo:</b>"
            "<ol>"
            "<li>Instala <b>Instalador de aplicación</b> desde Microsoft Store "
            "(botón de abajo) o desde https://aka.ms/getwinget.</li>"
            "<li>Vuelve aquí y pulsa <b>Reintentar</b>.</li>"
            "</ol>"
            "Sin WinGet la aplicación no puede listar ni gestionar paquetes.")
        info.setWordWrap(True)
        info.setOpenExternalLinks(True)
        layout.addWidget(info)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        retry_btn = QPushButton("Reintentar")
        retry_btn.setDefault(True)
        retry_btn.clicked.connect(self.accept)
        buttons.addWidget(retry_btn)
        store_btn = QPushButton("Abrir Microsoft Store")
        store_btn.clicked.connect(lambda: self.done(WinGetMissingDialog.OPEN_STORE))
        buttons.addWidget(store_btn)
        exit_btn = QPushButton("Salir")
        exit_btn.clicked.connect(self.reject)
        buttons.addWidget(exit_btn)
        layout.addLayout(buttons)
