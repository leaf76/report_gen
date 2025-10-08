import tempfile
import unittest
from pathlib import Path

from report_gui import exporter


class ExporterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.template = self.temp_path / "template.xlsx"
        self.template.write_bytes(b"dummy")
        self.script_py = self.temp_path / "fill_report.py"
        self.script_py.write_text("print('ok')")
        self.script_bin = self.temp_path / "fill_report.par"
        self.script_bin.write_text("binary")
        self.yaml = self.temp_path / "summary.yaml"
        self.yaml.write_text("---\nType: Record\n...")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_command_for_python_script(self):
        config = exporter.ExportConfig(
            template_path=self.template,
            sheet_name="Generic",
            column="D",
            debug_mode=True,
            script_path=self.script_py,
        )
        cmd = exporter.build_command(config, self.yaml)
        template_resolved = str(self.template.resolve())
        summary_resolved = str(self.yaml.resolve())
        self.assertEqual(cmd[0], "python")
        self.assertIn(f"--xlsx_file={template_resolved}", cmd)
        self.assertIn(f"--sheet_name=Generic", cmd)
        self.assertIn(f"--column=D", cmd)
        self.assertIn(f"--yaml_file={summary_resolved}", cmd)
        self.assertIn("--debug_mode=True", cmd)

    def test_build_command_for_binary_script(self):
        config = exporter.ExportConfig(
            template_path=self.template,
            sheet_name="Generic",
            column="D",
            debug_mode=False,
            script_path=self.script_bin,
        )
        cmd = exporter.build_command(config, self.yaml)
        self.assertEqual(cmd[0], str(self.script_bin.resolve()))
        self.assertNotIn("python", cmd[0])
        self.assertIn("--debug_mode=False", cmd)

    def test_export_runs_for_each_summary(self):
        other_yaml = self.temp_path / "summary2.yaml"
        other_yaml.write_text("---\nType: Record\n...")
        calls = []

        def fake_runner(command):
            calls.append(command)

        config = exporter.ExportConfig(
            template_path=self.template,
            sheet_name="Generic",
            column="D",
            debug_mode=False,
            script_path=self.script_py,
        )
        exporter.export_summaries(
            config,
            [self.yaml, other_yaml],
            runner=fake_runner,
        )

        self.assertEqual(len(calls), 2)
        self.assertTrue(any(str(self.yaml.resolve()) in part for part in calls[0]))
        self.assertTrue(any(str(other_yaml.resolve()) in part for part in calls[1]))

    def test_export_raises_when_template_missing(self):
        missing_template = self.temp_path / "missing.xlsx"
        config = exporter.ExportConfig(
            template_path=missing_template,
            sheet_name="Generic",
            column="D",
            debug_mode=False,
            script_path=self.script_py,
        )
        with self.assertRaises(exporter.ExportError):
            exporter.export_summaries(config, [self.yaml], runner=lambda _: None)

    def test_prepare_output_file_copies_template(self):
        output_path = self.temp_path / "output.xlsx"
        exporter.prepare_output_file(self.template, output_path)
        self.assertTrue(output_path.exists())
        self.assertEqual(
            output_path.read_bytes(),
            self.template.read_bytes(),
        )

    def test_prepare_output_file_missing_template_raises(self):
        missing = self.temp_path / "missing.xlsx"
        output_path = self.temp_path / "output.xlsx"
        with self.assertRaises(exporter.ExportError):
            exporter.prepare_output_file(missing, output_path)


if __name__ == "__main__":
    unittest.main()
