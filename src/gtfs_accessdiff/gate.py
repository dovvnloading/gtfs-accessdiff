"""Shared, opt-in CI exit policy for CLI and composite GitHub Action.

A nonzero code is a release-review workflow decision, never an assertion about
real-world access or a proof that the agency published incorrect data.
"""

from __future__ import annotations


def gate_exit_code(
    *,
    comparable_overlap: float,
    min_overlap: float,
    identity_concerns: int,
    information_losses: int,
    status_changes: int,
    comparison_status: str | None = None,
    fail_on_loss: bool = False,
    fail_on_status_change: bool = False,
) -> int:
    """Return 0=pass, 2=loss, 3=incomplete review, or 4=known-status change.

    Missing identity coverage is prioritized above any observed changes; it is
    unsafe to present a partial comparison as a complete release decision.
    An opt-in is required before this method can ever block a release.
    """
    if not (fail_on_loss or fail_on_status_change):
        return 0
    if comparison_status == "inconclusive_no_known_baseline":
        return 3
    if comparable_overlap <= 0 or comparable_overlap < min_overlap or identity_concerns > 0:
        return 3
    if fail_on_loss and information_losses > 0:
        return 2
    if fail_on_status_change and status_changes > 0:
        return 4
    return 0
