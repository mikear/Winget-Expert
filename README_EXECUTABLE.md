# WinGet Expert — Binarios

## Binarios disponibles (carpeta `dist/`)

| Archivo | Tipo | Descripción |
|---|---|---|
| `WinGet_Expert.exe` | Portable | Archivo único, no requiere Python ni instalación |
| `WinGet_Expert_Instalador.exe` | Instalador | Asistente en español (Inno Setup): accesos directos, menú Inicio y desinstalador |

Ambos se generan con el mismo icono y diseño del splash, y están
disponibles para descarga en el [README](README.md).

## Cómo regenerarlos

```powershell
# Portable (PyInstaller; tarda varios minutos)
pip install pyinstaller
pyinstaller winget_gui.spec
# → dist\WinGet_Expert.exe

# Instalador (Inno Setup 6)
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" instalador.iss
# → dist\WinGet_Expert_Instalador.exe
```

Notas importantes (ver `AGENTS.md`):
- `upx=False` a propósito: UPX corrompe las DLLs de Qt.
- Cierra cualquier instancia en ejecución antes de compilar: Windows
  bloquea el exe y la build falla con `PermissionError`.
- El icono se regenera con `python create_icon.py` (PySide6 + Pillow,
  solo desarrollo) a partir del diseño compartido en `src/ui/app_icon.py`.

## Características de los binarios

- **Tamaño:** ~45 MB (portable) / ~47 MB (instalador)
- **Independientes:** no requieren Python instalado
- **Icono propio:** el diseño del splash (caja azul + badge de descarga)
- **Sin consola:** solo interfaz gráfica
- **Idioma:** interfaz y asistente de instalación íntegramente en español

## Requisitos del sistema

- Windows 10/11 (64-bit)
- WinGet CLI instalado (viene con Windows 11 y "Instalador de aplicación")
- ~100 MB de espacio libre
- Conexión a internet (para instalar/actualizar paquetes)
