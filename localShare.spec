# -*- mode: python ; coding: utf-8 -*-
import sys

is_windows = sys.platform == "win32"


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('languages/*.json', 'languages'),
        ('themes/*.qss', 'themes'),
        ('version.json', '.'),
        ('assets/icon_64.png', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='localShare',
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
    icon='assets/icon_64.ico' if is_windows else None,
    version='file_version_info.txt' if is_windows else None,
)
