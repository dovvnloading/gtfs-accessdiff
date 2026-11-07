"""Deterministic comparison of published GTFS wheelchair-accessibility metadata.

This compares *data*, not the physical accessibility of stops or vehicles.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

MAX_STOPS_FILE_BYTES = 64 * 1024 * 1024
KNOWN_VALUES = frozenset({"1", "2"})
VALID_VALUES = frozenset({"0", "1", "2"})


class FeedError(ValueError):
    """Invalid or unsupported GTFS input; audit cannot be trusted."""


@dataclass(frozen=True)
class Stop:
    stop_id: str
    stop_name: str
    wheelchair_boarding: str
    parent_station: str


@dataclass(frozen=True)
class Finding:
    stop_id: str
    stop_name: str
    category: str
    old_value: str
    new_value: str
    explanation: str


@dataclass(frozen=True)
class AuditResult:
    status: str
    old_records: int
    new_records: int
    matched_records: int
    overlap: float
    min_overlap: float
    old_known_records: int
    new_known_records: int
    information_losses: int
    status_changes: int
    information_gains: int
    removed_record_ids: int
    added_record_ids: int
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            **{k: v for k, v in asdict(self).items() if k != "findings"},
            "schema_version": "0.2.0",
            "findings": [asdict(f) for f in self.findings],
            "scope": "GTFS stops.txt wheelchair_boarding, including parent inheritance",
            "disclaimer": "Changes to published metadata do not prove physical accessibility changes.",
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    def to_markdown(self) -> str:
        def clean(value: str) -> str:
            return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")

        lines = [
            "# GTFS AccessDiff report",
            "",
            f"**Result:** `{self.status}`",
            "",
            "This report compares published wheelchair-accessibility *data*. It does not establish whether a location is physically accessible.",
            "",
            "| Metric | Count |",
            "| --- | ---: |",
            f"| Location records in baseline | {self.old_records} |",
            f"| Location records in candidate | {self.new_records} |",
            f"| IDs matched across releases | {self.matched_records} |",
            f"| Overlap (matched / larger feed) | {self.overlap:.1%} |",
            f"| Records with known status, baseline | {self.old_known_records} |",
            f"| Records with known status, candidate | {self.new_known_records} |",
            f"| **Known information lost** | **{self.information_losses}** |",
            f"| Known status changed | {self.status_changes} |",
            f"| Previously unknown became known | {self.information_gains} |",
            f"| Removed IDs (not classified as losses) | {self.removed_record_ids} |",
            f"| Added IDs | {self.added_record_ids} |",
            "",
        ]
        if self.overlap < self.min_overlap:
            lines += [
                f"**Inconclusive:** ID overlap is below the configured {self.min_overlap:.0%} threshold. A change in identifiers may explain missing matches.",
                "",
            ]
        lines += ["## Changes requiring review", ""]
        if self.findings:
            lines += [
                "| Stop ID | Name | Finding | Before → After | Meaning |",
                "| --- | --- | --- | --- | --- |",
            ]
            for f in self.findings:
                lines.append(
                    f"| `{clean(f.stop_id)}` | {clean(f.stop_name)} | {clean(f.category)} | "
                    f"`{f.old_value}` → `{f.new_value}` | {clean(f.explanation)} |"
                )
        else:
            lines.append("No changes in comparable location accessibility metadata were detected.")
        lines += [
            "",
            "## Interpretation and limitations",
            "",
            "- `1` means wheelchair boarding/access is indicated; `2` means wheelchair boarding/access is indicated as unavailable; `unknown` means no published status is known.",
            "- A `loss` means a known published value changed to unknown; it does **not** prove a physical accessibility change.",
            "- A `status_change` requires human review. It may reflect a correction or a real service change.",
            "- Locations are matched by stable `stop_id`; new/removed IDs are counted, not called regressions. ID churn can make comparisons inconclusive.",
            "- GTFS parent-station inheritance is resolved before comparing each location.",
            "- Version 0.1 examines only `stops.txt`'s `wheelchair_boarding`, not trip access, pathways, live elevator status, or text-to-speech.",
            "- Run the official MobilityData GTFS validator separately; this tool is not a standards-compliance validator.",
            "",
        ]
        return "\n".join(lines)


def _read_csv_text(path: Path) -> str:
    """Read only root-level stops.txt; never extract untrusted ZIP members."""
    if path.is_dir():
        target = path / "stops.txt"
        if not target.is_file():
            raise FeedError(f"No stops.txt in directory: {path}")
        if target.stat().st_size > MAX_STOPS_FILE_BYTES:
            raise FeedError("stops.txt exceeds the configured 64 MiB size limit")
        try:
            return target.read_text(encoding="utf-8-sig")
        except UnicodeError as e:
            raise FeedError(f"Could not decode stops.txt as UTF-8: {e}") from e

    if not path.is_file() or path.suffix.lower() != ".zip":
        raise FeedError(f"Expected a GTFS .zip or an unpacked directory: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            matches = [entry for entry in archive.infolist() if entry.filename == "stops.txt"]
            if not matches:
                raise FeedError("ZIP has no root-level stops.txt")
            if len(matches) != 1:
                raise FeedError("ZIP contains duplicate root-level stops.txt entries")
            info = matches[0]
            if info.file_size > MAX_STOPS_FILE_BYTES:
                raise FeedError("stops.txt exceeds the configured 64 MiB size limit")
            with archive.open(info) as stream:
                # Do not trust only the ZIP entry's advertised uncompressed size.
                raw = stream.read(MAX_STOPS_FILE_BYTES + 1)
                if len(raw) > MAX_STOPS_FILE_BYTES:
                    raise FeedError("stops.txt exceeds the configured 64 MiB size limit")
                return raw.decode("utf-8-sig")
    except (zipfile.BadZipFile, OSError, UnicodeError, RuntimeError, EOFError) as e:
        raise FeedError(f"Could not read stops.txt from {path}: {e}") from e


def load_stops(path: str | Path) -> dict[str, Stop]:
    """Load a GTFS feed without any network requests or third-party dependencies."""
    text = _read_csv_text(Path(path))
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if not reader.fieldnames or "stop_id" not in reader.fieldnames:
            raise FeedError("stops.txt must contain a stop_id column")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise FeedError("stops.txt has duplicate column headers")
        if any(not name or "\x00" in name for name in reader.fieldnames):
            raise FeedError("stops.txt has blank or NUL-containing column headers")
        records: dict[str, Stop] = {}
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise FeedError(f"Too many columns in stops.txt data row {row_number}")
            if any(value is not None and "\x00" in value for value in row.values()):
                raise FeedError(f"NUL byte in stops.txt data row {row_number}")
            stop_id = (row.get("stop_id") or "").strip()
            if not stop_id:
                raise FeedError(f"Empty stop_id at stops.txt row {row_number}")
            if stop_id in records:
                raise FeedError(f"Duplicate stop_id {stop_id!r} at row {row_number}")
            value = (row.get("wheelchair_boarding") or "").strip()
            if value not in VALID_VALUES and value != "":
                raise FeedError(f"Invalid wheelchair_boarding {value!r} at row {row_number}")
            records[stop_id] = Stop(
                stop_id=stop_id,
                stop_name=(row.get("stop_name") or "").strip(),
                wheelchair_boarding=value,
                parent_station=(row.get("parent_station") or "").strip(),
            )
        if not records:
            raise FeedError("stops.txt has no stop records")
        for stop in records.values():
            if stop.parent_station and stop.parent_station not in records:
                raise FeedError(f"Stop {stop.stop_id!r} references nonexistent parent {stop.parent_station!r}")
        return records
    except csv.Error as e:
        raise FeedError(f"Malformed stops.txt CSV: {e}") from e


def resolved_wheelchair_values(stops: dict[str, Stop]) -> dict[str, str]:
    """Resolve 0/blank inheritance without recursion; unknown stays unknown."""
    values: dict[str, str] = {}
    for stop_id in stops:
        if stop_id in values:
            continue
        path: list[str] = []
        seen: set[str] = set()
        cursor = stop_id
        while cursor not in values:
            if cursor in seen:
                raise FeedError(f"Cycle in parent_station hierarchy involving {cursor!r}")
            seen.add(cursor)
            path.append(cursor)
            stop = stops[cursor]
            if stop.wheelchair_boarding in KNOWN_VALUES:
                result = stop.wheelchair_boarding
                break
            if not stop.parent_station:
                result = "unknown"
                break
            cursor = stop.parent_station
        else:
            result = values[cursor]
        for item in reversed(path):
            own_value = stops[item].wheelchair_boarding
            if own_value in KNOWN_VALUES:
                result = own_value
            values[item] = result
    return values


def compare_feeds(
    baseline: str | Path,
    candidate: str | Path,
    *,
    min_overlap: float = 0.75,
) -> AuditResult:
    if not 0 <= min_overlap <= 1:
        raise ValueError("min_overlap must be between 0 and 1")
    old = load_stops(baseline)
    new = load_stops(candidate)
    old_values = resolved_wheelchair_values(old)
    new_values = resolved_wheelchair_values(new)
    shared = sorted(old.keys() & new.keys())
    # Conservative measure: a nearly-empty new feed must not pass as 100%
    # comparable merely because all of its remaining stop IDs existed before.
    denominator = max(len(old), len(new))
    overlap = len(shared) / denominator if denominator else 0.0
    findings: list[Finding] = []
    losses = 0
    changes = 0
    gains = 0

    for stop_id in shared:
        before, after = old_values[stop_id], new_values[stop_id]
        if before == after:
            continue
        if before in KNOWN_VALUES and after == "unknown":
            category = "information_loss"
            explanation = "Previously published wheelchair status became unknown."
            losses += 1
        elif before in KNOWN_VALUES and after in KNOWN_VALUES:
            category = "status_change"
            explanation = "Published wheelchair status changed; confirm why before releasing."
            changes += 1
        elif before == "unknown" and after in KNOWN_VALUES:
            gains += 1
            continue
        else:
            continue
        findings.append(
            Finding(
                stop_id=stop_id,
                stop_name=new[stop_id].stop_name or old[stop_id].stop_name,
                category=category,
                old_value=before,
                new_value=after,
                explanation=explanation,
            )
        )

    if overlap < min_overlap:
        status = "inconclusive_low_id_overlap"
    elif losses:
        status = "information_losses_found"
    else:
        status = "no_information_losses_detected"

    return AuditResult(
        status=status,
        old_records=len(old),
        new_records=len(new),
        matched_records=len(shared),
        overlap=overlap,
        min_overlap=min_overlap,
        old_known_records=sum(v in KNOWN_VALUES for v in old_values.values()),
        new_known_records=sum(v in KNOWN_VALUES for v in new_values.values()),
        information_losses=losses,
        status_changes=changes,
        information_gains=gains,
        removed_record_ids=len(old.keys() - new.keys()),
        added_record_ids=len(new.keys() - old.keys()),
        findings=tuple(findings),
    )
