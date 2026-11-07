# GTFS AccessDiff report

**Result:** `information_losses_found`

This report compares published wheelchair-accessibility *data*. It does not establish whether a location is physically accessible.

| Metric | Count |
| --- | ---: |
| Location records in baseline | 6 |
| Location records in candidate | 6 |
| Shared IDs | 5 |
| IDs quarantined for identity review | 0 |
| Comparable records | 5 |
| ID overlap (shared / larger feed) | 83.3% |
| Comparable coverage (after identity checks) | 83.3% |
| Records with known status, baseline | 5 |
| Records with known status, candidate | 4 |
| **Known information lost** | **2** |
| Known status changed | 1 |
| Previously unknown became known | 1 |
| Removed IDs (not counted as loss) | 1 |
| Removed IDs with known baseline status | 1 |
| Added IDs | 1 |
| Added IDs with known candidate status | 1 |

## Effective accessibility-status transitions

Counts are for comparable shared stop IDs only, after identity quarantine and parent inheritance.

| Before | After | Records |
| --- | --- | ---: |
| `1` | `1` | 1 |
| `1` | `unknown` | 2 |
| `2` | `1` | 1 |
| `unknown` | `1` | 1 |

## Accessibility metadata changes requiring review

| Stop ID | Name | Finding | Before → After | Effective source (before → after) | Meaning |
| --- | --- | --- | --- | --- | --- |
| B | Oak Street | status\_change | 2 → 1 | B → B | Published wheelchair status changed; confirm why before releasing. |
| PLAT | Central Station Platform | information\_loss | 1 → unknown | STA → unknown | Previously published wheelchair status became unknown. |
| STA | Central Station | information\_loss | 1 → unknown | STA → unknown | Previously published wheelchair status became unknown. |

## Shared IDs requiring identity review

No shared IDs exceeded the conservative identity review checks.

## Shared source of inherited information losses

| Baseline source stop ID | Affected loss records | Example affected IDs |
| --- | ---: | --- |
| STA | 1 | PLAT |

## Added and removed ID samples (not automatically paired)

### Removed IDs

| Stop ID | Name | Effective wheelchair metadata |
| --- | --- | --- |
| D | Removed stop | 1 |

### Added IDs

| Stop ID | Name | Effective wheelchair metadata |
| --- | --- | --- |
| E | New stop | 1 |

## Interpretation and limitations

- `1` indicates some wheelchair access; `2` indicates wheelchair boarding/access is unavailable; `unknown` means no published status is known.
- `information_loss` means known published metadata became unknown; it **does not** demonstrate a physical accessibility change.
- `status_change` requires human review; it may be a correction or a real operational change.
- Explicit/inherited status sources show where an effective accessibility value originated in `stops.txt`.
- Location-type changes and movements beyond the configured distance are quarantined; matching IDs do **not** guarantee matching physical locations.
- Added/removed stop IDs are shown for review, never automatically paired by name or proximity.
- Shared ID comparisons cannot detect cases where both coordinates and names change without exceeding a check threshold.
- Only `stops.txt` is examined; trip access, pathways, live elevator status and text-to-speech are outside this version's scope.
- This is not a GTFS compliance validator; also run the official MobilityData GTFS validator.
