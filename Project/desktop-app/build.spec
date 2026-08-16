# -*- mode: python ; coding: utf-8 -*-
# Configuracion de PyInstaller para el ejecutable de un solo archivo de ChromaticVision
# Modo onefile: no se agrega un paso COLLECT, todo se empaqueta directamente en el EXE
# SPECPATH y los nombres Analysis/PYZ/EXE los inyecta PyInstaller al ejecutar este archivo

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

PROJECT_ROOT = Path(SPECPATH)
MONOREPO_ROOT = PROJECT_ROOT.parent

block_cipher = None

# flet no trae un hook de PyInstaller propio; sin esto, icons.json y otros
# datos internos del paquete (material, cupertino) faltan y la app no arranca
flet_datas = collect_data_files("flet")

analysis = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=flet_datas
    + [
        (
            str(MONOREPO_ROOT / "shared-color-science" / "color_matrix_reference.json"),
            "shared-color-science",
        ),
        (
            str(PROJECT_ROOT / "app" / "picker" / "data" / "color_names.json"),
            "desktop-app/app/picker/data",
        ),
    ],
    hiddenimports=["flet", "cv2", "mss", "pystray", "PIL", "numpy"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="ChromaticVision",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "assets" / "icons" / "app.ico"),
)
