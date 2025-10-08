"""Data models for report GUI application."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TestExecution:
    """Represents a single execution of a test case."""

    raw_name: str
    base_name: str
    iteration: int | None
    result: str
    details: list[str] = field(default_factory=list)
    sponge_properties: dict[str, Any] = field(default_factory=dict)
    begin_time: int | None = None
    end_time: int | None = None


@dataclass(slots=True)
class TestSummary:
    """Holds the parsed content from a test summary file."""

    requested_tests: list[str]
    executions: list[TestExecution]


@dataclass(slots=True)
class ResultTotals:
    """Aggregated result statistics."""

    total: int
    by_result: dict[str, int]
