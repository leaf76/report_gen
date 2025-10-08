#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv-build-linux}"
DIST_DIR="$ROOT_DIR/dist/linux"
SPEC_NAME="report-gen"
MAIN_MODULE="$ROOT_DIR/main.py"

python3 "$ROOT_DIR/scripts/build_linux.py"
