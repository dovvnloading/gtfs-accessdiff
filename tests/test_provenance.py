from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from gtfs_accessdiff.audit import compare_feeds, resolved_statuses, load_stops


HEADERS = ["stop_id", "stop_name", "location_type", "parent_station", "wheelchair_boarding", "stop_lat", "stop_lon"]


def make_zip(path: Path, records: list[tuple[str, ...]], *, headers=HEADERS):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(records)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("stops.txt", output.getvalue())


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.old, self.new = root / "old.zip", root / "new.zip"

    def test_inherited_loss_carries_source_and_group(self):
        old = [("ROOT", "Hub", "1", "", "1", "40", "-75"),
               ("PLATFORM", "Platform", "0", "ROOT", "0", "40", "-75"),
               ("AREA", "Boarding", "4", "PLATFORM", "", "40", "-75"),
               ("OVERRIDE", "Independent", "0", "ROOT", "2", "40", "-75")]
        new = [(s[0], s[1], s[2], s[3], "0" if s[0] == "ROOT" else s[4], s[5], s[6]) for s in old]
        make_zip(self.old, old)
        make_zip(self.new, new)
        report = compare_feeds(self.old, self.new)
        self.assertEqual(report.information_losses, 3)
        self.assertEqual(report.inherited_causes[0].baseline_source_id, "ROOT")
        self.assertEqual(report.inherited_causes[0].affected_records, 2)
        self.assertEqual(report.inherited_causes[0].affected_stop_id_sample, ("AREA", "PLATFORM"))
        self.assertEqual({f.stop_id: f.baseline_source_id for f in report.findings},
                         {"AREA": "ROOT", "PLATFORM": "ROOT", "ROOT": "ROOT"})
        self.assertEqual(resolved_statuses(load_stops(self.old))["OVERRIDE"].source_kind, "explicit")
        self.assertEqual(report.to_json(), compare_feeds(self.old, self.new).to_json())

    def test_transition_matrix_counts_all_comparable_values_and_excludes_quarantine(self):
        old = [("A", "A", "0", "", "1", "40", "-75"),
               ("B", "B", "0", "", "2", "40", "-75"),
               ("C", "C", "0", "", "0", "40", "-75"),
               ("D", "D", "0", "", "1", "40", "-75"),
               ("E", "E", "0", "", "2", "40", "-75"),
               ("F", "F", "0", "", "1", "40", "-75")]
        new = [("A", "A", "0", "", "1", "40", "-75"),
               ("B", "B", "0", "", "1", "40", "-75"),
               ("C", "C", "0", "", "2", "40", "-75"),
               ("D", "D", "0", "", "0", "40", "-75"),
               ("E", "E", "0", "", "2", "40", "-75"),
               ("F", "F", "0", "", "0", "41", "-75")]
        make_zip(self.old, old)
        make_zip(self.new, new)
        report = compare_feeds(self.old, self.new, min_overlap=0.75)
        matrix = {(x.baseline_value, x.candidate_value): x.records for x in report.status_transitions}
        self.assertEqual(matrix, {("1", "1"): 1, ("1", "unknown"): 1,
                                  ("2", "1"): 1, ("2", "2"): 1,
                                  ("unknown", "2"): 1})
        self.assertEqual(sum(matrix.values()), report.comparable_records)
        self.assertEqual(report.comparable_records, 5)
        self.assertEqual(report.information_losses, 1)
        self.assertEqual(report.status_changes, 1)
        self.assertEqual(report.information_gains, 1)
        data = report.as_dict()
        self.assertEqual(data["status_transition_total"], 5)
        self.assertEqual(len(data["status_transitions"]), 5)
        self.assertIn("## Effective accessibility-status transitions", report.to_markdown())
        self.assertIn("| `1` | `unknown` | 1 |", report.to_markdown())
        self.assertEqual(report.to_json(), compare_feeds(self.old, self.new, min_overlap=0.75).to_json())

    def test_location_type_change_is_quarantined_not_loss(self):
        make_zip(self.old, [("S", "Station", "1", "", "1", "40", "-75")])
        make_zip(self.new, [("S", "Stop", "0", "", "0", "40", "-75")])
        result = compare_feeds(self.old, self.new)
        self.assertEqual(result.information_losses, 0)
        self.assertEqual(result.comparable_records, 0)
        self.assertEqual(result.status, "inconclusive_low_id_overlap")
        self.assertIn("location_type changed", result.identity_concerns[0].reasons)

    def test_distant_reused_id_with_same_name_is_quarantined(self):
        make_zip(self.old, [("STOP", "Main", "0", "", "1", "40.000", "-75")])
        make_zip(self.new, [("STOP", "Main", "0", "", "0", "40.100", "-75")])
        report = compare_feeds(self.old, self.new)
        self.assertEqual(report.information_losses, 0)
        self.assertGreater(report.identity_concerns[0].moved_meters, 10000)

    def test_nearby_move_and_rename_are_not_automatically_reused(self):
        make_zip(self.old, [("X", "Old", "0", "", "1", "40", "-75")])
        make_zip(self.new, [("X", "New", "0", "", "0", "40.001", "-75")])
        report = compare_feeds(self.old, self.new)
        self.assertEqual(report.information_losses, 1)
        self.assertEqual(report.identity_concerns, ())

    def test_identity_review_stops_inherited_child_false_positives(self):
        old = [("STN", "Old Station", "1", "", "1", "40", "-75"),
               ("CH", "Platform", "0", "STN", "0", "40", "-75")]
        new = [("STN", "New Station", "1", "", "0", "40.02", "-75"),
               ("CH", "Platform", "0", "STN", "0", "40", "-75")]
        make_zip(self.old, old)
        make_zip(self.new, new)
        result = compare_feeds(self.old, self.new)
        self.assertEqual(result.information_losses, 0)
        self.assertEqual([c.stop_id for c in result.identity_concerns], ["CH", "STN"])
        self.assertIn("inherited source", result.identity_concerns[0].reasons[0])

    def test_partial_identity_review_has_distinct_status(self):
        old = [("A", "A", "0", "", "1", "40", "-75"),
               ("B", "B", "0", "", "1", "40", "-75")]
        new = [("A", "A", "0", "", "1", "40", "-75"),
               ("B", "B", "0", "", "0", "41", "-75")]
        make_zip(self.old, old)
        make_zip(self.new, new)
        report = compare_feeds(self.old, self.new, min_overlap=.5)
        self.assertEqual(report.status, "identity_review_required")
        self.assertEqual(report.comparable_overlap, .5)

    def test_added_removed_ids_have_bounded_stable_samples(self):
        make_zip(self.old, [(f"old{i:02d}", f"Old {i}", "0", "", "1", "", "") for i in range(40)])
        make_zip(self.new, [(f"new{i:02d}", f"New {i}", "0", "", "1", "", "") for i in range(40)])
        report = compare_feeds(self.old, self.new)
        d = report.as_dict()
        self.assertEqual(d["removed_record_ids"], 40)
        self.assertEqual(d["added_record_ids"], 40)
        self.assertEqual(d["removed_known_records"], 40)
        self.assertEqual(len(d["removed_id_samples"]), 25)
        self.assertEqual(d["removed_id_samples"][0]["stop_id"], "old00")
        self.assertIn("15 more removed IDs omitted", report.to_markdown())

    def test_report_limit_only_limits_details_not_counts(self):
        make_zip(self.old, [(str(i), "Old", "0", "", "1", "", "") for i in range(12)])
        make_zip(self.new, [(str(i), "New", "0", "", "0", "", "") for i in range(12)])
        result = compare_feeds(self.old, self.new)
        details = result.as_dict(max_findings=3)
        self.assertEqual(details["information_losses"], 12)
        self.assertEqual(details["findings_total"], 12)
        self.assertEqual(details["findings_omitted"], 9)
        self.assertEqual(len(details["findings"]), 3)
        self.assertIn("9 additional accessibility findings omitted", result.to_markdown(max_findings=3))

    def test_escape_untrusted_markdown(self):
        text = '<img src=x> | [bad](https://example.com) `code` *bold*'
        make_zip(self.old, [("A", text, "0", "", "1", "", "")])
        make_zip(self.new, [("A", text, "0", "", "0", "", "")])
        md = compare_feeds(self.old, self.new).to_markdown()
        self.assertIn("&lt;img src=x&gt;", md)
        self.assertIn("\\|", md)
        self.assertIn("\\[bad\\]", md)
        self.assertIn("\\`code\\`", md)
        self.assertNotIn("<img", md)

    def test_unicode_and_multiline_csv(self):
        make_zip(self.old, [("Z", "Łódź\nRondo | Center", "0", "", "1", "", "")])
        make_zip(self.new, [("Z", "Łódź\nRondo | Center", "0", "", "", "", "")])
        report = compare_feeds(self.old, self.new)
        self.assertEqual(report.information_losses, 1)
        self.assertIn("Łódź Rondo \\| Center", report.to_markdown())

    def test_explicit_override_after_inherited_stays_known(self):
        make_zip(self.old, [("S", "Station", "1", "", "1", "", ""),
                            ("C", "Child", "0", "S", "0", "", "")])
        make_zip(self.new, [("S", "Station", "1", "", "0", "", ""),
                            ("C", "Child", "0", "S", "1", "", "")])
        r = compare_feeds(self.old, self.new)
        self.assertEqual(r.information_losses, 1)
        self.assertEqual(r.findings[0].stop_id, "S")
        self.assertEqual(r.inherited_causes, ())


if __name__ == "__main__":
    unittest.main()
