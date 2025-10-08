"""Statistics helpers for aggregating test execution results."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from .models import ResultTotals, TestExecution


def compute_result_totals(executions: Iterable[TestExecution]) -> ResultTotals:
    """Compute overall result counts."""
    counter: Counter[str] = Counter()
    total = 0
    for execution in executions:
        counter[execution.result] += 1
        total += 1
    return ResultTotals(total=total, by_result=dict(counter))


def group_results_by_base(
    executions: Iterable[TestExecution],
) -> dict[str, ResultTotals]:
    """Group executions by base test name and compute totals."""
    grouped: dict[str, list[TestExecution]] = {}
    for execution in executions:
        grouped.setdefault(execution.base_name, []).append(execution)

    return {
        base: compute_result_totals(items)
        for base, items in grouped.items()
    }
