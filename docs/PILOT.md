# Real-feed pilot: reproducible protocol

**Status: planned, not yet executed.** Do not treat synthetic fixture results as
real-world impact evidence.

## Goal and acceptance criteria

We want three independent pairs of *dated*, published GTFS feeds. A useful
pilot should establish (a) whether feed identifiers are sufficiently stable,
(b) whether the checker correctly detects known-to-unknown data changes,
(c) how many flags appear to be legitimate or misleading after manual review,
and (d) whether a publisher would use the report in their release workflow.

Our primary outcomes are **not** the raw number of warnings. Review time,
explanations of true changes, and false positives are equally important.

## Candidate sources

1. [SEPTA versioned releases](https://github.com/septadev/GTFS/releases):
   possible pairs include `v202608232` → `v202608233` and `v202609060` →
   `v202609061`. SEPTA publishes the feed as a release asset named
   `gtfs_public.zip`, which may contain nested mode-specific GTFS archives.
   Inspect the archive and select the same mode in both releases. Check
   [SEPTA developer terms](https://www3.septa.org/developer/) before using or
   distributing source data. Release notes describe their schedule changes;
   they do **not** establish any accessibility regression on their own.
2. [PRT historical GTFS archive](https://data.wprdc.org/en/dataset/gtfs-archive):
   a possible source, **not pre-authorized for automated downloads**. The WPRDC
   site displays a data-use agreement that must be accepted to access/use the
   portal. Follow its conditions and the dataset's license before retrieving
   data; never bundle downloaded data in this repository without permission.
3. Another agency feed with two archived dated releases and clear data terms.
   Document exact URL, release ID/date, and license.

## Local procedure

1. Record publishing agency, publication dates, source URLs, data terms and
   locally computed SHA-256 hashes. Keep original archive files outside the
   source repository.
2. Confirm each version has a root-level `stops.txt`. If the downloaded asset
   contains `google_bus.zip`/`google_rail.zip` or other nested feeds, extract
   just the intended member to its own GTFS ZIP first. Do not mix modes.
3. Run the official [MobilityData GTFS validator](https://github.com/MobilityData/gtfs-validator)
   separately, noting any conformance warnings. Our tool is a **diff**, not a
   schema validator.
4. Run the comparison with blocking **disabled** initially:

   ```bash
   gtfs-accessdiff baseline.zip candidate.zip --format json --output pilot-report.json
   gtfs-accessdiff baseline.zip candidate.zip --format markdown --output pilot-report.md
   ```

5. Record `old_records`, `new_records`, `matched_records`, `overlap`,
   `information_losses`, `status_changes`, `information_gains`, `status` and
   reviewer notes. If overlap is inconclusive, do not interpret a small loss
   count as evidence of good quality.
6. For each reported stop, inspect the source rows and, where relevant, the
   former and current parent stations. Assign `confirmed metadata loss`,
   `legitimate correction`, `changed stop identity`, `uncertain`, or `tool
   defect`. Confirmed *metadata* loss is not a claim of physical inaccessibility.
7. Ask a feed publisher whether the output would have changed their release
   process. Record their feedback without including personal information.

## Minimal review log

| Source/release pair | Stop-ID overlap | Loss flags | Manually confirmed | False-positive / uncertain | Reviewer time | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Not yet run | — | — | — | — | — | Pending licensed source retrieval |

## Publication policy

Publish only source links, version identifiers, SHA-256 hashes, aggregate counts
and human-reviewed excerpts allowed by the source license. Do not redistribute
agency GTFS ZIPs in fixtures, issues, or GitHub Actions artifacts without
checking the license and terms. Do not post an identified accessibility defect
as a real-world hazard before confirming with the feed publisher.
