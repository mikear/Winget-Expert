"""
Ventana principal de la aplicación WinGet Expert
"""
import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtCore import QSize
from PySide6.QtGui import QAction, QColor, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView, QLineEdit, QMenu,
    QProgressBar, QStatusBar, QTableWidget,
    QTableWidgetItem, QToolBar, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QMainWindow, QCheckBox, QLabel,
)

from src.core import install_dates
from src.core.settings import AppSettings
from src.core.winget_client import WinGetClient
from src.core.models import Package
from src.ui import icons, mensajes
from src.ui.app_icon import icono_aplicacion
from src.ui.dialogs import (
    InstallDialog, OperationDialog, PackageDetailsDialog, RestoreDialog,
    SourcesDialog, StreamWorker, WinGetMissingDialog,
)
from src.ui.additional_dialogs import FilterSettingsDialog, UserManualDialog
from src.ui.theme import apply_theme
from src.version import APP_VERSION

_GITHUB_URL = 'https://github.com/'

_COLUMNS = ["Nombre", "ID", "Versión Instalada", "Versión Disponible",
            "Origen", "Estado", "Instalado", "Actualizado"]


class WorkerThread(QThread):
    """Thread para ejecutar operaciones de WinGet sin bloquear la UI"""
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:  # noqa: BLE001 - se reporta a la UI tal cual
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Ventana principal de WinGet Expert"""

    def __init__(self, app, splash=None):
        super().__init__()
        self.app = app
        self.settings = AppSettings()
        self.client = WinGetClient()
        self.packages = []
        self.filtered_packages = []
        self._worker = None
        self._busy = False
        self._pinned_ids = set()
        self._showing_updates = False
        self._tree_mode = False
        self._installed_sources = set()
        self._splash = splash

        self.setWindowIcon(icono_aplicacion())
        self.init_ui()
        self.restore_geometry()

        # Verificar WinGet antes de cargar nada; sin él no hay nada que gestionar
        self._splash_message("Comprobando WinGet...")
        if self._ensure_winget():
            self._splash_message("Cargando paquetes instalados...")
            self.refresh_packages()
            if self.settings.auto_check_updates:
                self.show_updates()
        else:
            QTimer.singleShot(0, self.close)

    # ------------------------------------------------------------------ #
    # Splash
    # ------------------------------------------------------------------ #

    def _splash_message(self, message: str):
        if self._splash is not None:
            self._splash.show_message(message)

    def _dismiss_splash(self):
        """Cierra el splash respetando un tiempo mínimo de visualización."""
        if self._splash is not None:
            splash, self._splash = self._splash, None

            def close_splash():
                splash.finish(self)
                splash.deleteLater()

            remaining = splash.remaining_ms()
            if remaining > 0:
                QTimer.singleShot(remaining, close_splash)
            else:
                close_splash()

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            # No bloquear el cierre más de 3 segundos si hay una operación en curso
            self._worker.wait(3000)
        self._dismiss_splash()
        self.settings.window_geometry = self.saveGeometry()
        self.settings.save()
        super().closeEvent(event)

    def restore_geometry(self):
        geometry = self.settings.get_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.setGeometry(100, 100, 1200, 760)

    def _ensure_winget(self) -> bool:
        """Verifica WinGet al arrancar y guía al usuario si falta.

        Retorna True si se puede continuar, False si el usuario elige salir.
        """
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        while not self.client.is_available():
            dialog = WinGetMissingDialog(self)
            code = dialog.exec()
            dialog.deleteLater()
            if code == WinGetMissingDialog.OPEN_STORE:
                QDesktopServices.openUrl(
                    QUrl('ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1'))
                continue  # re-verificar por si ya lo instaló
            if code == QDialog.DialogCode.Accepted:  # Reintentar
                continue
            return False  # Salir (o X)
        return True

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def init_ui(self):
        self.setWindowTitle("WinGet Expert")
        self.setMinimumSize(900, 600)

        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header con título y contador
        header_layout = QHBoxLayout()
        self.title_label = QLabel("<h2>Paquetes Instalados</h2>")
        self.count_label = QLabel("Total: 0")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)
        layout.addLayout(header_layout)

        # Aviso sobre Microsoft Store (solo visible en vista de actualizaciones
        # cuando hay apps de la Store instaladas)
        self.store_note = QLabel(
            "Nota: las aplicaciones de Microsoft Store también se actualizan desde la "
            "propia app <b>Microsoft Store</b>: si allí ves actualizaciones pendientes "
            "que aquí no aparecen, instálalas desde la Store sin problema.")
        self.store_note.setWordWrap(True)
        self.store_note.setStyleSheet(
            "QLabel { background-color: #1B3A4B; color: #CFE8F3; "
            "border: 1px solid #2F6F8F; border-radius: 4px; padding: 6px; }")
        self.store_note.setVisible(False)
        layout.addWidget(self.store_note)

        # Barra de búsqueda y filtros
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o ID...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("Buscar:"))
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("Fuente:"))
        self.source_filter = QComboBox()
        self.source_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.source_filter)

        self.updates_only = QCheckBox("Solo actualizables")
        self.updates_only.stateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.updates_only)

        self.show_system = QCheckBox("Incluir sistema")
        self.show_system.setChecked(self.settings.include_system)
        self.show_system.stateChanged.connect(self._on_system_toggle)
        filter_layout.addWidget(self.show_system)

        self.silent_check = QCheckBox("Silencioso")
        self.silent_check.setChecked(self.settings.silent_mode)
        self.silent_check.setToolTip(
            "Instalar/actualizar sin mostrar las ventanas del instalador (--silent)")
        self.silent_check.stateChanged.connect(self._on_silent_toggle)
        filter_layout.addWidget(self.silent_check)

        filter_layout.addWidget(QLabel("Vista:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Tabla", "Árbol"])
        self.view_combo.currentTextChanged.connect(self._on_view_changed)
        filter_layout.addWidget(self.view_combo)

        filter_layout.addWidget(QLabel("Agrupar:"))
        self.group_combo = QComboBox()
        self.group_combo.addItems(["Fuente", "Estado"])
        self.group_combo.currentTextChanged.connect(self.apply_filters)
        self.group_combo.setEnabled(False)
        filter_layout.addWidget(self.group_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        layout.addWidget(self.progress_bar)

        # Tabla de paquetes
        self.table = QTableWidget()
        self.table.setColumnCount(len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.doubleClicked.connect(lambda _: self.show_package_details())

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(_COLUMNS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # Conexión única de selección (evita callbacks duplicados al repoblar)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)

        # Árbol de paquetes (vista alternativa con agrupación)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(_COLUMNS))
        self.tree.setHeaderLabels(_COLUMNS)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemDoubleClicked.connect(lambda *_: self.show_package_details())
        self.tree.header().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(_COLUMNS)):
            self.tree.header().setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree.setVisible(False)
        layout.addWidget(self.tree)

        # Barra de herramientas única con grupos lógicos:
        #  [carga/vista]  [paquete]  [actualizaciones]  [copia seg.]  [opciones]
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.refresh_action = toolbar.addAction(icons.icon(icons.REFRESH), "Refrescar")
        self.refresh_action.setShortcut("F5")
        self.refresh_action.triggered.connect(self.refresh_packages)

        self.updates_action = toolbar.addAction(icons.icon(icons.UPDATES), "Actualizaciones")
        self.updates_action.setShortcut("Ctrl+U")
        self.updates_action.triggered.connect(self.show_updates)

        toolbar.addSeparator()

        self.install_action = toolbar.addAction(icons.icon(icons.INSTALL), "Instalar")
        self.install_action.setShortcut("Ctrl+I")
        self.install_action.triggered.connect(self.show_install_dialog)

        self.info_action = toolbar.addAction(icons.icon(icons.DETAILS), "Detalles")
        self.info_action.triggered.connect(self.show_package_details)

        self.uninstall_action = toolbar.addAction(icons.icon(icons.UNINSTALL), "Desinstalar")
        self.uninstall_action.triggered.connect(self.uninstall_selected)

        self.upgrade_selected_action = toolbar.addAction(
            icons.icon(icons.UPGRADE_ONE), "Actualizar Sel.")
        self.upgrade_selected_action.triggered.connect(self.upgrade_selected)

        self.upgrade_all_action = toolbar.addAction(
            icons.icon(icons.UPGRADE_ALL), "Actualizar Todo")
        self.upgrade_all_action.triggered.connect(self.upgrade_all)

        toolbar.addSeparator()

        self.backup_action = toolbar.addAction(icons.icon(icons.BACKUP), "Copia seg.")
        self.backup_action.setShortcut("Ctrl+N")
        self.backup_action.setToolTip(
            "Crear copia de seguridad de la lista de paquetes (JSON)")
        self.backup_action.triggered.connect(self.create_backup)

        self.restore_action = toolbar.addAction(icons.icon(icons.RESTORE), "Restaurar")
        self.restore_action.setShortcut("Ctrl+O")
        self.restore_action.triggered.connect(self.restore_backup)

        self.export_action = toolbar.addAction(icons.icon(icons.EXPORT), "Exportar")
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self.export_package_list)

        toolbar.addSeparator()

        self.options_action = toolbar.addAction(icons.icon(icons.OPTIONS), "Opciones")
        self.options_action.triggered.connect(self.show_options_menu)

        self.addToolBar(toolbar)
        self.actions_toolbar = toolbar

        self.statusBar().showMessage("Cargando paquetes...")
        self.update_action_buttons()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # Menú Archivo
        file_menu = menubar.addMenu("Archivo")

        new_action = file_menu.addAction("Nueva copia de seguridad")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.create_backup)

        open_action = file_menu.addAction("Abrir copia de seguridad")
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.restore_backup)

        file_menu.addSeparator()

        export_action = file_menu.addAction("Exportar Lista")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_package_list)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Salir")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Menú Editar
        edit_menu = menubar.addMenu("Editar")

        refresh_action = edit_menu.addAction(icons.icon(icons.REFRESH), "Refrescar Paquetes")
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_packages)

        search_updates_action = edit_menu.addAction(icons.icon(icons.UPDATES), "Buscar Actualizaciones")
        search_updates_action.setShortcut("Ctrl+U")
        search_updates_action.triggered.connect(self.show_updates)

        edit_menu.addSeparator()

        find_action = edit_menu.addAction("Buscar en la lista...")
        find_action.setShortcut("Ctrl+F")
        # search_input se crea después del menú: diferir la búsqueda del atributo
        find_action.triggered.connect(lambda: self.search_input.setFocus())

        # Menú Ver
        view_menu = menubar.addMenu("Ver")

        self.dark_theme_action = QAction("Tema oscuro", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.setChecked(self.settings.theme == 'dark')
        self.dark_theme_action.toggled.connect(self.toggle_theme)
        view_menu.addAction(self.dark_theme_action)

        view_menu.addSeparator()

        filters_action = view_menu.addAction("Configurar Filtros...")
        filters_action.triggered.connect(self.show_filter_settings)

        # Menú Herramientas
        tools_menu = menubar.addMenu("Herramientas")

        install_action = tools_menu.addAction(icons.icon(icons.INSTALL), "Instalar Paquete...")
        install_action.setShortcut("Ctrl+I")
        install_action.triggered.connect(self.show_install_dialog)

        tools_menu.addSeparator()

        sources_action = tools_menu.addAction(icons.icon(icons.SOURCES), "Gestionar Fuentes...")
        sources_action.triggered.connect(self.manage_sources)

        cache_action = tools_menu.addAction(icons.icon(icons.CLEAN), "Limpiar Temporales de WinGet...")
        cache_action.triggered.connect(self.clean_temp_files)

        # Menú Ayuda
        help_menu = menubar.addMenu("Ayuda")

        manual_action = help_menu.addAction(icons.icon(icons.MANUAL), "Manual de Usuario")
        manual_action.setShortcut("F1")
        manual_action.triggered.connect(self.show_user_manual)

        help_menu.addSeparator()

        about_action = help_menu.addAction("Acerca de...")
        about_action.triggered.connect(self.show_about)

    # ------------------------------------------------------------------ #
    # Tema
    # ------------------------------------------------------------------ #

    def toggle_theme(self, dark: bool):
        self.settings.theme = 'dark' if dark else 'light'
        self.settings.save()
        apply_theme(self.app, dark)

    # ------------------------------------------------------------------ #
    # Gestión de operación en segundo plano
    # ------------------------------------------------------------------ #

    def _start_worker(self, func, *args, on_finished, timeout_msg=None):
        """Lanza una operación en background con guardas de concurrencia."""
        if self._busy:
            mensajes.informar(self, "Operación en curso",
                              "Espera a que termine la operación actual.")
            return False
        self._busy = True
        self.set_loading(True)
        self._worker = WorkerThread(func, *args)
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(self.on_error)
        self._worker.start()
        return True

    def _finish_worker(self):
        self._busy = False
        self.set_loading(False)

    def set_loading(self, loading: bool):
        self.progress_bar.setVisible(loading)
        for act in (self.refresh_action, self.updates_action, self.install_action,
                    self.backup_action, self.restore_action, self.export_action,
                    self.options_action, self.upgrade_all_action):
            act.setEnabled(not loading)
        if loading:
            QGuiApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            # Restaurar solo si hay un cursor override activo
            try:
                while QGuiApplication.overrideCursor() is not None:
                    QGuiApplication.restoreOverrideCursor()
            except (RuntimeError, AttributeError):
                pass
        if loading:
            self.statusBar().showMessage("Trabajando...")
        else:
            self.statusBar().showMessage("Listo")
        self.update_action_buttons()

    def update_action_buttons(self):
        """Habilita acciones según selección y estado"""
        selected = self.current_package() is not None
        self.upgrade_selected_action.setEnabled(selected and not self._busy)
        self.uninstall_action.setEnabled(selected and not self._busy)
        self.info_action.setEnabled(selected and not self._busy)

    # ------------------------------------------------------------------ #
    # Obtención del paquete seleccionado (a prueba de ordenación)
    # ------------------------------------------------------------------ #

    def current_package(self) -> Package:
        """Paquete de la selección actual (tabla o árbol), por ID en UserRole."""
        pkg_id = self._current_package_id()
        if pkg_id is None:
            return None
        return next((p for p in self.filtered_packages if p.id == pkg_id), None)

    def _current_package_id(self):
        """ID de la selección actual o None (los grupos del árbol no tienen ID)."""
        if self._tree_mode:
            item = self.tree.currentItem()
            return item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    # ------------------------------------------------------------------ #
    # Filtros y tabla
    # ------------------------------------------------------------------ #

    def _on_system_toggle(self):
        self.settings.include_system = self.show_system.isChecked()
        self.settings.save()
        self.apply_filters()

    def _on_silent_toggle(self):
        self.settings.silent_mode = self.silent_check.isChecked()
        self.settings.save()
        mode = "silencioso" if self.settings.silent_mode else "interactivo"
        self.statusBar().showMessage(f"Modo de instalación: {mode}", 3000)

    def apply_filters(self):
        search_text = self.search_input.text().lower()
        source_filter = self.source_filter.currentText()
        updates_only = self.updates_only.isChecked()
        show_system = self.show_system.isChecked()

        filtered = []
        for pkg in self.packages:
            if search_text and search_text not in pkg.name.lower() and search_text not in pkg.id.lower():
                continue
            if source_filter and source_filter != "Todas":
                if source_filter == "Otras":
                    if pkg.source in ('winget', 'msstore'):
                        continue
                elif pkg.source != source_filter:
                    continue
            if updates_only and not pkg.has_update:
                continue
            if not show_system and self._is_system_package(pkg):
                continue
            filtered.append(pkg)

        self.filtered_packages = filtered
        self.populate_table(filtered)
        self.populate_tree(filtered)
        self.count_label.setText(f"Mostrando: {len(filtered)} / {len(self.packages)}")
        # La acción refleja actualizaciones reales (no solo visibles por filtro)
        self.upgrade_all_action.setEnabled(
            not self._busy and any(p.has_update and not p.pinned for p in self.packages))
        self.update_action_buttons()

    @staticmethod
    def _is_system_package(pkg) -> bool:
        system_indicators = (
            'microsoft.', 'msix\\', 'arp\\', 'windowsapps',
            '.net', 'visual c++', 'directx', 'windows ', 'xbox',
        )
        pkg_lower = (pkg.name + ' ' + pkg.id).lower()
        return any(indicator in pkg_lower for indicator in system_indicators)

    def populate_table(self, packages):
        # Desactivar ordenación durante la inserción: con sorting activo
        # Qt reordena filas a medida que se insertan y corrompe el llenado.
        sorting = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.table.setRowCount(len(packages))

        green = QColor(0, 160, 60)
        orange = QColor(255, 140, 0)
        red = QColor(220, 60, 60)

        for row, pkg in enumerate(packages):
            name_item = QTableWidgetItem(pkg.name)
            # Referencia estable al paquete: sobrevive a la ordenación de columnas
            name_item.setData(Qt.ItemDataRole.UserRole, pkg.id)
            self.table.setItem(row, 0, name_item)

            self.table.setItem(row, 1, QTableWidgetItem(pkg.id))
            self.table.setItem(row, 2, QTableWidgetItem(pkg.version))

            available_item = QTableWidgetItem(pkg.available_version or "-")
            if pkg.has_update:
                available_item.setForeground(green)
            self.table.setItem(row, 3, available_item)

            self.table.setItem(row, 4, QTableWidgetItem(pkg.source))

            status_item = QTableWidgetItem(pkg.status)
            if pkg.pinned:
                status_item.setForeground(red)
            elif pkg.has_update:
                status_item.setForeground(orange)
            self.table.setItem(row, 5, status_item)

            self.table.setItem(row, 6, QTableWidgetItem(pkg.install_date or "-"))
            self.table.setItem(row, 7, QTableWidgetItem(pkg.updated_date or "-"))

        self.table.setSortingEnabled(sorting)

    def _on_view_changed(self, text: str):
        is_tree = text == "Árbol"
        self._tree_mode = is_tree
        self.tree.setVisible(is_tree)
        self.table.setVisible(not is_tree)
        self.group_combo.setEnabled(is_tree)
        self.update_action_buttons()

    @staticmethod
    def _group_key(pkg: Package, group_by: str) -> str:
        if group_by == "Estado":
            return pkg.status
        return pkg.source or "Otras"

    def populate_tree(self, packages):
        """Llena el árbol agrupando por fuente o estado (grupos con conteo)."""
        sorting = self.tree.isSortingEnabled()
        self.tree.setSortingEnabled(False)
        self.tree.clear()

        green = QColor(0, 160, 60)
        orange = QColor(255, 140, 0)
        red = QColor(220, 60, 60)

        groups: dict = {}
        for pkg in packages:
            groups.setdefault(self._group_key(pkg, self.group_combo.currentText()), []).append(pkg)

        for group_name in sorted(groups):
            members = groups[group_name]
            group_item = QTreeWidgetItem([f"{group_name} ({len(members)})"])
            group_item.setFirstColumnSpanned(True)
            group_item.setExpanded(True)
            for pkg in members:
                child = QTreeWidgetItem([
                    pkg.name, pkg.id, pkg.version,
                    pkg.available_version or "-", pkg.source, pkg.status,
                    pkg.install_date or "-", pkg.updated_date or "-",
                ])
                # ID estable en UserRole (los grupos no llevan ID)
                child.setData(0, Qt.ItemDataRole.UserRole, pkg.id)
                if pkg.has_update:
                    child.setForeground(3, green)
                if pkg.pinned:
                    child.setForeground(5, red)
                elif pkg.has_update:
                    child.setForeground(5, orange)
                group_item.addChild(child)
            self.tree.addTopLevelItem(group_item)

        self.tree.setSortingEnabled(sorting)
        # Reordenar colapsa los grupos: volver a expandirlos siempre
        self.tree.expandAll()

    def on_selection_changed(self, *_):
        self.update_action_buttons()

    # ------------------------------------------------------------------ #
    # Carga de paquetes
    # ------------------------------------------------------------------ #

    def refresh_packages(self):
        """Refresca la lista de paquetes instalados (con estado de pines real)."""
        self._showing_updates = False
        self.title_label.setText("<h2>Paquetes Instalados</h2>")
        self.statusBar().showMessage("Cargando paquetes instalados...")
        self._start_worker(self._load_installed, on_finished=self.on_packages_loaded)

    def show_updates(self):
        """Muestra solo paquetes con actualizaciones disponibles."""
        self._showing_updates = True
        self.title_label.setText("<h2>Actualizaciones Disponibles</h2>")
        self.statusBar().showMessage("Buscando actualizaciones...")
        self._start_worker(self._load_upgrades, on_finished=self.on_packages_loaded)

    # La carga (winget + registro + Appx + fechas) corre íntegra en el worker:
    # _enrich_dates consulta el sistema por paquete y congelaría la UI.

    def _load_installed(self):
        pinned = self.client.list_pinned_ids()
        packages, error = self.client.list_packages()
        if not error:
            install_dates.refresh_install_dates()
            self._enrich_dates(packages)
        return pinned, (packages, error), None

    def _load_upgrades(self):
        pinned = self.client.list_pinned_ids()
        packages, error = self.client.get_upgrades()
        if not error:
            install_dates.refresh_install_dates()
            self._enrich_dates(packages)
        return pinned, (packages, error), None

    def _enrich_dates(self, packages):
        """Completa fechas: sistema (registro/Appx) + historial de esta app."""
        for pkg in packages:
            system_date = install_dates.get_install_date(pkg.id, pkg.name)
            hist_in = self.settings.history_last(pkg.id, 'instalado')
            hist_up = self.settings.history_last(pkg.id, 'actualizado')
            pkg.install_date = system_date or (hist_in['date'][:10] if hist_in else None)
            pkg.updated_date = hist_up['date'][:10] if hist_up else None

    def on_packages_loaded(self, result):
        pinned_ids, (packages, error), _dates = result

        if error:
            self._finish_worker()
            self._dismiss_splash()
            self.on_error(error)
            return

        self._pinned_ids = set(pinned_ids or [])
        for pkg in packages:
            pkg.pinned = pkg.id in self._pinned_ids
        self._enrich_dates(packages)
        self.packages = packages

        # Actualizar combo de fuentes conservando la selección
        sources = sorted({p.source for p in packages if p.source})
        if not self._showing_updates:
            # Vista de instalados: recordar qué fuentes hay instaladas
            self._installed_sources = set(sources)
        current_text = self.source_filter.currentText() or "Todas"
        self.source_filter.blockSignals(True)
        self.source_filter.clear()
        self.source_filter.addItems(["Todas"] + sources + (["Otras"] if len(sources) > 1 else []))
        self.source_filter.setCurrentText(current_text if current_text in
                                          (["Todas"] + sources + ["Otras"]) else "Todas")
        self.source_filter.blockSignals(False)

        self.apply_filters()
        self._finish_worker()
        self._dismiss_splash()

        # Aviso de Microsoft Store solo en vista de actualizaciones y si hay
        # apps de la Store instaladas (sus updates pueden verse solo en la Store)
        self.store_note.setVisible(
            self._showing_updates and 'msstore' in self._installed_sources)

        if self._showing_updates and not packages:
            self.statusBar().showMessage("No hay actualizaciones disponibles", 5000)

    # ------------------------------------------------------------------ #
    # Menú contextual y acciones de paquete
    # ------------------------------------------------------------------ #

    def current_packages(self) -> list:
        """Paquetes de todas las filas seleccionadas (multi-selección)."""
        ids = []
        if self._tree_mode:
            for item in self.tree.selectedItems():
                pkg_id = item.data(0, Qt.ItemDataRole.UserRole)
                if pkg_id:  # los grupos no llevan ID
                    ids.append(pkg_id)
        else:
            for row in self.table.selectionModel().selectedRows():
                item = self.table.item(row.row(), 0)
                if item:
                    ids.append(item.data(Qt.ItemDataRole.UserRole))
        pkgs = []
        for pkg_id in ids:
            pkg = next((p for p in self.filtered_packages if p.id == pkg_id), None)
            if pkg:
                pkgs.append(pkg)
        return pkgs

    def show_context_menu(self, pos):
        pkg = self.current_package()
        if pkg is None:
            return
        menu = QMenu(self)

        details = menu.addAction(icons.icon(icons.DETAILS), "Detalles")
        details.triggered.connect(self.show_package_details)

        if pkg.has_update:
            update = menu.addAction(icons.icon(icons.UPGRADE_ONE),
                                    f"Actualizar a {pkg.available_version}")
            update.triggered.connect(self.upgrade_selected)

        if pkg.pinned:
            pin = menu.addAction(icons.icon(icons.PIN), "Quitar fijado")
        else:
            pin = menu.addAction(icons.icon(icons.PIN), "Fijar (bloquear actualizaciones)")
        pin.triggered.connect(lambda: self.toggle_pin(pkg))

        copy_id = menu.addAction(icons.icon(icons.COPY), "Copiar ID")
        copy_id.triggered.connect(lambda: QGuiApplication.clipboard().setText(pkg.id))

        menu.addSeparator()
        uninstall = menu.addAction(icons.icon(icons.UNINSTALL), "Desinstalar")
        uninstall.triggered.connect(self.uninstall_selected)

        view = self.tree.viewport() if self._tree_mode else self.table.viewport()
        menu.exec(view.mapToGlobal(pos))

    def toggle_pin(self, pkg: Package):
        # Los IDs locales (MSIX\..., ARP\...) no están en el catálogo:
        # winget pin los rechaza, se informa sin llamar a winget.
        if pkg.id.upper().startswith(('MSIX\\', 'ARP\\')):
            mensajes.informar(
                self, "Fijar paquete",
                f"{pkg.name} no se puede fijar porque no está en el catálogo "
                "de WinGet (es una aplicación del sistema o de Microsoft Store).")
            return
        if pkg.pinned:
            self._start_worker(self.client.unpin_package, pkg.id,
                               on_finished=lambda r: self.on_pin_changed(r, pkg, False))
        else:
            self._start_worker(self.client.pin_package, pkg.id,
                               on_finished=lambda r: self.on_pin_changed(r, pkg, True))

    def on_pin_changed(self, result, pkg: Package, pinning: bool):
        self._finish_worker()
        success, message = result
        if success:
            pkg.pinned = pinning
            if pinning:
                self._pinned_ids.add(pkg.id)
            else:
                self._pinned_ids.discard(pkg.id)
            self.statusBar().showMessage(message, 5000)
            self.apply_filters()
        else:
            mensajes.advertir(self, "Error", message)

    # ------------------------------------------------------------------ #
    # Instalar / Desinstalar / Actualizar
    # ------------------------------------------------------------------ #

    def show_install_dialog(self):
        dialog = InstallDialog(self.client, self.settings, self)
        if dialog.exec():
            self.refresh_packages()

    def uninstall_selected(self):
        pkg = self.current_package()
        if pkg is None:
            return

        if not mensajes.pregunta(
                self, "Confirmar desinstalación",
                f"¿Desinstalar {pkg.name} ({pkg.id})?\n\nEsta acción eliminará la aplicación."):
            return

        result = self._run_operation(
            f"Desinstalar {pkg.name}",
            f"Desinstalando {pkg.name}... (salida de WinGet en vivo)",
            self.client.uninstall_package, pkg.id,
            silent=self.settings.silent_mode,
        )
        if result is None:
            return
        success, message = result
        if success:
            self.settings.add_history(pkg.id, pkg.name, 'desinstalado')
            self.statusBar().showMessage(message, 5000)
            self.refresh_packages()
        elif 'cancelada' in message.lower():
            self.statusBar().showMessage(message, 5000)
        else:
            mensajes.advertir(self, "Error", message)

    def show_package_details(self):
        pkg = self.current_package()
        if pkg is None:
            return
        if self._start_worker(self.client.show_package_info, pkg.id,
                              on_finished=lambda r: self.show_details_dialog(r, pkg)):
            self.statusBar().showMessage(f"Cargando detalles de {pkg.name}...")

    def show_details_dialog(self, info_result, pkg: Package):
        self._finish_worker()
        info, error = info_result
        if error:
            mensajes.advertir(self, "Error", f"No se pudo obtener información: {error}")
            return
        dialog = PackageDetailsDialog(pkg, info, self.settings.history_for(pkg.id), self)
        dialog.exec()

    def upgrade_selected(self):
        pkg = self.current_package()
        if pkg is None:
            return
        if not pkg.has_update:
            mensajes.informar(self, "Información",
                              "Este paquete no tiene actualizaciones disponibles")
            return

        if not mensajes.pregunta(
                self, "Confirmar actualización",
                f"¿Actualizar {pkg.name} ({pkg.version} → {pkg.available_version})?"):
            return

        result = self._run_operation(
            f"Actualizar {pkg.name}",
            f"{pkg.version} → {pkg.available_version} (salida de WinGet en vivo)",
            self.client.upgrade_package, pkg.id,
            silent=self.settings.silent_mode,
        )
        if result is None:
            return
        success, message = result
        if success:
            self.settings.add_history(pkg.id, pkg.name, 'actualizado',
                                      pkg.available_version or '')
            self.statusBar().showMessage(message, 5000)
            self.refresh_packages()
        elif 'cancelada' in message.lower():
            self.statusBar().showMessage(message, 5000)
        else:
            mensajes.advertir(self, "Error", message)

    def upgrade_all(self):
        # Usar todos los paquetes, no solo los visibles: el filtro de
        # búsqueda/fuente no debe dejar fuera actualizaciones pendientes.
        upgradable = [p for p in self.packages if p.has_update and not p.pinned]
        if not upgradable:
            mensajes.informar(self, "Información", "No hay actualizaciones disponibles")
            return

        if not mensajes.pregunta(
                self, "Confirmar actualización masiva",
                f"¿Actualizar {len(upgradable)} paquetes?\n\n"
                f"Los paquetes fijados ({sum(1 for p in self.packages if p.pinned)}) "
                f"no se tocarán.\nEsta operación puede tardar varios minutos."):
            return

        result = self._run_operation(
            f"Actualizar {len(upgradable)} paquetes",
            "Actualización masiva en curso... (salida de WinGet en vivo)",
            self.client.upgrade_all,
            silent=self.settings.silent_mode,
        )
        if result is None:
            return
        success, message = result
        if success:
            for pkg in upgradable:
                self.settings.add_history(pkg.id, pkg.name, 'actualizado',
                                          pkg.available_version or '')
        elif 'cancelada' not in message.lower():
            mensajes.advertir(self, "Error", message)
        self.statusBar().showMessage(message, 8000)
        self.refresh_packages()

    def _run_operation(self, title, subtitle, func, *args, **kwargs):
        """Ejecuta una operación larga mostrando el log de WinGet en vivo.

        Retorna (success, message) o None si no hubo resultado.
        """
        worker = StreamWorker(func, *args, **kwargs)
        dialog = OperationDialog(title, subtitle, worker, self)
        dialog.exec()
        return dialog.result

    def on_error(self, error_msg: str):
        self._finish_worker()
        mensajes.error(self, "Error", f"Error: {error_msg}")

    # ------------------------------------------------------------------ #
    # Copia de seguridad / Restaurar / Exportar
    # ------------------------------------------------------------------ #

    def create_backup(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar copia de seguridad",
            f"copia_seguridad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "Archivos JSON (*.json)",
        )
        if not filename:
            return
        import json
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'packages': [
                    {'id': p.id, 'name': p.name, 'version': p.version,
                     'source': p.source, 'pinned': p.pinned}
                    for p in self.packages
                ],
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            self.statusBar().showMessage(f"Copia de seguridad creada: {filename}", 5000)
        except OSError as e:
            mensajes.error(self, "Error", f"Error al crear la copia de seguridad: {e}")

    def restore_backup(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir copia de seguridad", "", "Archivos JSON (*.json)")
        if not filename:
            return
        import json
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            packages = backup_data.get('packages', [])
            # Aceptar tanto formato {'packages': [...]} como lista directa
            if isinstance(backup_data, list):
                packages = backup_data
            # Filtrar entradas sin ID válido
            packages = [p for p in packages if isinstance(p, dict) and p.get('id')]
            if not packages:
                mensajes.advertir(self, "Advertencia",
                                  "La copia de seguridad no contiene paquetes")
                return
            dialog = RestoreDialog(packages, self.client, self.settings, self)
            if dialog.exec():
                self.refresh_packages()
        except (OSError, json.JSONDecodeError) as e:
            mensajes.error(self, "Error", f"Error al leer la copia de seguridad: {e}")

    def export_package_list(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar lista de paquetes", "",
            "Archivos CSV (*.csv);;Archivos JSON (*.json);;Archivos TXT (*.txt)")
        if not filename:
            return
        try:
            if filename.endswith('.csv'):
                self._export_csv(filename)
            elif filename.endswith('.json'):
                self._export_json(filename)
            else:
                self._export_txt(filename)
            self.statusBar().showMessage(f"Lista exportada a: {filename}", 5000)
        except OSError as e:
            mensajes.error(self, "Error", f"Error al exportar: {e}")

    def _export_csv(self, filename):
        import csv
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Nombre', 'ID', 'Versión', 'Disponible', 'Fuente',
                             'Estado', 'Instalado', 'Actualizado'])
            for pkg in self.filtered_packages:
                writer.writerow([pkg.name, pkg.id, pkg.version,
                                 pkg.available_version or '-', pkg.source, pkg.status,
                                 pkg.install_date or '-', pkg.updated_date or '-'])

    def _export_json(self, filename):
        import json
        data = [{'name': p.name, 'id': p.id, 'version': p.version,
                 'available_version': p.available_version, 'source': p.source,
                 'status': p.status, 'has_update': p.has_update, 'pinned': p.pinned,
                 'install_date': p.install_date, 'updated_date': p.updated_date}
                for p in self.filtered_packages]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _export_txt(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Lista de Paquetes WinGet\n" + "=" * 50 + "\n\n")
            for pkg in self.filtered_packages:
                f.write(f"Nombre: {pkg.name}\nID: {pkg.id}\nVersión: {pkg.version}\n"
                        f"Disponible: {pkg.available_version or '-'}\n"
                        f"Fuente: {pkg.source}\nEstado: {pkg.status}\n"
                        f"Instalado: {pkg.install_date or '-'}\n"
                        f"Actualizado: {pkg.updated_date or '-'}\n" + "-" * 30 + "\n")

    # ------------------------------------------------------------------ #
    # Fuentes, caché, opciones
    # ------------------------------------------------------------------ #

    def manage_sources(self):
        dialog = SourcesDialog(self.client, self)
        dialog.exec()

    def show_options_menu(self):
        menu = QMenu(self)
        menu.addAction(icons.icon(icons.SOURCES), "Gestionar Fuentes", self.manage_sources)
        menu.addSeparator()
        menu.addAction(icons.icon(icons.EXPORT), "Exportar lista", self.export_package_list)
        menu.addAction(icons.icon(icons.CLEAN), "Limpiar Temporales de WinGet", self.clean_temp_files)
        menu.addSeparator()
        menu.addAction(icons.icon(icons.DETAILS), "Acerca de", self.show_about)

        # Anclar el menú bajo el botón de la acción en la barra de herramientas
        btn = self.actions_toolbar.widgetForAction(self.options_action)
        if btn is not None:
            menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        else:
            menu.exec(QGuiApplication.primaryScreen().availableGeometry().center())

    def clean_temp_files(self):
        """Limpieza segura: solo instaladores temporales de winget en %TEMP%."""
        if mensajes.pregunta(
                self, "Confirmar",
                "¿Eliminar los archivos temporales de WinGet?\n"
                "(Solo instaladores descargados en %TEMP%; no toca aplicaciones instaladas)"):
            self._start_worker(self.client.clean_temp_files,
                               on_finished=self.on_temp_cleaned)

    def on_temp_cleaned(self, result):
        self._finish_worker()
        success, message = result
        if success:
            self.statusBar().showMessage(message, 5000)
        else:
            mensajes.advertir(self, "Error", message)

    def show_filter_settings(self):
        dialog = FilterSettingsDialog(self.settings, self)
        if dialog.exec():
            self.show_system.setChecked(self.settings.include_system)
            self.apply_filters()

    def show_user_manual(self):
        dialog = UserManualDialog(self)
        dialog.exec()

    def show_about(self):
        mensajes.acerca_de(
            self, "Acerca de WinGet Expert",
            "<h2>WinGet Expert</h2>"
            f"<p><b>Versión:</b> {APP_VERSION}</p>"
            "<p>Interfaz gráfica para Windows Package Manager (WinGet) que facilita "
            "la gestión de paquetes y aplicaciones en Windows.</p>"
            "<p><b>Características:</b> instalar, actualizar y desinstalar paquetes; "
            "pines reales de winget; copias de seguridad y restauración; "
            "historial de acciones; gestión de fuentes; exportación en CSV/JSON/TXT; "
            "tema claro/oscuro.</p>"
            "<p>Requiere Windows 10/11 con WinGet CLI.</p>"
            "<hr>"
            "<p><b>Desarrollado por Diego A. Rábalo</b><br>"
            "Contacto: <a href='mailto:diego_rabalo@hotmail.com'>"
            "diego_rabalo@hotmail.com</a></p>"
            "<p>LinkedIn: "
            "<a href='https://linkedin.com/in/rabalo'>linkedin.com/in/rabalo</a><br>"
            "GitHub: "
            "<a href='https://github.com/mikear'>github.com/mikear</a></p>"
            "<p><small>Iconos: Font Awesome Free (CC BY 4.0)</small></p>"
        )
