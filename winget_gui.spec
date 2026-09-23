# -*- mode: python ; coding: utf-8 -*-

import os

base_path = os.path.dirname(os.path.abspath(SPEC))

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
    name='WinGet_GUI_Manager_Pro',
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
    description='WinGet GUI Manager Pro - Interfaz gráfica para Windows Package Manager',
    product_name='WinGet GUI Manager Pro',
    file_description='Gestor de paquetes Windows con interfaz gráfica',
    icon='assets/icon.ico',
)
