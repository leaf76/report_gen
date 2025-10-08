"""Formatting helpers for the GUI layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator, Tuple, TYPE_CHECKING

from .models import ResultTotals, TestExecution

if TYPE_CHECKING:  # pragma: no cover - typing aid
    from .view_model import GroupRow


_PREFERRED_ORDER = ["PASS", "FAIL", "ERROR", "SKIP", "UNKNOWN"]


def build_overall_summary_text(totals: ResultTotals) -> str:
    """Create a compact textual summary for overall statistics."""
    segments = [f"Total: {totals.total}"]
    for result, count in _ordered_results(totals.by_result):
        segments.append(f"{result}: {count}")
    return " | ".join(segments)


def _ordered_results(by_result: dict[str, int]) -> Iterator[Tuple[str, int]]:
    seen: set[str] = set()
    for result in _PREFERRED_ORDER:
        if result in by_result:
            yield result, by_result[result]
            seen.add(result)
    for result, count in by_result.items():
        if result not in seen:
            yield result, count


def group_row_to_tree_values(row: GroupRow) -> Tuple[str, int, int, int, int, int, int, str, str]:
    """Return the values tuple used in the grouped results tree view."""

    error_rate_str = f"{row.error_rate * 100:.1f}%" if row.total else "0.0%"
    return (
        row.base_name,
        row.total,
        row.by_result.get("PASS", 0),
        row.by_result.get("FAIL", 0),
        row.by_result.get("ERROR", 0),
        row.by_result.get("SKIP", 0),
        row.by_result.get("UNKNOWN", 0),
        error_rate_str,
        row.group_result,
    )


def format_execution_details(execution: TestExecution) -> str:
    """Format execution details text for the detail panel."""

    lines = [f"Test: {execution.raw_name}"]
    lines.append(f"Base: {execution.base_name}")
    if execution.iteration is not None:
        lines.append(f"Iteration: {execution.iteration}")
    lines.append(f"Result: {execution.result}")
    lines.append(f"Begin: {format_timestamp(execution.begin_time)}")
    lines.append(f"End: {format_timestamp(execution.end_time)}")

    if execution.details:
        lines.append("")
        lines.append("Details:")
        for index, detail in enumerate(execution.details, start=1):
            lines.append(f"[{index}] {detail}")

    if execution.sponge_properties:
        lines.append("")
        lines.append("Sponge Properties:")
        for key, value in sorted(execution.sponge_properties.items()):
            lines.append(f"- {key}: {value}")

    return "\n".join(lines)


def format_timestamp(timestamp_ms: int | None) -> str:
    """Convert epoch milliseconds to a human-readable UTC timestamp."""

    if timestamp_ms is None:
        return "-"
    try:
        seconds = int(timestamp_ms) / 1000
    except (TypeError, ValueError):
        return "-"
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def build_execution_summary_values(
    execution: TestExecution,
) -> Tuple[int | str, str, str, str]:
    """Prepare values displayed in the execution tree."""

    iteration = execution.iteration if execution.iteration is not None else "-"
    begin = format_timestamp(execution.begin_time)
    end = format_timestamp(execution.end_time)
    return (iteration, execution.result, begin, end)
