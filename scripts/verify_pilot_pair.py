"""Independent cross-check of the 2026 wheelchair metadata discontinuity.

Uses only pinned, publicly licensed GTFS ZIPs and MobilityData's pinned CLI.
Outputs small *summaries*, not raw agency feeds or complete validation reports.
Run only as a deliberate research workflow (not part of normal project CI).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import subprocess
import tempfile
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

SOURCE = "https://github.com/rozkladnik/gtfs-pwik-jaroslaw"
ATTRIBUTION = "Jarosławska Komunikacja Miejska GTFS, independently published by rozkladnik (CC BY 4.0)"
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
INPUTS = (
    ("baseline", "13.05.2026_1.1.0", "1f14d2c7711534ae219c632f74c63950cb474236669b42042a844a3c3229c5e7", "2026-05-14"),
    ("candidate", "13.05.2026_1.2.0", "809a5d3daad7bd7480fb3834538f817e495c979d724728bdcff67b4503ab87b6", "2026-06-04"),
)
VALIDATOR_VERSION = "8.0.1"
VALIDATOR_NAME = "gtfs-validator-8.0.1-cli.jar"
VALIDATOR_SHA256 = "19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2"
VALIDATOR_URL = f"https://github.com/MobilityData/gtfs-validator/releases/download/v{VALIDATOR_VERSION}/{VALIDATOR_NAME}"


def fetch_pinned(url: str, expected_sha256: str, destination: Path, *, max_bytes: int) -> int:
    """Download to a temporary file, verify both a size cap and SHA, then promote."""
    request = urllib.request.Request(url, headers={"User-Agent": "gtfs-accessdiff-independent-verification/0.3"})
    temp = destination.with_name(destination.name + ".download")
    total = 0
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temp.open("wb") as handle:
            while data := response.read(256 * 1024):
                total += len(data)
                if total > max_bytes:
                    raise ValueError(f"Download exceeded {max_bytes} bytes: {url}")
                digest.update(data)
                handle.write(data)
        actual_sha = digest.hexdigest()
        if actual_sha != expected_sha256:
            raise ValueError(f"SHA-256 mismatch for {url}: {actual_sha}")
        temp.replace(destination)
        return total
    finally:
        temp.unlink(missing_ok=True)


def _stops(path: Path) -> dict[str, dict[str, str]]:
    """Independently parse raw CSV columns (no use of gtfs_accessdiff)."""
    with zipfile.ZipFile(path) as archive:
        members = [member for member in archive.infolist() if member.filename == "stops.txt"]
        if len(members) != 1 or members[0].file_size > 64 * 1024 * 1024:
            raise ValueError("Expected exactly one bounded, root-level stops.txt")
        with archive.open(members[0]) as handle:
            source = handle.read(64 * 1024 * 1024 + 1)
    if len(source) > 64 * 1024 * 1024:
        raise ValueError("stops.txt exceeds size cap")
    reader = csv.DictReader(io.StringIO(source.decode("utf-8-sig"), newline=""), strict=True)
    if not reader.fieldnames or "stop_id" not in reader.fieldnames:
        raise ValueError("Missing stop_id column")
    records = {}
    for row in reader:
        if None in row or not row.get("stop_id") or row["stop_id"] in records:
            raise ValueError("Extra columns, duplicate IDs or missing stop IDs")
        records[row["stop_id"]] = {key: value or "" for key, value in row.items()}
    if not records:
        raise ValueError("Empty feed")
    return records


def independent_raw_diff(baseline: Path, candidate: Path, *, sample_size: int = 12) -> dict:
    """Count *literal* field changes; does not resolve parents or infer intent."""
    before, after = _stops(baseline), _stops(candidate)
    common = sorted(before.keys() & after.keys())
    transitions: Counter[tuple[str, str]] = Counter()
    direct_known_to_blank = []
    for stop_id in common:
        old = before[stop_id]
        new = after[stop_id]
        a, b = old.get("wheelchair_boarding", "").strip(), new.get("wheelchair_boarding", "").strip()
        transitions[(a or "blank", b or "blank")] += 1
        if a in ("1", "2") and b in ("", "0"):
            direct_known_to_blank.append({
                "stop_id": stop_id,
                "baseline_raw": a,
                "candidate_raw": b or "blank",
                "name_exact_match": old.get("stop_name") == new.get("stop_name"),
                "coordinates_exact_match": (old.get("stop_lat"), old.get("stop_lon")) == (new.get("stop_lat"), new.get("stop_lon")),
                "parent_exact_match": old.get("parent_station") == new.get("parent_station"),
            })
    return {
        "baseline_stop_records": len(before),
        "candidate_stop_records": len(after),
        "shared_ids": len(common),
        "added_ids": len(after.keys() - before.keys()),
        "removed_ids": len(before.keys() - after.keys()),
        "raw_transitions": [
            {"baseline": a, "candidate": b, "count": count}
            for (a, b), count in sorted(transitions.items())
        ],
        "raw_known_to_unknown_count": len(direct_known_to_blank),
        "raw_known_to_unknown_exact_name_count": sum(x["name_exact_match"] for x in direct_known_to_blank),
        "raw_known_to_unknown_exact_coord_count": sum(x["coordinates_exact_match"] for x in direct_known_to_blank),
        "raw_known_to_unknown_exact_parent_count": sum(x["parent_exact_match"] for x in direct_known_to_blank),
        "review_sample": direct_known_to_blank[:sample_size],
        "limitations": "Raw field check; does not resolve parent accessibility, verify real stop identity, or establish physical accessibility.",
    }


def summarize_validator_report(report_path: Path, system_path: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or not isinstance(report.get("notices"), list):
        raise ValueError("Unexpected official validator JSON schema: missing notices array")
    by_severity = Counter()
    codes = []
    for notice in report["notices"]:
        if not isinstance(notice, dict):
            raise ValueError("Invalid validator notice entry")
        code, severity, count = notice.get("code"), notice.get("severity"), notice.get("totalNotices")
        if not isinstance(code, str) or not isinstance(severity, str) or type(count) is not int or count < 0:
            raise ValueError("Unexpected validator notice shape")
        by_severity[severity] += count
        codes.append({"code": code, "severity": severity, "count": count})
    errors = None
    system_schema = "missing"
    system_keys = []
    if system_path.exists():
        system = json.loads(system_path.read_text(encoding="utf-8"))
        system_schema = type(system).__name__
        if isinstance(system, list):
            errors = len(system)
        elif isinstance(system, dict):
            system_keys = sorted(system.keys())[:20]
            for key in ("systemErrors", "errors", "notices"):
                if isinstance(system.get(key), list):
                    records = system[key]
                    errors = sum(item.get("totalNotices", 1) if isinstance(item, dict) and
                                 type(item.get("totalNotices", 1)) is int else 1 for item in records)
                    break
    return {
        "validator_version": report.get("summary", {}).get("validatorVersion") if isinstance(report.get("summary"), dict) else None,
        "notice_count_by_severity": dict(sorted(by_severity.items())),
        "notice_types": sorted(codes, key=lambda x: (-x["count"], x["severity"], x["code"]))[:25],
        "system_errors_count": errors,
        "system_errors_schema": system_schema,
        "system_errors_keys": system_keys,
        "system_errors_interpretation": "null means no recognized error array was exposed, not that the validator proved zero errors",
        "interpretation": "Independent GTFS compliance notices; they do not confirm cause, intent or physical effect of the metadata changes.",
    }


def verify(output_directory: Path) -> dict:
    output_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gtfs-independent-validator-") as directory:
        root = Path(directory)
        metadata = {}
        feeds = {}
        for label, tag, sha, date in INPUTS:
            target = root / (label + ".zip")
            url = f"{SOURCE}/releases/download/{tag}/gtfs.zip"
            size = fetch_pinned(url, sha, target, max_bytes=5 * 1024 * 1024)
            feeds[label] = target
            metadata[label] = {"source_release": tag, "published": date, "sha256": sha, "bytes": size, "url": url}
        raw = independent_raw_diff(feeds["baseline"], feeds["candidate"])
        jar = root / VALIDATOR_NAME
        fetch_pinned(VALIDATOR_URL, VALIDATOR_SHA256, jar, max_bytes=50 * 1024 * 1024)
        validations = {}
        for label, _, _, date in INPUTS:
            output = root / (label + "-validator")
            command = ["java", "-Xmx2g", "-jar", str(jar), "-i", str(feeds[label]), "-o", str(output), "-d", date, "-svu"]
            proc = subprocess.run(command, capture_output=True, text=True, timeout=240, check=False)
            if not (output / "report.json").exists():
                raise RuntimeError(f"Official validator failed for {label}, exit={proc.returncode}, stderr={proc.stderr[-1500:]}")
            validations[label] = summarize_validator_report(output / "report.json", output / "system_errors.json")
            validations[label]["process_exit_code"] = proc.returncode
            validations[label]["evaluation_date"] = date
        result = {
            "purpose": "Independent raw-field cross-check and third-party GTFS specification validation",
            "attribution": ATTRIBUTION, "source": SOURCE, "license": LICENSE,
            "official_validator": {"repository": "https://github.com/MobilityData/gtfs-validator", "version": VALIDATOR_VERSION,
                                   "jar_url": VALIDATOR_URL, "jar_sha256": VALIDATOR_SHA256},
            "release_provenance": metadata, "raw_comparison": raw, "validator_reports": validations,
            "review_status": "Automated research only; not reviewed with publisher and not a safety assessment",
            "no_archive_redistribution": True,
        }
        (output_directory / "independent-verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        lines = ["# Independent validation of the 2026 GTFS metadata discontinuity", "",
                 f"Publisher attribution: {ATTRIBUTION}. [Source]({SOURCE}) · [CC BY 4.0]({LICENSE}).", "",
                 f"MobilityData official GTFS Validator **v{VALIDATOR_VERSION}** (SHA-256 pinned) was run on both original GTFS archives; no source archives were republished.", "",
                 "**Caution:** validator conformance notices and raw field changes serve different purposes. Neither proves actual wheelchair access or publisher mistakes.", "",
                 "## Independent raw CSV comparison", "",
                 f"Shared stop IDs: **{raw['shared_ids']}**. Direct known → blank/0: **{raw['raw_known_to_unknown_count']}**.", "",
                 "| Raw before | Raw after | Stops |", "| --- | --- | ---: |"]
        for transition in raw["raw_transitions"]:
            lines.append(f"| `{transition['baseline']}` | `{transition['candidate']}` | {transition['count']} |")
        lines.extend(["", "## Independent validator notice counts", "", "| Source release | ERROR | WARNING | INFO | System errors |", "| --- | ---: | ---: | ---: | --- |"])
        for label, tag, _, _ in INPUTS:
            counts = validations[label]["notice_count_by_severity"]
            errs = validations[label]["system_errors_count"]
            lines.append(f"| `{tag}` | {counts.get('ERROR', 0)} | {counts.get('WARNING', 0)} | {counts.get('INFO', 0)} | {errs if errs is not None else 'uninterpreted'} |")
        lines.extend(["", "## Remaining work", "", "Inspect notice types and sample records, seek independent human/publisher review, and compare more unrelated transit feeds. This is a bounded, automated cross-check only.", ""])
        md = "\n".join(lines)
        (output_directory / "independent-verification.md").write_text(md, encoding="utf-8")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as writer:
                writer.write(md)
        return result


if __name__ == "__main__":
    output = Path(os.environ.get("GTFS_INDEPENDENT_REPORT_DIR", "independent-validation-results"))
    report = verify(output)
    print(f"Verified {report['raw_comparison']['shared_ids']} shared IDs; "
          f"{report['raw_comparison']['raw_known_to_unknown_count']} raw known→unknown metadata changes")
