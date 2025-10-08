"""Parses automation test summary YAML files into structured data."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

try:  # pragma: no cover - import resolution
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback
    from ruamel.yaml import YAML  # type: ignore

    _YAML = YAML(typ="safe")

    def _safe_load_all(stream: Iterable[str] | Iterator[str]) -> Iterator[Any]:
        return _YAML.load_all(stream)
else:  # pragma: no cover - primary path
    def _safe_load_all(stream: Iterable[str] | Iterator[str]) -> Iterator[Any]:
        return yaml.safe_load_all(stream)  # type: ignore

from .models import TestExecution, TestSummary


def parse_test_summary(path: str | Path) -> TestSummary:
    """Parse a test summary YAML file."""
    summary_path = Path(path)
    documents = list(_load_documents(summary_path))

    requested_tests: list[str] = []
    pending_userdata: dict[str, dict[str, Any]] = {}
    executions: list[TestExecution] = []

    for document in documents:
        if not isinstance(document, dict):
            continue
        doc_type = document.get("Type")
        if doc_type == "TestNameList":
            requested_tests = list(document.get("Requested Tests", []))
        elif doc_type == "UserData":
            test_name = document.get("Test Name")
            if test_name:
                pending_userdata[test_name] = document
        elif doc_type == "Record":
            execution = _build_execution(document, pending_userdata)
            if execution:
                executions.append(execution)

    return TestSummary(
        requested_tests=requested_tests,
        executions=_sort_executions(executions),
    )


def parse_multiple_test_summaries(
    paths: Sequence[str | Path],
) -> TestSummary:
    """Parse multiple summary files and combine the results."""

    combined_requested: list[str] = []
    seen_tests: set[str] = set()
    combined_executions: list[TestExecution] = []

    for path in paths:
        summary = parse_test_summary(path)
        for test in summary.requested_tests:
            if test not in seen_tests:
                seen_tests.add(test)
                combined_requested.append(test)
        combined_executions.extend(summary.executions)

    return TestSummary(
        requested_tests=combined_requested,
        executions=_sort_executions(combined_executions),
    )


def _load_documents(path: Path) -> list[Any]:
    with path.open("r", encoding="utf-8") as handle:
        return list(_safe_load_all(handle))


def _build_execution(
    record_doc: dict[str, Any],
    pending_userdata: dict[str, dict[str, Any]],
) -> TestExecution | None:
    raw_name = record_doc.get("Test Name")
    if not raw_name:
        return None

    user_doc = pending_userdata.pop(raw_name, {})
    base_name, iteration = _split_iteration(raw_name)
    result = _normalize_result(record_doc.get("Result"))
    details = _collect_details(record_doc)
    sponge_properties = _extract_sponge_properties(user_doc)
    begin_time = _safe_int(record_doc.get("Begin Time"))
    end_time = _safe_int(record_doc.get("End Time"))

    return TestExecution(
        raw_name=raw_name,
        base_name=base_name,
        iteration=iteration,
        result=result,
        details=details,
        sponge_properties=sponge_properties,
        begin_time=begin_time,
        end_time=end_time,
    )


def _split_iteration(raw_name: str) -> tuple[str, int | None]:
    if "_" not in raw_name:
        return raw_name, None
    head, tail = raw_name.rsplit("_", 1)
    return (head, int(tail)) if tail.isdigit() else (raw_name, None)


def _normalize_result(result: Any) -> str:
    if not isinstance(result, str):
        return "UNKNOWN"
    return result.strip().upper()


def _collect_details(record_doc: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    primary_detail = record_doc.get("Details")
    if isinstance(primary_detail, str) and primary_detail.strip():
        candidates.append(primary_detail.strip())

    extras = record_doc.get("Extras")
    if isinstance(extras, str) and extras.strip():
        candidates.append(extras.strip())

    extra_errors = record_doc.get("Extra Errors")
    if isinstance(extra_errors, dict):
        for payload in extra_errors.values():
            if isinstance(payload, dict):
                detail = payload.get("Details")
                if isinstance(detail, str) and detail.strip():
                    candidates.append(detail.strip())

    ordered_unique = list(OrderedDict.fromkeys(candidates).keys())
    return ordered_unique


def _extract_sponge_properties(user_doc: dict[str, Any]) -> dict[str, Any]:
    sponge_properties = user_doc.get("sponge_properties")
    if isinstance(sponge_properties, dict):
        return dict(sponge_properties)
    return {}


def _safe_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _sort_executions(executions: list[TestExecution]) -> list[TestExecution]:
    executions.sort(
        key=lambda execution: (
            execution.base_name,
            execution.iteration if execution.iteration is not None else -1,
            execution.begin_time or 0,
        )
    )
    return executions
