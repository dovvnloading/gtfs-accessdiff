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

    def test_zero_overlap_with_zero_threshold_is_still_inconclusive(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("B", "B", "0", "", "1")])
        exit_code, output, _ = self.call("--min-overlap", "0", "--fail-on-loss")
        self.assertEqual(exit_code, 3)
        self.assertIn("inconclusive_low_id_overlap", output)
        self.assertIn("Inconclusive:", output)
        self.assertEqual(self.call("--min-overlap", "0", "--fail-on-status-change")[0], 3)
        self.assertEqual(self.call("--min-overlap", "0")[0], 0)  # report-only remains nonblocking

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

    def test_identity_review_exit_three_even_with_high_overlap(self):
        self.before.write_bytes(b"")
        self.after.write_bytes(b"")
        from test_provenance import make_zip
        make_zip(self.before, [("A", "A", "0", "", "1", "40", "-75"),
                               ("B", "B", "0", "", "1", "40", "-75")])
        make_zip(self.after, [("A", "A", "0", "", "1", "40", "-75"),
                              ("B", "B", "0", "", "0", "41", "-75")])
        self.assertEqual(self.call("--fail-on-loss", "--min-overlap", "0.5")[0], 3)
        self.assertEqual(self.call("--fail-on-loss", "--min-overlap", "0.5", "--identity-distance-meters", "200000")[0], 2)

    def test_status_change_gate_is_separate_from_loss_gate(self):
        make_zip(self.before, [("A", "Stop", "0", "", "1")])
        make_zip(self.after, [("A", "Stop", "0", "", "2")])
        self.assertEqual(self.call()[0], 0)
        self.assertEqual(self.call("--fail-on-loss")[0], 0)
        self.assertEqual(self.call("--fail-on-status-change")[0], 4)
        self.assertEqual(self.call("--fail-on-loss", "--fail-on-status-change")[0], 4)

    def test_identity_quarantine_prioritized_above_other_detected_losses(self):
        from test_provenance import make_zip as make_geocoded_zip
        before = [("A", "A", "0", "", "1", "40", "-75"),
                  ("B", "B", "0", "", "1", "40", "-75")]
        after = [("A", "A", "0", "", "0", "40", "-75"),
                 ("B", "B", "0", "", "0", "42", "-75")]
        make_geocoded_zip(self.before, before)
        make_geocoded_zip(self.after, after)
        code, output, _ = self.call("--fail-on-loss", "--min-overlap", "0.5")
        self.assertEqual(code, 3)
        self.assertIn("information_losses_found", output)
        self.assertIn("Partial review required", output)

    def test_reject_nonfinite_cli_thresholds(self):
        import contextlib
        import io
        for option, value in (("--min-overlap", "nan"), ("--min-overlap", "inf"),
                              ("--identity-distance-meters", "inf"), ("--max-findings", "0")):
            with self.subTest(option=option, value=value):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as e:
                        main([str(self.before), str(self.after), option, value])
                self.assertEqual(e.exception.code, 2)

    def test_fail_on_loss_with_report_output_is_still_written(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "0")])
        dest = self.root / "report.json"
        status, _, _ = self.call("--fail-on-loss", "--format", "json", "--output", str(dest))
        self.assertEqual(status, 2)
        self.assertEqual(__import__("json").loads(dest.read_text())["information_losses"], 1)

    def test_json_to_file(self):
        make_zip(self.before, [("A", "A", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "1")])
        destination = self.root / "reports" / "report.json"
        status, _, _ = self.call("--format", "json", "--output", str(destination))
        self.assertEqual(status, 0)
        self.assertIn('"schema_version"', destination.read_text())

    def test_no_known_baseline_is_nonblocking_only_in_report_mode(self):
        make_zip(self.before, [("A", "Stop", "0", "", "0")])
        make_zip(self.after, [("A", "Stop", "0", "", "0")])
        code, output, _ = self.call()
        self.assertEqual(code, 0)
        self.assertIn("inconclusive_no_known_baseline", output)
        self.assertEqual(self.call("--fail-on-loss")[0], 3)
        self.assertEqual(self.call("--fail-on-status-change")[0], 3)


if __name__ == "__main__":
    unittest.main()
