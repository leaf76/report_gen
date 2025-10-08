import tempfile
import unittest
from pathlib import Path

from report_gui import data_loader, stats


SUMMARY_CONTENT = """---\nRequested Tests:\n- test_a\n- test_b\nType: TestNameList\n...\n---\nTest Name: test_a_0\nType: UserData\nsponge_properties:\n    metric_a: 42\ntimestamp: 1700000000000\n...\n---\nBegin Time: 1700000000100\nDetails: success detail\nEnd Time: 1700000000200\nExtra Errors: {}\nExtras: null\nParent: null\nResult: PASS\nRetry Parent: null\nSignature: test_a_0-1700000000100\nStacktrace: null\nTermination Signal Type: None\nTest Class: GenericTest\nTest Name: test_a_0\nType: Record\nUID: null\n...\n---\nTest Name: test_b_0\nType: UserData\nsponge_properties:\n    metric_b: 3.14\ntimestamp: 1700000000300\n...\n---\nBegin Time: 1700000000400\nDetails: failure detail\nEnd Time: 1700000000500\nExtra Errors:\n    err@1700000000400:\n        Details: deeper issue\n        Extras: null\n        Position: null\n        Stacktrace: null\nExtras: null\nParent: null\nResult: FAIL\nRetry Parent: null\nSignature: test_b_0-1700000000400\nStacktrace: null\nTermination Signal Type: AssertionError\nTest Class: GenericTest\nTest Name: test_b_0\nType: Record\nUID: null\n...\n"""


class DataLoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.summary_path = Path(self.temp_dir.name) / "summary.yaml"
        self.summary_path.write_text(SUMMARY_CONTENT)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_test_summary_returns_requested_tests_and_executions(self):
        summary = data_loader.parse_test_summary(self.summary_path)

        self.assertEqual(summary.requested_tests, ["test_a", "test_b"])
        self.assertEqual(len(summary.executions), 2)

        first = summary.executions[0]
        self.assertEqual(first.base_name, "test_a")
        self.assertEqual(first.iteration, 0)
        self.assertEqual(first.result, "PASS")
        self.assertEqual(first.details, ["success detail"])
        self.assertEqual(first.sponge_properties, {"metric_a": 42})
        self.assertEqual(first.begin_time, 1700000000100)
        self.assertEqual(first.end_time, 1700000000200)

        second = summary.executions[1]
        self.assertEqual(second.base_name, "test_b")
        self.assertEqual(second.iteration, 0)
        self.assertEqual(second.result, "FAIL")
        self.assertEqual(second.details, ["failure detail", "deeper issue"])

    def test_compute_statistics_counts_results(self):
        summary = data_loader.parse_test_summary(self.summary_path)
        totals = stats.compute_result_totals(summary.executions)

        self.assertEqual(totals.total, 2)
        self.assertEqual(totals.by_result, {"PASS": 1, "FAIL": 1})

        grouped = stats.group_results_by_base(summary.executions)

        self.assertIn("test_a", grouped)
        self.assertEqual(grouped["test_a"].total, 1)
        self.assertEqual(grouped["test_a"].by_result, {"PASS": 1})
        self.assertIn("test_b", grouped)
        self.assertEqual(grouped["test_b"].total, 1)
        self.assertEqual(grouped["test_b"].by_result, {"FAIL": 1})

    def test_parse_multiple_test_summaries_combines_results(self):
        another_content = SUMMARY_CONTENT.replace("test_b_0", "test_c_0").replace(
            "test_b", "test_c"
        )
        other_path = Path(self.temp_dir.name) / "summary2.yaml"
        other_path.write_text(another_content)

        combined = data_loader.parse_multiple_test_summaries(
            [self.summary_path, other_path]
        )

        self.assertEqual(
            combined.requested_tests,
            ["test_a", "test_b", "test_c"],
        )
        self.assertEqual(len(combined.executions), 4)
        base_names = {execution.base_name for execution in combined.executions}
        self.assertEqual(base_names, {"test_a", "test_b", "test_c"})


if __name__ == "__main__":
    unittest.main()
