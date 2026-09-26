# -*- mode: python ; coding: utf-8 -*-

import os
import sys

base_path = os.path.dirname(os.path.abspath(SPEC))
sys.path.insert(0, base_path)

from src.version import APP_VERSION  # noqa: E402

a = Analysis(
    ['main.py'],
    pathex=[base_path],
    binaries=[],
    datas=[(os.path.join(base_path, 'assets'), 'assets')],
    hiddenimports=[
        'src.core.winget_client',
        'src.core.models',
        'src.core.settings',
        'src.ui.main_window',
        'src.ui.dialogs',
        'src.ui.additional_dialogs',
        'src.ui.theme',
        'src.ui.app_icon',
        'src.ui.mensajes',
        'src.ui.splash',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PIL', 'Pillow',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
        'setuptools',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'WinGet_Expert_v{APP_VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX corrompe las DLLs de Qt: no comprimir
    console=False,  # Sin ventana de consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    description='WinGet Expert - Interfaz gráfica para Windows Package Manager',
    product_name='WinGet Expert',
    file_description='Gestor de paquetes Windows con interfaz gráfica',
    icon='assets/icon.ico',
)
