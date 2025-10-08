"""View-model helpers bridging parsed data and the GUI layer."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, List

from . import stats
from .models import ResultTotals, TestExecution


@dataclass(slots=True)
class GroupRow:
    """Aggregated statistics for a single base test name."""

    base_name: str
    total: int
    by_result: dict[str, int]
    latest_result: str
    group_result: str
    failure_count: int
    error_rate: float
    latency_averages: dict[str, float]


def build_group_rows(executions: Iterable[TestExecution]) -> List[GroupRow]:
    """Build grouped result rows for display."""
    grouped: dict[str, list[TestExecution]] = {}
    for execution in executions:
        grouped.setdefault(execution.base_name, []).append(execution)

    rows: list[GroupRow] = []
    for base_name, items in grouped.items():
        totals: ResultTotals = stats.compute_result_totals(items)
        latest_result = _latest_result(items)
        group_result = compute_group_result(totals.by_result)
        failure_count = totals.by_result.get("FAIL", 0) + totals.by_result.get("ERROR", 0)
        error_rate = failure_count / totals.total if totals.total else 0.0
        latency_averages = _compute_latency_averages(items)
        rows.append(
            GroupRow(
                base_name=base_name,
                total=totals.total,
                by_result=totals.by_result,
                latest_result=latest_result,
                group_result=group_result,
                failure_count=failure_count,
                error_rate=error_rate,
                latency_averages=latency_averages,
            )
        )

    rows.sort(key=lambda row: row.base_name)
    return rows


def _latest_result(executions: list[TestExecution]) -> str:
    latest = max(
        executions,
        key=lambda execution: (
            execution.begin_time or -1,
            execution.iteration if execution.iteration is not None else -1,
        ),
    )
    return latest.result


def compute_group_result(by_result: dict[str, int]) -> str:
    """Compute aggregated group result with error-first logic."""

    if not by_result:
        return "UNKNOWN"

    normalized = {key.upper(): count for key, count in by_result.items() if count > 0}

    if normalized.get("ERROR", 0) > 0:
        return "ERROR"
    if normalized.get("FAIL", 0) > 0:
        return "FAIL"

    total = sum(normalized.values())
    pass_count = normalized.get("PASS", 0)
    if pass_count == total and total > 0:
        return "PASS"

    for status in ("SKIP", "UNKNOWN"):
        if normalized.get(status, 0) > 0:
            return status

    return next(iter(normalized))


def collect_problem_tests(rows: Iterable[GroupRow]) -> list[str]:
    """Return test names whose aggregated result indicates failures or errors."""

    problem_status = {"FAIL", "ERROR"}
    return [
        row.base_name
        for row in rows
        if row.group_result.upper() in problem_status
    ]


def _compute_latency_averages(executions: Iterable[TestExecution]) -> dict[str, float]:
    latency_data: dict[str, list[float]] = defaultdict(list)
    for execution in executions:
        for key, value in execution.sponge_properties.items():
            if not isinstance(value, (int, float)):
                continue
            if "latency" not in key.lower():
                continue
            latency_data[key].append(float(value))

    return {
        key: sum(values) / len(values)
        for key, values in latency_data.items()
        if values
    }
