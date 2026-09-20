#!/usr/bin/env python3
"""Small cross-platform launcher for WaterlooWorks Job Exporter."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
EXPORTER = ROOT / "waterlooworks_exporter.py"
MARKER = VENV_DIR / ".waterlooworks_setup"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def setup_environment(python: Path) -> None:
    current_hash = requirements_hash()
    saved_hash = MARKER.read_text(encoding="utf-8").strip() if MARKER.exists() else ""

    if saved_hash != current_hash:
        print("\nFirst-time setup: installing the files the exporter needs.")
        print("You will not need to do this on future runs.\n")
        print("Installing Python requirements...")
        run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        print("\nInstalling the Chromium browser used by the exporter...")
        run([str(python), "-m", "playwright", "install", "chromium"])
        MARKER.write_text(current_hash, encoding="utf-8")


def main() -> None:
    print("WaterlooWorks Job Exporter")

    if not REQUIREMENTS.exists() or not EXPORTER.exists():
        print("\nThis launcher must stay in the same folder as requirements.txt and waterlooworks_exporter.py.")
        raise SystemExit(1)

    python = venv_python()
    if not python.exists():
        print("\nCreating a private Python environment for this project...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
        python = venv_python()

    try:
        setup_environment(python)
        print("\nOpening the browser... this may take a moment.", flush=True)
        run([str(python), str(EXPORTER)])
    except subprocess.CalledProcessError as exc:
        print(f"\nThe exporter stopped because a setup or runtime command failed (exit code {exc.returncode}).")
        print("See README.md for troubleshooting steps.")
        raise SystemExit(exc.returncode)


if __name__ == "__main__":
    main()
