"""Copy site-packages/playwright/driver into release/_internal/playwright/driver."""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path

import playwright

ROOT = Path(__file__).resolve().parents[1]
REL_DRIVER = ROOT / "apps" / "meat-worker" / "release" / "_internal" / "playwright" / "driver"
SRC = Path(inspect.getfile(playwright)).resolve().parent / "driver"


def main() -> int:
    if not (SRC / "node.exe").is_file():
        print("ERROR: source playwright driver missing:", SRC)
        return 1
    REL_DRIVER.parent.mkdir(parents=True, exist_ok=True)
    if REL_DRIVER.exists():
        shutil.rmtree(REL_DRIVER)
    shutil.copytree(SRC, REL_DRIVER)
    print("copied", SRC, "->", REL_DRIVER)
    print("node", (REL_DRIVER / "node.exe").is_file(), "cli", (REL_DRIVER / "package" / "cli.js").is_file())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
