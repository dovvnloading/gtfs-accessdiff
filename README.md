# GTFS AccessDiff

**Detect lost accessibility information between public-transit data releases.**

A free, offline-first, deterministic Python CLI that compares two versions of a
[General Transit Feed Specification](https://gtfs.org/) (GTFS) feed and points
out where known wheelchair-accessibility metadata became unknown.

> **Status:** working v0.2 prototype. Not production-certified, not a live rider
> information service, and not a substitute for the canonical GTFS validator.

## Why this exists

Transit agencies periodically publish updated data feeds. A feed can be
syntactically valid while dropping information from earlier versions. Someone
who depends on a trip planner cannot tell whether a missing accessibility
value means a stop became inaccessible or merely lost its metadata.

Our initial question is deliberately narrow: **For the same published stop ID,
was a known `wheelchair_boarding` value replaced with an unknown value?**

GTFS distinguishes `1` (accessible boarding indicated), `2` (inaccessible
boarding indicated), and `0` or blank (unknown; children may inherit the parent
station's value). We resolve inheritance before comparing. We do not infer
real-world accessibility, and we don't reclassify a `1 → 2` change as information
*loss*: we flag it separately for human review.

## See it work (no dependencies)

Python 3.11+ and the standard library are enough to run from the source tree:

```bash
PYTHONPATH=src python -m gtfs_accessdiff samples/baseline.zip samples/candidate.zip
```

Or install the CLI after cloning:

```bash
python -m pip install -e .
gtfs-accessdiff samples/baseline.zip samples/candidate.zip
```

The sample uses **invented stops**, not real agency data. Example summary:

```text
Result: information_losses_found
Stop IDs matched: 5 of 6 (83.3%)
Known information lost: 2
Known status changed: 1
Information gains: 1
```

Produce a machine-readable JSON or Markdown report:

```bash
gtfs-accessdiff samples/baseline.zip samples/candidate.zip \
  --format json --output report.json

gtfs-accessdiff samples/baseline.zip samples/candidate.zip \
  --format markdown --output report.md
```

Only **opt into CI failure after reviewing your feed's ID stability**:

```bash
gtfs-accessdiff previous.zip pending.zip --fail-on-loss
```

Exit codes: `0` normal (including findings without opt-in gating); `1` invalid
input; `2` known accessibility metadata loss with `--fail-on-loss`; `3`
inconclusive ID matching with `--fail-on-loss`. The ID-overlap threshold defaults
to 75% of the larger feed's stop count (`--min-overlap 0.75`).

## What v0.2 detects

- Explicit `1` or `2` becoming `0` or blank for an unchanged `stop_id`.
- Effective accessibility status becoming unknown because parent-station data
  disappeared, even if the child still has `wheelchair_boarding=0`.
- Known accessibility statuses changing `1 ↔ 2`, clearly marked for **review**.
- Counts of added/removed IDs, unknown-to-known gains, and overall matching
  coverage; low-overlap comparisons are explicitly inconclusive.
- Deterministic Markdown and JSON reports, with no uploaded data, API key,
  account, model call, server, or external dependency.

## What it does **not** detect (yet)

- Trip-level wheelchair access (`trips.txt`) or accessible paths (`pathways.txt`).
- Missing or changed `tts_stop_name` text-to-speech metadata.
- Live elevator outages, physical accessibility, actual vehicle availability,
  or whether an agency's facts are correct in the real world.
- Stops whose IDs were changed between feeds: these are counted as removed/added
  rather than called accessibility regressions.
- Nested GTFS archives; supply a feed ZIP with `stops.txt` at its root, or an
  unpacked GTFS directory.

A report saying **no information loss detected** does not prove accessibility or
GTFS compliance. Always use the [MobilityData GTFS validator](https://github.com/MobilityData/gtfs-validator)
for conformance and use human validation for agency-specific facts.

## How the comparison works

1. Read `stops.txt` from both local feed ZIPs or directories without extracting
   arbitrary ZIP members or making network requests.
2. Check unique stop identifiers, allowed wheelchair data values, and parent
   references. Resolve `0`/blank child values by following `parent_station`.
3. Compare records with the same `stop_id` only.
4. Classify `known → unknown` as information loss; `1 ↔ 2` as a review-needed
   metadata change; `unknown → known` as an improvement.
5. Mark a comparison inconclusive if shared IDs represent less than the configured share of the **larger** feed. A shrinking feed cannot appear fully matched merely because its remaining IDs are unchanged. Emit stable JSON or
   Markdown with evidence tied to stop IDs.

## Tests and contribution guide

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

See [CONTRIBUTING.md](CONTRIBUTING.md), the [research and competitor review](docs/RESEARCH.md),
and the [incremental GitHub backlog](docs/ROADMAP.md), and the [real-world pilot protocol](docs/PILOT.md), and the [GitHub publishing guide](docs/PUBLISH.md).

We intend to complement, not replace, existing open-source GTFS tools such as:
[MobilityData's validator](https://github.com/MobilityData/gtfs-validator),
[BlinkTag's accessibility validator](https://github.com/BlinkTagInc/gtfs-accessibility-validator),
and the [GTFS Diff specification](https://github.com/MobilityData/gtfs-diff).

**License:** MIT. Synthetic examples are freely usable under the repository's
license; real GTFS data must be handled under each publisher's terms.

**Project status:** See the [GitHub issues](https://github.com/dovvnloading/gtfs-accessdiff/issues) for scoped tasks. No live transit-feed audit has yet been verified.
