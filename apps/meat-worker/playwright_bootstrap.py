"""Ensure Playwright driver is findable when frozen (PyInstaller onedir)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def prepare_playwright_driver() -> Path | None:
    """Point Playwright at bundled driver under _MEIPASS.

    Root cause of WinError 2 on idle hosts: PyInstaller pulled *patchright*'s
    hook and shipped patchright/driver, while code imports *playwright* which
    looks for playwright/driver/node.exe next to the package (or via env).
    """
    if not getattr(sys, "frozen", False):
        return None

    meipass = Path(getattr(sys, "_MEIPASS", "") or Path(sys.executable).resolve().parent / "_internal")
    driver_dir = meipass / "playwright" / "driver"
    node = driver_dir / "node.exe"
    cli = driver_dir / "package" / "cli.js"

    # Fallback: reuse patchright driver tree if someone only shipped that
    if not node.is_file():
        alt = meipass / "patchright" / "driver"
        if (alt / "node.exe").is_file() and (alt / "package" / "cli.js").is_file():
            driver_dir = alt
            node = alt / "node.exe"
            cli = alt / "package" / "cli.js"

    if not node.is_file() or not cli.is_file():
        raise FileNotFoundError(
            "Playwright 驱动缺失：未找到 node.exe / cli.js。\n"
            f"期望路径: {meipass / 'playwright' / 'driver'}\n"
            "请使用仓库 apps/meat-worker/release 完整目录，或重新运行 scripts\\build-meat-worker.bat"
        )

    os.environ["PLAYWRIGHT_NODEJS_PATH"] = str(node)

    # Playwright resolves cli.js from package location; under PyInstaller that
    # path is often wrong — monkeypatch to the bundled driver.
    import playwright._impl._driver as drv  # noqa: WPS433

    def _compute() -> tuple[str, str]:
        return (os.environ.get("PLAYWRIGHT_NODEJS_PATH") or str(node), str(cli))

    drv.compute_driver_executable = _compute  # type: ignore[assignment]
    return driver_dir
