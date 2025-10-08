import tempfile
import unittest
from pathlib import Path

from report_gui import data_loader
from report_gui.view_model import (
    GroupRow,
    build_group_rows,
    compute_group_result,
    collect_problem_tests,
)


SUMMARY_CONTENT = """---\nRequested Tests:\n- test_a\n- test_b\n- test_c\nType: TestNameList\n...\n---\nTest Name: test_a_0\nType: UserData\nsponge_properties:\n    State change latency: 10\ntimestamp: 1700000000000\n...\n---\nBegin Time: 1700000000100\nDetails: success detail\nEnd Time: 1700000000200\nExtra Errors: {}\nExtras: null\nParent: null\nResult: PASS\nRetry Parent: null\nSignature: test_a_0-1700000000100\nStacktrace: null\nTermination Signal Type: None\nTest Class: GenericTest\nTest Name: test_a_0\nType: Record\nUID: null\n...\n---\nTest Name: test_b_0\nType: UserData\nsponge_properties:\n    State change latency: 30\ntimestamp: 1700000000300\n...\n---\nBegin Time: 1700000000400\nDetails: failure detail\nEnd Time: 1700000000500\nExtra Errors: {}\nExtras: null\nParent: null\nResult: FAIL\nRetry Parent: null\nSignature: test_b_0-1700000000400\nStacktrace: null\nTermination Signal Type: AssertionError\nTest Class: GenericTest\nTest Name: test_b_0\nType: Record\nUID: null\n...\n---\nTest Name: test_b_1\nType: UserData\nsponge_properties:\n    State change latency: 50\ntimestamp: 1700000000600\n...\n---\nBegin Time: 1700000000600\nDetails: still failing\nEnd Time: 1700000000700\nExtra Errors: {}\nExtras: null\nParent: null\nResult: FAIL\nRetry Parent: null\nSignature: test_b_1-1700000000600\nStacktrace: null\nTermination Signal Type: AssertionError\nTest Class: GenericTest\nTest Name: test_b_1\nType: Record\nUID: null\n...\n---\nTest Name: test_c_0\nType: UserData\nsponge_properties:\n    State change latency: 15\ntimestamp: 1700000000800\n...\n---\nBegin Time: 1700000000800\nDetails: skipped\nEnd Time: 1700000000900\nExtra Errors: {}\nExtras: null\nParent: null\nResult: SKIP\nRetry Parent: null\nSignature: test_c_0-1700000000800\nStacktrace: null\nTermination Signal Type: None\nTest Class: GenericTest\nTest Name: test_c_0\nType: Record\nUID: null\n...\n---\nTest Name: test_c_1\nType: UserData\nsponge_properties:\n    State change latency: 18\ntimestamp: 1700000001000\n...\n---\nBegin Time: 1700000001000\nDetails: still skip\nEnd Time: 1700000001100\nExtra Errors: {}\nExtras: null\nParent: null\nResult: PASS\nRetry Parent: null\nSignature: test_c_1-1700000001000\nStacktrace: null\nTermination Signal Type: None\nTest Class: GenericTest\nTest Name: test_c_1\nType: Record\nUID: null\n...\n"""


class ViewModelAggregationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.summary_path = Path(self.temp_dir.name) / "summary.yaml"
        self.summary_path.write_text(SUMMARY_CONTENT)
        self.summary = data_loader.parse_test_summary(self.summary_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_compute_group_result_pass_only_when_all_pass(self):
        rows = build_group_rows(self.summary.executions)
        result_map = {row.base_name: row.group_result for row in rows}

        self.assertEqual(result_map["test_a"], "PASS")
        self.assertEqual(result_map["test_b"], "FAIL")
        self.assertEqual(result_map["test_c"], "SKIP")

        row_b = next(row for row in rows if row.base_name == "test_b")
        self.assertEqual(row_b.failure_count, 2)
        self.assertAlmostEqual(row_b.error_rate, 1.0)
        self.assertAlmostEqual(row_b.latency_averages["State change latency"], 40.0)

    def test_compute_group_result_prioritizes_errors(self):
        computed = compute_group_result({"PASS": 1, "ERROR": 1, "FAIL": 1})
        self.assertEqual(computed, "ERROR")

    def test_collect_problem_tests_includes_non_pass_groups(self):
        rows = build_group_rows(self.summary.executions)
        problem_tests = collect_problem_tests(rows)

        self.assertIn("test_b", problem_tests)
        self.assertNotIn("test_a", problem_tests)
        self.assertNotIn("test_c", problem_tests)


if __name__ == "__main__":
    unittest.main()
