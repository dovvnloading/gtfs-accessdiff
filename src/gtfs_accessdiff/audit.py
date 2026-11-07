"""Deterministic, local-only comparison of published GTFS accessibility metadata.

A finding concerns the *published feed*, not actual physical accessibility.
GTFS conformance should be assessed with the MobilityData validator separately.
"""

from __future__ import annotations

import csv
import html
import io
import json
import math
import re
import zipfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

MAX_STOPS_FILE_BYTES = 64 * 1024 * 1024
KNOWN_VALUES = frozenset({"1", "2"})
VALID_VALUES = frozenset({"", "0", "1", "2"})
MAX_ID_SAMPLES = 25
DEFAULT_REPORT_LIMIT = 200
SCHEMA_VERSION = "0.3.0"


class FeedError(ValueError):
    """Invalid/unsupported GTFS input: its comparison cannot be trusted."""


@dataclass(frozen=True)
class Stop:
    stop_id: str
    stop_name: str
    wheelchair_boarding: str
    parent_station: str
    location_type: str = "0"
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class ResolvedStatus:
    value: str
    source_stop_id: str | None
    source_kind: str  # explicit | inherited | unknown


@dataclass(frozen=True)
class Finding:
    stop_id: str
    stop_name: str
    category: str
    old_value: str
    new_value: str
    explanation: str
    baseline_source_id: str | None = None
    candidate_source_id: str | None = None
    baseline_raw_value: str = ""
    candidate_raw_value: str = ""


@dataclass(frozen=True)
class IdentityConcern:
    stop_id: str
    old_name: str
    new_name: str
    old_location_type: str
    new_location_type: str
    moved_meters: int | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class IdSample:
    stop_id: str
    stop_name: str
    location_type: str
    effective_wheelchair_boarding: str
    parent_station: str


@dataclass(frozen=True)
class InheritedCause:
    baseline_source_id: str
    affected_records: int
    affected_stop_id_sample: tuple[str, ...]
    sample_omitted: int


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
    comparable_records: int = 0
    comparable_overlap: float = 0.0
    identity_concerns: tuple[IdentityConcern, ...] = ()
    removed_known_records: int = 0
    added_known_records: int = 0
    removed_id_samples: tuple[IdSample, ...] = ()
    added_id_samples: tuple[IdSample, ...] = ()
    inherited_causes: tuple[InheritedCause, ...] = ()
    identity_distance_meters: float = 500.0

    def as_dict(self, *, max_findings: int = DEFAULT_REPORT_LIMIT) -> dict[str, Any]:
        if max_findings < 1:
            raise ValueError("max_findings must be at least 1")
        body = {field.name: getattr(self, field.name) for field in fields(self) if field.name not in {
            "findings", "identity_concerns", "removed_id_samples", "added_id_samples", "inherited_causes",
        }}
        body.update({
            "schema_version": SCHEMA_VERSION,
            "findings": [asdict(f) for f in self.findings[:max_findings]],
            "findings_total": len(self.findings),
            "findings_omitted": max(0, len(self.findings) - max_findings),
            "identity_concerns": [asdict(i) for i in self.identity_concerns[:max_findings]],
            "identity_concerns_total": len(self.identity_concerns),
            "identity_concerns_omitted": max(0, len(self.identity_concerns) - max_findings),
            "removed_id_samples": [asdict(i) for i in self.removed_id_samples],
            "added_id_samples": [asdict(i) for i in self.added_id_samples],
            "inherited_causes": [asdict(i) for i in self.inherited_causes[:max_findings]],
            "inherited_causes_total": len(self.inherited_causes),
            "inherited_causes_omitted": max(0, len(self.inherited_causes) - max_findings),
            "scope": "GTFS stops.txt wheelchair_boarding, including parent inheritance",
            "disclaimer": "Changes to published metadata do not prove physical accessibility changes.",
        })
        return body

    def to_json(self, *, max_findings: int = DEFAULT_REPORT_LIMIT) -> str:
        return json.dumps(self.as_dict(max_findings=max_findings), indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    def to_markdown(self, *, max_findings: int = DEFAULT_REPORT_LIMIT) -> str:
        if max_findings < 1:
            raise ValueError("max_findings must be at least 1")

        lines = [
            "# GTFS AccessDiff report", "", f"**Result:** `{self.status}`", "",
            "This report compares published wheelchair-accessibility *data*. It does not establish whether a location is physically accessible.",
            "", "| Metric | Count |", "| --- | ---: |",
            f"| Location records in baseline | {self.old_records} |",
            f"| Location records in candidate | {self.new_records} |",
            f"| Shared IDs | {self.matched_records} |",
            f"| IDs quarantined for identity review | {len(self.identity_concerns)} |",
            f"| Comparable records | {self.comparable_records} |",
            f"| ID overlap (shared / larger feed) | {self.overlap:.1%} |",
            f"| Comparable coverage (after identity checks) | {self.comparable_overlap:.1%} |",
            f"| Records with known status, baseline | {self.old_known_records} |",
            f"| Records with known status, candidate | {self.new_known_records} |",
            f"| **Known information lost** | **{self.information_losses}** |",
            f"| Known status changed | {self.status_changes} |",
            f"| Previously unknown became known | {self.information_gains} |",
            f"| Removed IDs (not counted as loss) | {self.removed_record_ids} |",
            f"| Removed IDs with known baseline status | {self.removed_known_records} |",
            f"| Added IDs | {self.added_record_ids} |",
            f"| Added IDs with known candidate status | {self.added_known_records} |", "",
        ]
        if self.comparable_overlap < self.min_overlap:
            lines.extend([
                f"**Inconclusive:** comparable coverage is below the configured {self.min_overlap:.0%} threshold. Changed IDs and possible ID reuse can make comparisons incomplete.", "",
            ])
        elif self.identity_concerns:
            lines.extend(["**Partial review required:** suspicious shared IDs were not compared for accessibility regressions.", ""])

        lines.extend(["## Accessibility metadata changes requiring review", ""])
        if self.findings:
            lines.extend([
                "| Stop ID | Name | Finding | Before → After | Effective source (before → after) | Meaning |",
                "| --- | --- | --- | --- | --- | --- |",
            ])
            for f in self.findings[:max_findings]:
                source_before = f.baseline_source_id or "unknown"
                source_after = f.candidate_source_id or "unknown"
                lines.append(
                    f"| {_md(f.stop_id)} | {_md(f.stop_name)} | {_md(f.category)} | "
                    f"{_md(f.old_value)} → {_md(f.new_value)} | "
                    f"{_md(source_before)} → {_md(source_after)} | {_md(f.explanation)} |"
                )
            if len(self.findings) > max_findings:
                lines.append(f"\n**{len(self.findings) - max_findings} additional accessibility findings omitted** from this bounded report; counts include all findings.")
        else:
            lines.append("No changes were detected among comparable location accessibility values.")
        lines.extend(["", "## Shared IDs requiring identity review", ""])
        if self.identity_concerns:
            lines.extend([
                "| Stop ID | Old → new name | Reason | Moved (meters) |",
                "| --- | --- | --- | ---: |",
            ])
            for item in self.identity_concerns[:max_findings]:
                moved = str(item.moved_meters) if item.moved_meters is not None else "—"
                lines.append(f"| {_md(item.stop_id)} | {_md(item.old_name)} → {_md(item.new_name)} | {_md('; '.join(item.reasons))} | {moved} |")
            if len(self.identity_concerns) > max_findings:
                lines.append(f"\n**{len(self.identity_concerns) - max_findings} additional identity concerns omitted.**")
        else:
            lines.append("No shared IDs exceeded the conservative identity review checks.")
        lines.extend(["", "## Shared source of inherited information losses", ""])
        if self.inherited_causes:
            lines.extend(["| Baseline source stop ID | Affected loss records | Example affected IDs |", "| --- | ---: | --- |"])
            for cause in self.inherited_causes[:max_findings]:
                sample = ", ".join(_md(x) for x in cause.affected_stop_id_sample)
                if cause.sample_omitted:
                    sample += f" (+{cause.sample_omitted} omitted)"
                lines.append(f"| {_md(cause.baseline_source_id)} | {cause.affected_records} | {sample} |")
            if len(self.inherited_causes) > max_findings:
                lines.append(f"\n**{len(self.inherited_causes) - max_findings} additional groups omitted.**")
        else:
            lines.append("No inherited information losses detected.")
        lines.extend(["", "## Added and removed ID samples (not automatically paired)", ""])
        for label, records, count in (("Removed", self.removed_id_samples, self.removed_record_ids),
                                       ("Added", self.added_id_samples, self.added_record_ids)):
            lines.extend([f"### {label} IDs", ""])
            if not records:
                lines.extend(["None.", ""])
                continue
            lines.extend(["| Stop ID | Name | Effective wheelchair metadata |", "| --- | --- | --- |"])
            for item in records:
                lines.append(f"| {_md(item.stop_id)} | {_md(item.stop_name)} | {_md(item.effective_wheelchair_boarding)} |")
            if count > len(records):
                lines.append(f"\n{count - len(records)} more {label.lower()} IDs omitted from the sample.")
            lines.append("")
        lines.extend([
            "## Interpretation and limitations", "",
            "- `1` indicates some wheelchair access; `2` indicates wheelchair boarding/access is unavailable; `unknown` means no published status is known.",
            "- `information_loss` means known published metadata became unknown; it **does not** demonstrate a physical accessibility change.",
            "- `status_change` requires human review; it may be a correction or a real operational change.",
            "- Explicit/inherited status sources show where an effective accessibility value originated in `stops.txt`.",
            "- Location-type changes and movements beyond the configured distance are quarantined; matching IDs do **not** guarantee matching physical locations.",
            "- Added/removed stop IDs are shown for review, never automatically paired by name or proximity.",
            "- Shared ID comparisons cannot detect cases where both coordinates and names change without exceeding a check threshold.",
            "- Only `stops.txt` is examined; trip access, pathways, live elevator status and text-to-speech are outside this version's scope.",
            "- This is not a GTFS compliance validator; also run the official MobilityData GTFS validator.", "",
        ])
        return "\n".join(lines)


def _md(value: str) -> str:
    """Render untrusted GTFS strings as inert Markdown table text."""
    text = html.escape(value.replace("\r", " ").replace("\n", " "), quote=False)
    return re.sub(r"([\\|`*_[\]~])", r"\\\1", text)


def _read_csv_text(path: Path) -> str:
    """Read only root-level stops.txt; never extract arbitrary ZIP entries."""
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
            if info.is_dir():
                raise FeedError("stops.txt must be a regular ZIP file member")
            if info.file_size > MAX_STOPS_FILE_BYTES:
                raise FeedError("stops.txt exceeds the configured 64 MiB size limit")
            with archive.open(info) as stream:
                raw = stream.read(MAX_STOPS_FILE_BYTES + 1)
                if len(raw) > MAX_STOPS_FILE_BYTES:
                    raise FeedError("stops.txt exceeds the configured 64 MiB size limit")
                return raw.decode("utf-8-sig")
    except (zipfile.BadZipFile, OSError, UnicodeError, RuntimeError, EOFError, NotImplementedError) as e:
        raise FeedError(f"Could not read stops.txt from {path}: {e}") from e


def _coordinate(raw: str, *, latitude: bool) -> float | None:
    """Malformed/missing coordinates are not used as evidence of identity."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    bound = 90 if latitude else 180
    return value if math.isfinite(value) and -bound <= value <= bound else None


def load_stops(path: str | Path) -> dict[str, Stop]:
    """Parse stops.txt without making any network requests or using dependencies."""
    content = _read_csv_text(Path(path))
    try:
        reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
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
            raw_wheelchair = (row.get("wheelchair_boarding") or "").strip()
            if raw_wheelchair not in VALID_VALUES:
                raise FeedError(f"Invalid wheelchair_boarding {raw_wheelchair!r} at row {row_number}")
            location_type = (row.get("location_type") or "0").strip() or "0"
            if location_type not in {"0", "1", "2", "3", "4"}:
                raise FeedError(f"Invalid location_type {location_type!r} at row {row_number}")
            records[stop_id] = Stop(
                stop_id=stop_id,
                stop_name=(row.get("stop_name") or "").strip(),
                wheelchair_boarding=raw_wheelchair,
                parent_station=(row.get("parent_station") or "").strip(),
                location_type=location_type,
                latitude=_coordinate(row.get("stop_lat") or "", latitude=True),
                longitude=_coordinate(row.get("stop_lon") or "", latitude=False),
            )
        if not records:
            raise FeedError("stops.txt has no stop records")
        for stop in records.values():
            if stop.parent_station and stop.parent_station not in records:
                raise FeedError(f"Stop {stop.stop_id!r} references nonexistent parent {stop.parent_station!r}")
        return records
    except csv.Error as e:
        raise FeedError(f"Malformed stops.txt CSV: {e}") from e


def resolved_statuses(stops: dict[str, Stop]) -> dict[str, ResolvedStatus]:
    """Find the explicit source of inherited values; detect cycles iteratively."""
    values: dict[str, ResolvedStatus] = {}
    for stop_id in stops:
        if stop_id in values:
            continue
        pending: list[str] = []
        seen: set[str] = set()
        cursor = stop_id
        while cursor not in values:
            if cursor in seen:
                raise FeedError(f"Cycle in parent_station hierarchy involving {cursor!r}")
            seen.add(cursor)
            pending.append(cursor)
            stop = stops[cursor]
            if stop.wheelchair_boarding in KNOWN_VALUES:
                resolution = ResolvedStatus(stop.wheelchair_boarding, cursor, "explicit")
                break
            if not stop.parent_station:
                resolution = ResolvedStatus("unknown", None, "unknown")
                break
            cursor = stop.parent_station
        else:
            resolution = values[cursor]
        for item in reversed(pending):
            own = stops[item].wheelchair_boarding
            if own in KNOWN_VALUES:
                resolution = ResolvedStatus(own, item, "explicit")
            elif resolution.value in KNOWN_VALUES:
                resolution = ResolvedStatus(resolution.value, resolution.source_stop_id, "inherited")
            values[item] = resolution
    return values


def resolved_wheelchair_values(stops: dict[str, Stop]) -> dict[str, str]:
    """Backward-compatible value-only view of resolved statuses."""
    return {stop_id: resolved.value for stop_id, resolved in resolved_statuses(stops).items()}


def _haversine_meters(a: Stop, b: Stop) -> float | None:
    if None in (a.latitude, a.longitude, b.latitude, b.longitude):
        return None
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(b.longitude - a.longitude)
    h = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 2 * 6_371_000 * math.asin(min(1.0, math.sqrt(h)))


def _identity_concern(old: Stop, new: Stop, distance_threshold: float) -> IdentityConcern | None:
    reasons = []
    if old.location_type != new.location_type:
        reasons.append("location_type changed")
    distance = _haversine_meters(old, new)
    if distance is not None and distance > distance_threshold:
        reasons.append("coordinates moved beyond review threshold")
    if not reasons:
        return None
    return IdentityConcern(
        stop_id=new.stop_id, old_name=old.stop_name, new_name=new.stop_name,
        old_location_type=old.location_type, new_location_type=new.location_type,
        moved_meters=round(distance) if distance is not None else None,
        reasons=tuple(reasons),
    )


def _id_samples(ids: set[str], stops: dict[str, Stop], values: dict[str, ResolvedStatus]) -> tuple[IdSample, ...]:
    return tuple(IdSample(
        stop_id=stop_id, stop_name=stops[stop_id].stop_name,
        location_type=stops[stop_id].location_type,
        effective_wheelchair_boarding=values[stop_id].value,
        parent_station=stops[stop_id].parent_station,
    ) for stop_id in sorted(ids)[:MAX_ID_SAMPLES])


def compare_feeds(
    baseline: str | Path,
    candidate: str | Path,
    *,
    min_overlap: float = 0.75,
    identity_distance_meters: float = 500.0,
) -> AuditResult:
    if not math.isfinite(min_overlap) or not 0 <= min_overlap <= 1:
        raise ValueError("min_overlap must be between 0 and 1")
    if not math.isfinite(identity_distance_meters) or identity_distance_meters <= 0:
        raise ValueError("identity_distance_meters must be a positive finite number")
    old, new = load_stops(baseline), load_stops(candidate)
    old_values, new_values = resolved_statuses(old), resolved_statuses(new)
    shared = sorted(old.keys() & new.keys())
    removed, added = old.keys() - new.keys(), new.keys() - old.keys()
    denominator = max(len(old), len(new))
    overlap = len(shared) / denominator
    findings: list[Finding] = []
    concerns: list[IdentityConcern] = []
    losses = changes = gains = 0
    inherited_losses: dict[str, list[str]] = {}

    # Review identity changes before comparing ANY dependent inherited values.
    # A reused station ID can otherwise create misleading child-level losses.
    shared_concerns = {
        stop_id: concern for stop_id in shared
        if (concern := _identity_concern(old[stop_id], new[stop_id], identity_distance_meters))
    }
    for stop_id in shared:
        before, after = old_values[stop_id], new_values[stop_id]
        concern = shared_concerns.get(stop_id)
        suspicious_source = next((source for source in (before.source_stop_id, after.source_stop_id)
                                  if source in shared_concerns), None)
        if concern is None and suspicious_source is not None:
            concern = IdentityConcern(
                stop_id=stop_id, old_name=old[stop_id].stop_name,
                new_name=new[stop_id].stop_name,
                old_location_type=old[stop_id].location_type,
                new_location_type=new[stop_id].location_type,
                moved_meters=None,
                reasons=(f"inherited source {suspicious_source!r} requires identity review",),
            )
        if concern:
            concerns.append(concern)
            continue
        if before.value == after.value:
            continue
        if before.value in KNOWN_VALUES and after.value == "unknown":
            category = "information_loss"
            explanation = "Previously published wheelchair status became unknown."
            losses += 1
            if before.source_stop_id and before.source_stop_id != stop_id:
                inherited_losses.setdefault(before.source_stop_id, []).append(stop_id)
        elif before.value in KNOWN_VALUES and after.value in KNOWN_VALUES:
            category = "status_change"
            explanation = "Published wheelchair status changed; confirm why before releasing."
            changes += 1
        elif before.value == "unknown" and after.value in KNOWN_VALUES:
            gains += 1
            continue
        else:
            continue
        findings.append(Finding(
            stop_id=stop_id, stop_name=new[stop_id].stop_name or old[stop_id].stop_name,
            category=category, old_value=before.value, new_value=after.value,
            explanation=explanation, baseline_source_id=before.source_stop_id,
            candidate_source_id=after.source_stop_id,
            baseline_raw_value=old[stop_id].wheelchair_boarding,
            candidate_raw_value=new[stop_id].wheelchair_boarding,
        ))

    comparable = len(shared) - len(concerns)
    comparable_overlap = comparable / denominator
    if comparable_overlap < min_overlap:
        status = "inconclusive_low_id_overlap"
    elif losses:
        status = "information_losses_found"
    elif concerns:
        status = "identity_review_required"
    else:
        status = "no_information_losses_detected"

    return AuditResult(
        status=status,
        old_records=len(old), new_records=len(new), matched_records=len(shared),
        overlap=overlap, min_overlap=min_overlap,
        old_known_records=sum(v.value in KNOWN_VALUES for v in old_values.values()),
        new_known_records=sum(v.value in KNOWN_VALUES for v in new_values.values()),
        information_losses=losses, status_changes=changes, information_gains=gains,
        removed_record_ids=len(removed), added_record_ids=len(added),
        findings=tuple(findings), comparable_records=comparable,
        comparable_overlap=comparable_overlap, identity_concerns=tuple(concerns),
        removed_known_records=sum(old_values[i].value in KNOWN_VALUES for i in removed),
        added_known_records=sum(new_values[i].value in KNOWN_VALUES for i in added),
        removed_id_samples=_id_samples(removed, old, old_values),
        added_id_samples=_id_samples(added, new, new_values),
        inherited_causes=tuple(InheritedCause(
            baseline_source_id=source, affected_records=len(ids),
            affected_stop_id_sample=tuple(sorted(ids)[:MAX_ID_SAMPLES]),
            sample_omitted=max(0, len(ids) - MAX_ID_SAMPLES),
        ) for source, ids in sorted(inherited_losses.items())),
        identity_distance_meters=identity_distance_meters,
    )
