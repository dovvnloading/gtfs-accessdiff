"""Release-review gate policy. All tests are local and deterministic."""
from __future__ import annotations

import unittest

from gtfs_accessdiff.gate import gate_exit_code


class GateTests(unittest.TestCase):
    def base(self, **kwargs):
        options = {"comparable_overlap": 1.0, "min_overlap": 0.75,
                   "identity_concerns": 0, "information_losses": 0,
                   "status_changes": 0, "fail_on_loss": False,
                   "fail_on_status_change": False}
        options.update(kwargs)
        return gate_exit_code(**options)

    def test_no_opt_in_is_never_blocking(self):
        self.assertEqual(self.base(information_losses=12, status_changes=2,
                                   comparable_overlap=0.1, identity_concerns=3), 0)

    def test_loss_gate_only_blocks_losses(self):
        self.assertEqual(self.base(information_losses=1, fail_on_loss=True), 2)
        self.assertEqual(self.base(status_changes=1, fail_on_loss=True), 0)

    def test_status_gate_only_blocks_known_status_change(self):
        self.assertEqual(self.base(status_changes=1, fail_on_status_change=True), 4)
        self.assertEqual(self.base(information_losses=1, fail_on_status_change=True), 0)

    def test_when_both_enabled_loss_comes_before_status_change(self):
        self.assertEqual(self.base(information_losses=2, status_changes=1,
                                   fail_on_loss=True, fail_on_status_change=True), 2)

    def test_identity_concerns_precede_detected_loss_and_change(self):
        self.assertEqual(self.base(information_losses=1, status_changes=1,
                                   identity_concerns=1, fail_on_loss=True,
                                   fail_on_status_change=True), 3)

    def test_low_coverage_always_requires_review_when_any_gate_enabled(self):
        self.assertEqual(self.base(comparable_overlap=0.5, min_overlap=0.75,
                                   information_losses=2, fail_on_loss=True), 3)
        self.assertEqual(self.base(comparable_overlap=0.75, min_overlap=0.75,
                                   status_changes=1, fail_on_status_change=True), 4)

if __name__ == "__main__":
    unittest.main()
