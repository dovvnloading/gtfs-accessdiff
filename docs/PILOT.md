# Licensed real-feed pilot: reproducible protocol

**Status: automated pilot runnable on GitHub Actions; manual verification and upstream feedback outstanding.** An automated difference is evidence about *published data*, not physical accessibility or a user impact.

## Goal

Establish whether accessibility metadata regressions can be usefully detected between successive published releases, how stable the feed's stop identifiers are, and how much manual review they require. We do **not** optimize for the raw number of warnings or claim that a loss flag is necessarily a publisher error.

## First test source: explicit CC BY 4.0 license

**Attribution:** [Jarosławska Komunikacja Miejska GTFS](https://github.com/rozkladnik/gtfs-pwik-jaroslaw), published by `rozkladnik`; [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). The feed repository explicitly states its license and that its stops have wheelchair-accessibility information. It also warns some stop coordinates are approximate. That is why coordinate changes are *review signals*, never proof of different stop identity.

The bounded [pilot script](../scripts/pilot_release_pairs.py) uses only these four explicitly enumerated GitHub release assets, ordered by publication date:

- `115` — June 26, 2026
- `13.05.2026_1.6.0` — August 3, 2026
- `v119_09_01_2026` — September 6, 2026
- `v120_11_01_2026` — October 22, 2026

The workflow compares **three adjacent publication pairs**. Actual publication order—not lexicographical tags or presumptive service-date order—is the only basis for pairing. It records release URLs, downloaded SHA-256 hashes, source sizes, exact counts, ID review flags and overlap. The script downloads feeds into a temporary directory (5 MiB download cap per asset), checks `stops.txt`, and publishes only an aggregate JSON/Markdown report. No provider ZIP is committed or uploaded as a CI artifact.

To reproduce in an environment that can download GitHub release assets:

```bash
PYTHONPATH=src python scripts/pilot_release_pairs.py
```

Or run the [Licensed real-feed pilot workflow](../.github/workflows/pilot.yml) manually from the GitHub Actions UI. It has `contents: read` permissions and no secrets.

**This first automated pass is not the canonical MobilityData validator**; running that tool independently remains an acceptance criterion.

## Human review needed before closing [issue #1](https://github.com/dovvnloading/gtfs-accessdiff/issues/1)

1. Verify hashes, `stops.txt` column values and release provenance. Inspect any found metadata loss in both feeds and any original source station with inherited information.
2. Distinguish missing published metadata from intentional data cleanup, location-ID reuse, and real operational changes. Review removed/added ID samples; do not pair by name alone.
3. Run the [MobilityData GTFS validator](https://github.com/MobilityData/gtfs-validator) independently for each selected archive, recording warnings separately.
4. Record manual-review time and false positives. If possible, ask the publisher whether the report would be actionable in their workflow.
5. Publish only attribution-compliant aggregates and reviewed excerpts. Never describe a stop as physically inaccessible based only on a GTFS diff.

### Manual review log

| Release pair | Comparable ID coverage | Automated loss flags | Human-confirmed loss | False positive / uncertain | Reviewer time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pending validated pilot | — | — | Pending | Pending | — |

## Additional potential source (not automatically downloaded)

[SEPTA publishes historical feeds on GitHub](https://github.com/septadev/GTFS/releases), but [its developer page requires agreement to its separate data-use license](https://www3.septa.org/developer/). The pilot deliberately does not download those archives by default. Similarly, [Pittsburgh Regional Transit's historical feeds](https://data.wprdc.org/en/dataset/gtfs-archive) have their own portal and terms. Check terms before adding either feed.

## Publication policy

This project keeps **source ZIPs out of the repository**, stores only version identifiers, URLs, SHA-256 hashes and aggregated findings, attributes CC BY 4.0 data, and does not publish unreviewed physical-accessibility or user-impact claims. Findings require a human review before any outreach to an agency or safety claim.
