# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir for MeatWorker.exe — run via scripts/build-meat-worker.bat

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).resolve().parents[1]
MW = ROOT / "apps" / "meat-worker"
CLIENT = ROOT / "mcp" / "servers" / "douyin_chanmama_client.py"

datas = [
    (str(CLIENT), "."),
    (str(MW / "config.example.json"), "."),
]
binaries = []
hiddenimports = [
    "pystray._win32",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "playwright",
    "playwright.sync_api",
    "douyin_chanmama_client",
    "handlers",
    "handlers.douyin_collect",
    "config",
    "worker_core",
    "ui",
    "ui.tray_app",
]

tmp_ret = collect_all("playwright")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    [str(MW / "__main__.py")],
    pathex=[str(MW), str(ROOT / "mcp" / "servers")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="MeatWorker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="meat-worker",
)
