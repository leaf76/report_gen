"""Builds the Report Generator into a standalone executable for Linux."""

from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = Path(os.environ.get("VENV_DIR", ROOT_DIR / ".venv-build-linux"))
DIST_DIR = ROOT_DIR / "dist" / "linux"
SPEC_NAME = "report-gen"
MAIN_MODULE = ROOT_DIR / "main.py"
REQUIREMENTS_LINUX = ROOT_DIR / "requirements-linux.txt"
REQUIREMENTS_TXT = ROOT_DIR / "requirements.txt"
TEMPLATE_PATH = ROOT_DIR / "[Template] [LEA] SASS Certification Automation Test Report.xlsx"
FILL_REPORT = ROOT_DIR / "fill_report.py"


def run(cmd: list[str], **kwargs) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)


def ensure_venv() -> None:
    if not VENV_DIR.exists():
        run(["python3", "-m", "venv", str(VENV_DIR)])
    if sys.platform == "win32":
        raise RuntimeError("Windows is not supported by build_linux.py")


def venv_python() -> Path:
    return VENV_DIR / "bin" / "python"


def _resolve_requirements() -> Path:
    # Prefer Linux-specific requirements if present, otherwise fallback.
    if REQUIREMENTS_LINUX.exists():
        return REQUIREMENTS_LINUX
    if REQUIREMENTS_TXT.exists():
        return REQUIREMENTS_TXT
    raise FileNotFoundError(
        "No requirements file found (expected requirements-linux.txt or requirements.txt)."
    )


def install_dependencies() -> None:
    python = venv_python()
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    req = _resolve_requirements()
    run([str(python), "-m", "pip", "install", "-r", str(req)])


def run_pyinstaller() -> None:
    python = venv_python()
    cmd = [
        str(python),
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name",
        SPEC_NAME,
        str(MAIN_MODULE),
    ]
    if FILL_REPORT.exists():
        cmd.extend(["--add-data", f"{FILL_REPORT}:{'.'}"])
    else:
        print(f"WARN: fill_report not found at {FILL_REPORT}; skipping bundling.")
    if TEMPLATE_PATH.exists():
        cmd.extend(["--add-data", f"{TEMPLATE_PATH}:templates"])
    else:
        print(f"WARN: template not found at {TEMPLATE_PATH}; skipping bundling.")
    run(cmd)


def copy_artifacts() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    source = ROOT_DIR / "dist" / SPEC_NAME
    if not source.exists():
        raise FileNotFoundError(f"Expected build output at {source}")
    target = DIST_DIR / SPEC_NAME
    if target.exists():
        subprocess.run(["rm", "-rf", str(target)], check=True)
    run(["cp", "-R", str(source), str(target)])


def main() -> None:
    ensure_venv()
    install_dependencies()
    run_pyinstaller()
    copy_artifacts()
    print("Build complete.")
    print(f"Artifacts located at: {DIST_DIR / SPEC_NAME}")


if __name__ == "__main__":
    main()
