# Maintainer review protocol for accessibility-metadata changes

**Scope:** A change to published GTFS data, not a verified change in physical wheelchair accessibility. An automated warning does not establish a publisher mistake.

## Review unit

Review **release pairs**, then sample a bounded number of stop IDs. Many changed IDs in one automated export may stem from **one** underlying edit, not independent incidents. Record source URLs, license attribution, SHA-256 archive digests, release dates, stop-ID overlap and whether known wheelchair metadata exists before claiming a regression was meaningfully evaluated.

## Classify a sample

| Code | When to use it |
| --- | --- |
| `actionable_confirmed` | A maintainer verifies the change is unexpected and would trigger correction or release review. |
| `intentional_correction` | The publisher removed/changed a previously inaccurate or unverified value deliberately. |
| `export_pipeline_change` | The raw metadata change is explained by a generator, schema, source integration or format change. |
| `identity_unresolved` | Same stop ID cannot reliably be treated as the same location. |
| `unknown_pending_publisher` | The reviewer cannot determine intent without publisher context. |
| `tool_false_positive` | The implementation incorrectly interprets fields; attach a synthetic regression test. |
| `no_known_baseline` | No safely comparable baseline record has known wheelchair status; zero detected losses is inconclusive. |

## Reviewer worksheet

| Question | Evidence / response |
| --- | --- |
| Feed publisher, version pair, URLs and hashes | |
| Reviewer role (publisher, independent GTFS maintainer, user) | |
| Bounded stop-ID sample and raw field changes | |
| Same stop identity? Parent-station inheritance? | |
| Did you need an existing file diff or other validator? | |
| Outcome code and supporting explanation | |
| Was the alert actionable? Would you block a release? | |
| Start and finish time; minutes spent on review | |
| Detector bug or wording improvement requested | |

Aggregate the total **review minutes**, number of independently evaluated warning groups, actionable outcomes, intended corrections, unresolved cases and demonstrable tool defects. Never substitute automated raw counts for human-confirmed outcomes.

**Outreach:** Do not contact operators or unofficial feed publishers on the repository owner's behalf without a deliberate human decision. A request for interpretation should be private/respectful, emphasize that no physical accessibility problem has been alleged, and offer to share only the relevant bounded data diff.

Related: [Issue #1](https://github.com/dovvnloading/gtfs-accessdiff/issues/1), [first-publisher pilot](PILOT_RESULTS_2026.md), [Transport GZM study](PILOT_GZM_2026.md).
