"""
Modelos de datos para WinGet GUI Manager
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Package:
    """Representa un paquete instalado o disponible en WinGet"""
    name: str
    id: str
    version: str
    available_version: Optional[str] = None
    source: str = "winget"
    pinned: bool = False
    install_date: Optional[str] = None   # 'YYYY-MM-DD' o None si se desconoce
    updated_date: Optional[str] = None   # idem (solo acciones vía esta app)

    @property
    def has_update(self) -> bool:
        """Verifica si hay actualización disponible"""
        if not self.available_version or self.available_version.lower() == "unknown":
            return False
        return self.version != self.available_version

    @property
    def status(self) -> str:
        """Estado del paquete"""
        if self.pinned:
            return "Fijado"
        elif self.has_update:
            return "Actualizable"
        return "Actualizado"

    def to_dict(self) -> dict:
        """Convierte el paquete a diccionario para JSON"""
        return {
            'name': self.name,
            'id': self.id,
            'version': self.version,
            'available_version': self.available_version,
            'source': self.source,
            'pinned': self.pinned,
            'install_date': self.install_date,
            'updated_date': self.updated_date,
        }
