"""
Cuadros de mensaje y botoneras con textos en español.

Qt muestra por defecto los botones estándar (Yes/No/OK/Cancel/Close) en
inglés si no se cargan sus traducciones; toda la aplicación pasa por aquí
para que ningún botón de diálogo aparezca en otro idioma.
"""
from PySide6.QtWidgets import QDialogButtonBox, QMessageBox


def _box(parent, titulo: str, texto: str, icono) -> QMessageBox:
    box = QMessageBox(parent)
    box.setIcon(icono)
    box.setWindowTitle(titulo)
    box.setText(texto)
    return box


def informar(parent, titulo: str, texto: str):
    """Cuadro de información con botón 'Aceptar'."""
    box = _box(parent, titulo, texto, QMessageBox.Icon.Information)
    aceptar = box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(aceptar)
    box.exec()


def advertir(parent, titulo: str, texto: str):
    """Cuadro de advertencia con botón 'Aceptar'."""
    box = _box(parent, titulo, texto, QMessageBox.Icon.Warning)
    aceptar = box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(aceptar)
    box.exec()


def error(parent, titulo: str, texto: str):
    """Cuadro de error con botón 'Aceptar'."""
    box = _box(parent, titulo, texto, QMessageBox.Icon.Critical)
    aceptar = box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(aceptar)
    box.exec()


def acerca_de(parent, titulo: str, texto: str):
    """Cuadro 'Acerca de' con botón 'Cerrar'."""
    box = _box(parent, titulo, texto, QMessageBox.Icon.Information)
    cerrar = box.addButton("Cerrar", QMessageBox.ButtonRole.AcceptRole)
    box.setDefaultButton(cerrar)
    box.exec()


def pregunta(parent, titulo: str, texto: str,
             texto_si: str = "Sí", texto_no: str = "No") -> bool:
    """Pregunta Sí/No en español; retorna True solo si responde 'Sí'."""
    box = _box(parent, titulo, texto, QMessageBox.Icon.Question)
    si = box.addButton(texto_si, QMessageBox.ButtonRole.YesRole)
    no = box.addButton(texto_no, QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(si)
    box.exec()
    return box.clickedButton() is si


def botonera_cerrar() -> QDialogButtonBox:
    """QDialogButtonBox con el botón de cierre etiquetado 'Cerrar'."""
    box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    box.button(QDialogButtonBox.StandardButton.Close).setText("Cerrar")
    return box


def botonera_aceptar_cancelar() -> QDialogButtonBox:
    """QDialogButtonBox Aceptar/Cancelar en español."""
    box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    box.button(QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
    box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
    return box
