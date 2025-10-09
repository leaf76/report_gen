from __future__ import annotations

import itertools

from report_gui.layout import (
    compute_exec_tree_widths,
    compute_group_tree_widths,
)


GROUP_BASE = {
    "test": 260,
    "total": 60,
    "pass": 60,
    "fail": 60,
    "error": 70,
    "skip": 70,
    "unknown": 80,
    "error_rate": 100,
    "result": 100,
}

EXEC_BASE = {
    "iteration": 80,
    "result": 80,
    "begin": 200,
    "end": 200,
}


def test_group_widths_keys_and_types():
    out = compute_group_tree_widths(800, GROUP_BASE)
    assert set(out.keys()) == set(GROUP_BASE.keys())
    assert all(isinstance(v, int) for v in out.values())


def test_group_widths_minimum_and_idempotent():
    # Very small container should clamp test column to minimum
    small = compute_group_tree_widths(100, GROUP_BASE)
    assert small["test"] >= 120

    # Idempotency: same input -> same output
    small2 = compute_group_tree_widths(100, GROUP_BASE)
    assert small == small2


def test_exec_widths_keys_types_non_negative():
    out = compute_exec_tree_widths(800, EXEC_BASE)
    assert set(out.keys()) == set(EXEC_BASE.keys())
    assert all(isinstance(v, int) for v in out.values())
    assert all(v >= 0 for v in out.values())


def test_exec_widths_shrink_and_grow_monotonic():
    # Check that as container grows, flex columns do not decrease
    widths = []
    for w in [200, 300, 400, 600, 900, 1200, 1800]:
        out = compute_exec_tree_widths(w, EXEC_BASE)
        widths.append((out["begin"], out["end"]))
    for (b1, e1), (b2, e2) in itertools.pairwise(widths):
        assert b2 >= b1
        assert e2 >= e1


def test_exec_widths_idempotentacross_calls():
    # Same container size should yield identical results
    out1 = compute_exec_tree_widths(512, EXEC_BASE)
    out2 = compute_exec_tree_widths(512, EXEC_BASE)
    assert out1 == out2


def test_exec_widths_extreme_small_and_zero():
    # Zero/negative widths shouldn't raise and must be non-negative
    out0 = compute_exec_tree_widths(0, EXEC_BASE)
    out_neg = compute_exec_tree_widths(-100, EXEC_BASE)
    for out in (out0, out_neg):
        assert all(v >= 0 for v in out.values())

