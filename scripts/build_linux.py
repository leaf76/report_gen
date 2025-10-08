"""Builds the Report Generator into a standalone executable for Linux."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
VENV_DIR = Path(sys.environ.get("VENV_DIR", ROOT_DIR / ".venv-build-linux"))
DIST_DIR = ROOT_DIR / "dist" / "linux"
SPEC_NAME = "report-gen"
MAIN_MODULE = ROOT_DIR / "main.py"
REQUIREMENTS = ROOT_DIR / "requirements-linux.txt"
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


def install_dependencies() -> None:
    python = venv_python()
    run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])


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
        "--add-data",
        f"{FILL_REPORT}:{'.'}",
        "--add-data",
        f"{TEMPLATE_PATH}:templates",
        str(MAIN_MODULE),
    ]
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
