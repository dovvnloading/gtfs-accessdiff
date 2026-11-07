from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from gtfs_accessdiff.cli import main
from test_audit import make_zip


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.before = self.root / "before.zip"
        self.after = self.root / "after.zip"

    def call(self, *args):
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            with contextlib.redirect_stderr(io.StringIO()) as stderr:
                exit_code = main([str(self.before), str(self.after), *args])
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_exit_two_on_lost_information(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "0")])
        exit_code, output, _ = self.call("--fail-on-loss")
        self.assertEqual(exit_code, 2)
        self.assertIn("information_losses_found", output)

    def test_opt_in_gating(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "0")])
        self.assertEqual(self.call()[0], 0)

    def test_exit_three_on_inconclusive_comparison(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("B", "B", "0", "", "1")])
        self.assertEqual(self.call("--fail-on-loss")[0], 3)

    def test_output_cannot_overwrite_input_archive(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "1")])
        original = self.before.read_bytes()
        status, _, err = self.call("--output", str(self.before))
        self.assertEqual(status, 1)
        self.assertIn("must not overwrite", err)
        self.assertEqual(self.before.read_bytes(), original)

    def test_output_cannot_overwrite_directory_stops_file(self):
        directory = self.root / "unpacked"
        directory.mkdir()
        source = directory / "stops.txt"
        source.write_text("stop_id,wheelchair_boarding\nA,1\n")
        make_zip(self.after, [("A", "A", "0", "", "1")])
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            code = main([str(directory), str(self.after), "--output", str(source)])
        self.assertEqual(code, 1)
        self.assertIn("must not overwrite", errors.getvalue())
        self.assertEqual(source.read_text(), "stop_id,wheelchair_boarding\nA,1\n")

    def test_json_to_file(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "1")])
        destination = self.root / "reports" / "report.json"
        status, _, _ = self.call("--format", "json", "--output", str(destination))
        self.assertEqual(status, 0)
        self.assertIn('"schema_version"', destination.read_text())


if __name__ == "__main__":
    unittest.main()
