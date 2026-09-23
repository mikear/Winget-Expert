"""
Diálogos adicionales: configuración de filtros y manual de usuario.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QLabel, QVBoxLayout,
    QTabWidget, QTextEdit,
)


class FilterSettingsDialog(QDialog):
    """Diálogo de configuración de filtros (persistida en settings)"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Configurar Filtros")
        self.setMinimumWidth(480)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        filter_group = QGroupBox("Filtros de Visualización")
        filter_layout = QVBoxLayout(filter_group)

        self.system_checkbox = QCheckBox("Mostrar paquetes del sistema por defecto")
        self.system_checkbox.setChecked(self.settings.include_system)
        filter_layout.addWidget(self.system_checkbox)
        layout.addWidget(filter_group)

        update_group = QGroupBox("Actualizaciones")
        update_layout = QVBoxLayout(update_group)

        self.auto_check_checkbox = QCheckBox("Buscar actualizaciones automáticamente al iniciar")
        self.auto_check_checkbox.setChecked(self.settings.auto_check_updates)
        update_layout.addWidget(self.auto_check_checkbox)
        layout.addWidget(update_group)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        self.settings.include_system = self.system_checkbox.isChecked()
        self.settings.auto_check_updates = self.auto_check_checkbox.isChecked()
        self.settings.save()
        super().accept()


class UserManualDialog(QDialog):
    """Diálogo del manual de usuario"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual de Usuario - WinGet GUI Manager Pro")
        self.resize(900, 680)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        tab_widget = QTabWidget()

        intro_tab = QTextEdit()
        intro_tab.setHtml("""
        <h2>Bienvenido a WinGet GUI Manager Pro</h2>

        <h3>¿Qué es WinGet GUI Manager Pro?</h3>
        <p>Es una interfaz gráfica para Windows Package Manager (WinGet) que facilita
        la gestión de paquetes y aplicaciones en Windows.</p>

        <h3>Características Principales:</h3>
        <ul>
        <li><b>Gestión Completa:</b> Instalar, actualizar, desinstalar paquetes</li>
        <li><b>Búsqueda Avanzada:</b> Filtros por nombre, fuente, estado</li>
        <li><b>Backup y Restauración:</b> Guarda y restaura tus aplicaciones</li>
        <li><b>Gestión de Fuentes:</b> Administra repositorios de paquetes</li>
        <li><b>Pines reales de WinGet:</b> Bloquea actualizaciones de paquetes específicos</li>
        <li><b>Historial de acciones:</b> Registro de instalaciones y actualizaciones</li>
        <li><b>Exportación Múltiple:</b> CSV, JSON, TXT</li>
        <li><b>Tema claro/oscuro:</b> Se recuerda tu preferencia</li>
        </ul>

        <h3>Requisitos:</h3>
        <ul>
        <li>Windows 10 o 11 (64-bit)</li>
        <li>WinGet CLI instalado</li>
        <li>Conexión a internet para instalar paquetes</li>
        </ul>
        """)
        intro_tab.setReadOnly(True)
        tab_widget.addTab(intro_tab, "Introducción")

        basic_tab = QTextEdit()
        basic_tab.setHtml("""
        <h2>Guía de Uso Básico</h2>

        <h3>1. Listar Paquetes Instalados</h3>
        <p>Al iniciar la aplicación, verás automáticamente todos los paquetes instalados en tu sistema.</p>

        <h3>2. Buscar y Filtrar</h3>
        <p>Usa la barra de búsqueda para filtrar por nombre o ID del paquete.</p>
        <ul>
        <li><b>Fuente:</b> winget, msstore, otras</li>
        <li><b>Solo actualizables:</b> Mostrar solo paquetes con actualizaciones</li>
        <li><b>Incluir sistema:</b> Mostrar/ocultar paquetes del sistema</li>
        <li><b>Vista Tabla/Árbol:</b> El árbol agrupa los paquetes por
        <b>Fuente</b> o por <b>Estado</b> (usa el desplegable "Agrupar"). Las
        columnas <b>Instalado</b> y <b>Actualizado</b> muestran la fecha de
        instalación (registro de Windows) y la última actualización hecha
        desde esta aplicación; "—" significa fecha desconocida</li>
        </ul>

        <h3>3. Actualizar Paquetes</h3>
        <ul>
        <li><b>Individual:</b> Selecciona un paquete y haz clic en "Actualizar Sel." (o usa el menú contextual con clic derecho)</li>
        <li><b>Masiva:</b> Usa "Actualizar Todo" para todos los actualizables</li>
        <li><b>Bloquear actualizaciones:</b> Clic derecho → "Fijar". Usa el pin real de WinGet, por lo que el paquete tampoco se actualizará desde la línea de comandos</li>
        </ul>

        <h3>4. Instalar Nuevos Paquetes</h3>
        <ol>
        <li>Haz clic en "Instalar Nuevo"</li>
        <li>Busca el paquete que quieres instalar</li>
        <li>Haz clic en "Instalar" junto al paquete</li>
        </ol>

        <h3>5. Desinstalar Paquetes</h3>
        <ol>
        <li>Selecciona el paquete en la tabla</li>
        <li>Haz clic en "Desinstalar" (o clic derecho)</li>
        <li>Confirma la acción</li>
        </ol>
        """)
        basic_tab.setReadOnly(True)
        tab_widget.addTab(basic_tab, "Uso Básico")

        why_tab = QTextEdit()
        fa = ("<span style=\"font-family:'Font Awesome 6 Free'; font-size:16px;\">"
              "{}</span>")
        why_tab.setHtml("""
        <h2>Por qué mantener tus aplicaciones actualizadas</h2>
        <p>Mantener el software al día no es solo tener lo último: es una de las
        medidas más eficaces para la salud y seguridad de tu equipo.</p>

        <h3>{shield} Seguridad</h3>
        <p>Cada actualización corrige vulnerabilidades que el malware y los
        atacantes explotan. Un programa desactualizado es la puerta de entrada
        más común a infecciones y robo de datos.</p>

        <h3>{gauge} Rendimiento</h3>
        <p>Las nuevas versiones optimizan el consumo de memoria y CPU, reducen
        tiempos de arranque y alargan la vida útil de tu equipo.</p>

        <h3>{rocket} Nuevas funciones</h3>
        <p>Accedes a mejoras, nuevas herramientas y cambios de diseño sin costo
        adicional, aprovechando al máximo cada aplicación.</p>

        <h3>{bug} Corrección de errores</h3>
        <p>Los fallos, cierres inesperados y comportamientos extraños se corrigen
        en cada versión. Si algo te falla, actualizar es el primer paso.</p>

        <h3>{plug} Compatibilidad</h3>
        <p>Windows, los controladores y el resto de tus programas avanzan juntos.
        Las versiones antiguas dejan de funcionar bien con el sistema y entre sí.</p>

        <p><b>Consejo:</b> usa el filtro <b>Solo actualizables</b> y el botón
        <b>Actualizar Todo</b> para ponerte al día en minutos. Los paquetes
        críticos puedes fijarlos con <b>Fijar</b> para revisarlos con calma.</p>
        """.format(
            shield=fa.format("&#xf3ed;"),
            gauge=fa.format("&#xf625;"),
            rocket=fa.format("&#xf135;"),
            bug=fa.format("&#xf188;"),
            plug=fa.format("&#xf1e6;"),
        ))
        why_tab.setReadOnly(True)
        tab_widget.addTab(why_tab, "Por qué actualizar")

        advanced_tab = QTextEdit()
        advanced_tab.setHtml("""
        <h2>Funciones Avanzadas</h2>

        <h3>1. Backup y Restauración</h3>
        <ul>
        <li><b>Crear Backup:</b> "Backup" guarda un JSON con todos tus paquetes</li>
        <li><b>Restaurar:</b> "Restaurar" reinstala los paquetes del backup que elijas,
        con un resumen de éxitos y fallos al final</li>
        </ul>

        <h3>2. Gestión de Fuentes</h3>
        <ol>
        <li>"Opciones" → "Gestionar Fuentes"</li>
        <li>Ingresa nombre y URL de la fuente</li>
        <li>Haz clic en "Agregar"</li>
        </ol>

        <h3>3. Exportación de Datos</h3>
        <ul>
        <li><b>CSV:</b> Para importar en Excel</li>
        <li><b>JSON:</b> Para procesamiento de datos</li>
        <li><b>TXT:</b> Para documentación</li>
        </ul>

        <h3>4. Limpieza de Temporales</h3>
        <p>"Opciones" → "Limpiar Temporales de WinGet" elimina únicamente los
        instaladores temporales descargados en %TEMP%. No toca aplicaciones
        instaladas ni paquetes portables.</p>

        <h3>5. Detalles e Historial</h3>
        <p>Selecciona un paquete y haz doble clic (o "Detalles") para ver su
        información completa y el historial de acciones realizadas desde la
        aplicación (instalaciones, actualizaciones, desinstalaciones).</p>

        <h3>6. Tema claro/oscuro</h3>
        <p>Menú "Ver" → "Tema oscuro". La preferencia se guarda automáticamente.</p>
        """)
        advanced_tab.setReadOnly(True)
        tab_widget.addTab(advanced_tab, "Funciones Avanzadas")

        shortcuts_tab = QTextEdit()
        shortcuts_tab.setHtml("""
        <h2>Atajos de Teclado</h2>

        <table border="1" cellpadding="5" cellspacing="0">
        <tr><th><b>Acción</b></th><th><b>Atajo</b></th></tr>
        <tr><td>Nuevo Backup</td><td>Ctrl + N</td></tr>
        <tr><td>Abrir Backup</td><td>Ctrl + O</td></tr>
        <tr><td>Exportar Lista</td><td>Ctrl + E</td></tr>
        <tr><td>Instalar Paquete</td><td>Ctrl + I</td></tr>
        <tr><td>Buscar Actualizaciones</td><td>Ctrl + U</td></tr>
        <tr><td>Buscar en la lista</td><td>Ctrl + F</td></tr>
        <tr><td>Seleccionar Todo</td><td>Ctrl + A</td></tr>
        <tr><td>Refrescar Paquetes</td><td>F5</td></tr>
        <tr><td>Manual de Usuario</td><td>F1</td></tr>
        <tr><td>Salir</td><td>Ctrl + Q</td></tr>
        </table>

        <h3>Consejos:</h3>
        <ul>
        <li>Doble clic en un paquete para ver sus detalles</li>
        <li>Clic derecho para el menú contextual (actualizar, fijar, copiar ID, desinstalar)</li>
        <li>Fija los paquetes críticos para que "Actualizar Todo" no los toque</li>
        <li>Las columnas se pueden ordenar haciendo clic en su encabezado</li>
        </ul>
        """)
        shortcuts_tab.setReadOnly(True)
        tab_widget.addTab(shortcuts_tab, "Atajos")

        troubleshooting_tab = QTextEdit()
        troubleshooting_tab.setHtml("""
        <h2>Solución de Problemas</h2>

        <h4>1. "WinGet no encontrado"</h4>
        <p><b>Solución:</b> Instala "Instalador de aplicación" desde Microsoft Store
        y reinicia la aplicación.</p>

        <h4>2. "Error de permisos"</h4>
        <p><b>Solución:</b> Ejecuta la aplicación como administrador y cierra las
        aplicaciones que estén usando el paquete.</p>

        <h4>3. "No se puede desinstalar un paquete"</h4>
        <p><b>Solución:</b> Cierra la aplicación antes de desinstalar y verifica que
        no sea un componente crítico del sistema.</p>

        <h4>4. "Error de conexión"</h4>
        <p><b>Solución:</b> Verifica tu conexión a internet y prueba
        <code>winget source reset --force</code> en una terminal.</p>

        <h4>5. La lista aparece vacía</h4>
        <p><b>Solución:</b> Pulsa F5 para refrescar. Si WinGet está actualizando sus
        fuentes, la primera carga puede tardar unos segundos.</p>

        <h4>6. Veo actualizaciones en Microsoft Store que aquí no aparecen</h4>
        <p><b>Explicación:</b> La aplicación muestra exactamente lo que WinGet
        reporta. La Microsoft Store gestiona sus apps por su cuenta y no siempre
        informa de sus actualizaciones a WinGet. Instala esas actualizaciones
        desde la propia Store sin problema; después WinGet las verá al día.</p>
        """)
        troubleshooting_tab.setReadOnly(True)
        tab_widget.addTab(troubleshooting_tab, "Solución de Problemas")

        layout.addWidget(tab_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)
