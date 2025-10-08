import unittest
from pathlib import Path
from unittest import mock

import main


class MainModuleTests(unittest.TestCase):
    def test_main_without_path_runs_gui_without_argument(self):
        with mock.patch("main.run_app") as run_app_mock:
            exit_code = main.main([])
        self.assertEqual(exit_code, 0)
        run_app_mock.assert_called_once_with(None)

    def test_main_with_path_passes_resolved_path_to_gui(self):
        summary_arg = "reports/sample.yaml"
        with mock.patch("main.run_app") as run_app_mock:
            exit_code = main.main([summary_arg])
        self.assertEqual(exit_code, 0)
        run_app_mock.assert_called_once()
        passed_paths = run_app_mock.call_args.args[0]
        self.assertEqual(len(passed_paths), 1)
        self.assertEqual(
            passed_paths[0],
            Path(summary_arg).expanduser().resolve(),
        )

    def test_main_with_multiple_paths_passes_all_to_gui(self):
        summary_args = ["reports/a.yaml", "../b.yaml"]
        with mock.patch("main.run_app") as run_app_mock:
            exit_code = main.main(summary_args)
        self.assertEqual(exit_code, 0)
        run_app_mock.assert_called_once()
        passed_paths = run_app_mock.call_args.args[0]
        expected = [Path(arg).expanduser().resolve() for arg in summary_args]
        self.assertEqual(passed_paths, expected)


if __name__ == "__main__":
    unittest.main()
