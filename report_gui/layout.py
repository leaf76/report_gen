"""Layout computation helpers for responsive sizing.

These helpers encapsulate width calculations so they can be unit-tested
without requiring a live Tkinter environment.
"""

from __future__ import annotations

from typing import Dict


# Constants used for available-width calculation
_SCROLLBAR_W = 18
_PADDING_W = 8
_MIN_TEST_W = 120
_MIN_FLEX_W = 120


def compute_group_tree_widths(container_w: int, base_widths: Dict[str, int]) -> Dict[str, int]:
    """Compute column widths for the Group tree.

    - `base_widths` must include: "test", "total", "pass", "fail", "error",
      "skip", "unknown", "error_rate", "result".
    - Returns a dict with the same keys and integer widths.
    """
    container_w = int(max(0, container_w))
    avail = max(0, container_w - _SCROLLBAR_W - _PADDING_W)

    widths = dict(base_widths)
    fixed_cols = (
        "total",
        "pass",
        "fail",
        "error",
        "skip",
        "unknown",
        "error_rate",
        "result",
    )
    fixed_total = sum(int(widths[c]) for c in fixed_cols)
    base_test = int(widths["test"]) if "test" in widths else 0
    base_total = fixed_total + base_test

    if avail >= base_total:
        new_test = avail - fixed_total
    else:
        deficit = base_total - avail
        new_test = max(_MIN_TEST_W, base_test - deficit)

    out: Dict[str, int] = {c: int(widths[c]) for c in fixed_cols}
    out["test"] = int(max(_MIN_TEST_W, new_test))
    return out


def compute_exec_tree_widths(container_w: int, base_widths: Dict[str, int]) -> Dict[str, int]:
    """Compute column widths for the Execution tree.

    - `base_widths` must include: "iteration", "result", "begin", "end".
    - Fixed columns: iteration, result
    - Flex columns: begin, end share remaining space equally (with minimums)
    """
    container_w = int(max(0, container_w))
    avail = max(0, container_w - _SCROLLBAR_W - _PADDING_W)

    widths = dict(base_widths)
    fixed_cols = ("iteration", "result")
    flex_cols = ("begin", "end")
    fixed_total = sum(int(widths[c]) for c in fixed_cols)
    base_flex_total = sum(int(widths[c]) for c in flex_cols)
    base_total = fixed_total + base_flex_total

    if avail >= base_total:
        extra = avail - fixed_total
        each = max(_MIN_FLEX_W, extra // 2)
        begin_w = int(each)
        end_w = int(extra - each)
    else:
        # Not enough space: assign minimums but clamp to available remainder
        # This keeps values stable and non-negative to avoid oscillation.
        remaining_for_flex = max(0, avail - fixed_total)
        # If there's no room, set both to 0; otherwise split at least MIN_FLEX.
        if remaining_for_flex <= 0:
            begin_w = 0
            end_w = 0
        else:
            each = max(_MIN_FLEX_W, remaining_for_flex // 2)
            # Do not exceed remaining space
            each = min(each, remaining_for_flex)
            begin_w = int(each)
            end_w = int(max(0, remaining_for_flex - each))

    out: Dict[str, int] = {
        "iteration": int(widths["iteration"]),
        "result": int(widths["result"]),
        "begin": int(max(0, begin_w)),
        "end": int(max(0, end_w)),
    }
    return out

