"""Application entry point for the automation test summary GUI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from report_gui.gui import run_app


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Launch the automation test summary GUI.",
    )
    parser.add_argument(
        "summary",
        nargs="*",
        help="Optional paths to test summary YAML files to preload.",
    )
    return parser


def _resolve_summary(path_input: str | Path) -> Path:
    return Path(path_input).expanduser().resolve()


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and launch the GUI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    summary_paths = None
    if args.summary:
        summary_paths = [_resolve_summary(path) for path in args.summary]
    run_app(summary_paths)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    raise SystemExit(main())
