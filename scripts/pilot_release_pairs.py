"""Reproduce a bounded GTFS release-to-release pilot on explicitly licensed data.

Only the openly CC-BY-4.0-licensed releases enumerated below may be downloaded.
Run on a disposable CI runner; never commit downloaded feeds to this project.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.request
from datetime import date
from pathlib import Path

from gtfs_accessdiff.audit import compare_feeds, load_stops

SOURCE = "https://github.com/rozkladnik/gtfs-pwik-jaroslaw"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
ATTRIBUTION = "Jarosławska Komunikacja Miejska GTFS, published by rozkladnik (CC BY 4.0)"
RELEASES = (
    # In increasing GitHub release publication time (not tag lexical order).
    ("01.02.2026", "2026-01-01"),
    ("01.02.2026-1.0.1", "2026-01-01"),
    ("01.02.2026-1.0.2", "2026-01-17"),
    ("1.02.2026-1.0.3", "2026-02-13"),
    ("1.02.2026-1.0.4", "2026-02-20"),
    ("1.02.2026-1.0.5", "2026-02-20"),
    ("1.02.2026-1.0.6", "2026-02-26"),
    ("03.01.2026-1.0.7", "2026-02-27"),
    ("03.01.2026-1.0.8", "2026-03-04"),
    ("04.01.2026-1.0.9A", "2026-03-30"),
    ("20.04.2026_1.1.0", "2026-04-18"),
    ("13.05.2026_1.1.0", "2026-05-14"),
    ("13.05.2026_1.2.0", "2026-06-04"),
    ("13.05.2026_1.4.0", "2026-06-11"),
    ("115", "2026-06-26"),
    ("13.05.2026_1.6.0", "2026-08-03"),
    ("01.09.2026_1.7.0", "2026-08-30"),
    ("v118_09_01_2026", "2026-09-03"),
    ("v119_09_01_2026", "2026-09-06"),
    ("v120_11_01_2026", "2026-10-22"),
)
MAX_DOWNLOAD = 5 * 1024 * 1024


def release_url(tag: str) -> str:
    if tag not in {item[0] for item in RELEASES}:
        raise ValueError("Only allowlisted releases are accepted")
    return f"{SOURCE}/releases/download/{tag}/gtfs.zip"


def _download(tag: str, output: Path) -> dict[str, str | int]:
    url = release_url(tag)
    req = urllib.request.Request(url, headers={"User-Agent": "GTFS-AccessDiff-research-pilot/0.3"})
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(req, timeout=45) as response, output.open("wb") as dest:
        while True:
            data = response.read(1024 * 256)
            if not data:
                break
            size += len(data)
            if size > MAX_DOWNLOAD:
                raise ValueError(f"{tag}: download exceeds 5 MiB safety cap")
            digest.update(data)
            dest.write(data)
    load_stops(output)  # reject unsupported or corrupt stops.txt before any comparison
    return {"url": url, "sha256": digest.hexdigest(), "bytes": size}


def run(output_directory: Path) -> dict:
    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gtfs-accessdiff-pilot-") as scratch:
        root = Path(scratch)
        downloaded = {}
        release_metadata = []
        for tag, published in RELEASES:
            target = root / f"{len(release_metadata)}.zip"
            meta = _download(tag, target)
            downloaded[tag] = target
            release_metadata.append({"tag": tag, "published_at_utc": published, **meta})

        pairs = []
        for (baseline, _), (candidate, _) in zip(RELEASES, RELEASES[1:]):
            audit = compare_feeds(downloaded[baseline], downloaded[candidate])
            pairs.append({
                "baseline": baseline, "candidate": candidate,
                "status": audit.status,
                "baseline_records": audit.old_records,
                "candidate_records": audit.new_records,
                "matched_ids": audit.matched_records,
                "comparable_ids": audit.comparable_records,
                "comparable_overlap": round(audit.comparable_overlap, 6),
                "identity_concerns": len(audit.identity_concerns),
                "known_information_losses": audit.information_losses,
                "known_status_changes": audit.status_changes,
                "information_gains": audit.information_gains,
                "removed_ids": audit.removed_record_ids,
                "added_ids": audit.added_record_ids,
            })

    report = {
        "release_count": len(release_metadata),
        "pair_count": len(pairs),
        "source": SOURCE,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "method": "GTFS AccessDiff 0.3, stops.txt wheelchair_boarding comparison; no external conformance validator",
        "review_status": "Automated only; per-location changes have not been confirmed by a publisher",
        "note": "This study measures changes to published data, not physical wheelchair access.",
        "releases": release_metadata,
        "pairs": pairs,
    }
    (output_directory / "pilot-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Real-GTFS comparison pilot (automated observations)", "",
        f"**Attribution:** {ATTRIBUTION}. [License]({LICENSE}). [Source]({SOURCE}).", "",
        "The original feed ZIPs are downloaded into a temporary directory and not republished. This is an **unofficial**, independently compiled transit-data feed, not an official agency export.",
        "This pilot does **not** show whether actual accessibility changed; it has **not** received publisher review.", "",
        "| Baseline → candidate | Comparable ID overlap | Published metadata losses | Status changes | ID review flags | Removed / added IDs |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for pair in pairs:
        lines.append(
            f"| {pair['baseline']} → {pair['candidate']} | {pair['comparable_overlap']:.1%} | "
            f"{pair['known_information_losses']} | {pair['known_status_changes']} | "
            f"{pair['identity_concerns']} | {pair['removed_ids']} / {pair['added_ids']} |"
        )
    lines.extend(["", "## Release provenance", "", "| Tag | Publication (UTC) | SHA-256 | Bytes |", "| --- | --- | --- | ---: |"])
    for release in release_metadata:
        lines.append(f"| [{release['tag']}]({release['url']}) | {release['published_at_utc']} | `{release['sha256']}` | {release['bytes']} |")
    lines.extend(["", "**Remaining:** human-review each finding, run the independent official validator, and ask the publisher for feedback. Until then do not claim any regression reflects a real-world hazard.", ""])
    summary = "\n".join(lines)
    (output_directory / "pilot-summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)
    return report


if __name__ == "__main__":
    run(Path(os.environ.get("GTFS_PILOT_REPORT_DIR", "pilot-results")))
