# 2026 historical GTFS pilot: automated results

**Source and attribution:** [Jarosławska Komunikacja Miejska GTFS](https://github.com/rozkladnik/gtfs-pwik-jaroslaw), independently compiled and published by `rozkladnik` (unofficial, not the transit agency). Publisher feed files are available under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The tool source code is MIT-licensed; publisher feeds retain their separate license.

**Reproduction:** Run `PYTHONPATH=src python scripts/pilot_release_pairs.py` in this repository, or inspect [successful GitHub Actions pilot run 42322378463](https://github.com/dovvnloading/gtfs-accessdiff/actions/runs/42322378463) for downloaded aggregate artifacts. This record was created from the successful run on November 6, 2026 (America/New_York; CI execution in UTC November 7), using [GTFS AccessDiff v0.3 commit `10d3bb2`](https://github.com/dovvnloading/gtfs-accessdiff/commit/10d3bb2901460e0ac736ee826cb14021364c1b44).

**Scope and status:** 20 assets published during 2026 by **one** unofficial feed publisher, compared in **19 adjacent release pairs**. **18 pairs were comparable**; **one was not compared** because the earlier release contained invalid `location_type` metadata. The research is automated only. **The 132 raw changes have now been replicated by an independent CSV comparison, and both source archives run through MobilityData Validator v8.0.1**, but publisher intent, physical accessibility, rider impact, and whether the changes are erroneous remain unverified. See [independent verification](INDEPENDENT_VALIDATION_2026.md). See [pilot protocol](PILOT.md) and [issue #1](https://github.com/dovvnloading/gtfs-accessdiff/issues/1) for human review and further independent-feed validation.

## What was observed

- **132 potential known → unknown metadata losses in one release pair:** `13.05.2026_1.1.0` (published May 14, 2026) to `13.05.2026_1.2.0` (June 4, 2026). Both have 145 stop IDs, all safely comparable by this tool's conservative matching rules, and no ID churn in that pair. The total known wheelchair status falls from **144 to 12**. **This is a published-data discontinuity, not evidence that any stop became physically inaccessible.**
- The bounded JSON sample shows five unchanged stop IDs with explicit baseline `wheelchair_boarding=2` (published wheelchair boarding unavailable) becoming blank (unknown) in the candidate. Samples do not establish why the publisher changed the data.
- A different release pair, `01.09.2026_1.7.0` → `v118_09_01_2026`, shows **2 known status changes** and **81 information gains**, rather than information losses.
- `01.02.2026` could not be compared: `stops.txt` contains `location_type` of `Jarosław` at row 109 instead of the specification's enumerated values. One adjacent comparison was marked `input_unusable`, **not** reported clean or silently excluded from the count.
- These are **not** 132 distinct agencies or 132 independently reviewed incidents: the flagged records arise from the same update of one unofficial feed.

## Sample of records requiring human review

| Published stop ID | Raw status in baseline | Raw status in candidate | Effective status |
| --- | --- | --- | --- |
| `Jar_BaCh_01` | `2` | `blank` | `2` → `unknown` |
| `Jar_BaCh_02` | `2` | `blank` | `2` → `unknown` |
| `Jar_BaCh_03` | `2` | `blank` | `2` → `unknown` |
| `Jar_BaCh_04` | `2` | `blank` | `2` → `unknown` |
| `Jar_Band_01` | `2` | `blank` | `2` → `unknown` |

These IDs are publisher-provided labels, not verified real-world stop identities. None has been reviewed with the publisher. The full machine-recorded sample, counts, provenance and limitations are in [pilot-2026-aggregate.json](research/pilot-2026-aggregate.json).

## All 19 adjacent release pairs

`Removed / added` refers to stop IDs, **not** to changes in physical stop access.

| Baseline → candidate | Comparable overlap | Known before → after | Potential losses | Status changes | Removed / added |
| --- | ---: | ---: | ---: | ---: | ---: |
| `01.02.2026` → `01.02.2026-1.0.1` | not compared | — | — | — | — |
| `01.02.2026-1.0.1` → `01.02.2026-1.0.2` | 99.3% | 145 → 144 | 0 | 0 | 1 / 0 |
| `01.02.2026-1.0.2` → `1.02.2026-1.0.3` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `1.02.2026-1.0.3` → `1.02.2026-1.0.4` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `1.02.2026-1.0.4` → `1.02.2026-1.0.5` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `1.02.2026-1.0.5` → `1.02.2026-1.0.6` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `1.02.2026-1.0.6` → `03.01.2026-1.0.7` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `03.01.2026-1.0.7` → `03.01.2026-1.0.8` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `03.01.2026-1.0.8` → `04.01.2026-1.0.9A` | 99.3% | 144 → 144 | 0 | 0 | 0 / 1 |
| `04.01.2026-1.0.9A` → `20.04.2026_1.1.0` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `20.04.2026_1.1.0` → `13.05.2026_1.1.0` | 100.0% | 144 → 144 | 0 | 0 | 0 / 0 |
| `13.05.2026_1.1.0` → `13.05.2026_1.2.0` | 100.0% | 144 → 12 | 132 | 0 | 0 / 0 |
| `13.05.2026_1.2.0` → `13.05.2026_1.4.0` | 100.0% | 12 → 12 | 0 | 0 | 0 / 0 |
| `13.05.2026_1.4.0` → `115` | 100.0% | 12 → 12 | 0 | 0 | 0 / 0 |
| `115` → `13.05.2026_1.6.0` | 100.0% | 12 → 12 | 0 | 0 | 0 / 0 |
| `13.05.2026_1.6.0` → `01.09.2026_1.7.0` | 100.0% | 12 → 12 | 0 | 0 | 0 / 0 |
| `01.09.2026_1.7.0` → `v118_09_01_2026` | 100.0% | 12 → 93 | 0 | 2 | 0 / 0 |
| `v118_09_01_2026` → `v119_09_01_2026` | 100.0% | 93 → 93 | 0 | 0 | 0 / 0 |
| `v119_09_01_2026` → `v120_11_01_2026` | 99.3% | 93 → 93 | 0 | 0 | 0 / 1 |

## Publication provenance

Sources below identify the original publisher archives. **No source ZIPs have been republished here.** SHA-256 digests are for reproducing the analysis and detecting changes in retrieved assets.

| Publisher release tag | Published UTC | SHA-256 (original ZIP) | ZIP bytes | Parser result |
| --- | --- | --- | ---: | --- |
| [01.02.2026](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/01.02.2026/gtfs.zip) | 2026-01-01 | `5bc5bd9165e5791f016be166e11db87a2b5b9ed74603a3cb192293e13f172d14` | 36,824 | unusable |
| [01.02.2026-1.0.1](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/01.02.2026-1.0.1/gtfs.zip) | 2026-01-01 | `6a6526d2b832d928174f0c4df1cb9e45f778e9d9f0d6ebefeb5a9eb00b7bd979` | 31,310 | accepted |
| [01.02.2026-1.0.2](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/01.02.2026-1.0.2/gtfs.zip) | 2026-01-17 | `71062f26d099f9ded77da4ca34244ecfff31c026128a7f4a9a328b55f3dc9b0e` | 31,426 | accepted |
| [1.02.2026-1.0.3](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/1.02.2026-1.0.3/gtfs.zip) | 2026-02-13 | `99aec6d2819f23418f26eacb52f18b5b13c0ca605d547fcd862831ca397b3c43` | 194,730 | accepted |
| [1.02.2026-1.0.4](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/1.02.2026-1.0.4/gtfs.zip) | 2026-02-20 | `1ed52a31f5ff8b2dace3b4323565a7f047018ca6dca5ed6374126a50a9fa33f7` | 193,473 | accepted |
| [1.02.2026-1.0.5](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/1.02.2026-1.0.5/gtfs.zip) | 2026-02-20 | `0991700280f8b1d2fb4d435719537d36c45a4ae15b5a24b45980019bf84a036a` | 193,401 | accepted |
| [1.02.2026-1.0.6](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/1.02.2026-1.0.6/gtfs.zip) | 2026-02-26 | `954d66b7c665c1f5582ae74cbcbb0a40673a912649dc00058a88b259d9301d40` | 194,652 | accepted |
| [03.01.2026-1.0.7](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/03.01.2026-1.0.7/gtfs.zip) | 2026-02-27 | `dec5c89e7a22b2b0481ddffa22d5786e5852d7c6dbae0b59efd9e155a9a46a21` | 193,820 | accepted |
| [03.01.2026-1.0.8](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/03.01.2026-1.0.8/gtfs.zip) | 2026-03-04 | `28b3a589ff534f36a94e4226a1f95c296c49bbd92adcec1a35f61b3585598575` | 193,745 | accepted |
| [04.01.2026-1.0.9A](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/04.01.2026-1.0.9A/gtfs.zip) | 2026-03-30 | `152920df63d6691a791637975a8dfd0061152ab29481d21929d186a9f8265510` | 194,198 | accepted |
| [20.04.2026_1.1.0](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/20.04.2026_1.1.0/gtfs.zip) | 2026-04-18 | `9c2da81758321c1f6bb470776a3e1989aebca0334c234e6fc9a4d1c74a31efad` | 124,494 | accepted |
| [13.05.2026_1.1.0](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/13.05.2026_1.1.0/gtfs.zip) | 2026-05-14 | `1f14d2c7711534ae219c632f74c63950cb474236669b42042a844a3c3229c5e7` | 125,537 | accepted |
| [13.05.2026_1.2.0](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/13.05.2026_1.2.0/gtfs.zip) | 2026-06-04 | `809a5d3daad7bd7480fb3834538f817e495c979d724728bdcff67b4503ab87b6` | 195,856 | accepted |
| [13.05.2026_1.4.0](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/13.05.2026_1.4.0/gtfs.zip) | 2026-06-11 | `2fb495e3047f0d750c700314da7dd83826c713e1a189c6c4409229c1dd15c66d` | 196,235 | accepted |
| [115](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/115/gtfs.zip) | 2026-06-26 | `257eef311e5d560c2ef276b5021b3fdb5e0d3790827898fd1cf573278a89995a` | 196,940 | accepted |
| [13.05.2026_1.6.0](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/13.05.2026_1.6.0/gtfs.zip) | 2026-08-03 | `2e8392e808b461647b7d0e1cf90374e315d4fcb01a32701f94380d4b2918972c` | 197,025 | accepted |
| [01.09.2026_1.7.0](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/01.09.2026_1.7.0/gtfs.zip) | 2026-08-30 | `5af32af600f64cad784edd9cbfb684ba77032bf070d251e6f14e1372e51659aa` | 197,159 | accepted |
| [v118_09_01_2026](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/v118_09_01_2026/gtfs.zip) | 2026-09-03 | `2a2971d817c682592fd2df77ee30c8a992b093694220f9ad11f18fd1d0e7e9a9` | 196,871 | accepted |
| [v119_09_01_2026](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/v119_09_01_2026/gtfs.zip) | 2026-09-06 | `1bb2cd0364ccebf12bb873555d3e9a2f761f9eab571ff1c2654a63c74314fe1e` | 196,460 | accepted |
| [v120_11_01_2026](https://github.com/rozkladnik/gtfs-pwik-jaroslaw/releases/download/v120_11_01_2026/gtfs.zip) | 2026-10-22 | `bbe48b01a55319caaad84f9e08500c8def739475f706afb65f463c937144081c` | 202,799 | accepted |

## What is *not* yet established

- Whether the 132 changes were accidental loss, deliberate data correction, a change in source collection practice, or another reason.
- The independent validator evaluated the notable two releases and reported zero ERROR-level notices; additional historic releases and the tool's unrecognized system-errors schema still need study. See [verification](INDEPENDENT_VALIDATION_2026.md).
- Whether agency-maintainer workflows would benefit from this report, or how many review minutes it saves.
- Whether the same pattern occurs frequently in other independent transit feed publishers.

### Next research steps

1. The independent raw CSV comparison and official validator run have been completed for the notable pair; inspect the relevant `stops.txt` entries and source documentation with a human reviewer next.
2. Contact the unofficial publisher respectfully for context *before* making operational or safety claims.
3. Test releases from additional independent agencies with clearly verified redistribution/data-use terms. Track true/false-positive review outcomes and time-to-review.
