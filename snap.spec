# -*- mode: python ; coding: utf-8 -*-
# snap.spec — PyInstaller build specification for Snap Companion
#
# PRE-BUILD CHECKLIST (run these once before `pyinstaller snap.spec`):
#   1.  pip install pyinstaller Pillow
#   2.  python build_icon.py          ← generates addon/icon.png & addon/icon.ico
#   3.  Confirm companion/bot_secrets.py exists and has your bot token filled in
#
# Build:
#   pyinstaller snap.spec
# Output: dist/Snap.exe  (single, no-console exe)

import os

block_cipher = None

a = Analysis(
    ['companion/main.py'],
    pathex=['companion'],          # treat companion/ as a source root
    binaries=[],
    datas=[
        # WoW addon folder — extracted to sys._MEIPASS/addon/ at runtime
        ('addon', 'addon'),
        # Fonts are downloaded at runtime next to the exe; only bundle them
        # if they were pre-downloaded (e.g. a local build after running the app once).
        *([('companion/assets', 'assets')] if os.path.isdir('companion/assets') else []),
    ],
    hiddenimports=[
        'discord',
        'discord.ext.commands',
        'aiohttp',
        'imageio_ffmpeg',
        'watchdog.observers.winapi',
        'watchdog.events',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Resolve icon path — falls back gracefully if build_icon.py wasn't run
_ico = 'addon/icon.ico' if os.path.exists('addon/icon.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Snap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # no black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_ico,
)

