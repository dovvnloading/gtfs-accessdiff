from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from gtfs_accessdiff.audit import FeedError, compare_feeds, load_stops, resolved_wheelchair_values


HEADERS = ["stop_id", "stop_name", "location_type", "parent_station", "wheelchair_boarding"]


def make_zip(path: Path, rows: list[tuple[str, str, str, str, str]], *, columns=HEADERS):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("stops.txt", output.getvalue())


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.before = self.root / "before.zip"
        self.after = self.root / "after.zip"

    def test_detects_loss_through_parent_inheritance(self):
        old_rows = [
            ("STATION", "Central", "1", "", "1"),
            ("PLATFORM", "Central Platform", "0", "STATION", "0"),
        ]
        new_rows = [
            ("STATION", "Central", "1", "", "0"),
            ("PLATFORM", "Central Platform", "0", "STATION", ""),
        ]
        make_zip(self.before, old_rows)
        make_zip(self.after, new_rows)
        report = compare_feeds(self.before, self.after)
        self.assertEqual(report.information_losses, 2)
        self.assertEqual(report.status, "information_losses_found")
        self.assertEqual([x.stop_id for x in report.findings], ["PLATFORM", "STATION"])
        self.assertTrue(all(x.new_value == "unknown" for x in report.findings))

    def test_status_change_requires_review_but_is_not_information_loss(self):
        make_zip(self.before, [("A", "Accessible", "0", "", "1")])
        make_zip(self.after, [("A", "Accessible", "0", "", "2")])
        report = compare_feeds(self.before, self.after)
        self.assertEqual(report.status_changes, 1)
        self.assertEqual(report.information_losses, 0)
        self.assertEqual(report.findings[0].category, "status_change")
        self.assertEqual(report.status, "no_information_losses_detected")

    def test_information_gain_is_counted_not_reported_as_regression(self):
        make_zip(self.before, [("A", "Stop A", "0", "", "0")])
        make_zip(self.after, [("A", "Stop A", "0", "", "1")])
        report = compare_feeds(self.before, self.after)
        self.assertEqual(report.information_gains, 1)
        self.assertEqual(report.findings, ())

    def test_added_removed_ids_are_not_automatically_regressions(self):
        make_zip(self.before, [("A", "Stop A", "0", "", "1"), ("B", "Old", "0", "", "1")])
        make_zip(self.after, [("A", "Stop A", "0", "", "1"), ("C", "New", "0", "", "")])
        report = compare_feeds(self.before, self.after)
        self.assertEqual(report.removed_record_ids, 1)
        self.assertEqual(report.added_record_ids, 1)
        self.assertEqual(report.information_losses, 0)
        self.assertEqual(report.status, "inconclusive_low_id_overlap")

    def test_invalid_values_are_rejected(self):
        make_zip(self.before, [("A", "Stop A", "0", "", "3")])
        with self.assertRaisesRegex(FeedError, "Invalid wheelchair_boarding"):
            load_stops(self.before)

    def test_duplicate_id_is_rejected(self):
        make_zip(self.before, [("A", "Stop A", "0", "", "1"), ("A", "Other", "0", "", "2")])
        with self.assertRaisesRegex(FeedError, "Duplicate stop_id"):
            load_stops(self.before)

    def test_missing_parent_and_cycles_are_rejected(self):
        make_zip(self.before, [("A", "A", "0", "MISSING", "0")])
        with self.assertRaisesRegex(FeedError, "nonexistent parent"):
            load_stops(self.before)
        make_zip(self.before, [("A", "A", "0", "B", "0"), ("B", "B", "0", "A", "0")])
        with self.assertRaisesRegex(FeedError, "Cycle"):
            resolved_wheelchair_values(load_stops(self.before))

    def test_directory_input(self):
        directory = self.root / "unpacked"
        directory.mkdir()
        (directory / "stops.txt").write_text("stop_id,stop_name,wheelchair_boarding\nA,Test,1\n", encoding="utf-8")
        self.assertEqual(load_stops(directory)["A"].wheelchair_boarding, "1")

    def test_no_column_means_unknown_not_inaccessible(self):
        make_zip(self.before, [("A", "Stop A", "0", "", "1")])
        make_zip(self.after, [("A", "Stop A", "0", "")], columns=HEADERS[:-1])
        report = compare_feeds(self.before, self.after)
        self.assertEqual(report.information_losses, 1)
        self.assertEqual(report.findings[0].new_value, "unknown")

    def test_missing_zip_member_is_rejected(self):
        with zipfile.ZipFile(self.before, "w") as archive:
            archive.writestr("nested/stops.txt", "stop_id\nA\n")
        with self.assertRaisesRegex(FeedError, "root-level stops.txt"):
            load_stops(self.before)

    def test_deep_parent_hierarchy_does_not_overflow(self):
        # Malformed but parseable feeds may be adversarial; avoid recursion limits.
        rows = [("P0", "Root", "1", "", "1")]
        rows.extend((f"P{i}", f"Child {i}", "0", f"P{i-1}", "0") for i in range(1, 1600))
        make_zip(self.before, rows)
        values = resolved_wheelchair_values(load_stops(self.before))
        self.assertEqual(values["P1599"], "1")

    def test_ambiguous_duplicate_stops_member_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.before, "w") as archive:
                archive.writestr("stops.txt", "stop_id,wheelchair_boarding\nA,1\n")
                archive.writestr("stops.txt", "stop_id,wheelchair_boarding\nA,2\n")
        with self.assertRaisesRegex(FeedError, "duplicate root-level"):
            load_stops(self.before)

    def test_report_is_reproducible_and_machine_readable(self):
        make_zip(self.before, [("A", "Stop | A", "0", "", "1")])
        make_zip(self.after, [("A", "Stop | A", "0", "", "0")])
        report = compare_feeds(self.before, self.after)
        data = json.loads(report.to_json())
        self.assertEqual(data["schema_version"], "0.3.0")
        self.assertEqual(data["information_losses"], 1)
        self.assertIn("Stop \\| A", report.to_markdown())
        self.assertEqual(report.to_json(), compare_feeds(self.before, self.after).to_json())

    def test_major_shrink_must_not_appear_fully_matched(self):
        make_zip(self.before, [(str(i), f"Stop {i}", "0", "", "1") for i in range(10)])
        make_zip(self.after, [("0", "Stop 0", "0", "", "1")])
        report = compare_feeds(self.before, self.after)
        self.assertEqual(report.matched_records, 1)
        self.assertAlmostEqual(report.overlap, 0.1)
        self.assertEqual(report.status, "inconclusive_low_id_overlap")

    def test_large_candidate_growth_is_inconclusive(self):
        make_zip(self.before, [("0", "Stop 0", "0", "", "1")])
        make_zip(self.after, [(str(i), f"Stop {i}", "0", "", "1") for i in range(10)])
        self.assertAlmostEqual(compare_feeds(self.before, self.after).overlap, 0.1)

    def test_duplicate_column_header_rejected(self):
        make_zip(self.before, [("A", "A", "1")], columns=["stop_id", "stop_name", "stop_name"])
        with self.assertRaisesRegex(FeedError, "duplicate column headers"):
            load_stops(self.before)

    def test_extra_data_columns_rejected(self):
        make_zip(self.before, [("A", "A", "1")], columns=["stop_id", "stop_name"])
        with self.assertRaisesRegex(FeedError, "Too many columns"):
            load_stops(self.before)

    def test_invalid_utf8_rejected(self):
        with zipfile.ZipFile(self.before, "w") as archive:
            archive.writestr("stops.txt", b"stop_id,stop_name\nA,\xff\n")
        with self.assertRaisesRegex(FeedError, "Could not read stops.txt"):
            load_stops(self.before)

    def test_nul_byte_rejected(self):
        with zipfile.ZipFile(self.before, "w") as archive:
            archive.writestr("stops.txt", "stop_id,stop_name\nA,Hi\x00there\n")
        with self.assertRaisesRegex(FeedError, "NUL byte"):
            load_stops(self.before)

    def test_unbalanced_csv_quote_rejected(self):
        with zipfile.ZipFile(self.before, "w") as archive:
            archive.writestr("stops.txt", 'stop_id,stop_name\nA,"unterminated\n')
        with self.assertRaisesRegex(FeedError, "Malformed stops.txt CSV"):
            load_stops(self.before)

    def test_empty_csv_rejected(self):
        with zipfile.ZipFile(self.before, "w") as archive:
            archive.writestr("stops.txt", "stop_id,stop_name\n")
        with self.assertRaisesRegex(FeedError, "no stop records"):
            load_stops(self.before)

    def test_override_overlap_threshold(self):
        make_zip(self.before, [("A", "A", "0", "", "1"), ("B", "B", "0", "", "1")])
        make_zip(self.after, [("A", "A", "0", "", "1"), ("C", "C", "0", "", "1")])
        report = compare_feeds(self.before, self.after, min_overlap=0.5)
        self.assertEqual(report.status, "no_information_losses_detected")


if __name__ == "__main__":
    unittest.main()
