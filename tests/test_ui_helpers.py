import unittest

from report_gui import view_model
from report_gui.models import ResultTotals, TestExecution
from report_gui.ui_helpers import (
    build_execution_summary_values,
    build_overall_summary_text,
    format_execution_details,
    group_row_to_tree_values,
)


class UIHelpersTests(unittest.TestCase):
    def test_build_overall_summary_text_formats_known_results(self):
        totals = ResultTotals(total=5, by_result={"PASS": 3, "FAIL": 2})
        text = build_overall_summary_text(totals)
        self.assertEqual(text, "Total: 5 | PASS: 3 | FAIL: 2")

    def test_build_overall_summary_text_handles_empty_counts(self):
        totals = ResultTotals(total=0, by_result={})
        text = build_overall_summary_text(totals)
        self.assertEqual(text, "Total: 0")

    def test_group_row_to_tree_values_includes_test_name(self):
        row = view_model.GroupRow(
            base_name="test_case",
            total=4,
            by_result={"PASS": 3, "FAIL": 1},
            latest_result="FAIL",
            group_result="FAIL",
            failure_count=1,
            error_rate=0.25,
            latency_averages={"State change latency": 12.5},
        )

        values = group_row_to_tree_values(row)

        self.assertEqual(values[0], "test_case")
        self.assertEqual(values[1], 4)
        self.assertEqual(values[2], 3)
        self.assertEqual(values[3], 1)
        self.assertEqual(values[7], "25.0%")
        self.assertEqual(values[8], "FAIL")

    def test_format_execution_details_numbers_each_detail(self):
        execution = TestExecution(
            raw_name="test_case_0",
            base_name="test_case",
            iteration=0,
            result="FAIL",
            details=["first issue", "second issue"],
            begin_time=1700000000100,
            end_time=1700000000200,
        )

        text = format_execution_details(execution)

        self.assertIn("Begin:", text)
        self.assertIn("UTC", text)
        self.assertIn("Details:", text)
        self.assertIn("[1] first issue", text)
        self.assertIn("[2] second issue", text)

    def test_format_execution_details_handles_missing_times(self):
        execution = TestExecution(
            raw_name="test_case_1",
            base_name="test_case",
            iteration=None,
            result="PASS",
            details=[],
        )

        text = format_execution_details(execution)

        self.assertIn("Begin: -", text)
        self.assertIn("End: -", text)

    def test_build_execution_summary_values_formats_timestamps(self):
        execution = TestExecution(
            raw_name="test_case_2",
            base_name="test_case",
            iteration=2,
            result="PASS",
            begin_time=1700000000100,
            end_time=1700000000200,
        )

        values = build_execution_summary_values(execution)

        self.assertEqual(values[0], 2)
        self.assertIn("UTC", values[2])
        self.assertIn("UTC", values[3])


if __name__ == "__main__":
    unittest.main()
