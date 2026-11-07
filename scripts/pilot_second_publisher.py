"""Reproduce a bounded GTFS release-to-release pilot on explicitly licensed data.

Only pinned, CC BY 4.0-licensed Transport GZM releases may be downloaded.
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

from gtfs_accessdiff.audit import FeedError, compare_feeds, load_stops, resolved_statuses

SOURCE = "https://github.com/TransportGZM-GTFS-mirror/TransportGZM-GTFS-extended-ver"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
ATTRIBUTION = "Zarząd Transportu Metropolitalnego (ZTM / Transport GZM), mirrored on GitHub (CC BY 4.0)"
RELEASES = (
    ("31-08-2026", "2026-08-31"),
    ("30-10-2026", "2026-10-30"),
    ("31-10-2026", "2026-10-31"),
)
MAX_DOWNLOAD = 35 * 1024 * 1024
# Pinned release ZIP checksums and byte lengths from GitHub's release-asset metadata.
PINNED = {
    "31-08-2026": ("49ef8c18c4b1b7168ebc91b9e5b7dec3e7375cc2706b5ec65ff17076eb685322", 18974638),
    "30-10-2026": ("f9895139101cee064c594bb6d7f28ec3de0ffecbae5c64a71a238adb1e843f3a", 21947813),
    "31-10-2026": ("ed7d1de61d1505efef2415b7e9af05aa9f03863639610ed84c05026597d0cd68", 21901669),
}


def release_url(tag: str) -> str:
    if tag not in {item[0] for item in RELEASES}:
        raise ValueError("Only allowlisted releases are accepted")
    return f"{SOURCE}/releases/download/{tag}/TransportGZM-GTFS.zip"


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
                raise ValueError(f"{tag}: download exceeds 35 MiB safety cap")
            digest.update(data)
            dest.write(data)
    checksum = digest.hexdigest()
    expected_checksum, expected_size = PINNED[tag]
    if size != expected_size or checksum != expected_checksum:
        output.unlink(missing_ok=True)
        raise ValueError(f"{tag}: release ZIP differs from pinned SHA-256 or byte count")
    return {"url": url, "sha256": checksum, "bytes": size}


def run(output_directory: Path) -> dict:
    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gtfs-accessdiff-pilot-") as scratch:
        root = Path(scratch)
        downloaded: dict[str, Path] = {}
        release_metadata: list[dict] = []
        validation_errors: dict[str, str] = {}
        for tag, published in RELEASES:
            target = root / f"{len(release_metadata)}.zip"
            meta = _download(tag, target)
            downloaded[tag] = target
            try:
                # Reject release-specific parse defects before attempting any pairs.
                resolved_statuses(load_stops(target))
                meta["input_check"] = "accepted"
            except FeedError as error:
                meta["input_check"] = "unusable"
                meta["input_error"] = str(error)
                validation_errors[tag] = str(error)
            release_metadata.append({"tag": tag, "published_at_utc": published, **meta})

        pairs: list[dict] = []
        for (baseline, _), (candidate, _) in zip(RELEASES, RELEASES[1:]):
            result = {"baseline": baseline, "candidate": candidate}
            if baseline in validation_errors or candidate in validation_errors:
                pairs.append({**result,
                    "status": "input_unusable",
                    "unusable_tags": [tag for tag in (baseline, candidate) if tag in validation_errors],
                    "note": "No accessibility comparison attempted; input failed parsing. Consult original release and independent validator.",
                })
                continue
            try:
                audit = compare_feeds(downloaded[baseline], downloaded[candidate])
            except FeedError as error:
                pairs.append({**result, "status": "input_unusable", "unusable_tags": [baseline, candidate],
                              "note": f"Comparison validation failed: {error}"})
                continue
            pairs.append({**result,
                "status": audit.status,
                "baseline_records": audit.old_records,
                "candidate_records": audit.new_records,
                "matched_ids": audit.matched_records,
                "comparable_ids": audit.comparable_records,
                "comparable_overlap": round(audit.comparable_overlap, 6),
                "identity_concerns": len(audit.identity_concerns),
                "baseline_known_records": audit.old_known_records,
                "baseline_comparable_known_records": audit.baseline_comparable_known_records,
                "candidate_known_records": audit.new_known_records,
                "known_information_losses": audit.information_losses,
                "loss_sample": [
                    {"stop_id": f.stop_id, "old_value": f.old_value, "new_value": f.new_value,
                     "baseline_raw_value": f.baseline_raw_value,
                     "candidate_raw_value": f.candidate_raw_value,
                     "baseline_source_id": f.baseline_source_id}
                    for f in audit.findings if f.category == "information_loss"
                ][:5],
                "known_status_changes": audit.status_changes,
                "information_gains": audit.information_gains,
                "removed_ids": audit.removed_record_ids,
                "added_ids": audit.added_record_ids,
            })


    report = {
        "release_count": len(release_metadata),
        "pair_count": len(pairs),
        "usable_pair_count": sum(p["status"] != "input_unusable" for p in pairs),
        "evaluable_pair_count": sum(p.get("baseline_comparable_known_records", 0) > 0 for p in pairs),
        "no_known_baseline_pair_count": sum(p["status"] == "inconclusive_no_known_baseline" for p in pairs),
        "unusable_pair_count": sum(p["status"] == "input_unusable" for p in pairs),
        "source": SOURCE,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "method": "GTFS AccessDiff 0.4, stop_id-matched wheelchair_boarding comparison; independent second publisher; no external validator",
        "review_status": "Automated only; per-location changes have not been confirmed by a publisher",
        "note": "This study measures changes to published data, not physical wheelchair access.",
        "releases": release_metadata,
        "pairs": pairs,
    }
    (output_directory / "pilot-summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Transport GZM second-publisher pilot (automated observations)", "",
        f"**Attribution:** {ATTRIBUTION}. [License]({LICENSE}). [Source]({SOURCE}).", "",
        "The original feed ZIPs are downloaded into a temporary directory and not republished. This is a **GitHub mirror of published ZTM data**, not a separately verified agency archive.",
        "This pilot does **not** show whether actual accessibility changed; it has **not** received publisher review.", "",
        "| Baseline → candidate | Comparable overlap | Known status before / after | Potential metadata losses | Status changes | Identity review flags | Removed / added IDs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for pair in pairs:
        if pair["status"] == "input_unusable":
            lines.append(f"| {pair['baseline']} → {pair['candidate']} | input unusable | — | — | — | — | — |")
            continue
        lines.append(
            f"| {pair['baseline']} → {pair['candidate']} | {pair['comparable_overlap']:.1%} | "
            f"{pair['baseline_known_records']} / {pair['candidate_known_records']} | "
            f"{pair['known_information_losses']} | {pair['known_status_changes']} | "
            f"{pair['identity_concerns']} | {pair['removed_ids']} / {pair['added_ids']} |"
        )
    if report["no_known_baseline_pair_count"]:
        lines.extend(["", f"**Important coverage limitation:** {report['no_known_baseline_pair_count']} pair(s) had zero known baseline wheelchair status among comparable IDs. These are **inconclusive**, not evidence that accessibility metadata was preserved.", ""])
    lines.extend(["", "## Release provenance", "", "| Tag | Publication (UTC) | SHA-256 | Bytes | Parse result |", "| --- | --- | --- | ---: | --- |"])
    for release in release_metadata:
        lines.append(f"| [{release['tag']}]({release['url']}) | {release['published_at_utc']} | `{release['sha256']}` | {release['bytes']} | {release['input_check']} |")
    if validation_errors:
        lines.extend(["", "## Unusable release notes (require independent validation)", ""])
        for tag, error in sorted(validation_errors.items()):
            # Untrusted error text is rendered as plain code-ish text, not source HTML.
            safe_error = error.replace("|", "\\|").replace("`", "\\`").replace("\r", " ").replace("\n", " ")
            lines.append(f"- **{tag}:** {safe_error}")
    lines.extend(["", "**Remaining:** human-review each finding, run the independent official validator, and ask the publisher for feedback. Until then do not claim any regression reflects a real-world hazard.", ""])
    summary = "\n".join(lines)
    (output_directory / "pilot-summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(summary)
    if report["usable_pair_count"] == 0:
        raise RuntimeError("No usable GTFS release pairs; see generated summary for input errors")
    return report


if __name__ == "__main__":
    run(Path(os.environ.get("GTFS_GZM_REPORT_DIR", "pilot-results")))
