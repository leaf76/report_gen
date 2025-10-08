"""Handles exporting parsed summaries into the Excel report template."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List
import shutil

class ExportError(RuntimeError):
    """Raised when exporting summaries fails."""


def _default_script() -> Path:
    return Path(__file__).resolve().parent.parent / "fill_report.py"


@dataclass(slots=True)
class ExportConfig:
    """Configuration for exporting summaries."""

    template_path: Path
    sheet_name: str
    column: str
    debug_mode: bool = False
    script_path: Path = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.script_path is None:
            self.script_path = _default_script()
        self.template_path = Path(self.template_path).expanduser().resolve()
        self.script_path = Path(self.script_path).expanduser().resolve()
        self.column = self.column.strip()
        if not self.column:
            raise ExportError("Column must not be empty.")
        if not self.sheet_name.strip():
            raise ExportError("Sheet name must not be empty.")


def build_command(config: ExportConfig, summary_path: Path) -> List[str]:
    """Build the command to execute the fill_report script."""

    script = config.script_path
    if not script.exists():
        raise ExportError(f"Script not found: {script}")

    summary_path = Path(summary_path).expanduser().resolve()
    if not summary_path.exists():
        raise ExportError(f"Summary file not found: {summary_path}")

    command: list[str]
    if script.suffix == ".py":
        command = ["python", str(script)]
    else:
        command = [str(script)]

    command.extend(
        [
            f"--xlsx_file={config.template_path}",
            f"--sheet_name={config.sheet_name}",
            f"--column={config.column}",
            f"--yaml_file={summary_path}",
            f"--debug_mode={'True' if config.debug_mode else 'False'}",
        ]
    )
    return command


def prepare_output_file(template_path: Path, output_path: Path) -> Path:
    """Create a writable copy of the template for export."""

    template_path = Path(template_path).expanduser().resolve()
    if not template_path.exists():
        raise ExportError(f"Template not found: {template_path}")

    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, output_path)
    return output_path


def export_summaries(
    config: ExportConfig,
    summary_paths: Iterable[Path],
    *,
    runner: Callable[[List[str]], None] | None = None,
) -> None:
    """Export each summary into the Excel template via fill_report."""

    if runner is None:
        runner = lambda cmd: subprocess.run(cmd, check=True)

    if not config.template_path.exists():
        raise ExportError(f"Template not found: {config.template_path}")

    executed = False
    for summary_path in summary_paths:
        command = build_command(config, Path(summary_path))
        runner(command)
        executed = True

    if not executed:
        raise ExportError("No summaries provided for export.")
