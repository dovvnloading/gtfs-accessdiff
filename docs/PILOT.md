# Licensed real-feed pilot: reproducible protocol

**Status: 2026 historical pilot and independent GTFS validation of the notable release pair completed in GitHub Actions; human/publisher feedback outstanding.** An automated difference is evidence about *published data*, not physical accessibility or a user impact.

## Goal

Establish whether accessibility metadata regressions can be usefully detected between successive published releases, how stable the feed's stop identifiers are, and how much manual review they require. We do **not** optimize for the raw number of warnings or claim that a loss flag is necessarily a publisher error.

## First test source: explicit CC BY 4.0 license

**Attribution:** [Jarosławska Komunikacja Miejska GTFS](https://github.com/rozkladnik/gtfs-pwik-jaroslaw), independently compiled and published by `rozkladnik` (**unofficial; not affiliated with the transit operator**); [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). The feed repository explicitly states its license and that its stops have wheelchair-accessibility information. It also warns some stop coordinates are approximate. That is why coordinate changes are *review signals*, never proof of different stop identity.

The bounded [pilot script](../scripts/pilot_release_pairs.py) uses **all 20 versioned GitHub release assets from 2026** identified on November 6, ordered by their publication time. It compares **19 adjacent release pairs** (one unofficial feed, *not* 19 independent agencies). The release tags and exact publication-date metadata are enumerated in the script, which also records downloaded ZIP SHA-256 hashes, counts, stop-ID overlaps, changed-status counts, and identity review flags.

The script downloads each asset into a temporary directory (5 MiB download cap), checks root-level `stops.txt`, and publishes only aggregate JSON/Markdown outputs as CI artifacts. It marks invalid input as unusable instead of reporting a clean comparison; the workflow fails if no pairs are usable. **No publisher ZIP is committed or uploaded as an artifact.**

**Automated outcome:** [the published 2026 results](PILOT_RESULTS_2026.md) include 18 comparable adjacent pairs out of 19, one malformed early release, and a notable set of **132 candidate metadata losses within one release pair**. An [independent raw-field cross-check and official GTFS validator run](INDEPENDENT_VALIDATION_2026.md) replicated all 132 raw changes, but the publisher intent and impact remain unknown. A versioned [aggregate JSON record](research/pilot-2026-aggregate.json) preserves the release hashes and bounded review samples.

To reproduce in an environment that can download GitHub release assets:

```bash
PYTHONPATH=src python scripts/pilot_release_pairs.py
```

Or run the [Licensed real-feed pilot workflow](../.github/workflows/pilot.yml) manually from the GitHub Actions UI. It has `contents: read` permissions and no secrets.

**The historical 20-release sweep is not a GTFS conformance check.** The [separate validator cross-check](INDEPENDENT_VALIDATION_2026.md) covers the most notable *two* releases only, not all 20 archives.

## Human review needed before closing [issue #1](https://github.com/dovvnloading/gtfs-accessdiff/issues/1)

1. Verify hashes, `stops.txt` column values and release provenance. Inspect any found metadata loss in both feeds and any original source station with inherited information.
2. Distinguish missing published metadata from intentional data cleanup, location-ID reuse, and real operational changes. Review removed/added ID samples; do not pair by name alone.
3. [Completed for the 132-flag pair](INDEPENDENT_VALIDATION_2026.md): run the [MobilityData GTFS validator](https://github.com/MobilityData/gtfs-validator) and record notices separately. Other releases still need independent validation as appropriate.
4. Record manual-review time and false positives. If possible, ask the publisher whether the report would be actionable in their workflow.
5. Publish only attribution-compliant aggregates and reviewed excerpts. Never describe a stop as physically inaccessible based only on a GTFS diff.

### Manual review log

| Release pair | Comparable ID coverage | Automated loss flags | Human-confirmed loss | False positive / uncertain | Reviewer time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `13.05.2026_1.1.0` → `13.05.2026_1.2.0` | 100% | 132 | Not yet reviewed | Unknown | Not yet measured |
| `01.02.2026` → `01.02.2026-1.0.1` | Unusable input | Not compared | Not reviewed | Not applicable | Not yet measured |

## Additional potential source (not automatically downloaded)

[SEPTA publishes historical feeds on GitHub](https://github.com/septadev/GTFS/releases), but [its developer page requires agreement to its separate data-use license](https://www3.septa.org/developer/). The pilot deliberately does not download those archives by default. Similarly, [Pittsburgh Regional Transit's historical feeds](https://data.wprdc.org/en/dataset/gtfs-archive) have their own portal and terms. Check terms before adding either feed.

## Publication policy

This project keeps **source ZIPs out of the repository**, stores only version identifiers, URLs, SHA-256 hashes and aggregated findings, attributes CC BY 4.0 data, and does not publish unreviewed physical-accessibility or user-impact claims. Findings require a human review before any outreach to an agency or safety claim.
