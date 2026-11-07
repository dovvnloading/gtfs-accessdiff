# GTFS AccessDiff

[![Tests](https://github.com/dovvnloading/gtfs-accessdiff/actions/workflows/tests.yml/badge.svg)](https://github.com/dovvnloading/gtfs-accessdiff/actions/workflows/tests.yml)

**Review lost wheelchair-accessibility information between published GTFS feed releases.**

GTFS AccessDiff is a free, offline-first Python CLI **and optional composite GitHub Action**. It compares two local GTFS ZIPs (or extracted directories) and finds known `stops.txt.wheelchair_boarding` information that became unknown. Parent-station inheritance is resolved and explained. It has no paid APIs, external runtime dependencies, accounts or telemetry.

> **Status:** v0.3 research prototype. Not a safety certification, GTFS conformance validator, or live rider information service. A change in the *data* never proves a physical access change.

## Quick start

Use Python 3.11 or newer. No installation is needed from the repository root:

```bash
PYTHONPATH=src python -m gtfs_accessdiff samples/baseline.zip samples/candidate.zip
PYTHONPATH=src python -m unittest discover -s tests -v
```

To install a normal command:

```bash
python -m pip install -e .
gtfs-accessdiff samples/baseline.zip samples/candidate.zip --format markdown
```

Create JSON and Markdown reports for human review:

```bash
gtfs-accessdiff previous.zip pending.zip --format json --output report.json
gtfs-accessdiff previous.zip pending.zip --format markdown --output report.md
```

For a preview, both ZIPs must have `stops.txt` at the root. If feeds come as nested archives, choose the *same* mode and extract its GTFS ZIP in both versions first.

### What the reports mean

| Result | Interpretation |
| --- | --- |
| `information_losses_found` | One or more **comparable** stop IDs changed from known `1`/`2` to unknown. |
| `identity_review_required` | At least one shared ID has a suspicious identity change; no comparable information losses were found. |
| `inconclusive_low_id_overlap` | Too few records were safely comparable to trust a negative result. |
| `no_information_losses_detected` | No metadata losses among comparable IDs **within this tool's narrow scope**. |

We **never** call a `1 → 2` change an information loss. Such changes are reported separately as `status_change`, because a correction or operational change may explain them. `0`/empty indicates unknown for parentless stops and inherits an explicit parent value for appropriate child locations, per the [GTFS Schedule specification](https://gtfs.org/documentation/schedule/reference/).

To reduce unsupported matches, IDs with changed `location_type`, or a coordinate movement greater than 500 meters by default, are *quarantined for identity review*. A child inheriting information from a suspicious source station is also quarantined. **We do not automatically match new/removed IDs by name or position.** The default comparison requires at least 75% safely comparable IDs relative to the larger feed; use `--min-overlap` to configure it.

## Using the GitHub Action

Projects already managing two GTFS archives can add our no-network composite action to their own GitHub Actions workflow. It reads only specified local paths, emits both JSON and Markdown, and uses no GitHub token. The **caller** decides if and when to upload reports.

```yaml
name: GTFS accessibility review
on: [workflow_dispatch]
permissions:
  contents: read
jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: dovvnloading/gtfs-accessdiff@main # Pin a reviewed commit SHA for production use
        with:
          baseline: feeds/approved.zip
          candidate: feeds/proposed.zip
          fail-on-loss: 'false' # Review the feed's ID stability before enabling
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: gtfs-accessibility-review
          path: gtfs-accessdiff-reports/
```

See [the complete workflow example](examples/github-action.yml). The action **does not** download provider feeds, execute data as code, open PR comments, or need write permissions. Avoid using `pull_request_target` for untrusted feed changes.

### Opt-in CI gate

After validating your feed's stop-ID stability, add `--fail-on-loss` to the CLI, or set `fail-on-loss: 'true'` in the Action. The reports are generated *before* optional gating. Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | Report generated; no blocking condition, or gating not enabled. |
| `1` | Invalid/unreadable input or output failure. |
| `2` | Comparable metadata loss, with opt-in gate. |
| `3` | ID overlap inconclusive or identity review required, with opt-in gate. |

`--max-findings 200` caps individual accessibility and identity findings displayed in JSON/Markdown, **not** aggregate counts. Bounded samples of up to 25 removed and added IDs appear separately. Reports include `findings_total`, `findings_omitted`, source station IDs for inherited values, and groups of children affected by a common source.

Additional CLI settings:

```bash
gtfs-accessdiff previous.zip pending.zip \
  --identity-distance-meters 500 \
  --min-overlap 0.75 \
  --max-findings 200 \
  --format json --output report.json
```

## Comparison design and limitations

1. Parse `stops.txt` from both input feeds (bounded to 64 MiB per member) without extracting ZIP files or using the network.
2. Reject duplicate IDs/columns, malformed CSV and inconsistent parent references. Resolve explicit and inherited wheelchair values with the source stop ID.
3. Compare shared stop IDs **only**. Quarantine changed location types, large coordinate moves and their inherited dependents for human identity review. Missing/malformed coordinates are not used to infer identity.
4. Classify known → unknown as metadata loss, known ↔ known as status change, and unknown → known as information gain. Report removed/added IDs separately, without fuzzy pairing.
5. Export deterministic, versioned JSON (`schema_version: 0.3.0`) or sanitized Markdown with exact aggregate counts. Low comparable overlap is inconclusive.

This release does **not** compare trip-level wheelchair access, pathway connectivity, text-to-speech fields, live elevator information, stop identities after an ID change, or real-world physical accessibility. Location-name changes alone do not prove a change of identity. All safety-relevant conclusions require human review and the canonical [MobilityData GTFS validator](https://github.com/MobilityData/gtfs-validator) for independent standards conformance.

## Research and open-source development

- [Research and competitor analysis](docs/RESEARCH.md)
- [Reproducible real-feed pilot protocol](docs/PILOT.md)
- [Project roadmap](docs/ROADMAP.md)
- [Issue tracker](https://github.com/dovvnloading/gtfs-accessdiff/issues)
- [Contribution guide](CONTRIBUTING.md) and [security policy](SECURITY.md)

Synthetic sample GTFS ZIPs and example outputs are included for tests only. **Never redistribute another agency's archives here without confirming that the license permits it.** The project's code and synthetic samples are MIT licensed. Publisher data carries its own terms.

We intend to complement—not replace—the [MobilityData validator](https://github.com/MobilityData/gtfs-validator), [GTFS Diff](https://github.com/MobilityData/gtfs-diff), and existing accessibility checks.
