# Independent validation of the 132 metadata-loss flags (2026)

**Status: automated cross-check completed; publisher intent and user impact are unverified.** The independent verifier ran successfully in [GitHub Actions](https://github.com/dovvnloading/gtfs-accessdiff/actions/runs/42324858322). The [aggregate JSON results](research/independent-validation-2026.json) record the exact input asset SHA-256 hashes and per-release third-party validator notices. No original feed ZIPs or validator executable are committed or redistributed.

## Source, permission, and scope

- **Publisher and attribution:** [Jarosławska Komunikacja Miejska GTFS](https://github.com/rozkladnik/gtfs-pwik-jaroslaw), an *unofficial* independently compiled feed published by `rozkladnik` under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is not the agency's official export.
- **Compared archives:** `13.05.2026_1.1.0` (released May 14, 2026; SHA-256 `1f14d2c7711534ae219c632f74c63950cb474236669b42042a844a3c3229c5e7`) and `13.05.2026_1.2.0` (June 4, 2026; SHA-256 `809a5d3daad7bd7480fb3834538f817e495c979d724728bdcff67b4503ab87b6`). Their [download locations](research/independent-validation-2026.json) are in the JSON record.
- **Independent validator:** [MobilityData GTFS Validator v8.0.1](https://github.com/MobilityData/gtfs-validator/releases/tag/v8.0.1), its CLI JAR downloaded and checked against publisher SHA-256 `19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2` before execution. Java 21 was used; each feed's validation date was its own publication date.
- **Method:** `scripts/verify_pilot_pair.py` independently parses both raw `stops.txt` CSV files using Python's standard library; it never imports GTFS AccessDiff's comparison code. Separately it runs the official Java validator against both original archives. Both processes run on temporary files in a least-privilege GitHub Actions workflow.

## Independently reproduced raw `wheelchair_boarding` field changes

Both archives contain **145 matching published `stop_id` values**. The raw-field cross-check found the same **132 known (`1`/`2`) → unknown (`0`/empty)** changes as our primary comparison engine:

| Raw baseline field | Raw candidate field | Records |
| --- | --- | ---: |
| `2` | blank | 116 |
| `1` | blank | 15 |
| `2` | `0` | 1 |
| `1` | `1` | 10 |
| `2` | `2` | 2 |
| blank | blank | 1 |
| **Total shared IDs** | | **145** |

Among the **132** changed raw values, **131** retain exactly matching published coordinates, **132** retain the same parent-station field, and **55** retain the exact same stop name. The source explicitly says some stop coordinates are approximate; neither identical coordinates nor matching identifiers prove that physical stop identity or wheelchair access was unchanged. The changed names may reflect routine editing; their cause is unknown.

This verifies the literal before/after data difference independently. It does **not** establish accidental removal, physical inaccessibility, agency responsibility, or rider impact. The original release descriptions are empty, and the two release tags point to the same source commit; the archival ZIP assets hold the relevant dated data.

## MobilityData validator results (conformance, not regression detection)

| Release | ERROR notices | WARNING notices | INFO notices |
| --- | ---: | ---: | ---: |
| May 14, 2026 baseline | 0 | 711 | 4 |
| June 4, 2026 candidate | 0 | 77 | 40 |

The largest warning group in the baseline concerned `equal_shape_distance_same_coordinates` (703 notices); the candidate had 51 of these, plus 16 `stop_too_far_from_shape` warnings. These are not accessibility-regression verdicts. The official validator's zero ERROR-notice count does **not** imply the feeds are complete or that optional accessibility metadata did not disappear. The validator's system-errors report was not interpreted in the initial automated summary, so we do not claim a separate zero system-error count.

## How to reproduce

A GitHub Actions runner with GitHub release download access, Python 3.11+, Java 21 and internet access can execute:

```bash
python scripts/verify_pilot_pair.py
```

Or use [the reproducible cross-check workflow](../.github/workflows/independent-validator.yml). The script downloads only the two SHA-pinned feed ZIPs and the SHA-pinned official validator CLI, checks size limits and hashes, computes an independent transition matrix and aggregates notice counts. Its outputs are two small summary files; source ZIPs and the validator JAR are destroyed with the temporary directory. The public GitHub workflow deliberately uses `contents: read` and no credentials beyond normal checkout permissions.

## What remains before calling this a confirmed regression

1. A human or the publisher must review representative stop-level records, including name edits, to explain why the field became unknown.
2. A second, unrelated publisher and several feed version pairs should be studied to estimate prevalence and false-positive costs. One 132-record event is **one** correlated publication change, not 132 independent incidents.
3. We need a maintainer usability test: time to understand, dismiss, or correct a report, and whether the warning would have altered their release workflow.
4. Do not make claims about actual physical access, operator performance, or safety outcomes from static GTFS metadata alone.
