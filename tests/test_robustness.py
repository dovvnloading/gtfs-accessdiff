from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from gtfs_accessdiff.audit import FeedError, compare_feeds, load_stops


class RobustnessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.before = self.dir / 'before.zip'
        self.after = self.dir / 'after.zip'

    def csv_zip(self, path, csv_text):
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as zf:
            zf.writestr('stops.txt', csv_text)

    def test_corrupted_crc_never_returns_clean_report(self):
        source = 'stop_id,wheelchair_boarding\nA,1\n'
        self.csv_zip(self.before, source)
        self.csv_zip(self.after, source)
        raw = self.after.read_bytes()
        offset = raw.index(b'A,1')
        self.after.write_bytes(raw[:offset] + b'A,2' + raw[offset+3:])
        with self.assertRaisesRegex(FeedError, 'Could not read stops.txt'):
            compare_feeds(self.before, self.after)

    def test_decompression_size_guard_checks_member_metadata(self):
        payload = 'stop_id,wheelchair_boarding\n' + ''.join(f'{i},1\n' for i in range(100))
        with zipfile.ZipFile(self.before, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('stops.txt', payload)
        with patch('gtfs_accessdiff.audit.MAX_STOPS_FILE_BYTES', 128):
            with self.assertRaisesRegex(FeedError, 'size limit'):
                load_stops(self.before)

    def test_byte_limit_works_for_directory_input(self):
        directory = self.dir / 'unpacked'
        directory.mkdir()
        (directory / 'stops.txt').write_text('stop_id,wheelchair_boarding\n' + 'A' * 200)
        with patch('gtfs_accessdiff.audit.MAX_STOPS_FILE_BYTES', 128):
            with self.assertRaisesRegex(FeedError, 'size limit'):
                load_stops(directory)

    def test_malformed_coordinate_is_not_used_as_identity_evidence(self):
        self.csv_zip(self.before, 'stop_id,stop_name,stop_lat,stop_lon,wheelchair_boarding\nA,Hello,nan,999,1\n')
        self.csv_zip(self.after, 'stop_id,stop_name,stop_lat,stop_lon,wheelchair_boarding\nA,Hello,40,-75,0\n')
        result = compare_feeds(self.before, self.after)
        self.assertEqual(result.information_losses, 1)
        self.assertFalse(result.identity_concerns)

    def test_cycle_is_rejected_even_when_both_nodes_have_explicit_values(self):
        # Older resolution stopped following a parent when it encountered an
        # explicit status, allowing an invalid cycle to pass undetected.
        csv_text = ("stop_id,stop_name,location_type,parent_station,wheelchair_boarding\n"
                    "A,A,0,B,1\nB,B,0,A,2\n")
        self.csv_zip(self.before, csv_text)
        self.csv_zip(self.after, csv_text)
        with self.assertRaisesRegex(FeedError, "Cycle in parent_station"):
            compare_feeds(self.before, self.after)

    def test_invalid_location_type_fails_closed(self):
        self.csv_zip(self.before, 'stop_id,location_type,wheelchair_boarding\nA,999,1\n')
        with self.assertRaisesRegex(FeedError, 'Invalid location_type'):
            load_stops(self.before)

    def test_common_zero_and_blank_location_types_are_equivalent(self):
        self.csv_zip(self.before, 'stop_id,location_type,wheelchair_boarding\nA,,1\n')
        self.csv_zip(self.after, 'stop_id,location_type,wheelchair_boarding\nA,0,0\n')
        result = compare_feeds(self.before, self.after)
        self.assertEqual(result.information_losses, 1)
        self.assertFalse(result.identity_concerns)

    def test_identity_groups_are_limited_in_json_too(self):
        before = 'stop_id,location_type,wheelchair_boarding\n' + ''.join(f'{i},1,1\n' for i in range(10))
        after = 'stop_id,location_type,wheelchair_boarding\n' + ''.join(f'{i},0,0\n' for i in range(10))
        self.csv_zip(self.before, before)
        self.csv_zip(self.after, after)
        report = compare_feeds(self.before, self.after, min_overlap=0)
        data = json.loads(report.to_json(max_findings=2))
        self.assertEqual(data['identity_concerns_total'], 10)
        self.assertEqual(data['identity_concerns_omitted'], 8)
        self.assertEqual(len(data['identity_concerns']), 2)
        self.assertEqual(report.information_losses, 0)

    def test_markdown_does_not_render_html_from_id_sample(self):
        self.csv_zip(self.before, 'stop_id,stop_name,wheelchair_boarding\nA,<b>Bad</b>,1\n')
        self.csv_zip(self.after, 'stop_id,stop_name,wheelchair_boarding\nB,<b>Bad</b>,1\n')
        text = compare_feeds(self.before, self.after).to_markdown()
        self.assertNotIn('<b>', text)
        self.assertIn('&lt;b&gt;', text)


if __name__ == '__main__':
    unittest.main()
