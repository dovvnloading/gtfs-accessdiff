# GTFS AccessDiff report

**Result:** `information_losses_found`

This report compares published wheelchair-accessibility *data*. It does not establish whether a location is physically accessible.

| Metric | Count |
| --- | ---: |
| Location records in baseline | 6 |
| Location records in candidate | 6 |
| IDs matched across releases | 5 |
| Overlap (matched / larger feed) | 83.3% |
| Records with known status, baseline | 5 |
| Records with known status, candidate | 4 |
| **Known information lost** | **2** |
| Known status changed | 1 |
| Previously unknown became known | 1 |
| Removed IDs (not classified as losses) | 1 |
| Added IDs | 1 |

## Changes requiring review

| Stop ID | Name | Finding | Before → After | Meaning |
| --- | --- | --- | --- | --- |
| `B` | Oak Street | status_change | `2` → `1` | Published wheelchair status changed; confirm why before releasing. |
| `PLAT` | Central Station Platform | information_loss | `1` → `unknown` | Previously published wheelchair status became unknown. |
| `STA` | Central Station | information_loss | `1` → `unknown` | Previously published wheelchair status became unknown. |

## Interpretation and limitations

- `1` means wheelchair boarding/access is indicated; `2` means wheelchair boarding/access is indicated as unavailable; `unknown` means no published status is known.
- A `loss` means a known published value changed to unknown; it does **not** prove a physical accessibility change.
- A `status_change` requires human review. It may reflect a correction or a real service change.
- Locations are matched by stable `stop_id`; new/removed IDs are counted, not called regressions. ID churn can make comparisons inconclusive.
- GTFS parent-station inheritance is resolved before comparing each location.
- Version 0.1 examines only `stops.txt`'s `wheelchair_boarding`, not trip access, pathways, live elevator status, or text-to-speech.
- Run the official MobilityData GTFS validator separately; this tool is not a standards-compliance validator.
