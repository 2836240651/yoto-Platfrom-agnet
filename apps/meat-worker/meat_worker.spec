# -*- mode: python ; coding: utf-8 -*-
# onedir → apps/meat-worker/release — bundles real playwright/driver (not patchright).

from pathlib import Path

import playwright

ROOT = Path(SPECPATH).resolve().parents[1]
MW = ROOT / "apps" / "meat-worker"
CLIENT = ROOT / "mcp" / "servers" / "douyin_chanmama_client.py"
PW_DRIVER = Path(playwright.__file__).resolve().parent / "driver"

datas = [
    (str(CLIENT), "."),
    (str(MW / "config.example.json"), "."),
    (str(MW / "playwright_bootstrap.py"), "."),
    # Critical: playwright looks for driver/node.exe + package/cli.js
    (str(PW_DRIVER), "playwright/driver"),
]

hiddenimports = [
    "pystray._win32",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "playwright",
    "playwright.sync_api",
    "playwright._impl._driver",
    "douyin_chanmama_client",
    "playwright_bootstrap",
    "handlers",
    "handlers.douyin_collect",
    "config",
    "worker_core",
    "ui",
    "ui.tray_app",
]

a = Analysis(
    [str(MW / "__main__.py")],
    pathex=[str(MW), str(ROOT / "mcp" / "servers")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "numpy",
        "scipy",
        "pandas",
        "patchright",
        "matplotlib",
        "tkinter.test",
    ],
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
