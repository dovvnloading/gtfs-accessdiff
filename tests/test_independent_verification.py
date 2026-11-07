"""Deterministic independent-verification tests. No internet or Java required."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from io import BytesIO

from scripts.verify_pilot_pair import independent_raw_diff, summarize_validator_report, fetch_pinned


def write_archive(path: Path, body: str) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon,parent_station,wheelchair_boarding\n" + body)


class IndependentVerificationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_direct_raw_changes_are_not_confused_with_inheritance(self):
        old, new = self.root / "old.zip", self.root / "new.zip"
        write_archive(old, "A,One,40,-75,,2\nB,Two,40.1,-75,,1\nC,Three,40.2,-75,,0\n")
        write_archive(new, "A,One,40,-75,,\nB,Two,40.1,-75,,2\nC,Three,40.2,-75,,1\n")
        result = independent_raw_diff(old, new)
        self.assertEqual(result["shared_ids"], 3)
        self.assertEqual(result["raw_known_to_unknown_count"], 1)
        self.assertEqual(result["raw_known_to_unknown_exact_name_count"], 1)
        self.assertEqual(result["raw_known_to_unknown_exact_coord_count"], 1)
        self.assertEqual(result["review_sample"][0]["stop_id"], "A")
        self.assertEqual(sum(t["count"] for t in result["raw_transitions"]), 3)

    def test_added_removed_not_paired_by_name(self):
        old, new = self.root / "old.zip", self.root / "new.zip"
        write_archive(old, "O,Same,40,-75,,1\n")
        write_archive(new, "N,Same,40,-75,,\n")
        result = independent_raw_diff(old, new)
        self.assertEqual(result["shared_ids"], 0)
        self.assertEqual(result["added_ids"], 1)
        self.assertEqual(result["removed_ids"], 1)
        self.assertEqual(result["raw_known_to_unknown_count"], 0)

    def test_rejects_duplicate_raw_ids(self):
        old, new = self.root / "old.zip", self.root / "new.zip"
        write_archive(old, "O,One,40,-75,,1\nO,Two,40,-75,,\n")
        write_archive(new, "O,One,40,-75,,\n")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            independent_raw_diff(old, new)

    def test_summarizes_notice_counts_without_claiming_pass(self):
        report, system = self.root / "report.json", self.root / "system_errors.json"
        report.write_text(json.dumps({"summary": {"validatorVersion": "8.0.1"}, "notices": [
            {"code": "abc", "severity": "WARNING", "totalNotices": 8},
            {"code": "def", "severity": "ERROR", "totalNotices": 2},
        ]}))
        system.write_text(json.dumps({"systemErrors": []}))
        result = summarize_validator_report(report, system)
        self.assertEqual(result["notice_count_by_severity"], {"ERROR": 2, "WARNING": 8})
        self.assertEqual(result["system_errors_count"], 0)
        self.assertEqual(result["system_errors_schema"], "dict")
        self.assertEqual(result["system_errors_keys"], ["systemErrors"])
        self.assertEqual(result["validator_version"], "8.0.1")

    def test_unrecognized_system_error_schema_marked_unknown(self):
        report, system = self.root / "report.json", self.root / "system_errors.json"
        report.write_text('{"notices": []}')
        system.write_text('{"some_new_field": true}')
        result = summarize_validator_report(report, system)
        self.assertIsNone(result["system_errors_count"])
        self.assertEqual(result["system_errors_schema"], "dict")
        self.assertEqual(result["system_errors_keys"], ["some_new_field"])

    def test_official_system_errors_notice_schema_is_counted(self):
        report, system = self.root / "report.json", self.root / "system_errors.json"
        report.write_text('{"notices": []}')
        system.write_text('{"notices": [{"totalNotices": 2}, {"totalNotices": 3}]}')
        actual = summarize_validator_report(report, system)
        self.assertEqual(actual["system_errors_count"], 5)
        self.assertEqual(actual["system_errors_keys"], ["notices"])

    def test_corrupt_notice_shape_is_not_accepted(self):
        report = self.root / "report.json"
        report.write_text('{"notices": [{"code": "abc", "severity": "ERROR", "totalNotices": "2"}]}')
        with self.assertRaisesRegex(ValueError, "notice shape"):
            summarize_validator_report(report, self.root / "system_errors.json")

    def test_download_checksum_mismatch_never_promoted(self):
        target = self.root / "data.zip"
        data = b"no good"
        mock = unittest.mock.MagicMock()
        mock.__enter__.return_value = BytesIO(data)
        with patch("scripts.verify_pilot_pair.urllib.request.urlopen", return_value=mock):
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                fetch_pinned("https://example.com/feed", hashlib.sha256(b"expected").hexdigest(), target, max_bytes=30)
        self.assertFalse(target.exists())
        self.assertFalse(target.with_name(target.name + ".download").exists())

    def test_download_size_cap_prevents_promotion(self):
        target = self.root / "data.zip"
        mock = unittest.mock.MagicMock()
        mock.__enter__.return_value = BytesIO(b"too many bytes")
        with patch("scripts.verify_pilot_pair.urllib.request.urlopen", return_value=mock):
            with self.assertRaisesRegex(ValueError, "exceeded"):
                fetch_pinned("https://example.com/feed", hashlib.sha256(b"too many bytes").hexdigest(), target, max_bytes=3)
        self.assertFalse(target.exists())

if __name__ == "__main__":
    unittest.main()
