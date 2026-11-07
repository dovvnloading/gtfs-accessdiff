"""Offline tests for the licensed real-feed research runner.

The tests create artificial, tiny GTFS archives; they never contact a publisher.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import pilot_release_pairs as pilot


def write_feed(path: Path, wheelchair: str, *, location_type: str = "0") -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "stops.txt",
            f"stop_id,stop_name,location_type,wheelchair_boarding\nA,Test,{location_type},{wheelchair}\n",
        )


class PilotTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def test_allowlist_rejects_unapproved_asset(self) -> None:
        with self.assertRaisesRegex(ValueError, "allowlisted"):
            pilot.release_url("../not-a-version")

    def test_unusable_source_does_not_cancel_other_release_pairs(self) -> None:
        releases = tuple((tag, "2026-01-01") for tag in "ABCDE")
        # Three healthy snapshots and a changed baseline; C has malformed GTFS.
        specs = {"A": ("1", "0"), "B": ("0", "0"), "C": ("1", "Jarosław"),
                 "D": ("1", "0"), "E": ("0", "0")}

        def fake_download(tag: str, target: Path) -> dict[str, str | int]:
            wheelchair, location_type = specs[tag]
            write_feed(target, wheelchair, location_type=location_type)
            data = target.read_bytes()
            return {"url": f"https://example.invalid/{tag}.zip",
                    "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}

        output = self.root / "out"
        summary_path = self.root / "step-summary.md"
        with patch.object(pilot, "RELEASES", releases), patch.object(pilot, "_download", side_effect=fake_download), patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}):
            report = pilot.run(output)

        self.assertEqual(report["release_count"], 5)
        self.assertEqual(report["pair_count"], 4)
        self.assertEqual(report["usable_pair_count"], 2)
        self.assertEqual(report["unusable_pair_count"], 2)
        self.assertEqual([p["status"] for p in report["pairs"]], [
            "information_losses_found", "input_unusable", "input_unusable", "information_losses_found",
        ])
        self.assertEqual([p["known_information_losses"] for p in report["pairs"] if p["status"] != "input_unusable"], [1, 1])
        self.assertEqual(report["pairs"][0]["baseline_known_records"], 1)
        self.assertEqual(report["pairs"][0]["candidate_known_records"], 0)
        self.assertEqual(report["pairs"][0]["loss_sample"][0]["stop_id"], "A")
        self.assertEqual(report["pairs"][0]["loss_sample"][0]["baseline_raw_value"], "1")
        self.assertEqual(report["pairs"][1]["unusable_tags"], ["C"])
        self.assertEqual(report["pairs"][2]["unusable_tags"], ["C"])
        invalid = next(release for release in report["releases"] if release["tag"] == "C")
        self.assertEqual(invalid["input_check"], "unusable")
        self.assertIn("Invalid location_type", invalid["input_error"])
        self.assertEqual(json.loads((output / "pilot-summary.json").read_text()), report)
        markdown = (output / "pilot-summary.md").read_text(encoding="utf-8")
        self.assertIn("input unusable", markdown)
        self.assertIn("Jarosław", markdown)
        self.assertEqual(summary_path.read_text(encoding="utf-8"), markdown)

    def test_no_usable_pilot_pairs_is_not_reported_as_success(self) -> None:
        releases = (("BAD_A", "2026-01-01"), ("BAD_B", "2026-01-02"))

        def fake_download(tag: str, target: Path) -> dict[str, str | int]:
            write_feed(target, "1", location_type="unparseable")
            return {"url": f"https://example.invalid/{tag}.zip", "sha256": "test", "bytes": target.stat().st_size}

        with patch.object(pilot, "RELEASES", releases), patch.object(pilot, "_download", side_effect=fake_download), patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.root / "summary.md")}):
            with self.assertRaisesRegex(RuntimeError, "No usable GTFS release pairs"):
                pilot.run(self.root / "out")
        report = json.loads((self.root / "out" / "pilot-summary.json").read_text())
        self.assertEqual(report["unusable_pair_count"], 1)
        self.assertEqual(report["usable_pair_count"], 0)

    def test_clean_pilot_does_not_invent_regressions(self) -> None:
        releases = (("A", "2026-01-01"), ("B", "2026-01-02"))

        def fake_download(tag: str, target: Path) -> dict[str, str | int]:
            write_feed(target, "1")
            return {"url": f"https://example.invalid/{tag}.zip", "sha256": "test", "bytes": target.stat().st_size}

        with patch.object(pilot, "RELEASES", releases), patch.object(pilot, "_download", side_effect=fake_download), patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(self.root / "summary.md")}):
            result = pilot.run(self.root / "out")
        self.assertEqual(result["usable_pair_count"], 1)
        self.assertEqual(result["unusable_pair_count"], 0)
        self.assertEqual(result["pairs"][0]["known_information_losses"], 0)
        self.assertEqual(result["pairs"][0]["status"], "no_information_losses_detected")


if __name__ == "__main__":
    unittest.main()
