#!/usr/bin/env python3
"""Bootstrap Numel Playground runtime environment and start the app."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parent
REQ_FILE = ROOT_DIR / "requirements.txt"
VENV_DIR = ROOT_DIR / ".venv"
STATE_FILE = ROOT_DIR / ".numel" / "state" / "bootstrap-state.json"
TARGET_PYTHON_MINOR = "3.14"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: Sequence[str], *, cwd: Path | None = None) -> None:
    print(f"[bootstrap] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _read_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(state: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _python_version(python_exe: Path) -> str:
    out = subprocess.check_output(
        [str(python_exe), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"],
        text=True,
    )
    return out.strip()


def _ensure_venv_and_requirements(uv_bin: str) -> Path:
    if not REQ_FILE.exists():
        raise FileNotFoundError(f"Missing requirements file: {REQ_FILE}")

    venv_python = _venv_python()
    current_hash = _sha256(REQ_FILE)
    state = _read_state()

    recreate_venv = not venv_python.exists()
    if not recreate_venv:
        version = _python_version(venv_python)
        recreate_venv = not version.startswith(f"{TARGET_PYTHON_MINOR}.")

    if recreate_venv:
        _run([uv_bin, "venv", "--python", TARGET_PYTHON_MINOR, str(VENV_DIR)], cwd=ROOT_DIR)
        venv_python = _venv_python()

    needs_sync = recreate_venv or state.get("requirements_sha256") != current_hash
    if needs_sync:
        _run(
            [uv_bin, "pip", "install", "--python", str(venv_python), "-r", str(REQ_FILE)],
            cwd=ROOT_DIR,
        )
        state = {
            "requirements_sha256": current_hash,
            "venv_python": str(venv_python),
            "venv_python_version": _python_version(venv_python),
            "platform": platform.platform(),
        }
        _write_state(state)

    return venv_python


def main(argv: list[str]) -> int:
    uv_bin = os.environ.get("UV_BIN", "uv")
    venv_python = _ensure_venv_and_requirements(uv_bin)
    app_path = ROOT_DIR / "app" / "app.py"
    cmd = [str(venv_python), str(app_path), *argv]
    return subprocess.call(cmd, cwd=str(ROOT_DIR / "app"))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
