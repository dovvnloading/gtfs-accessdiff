"""Command-line entry point for GTFS AccessDiff."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

from .audit import DEFAULT_REPORT_LIMIT, FeedError, compare_feeds
from .gate import gate_exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gtfs-accessdiff",
        description="Compare known wheelchair boarding metadata in two GTFS releases.",
    )
    parser.add_argument("baseline", help="Previously approved GTFS zip or directory")
    parser.add_argument("candidate", help="New GTFS zip or directory")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write report here instead of stdout")
    parser.add_argument(
        "--min-overlap", type=float, default=0.75,
        help="Minimum comparable stop-ID coverage for a conclusive result (default: 0.75)",
    )
    parser.add_argument(
        "--identity-distance-meters", type=float, default=500.0,
        help="Quarantine shared IDs whose coordinates moved more than this distance (default: 500)",
    )
    parser.add_argument(
        "--max-findings", type=int, default=DEFAULT_REPORT_LIMIT,
        help="Maximum accessibility/identity findings to include in report (default: 200; counts remain exact)",
    )
    parser.add_argument(
        "--fail-on-loss", action="store_true",
        help="Exit 2 for information loss, or 3 if comparison is inconclusive or needs identity review",
    )
    parser.add_argument(
        "--fail-on-status-change", action="store_true",
        help="Exit 4 for a comparable known status 1↔2 change, or 3 if identity review is incomplete",
    )
    args = parser.parse_args(argv)
    if not math.isfinite(args.min_overlap) or not 0 <= args.min_overlap <= 1:
        parser.error("--min-overlap must be a finite number between 0 and 1")
    if not math.isfinite(args.identity_distance_meters) or args.identity_distance_meters <= 0:
        parser.error("--identity-distance-meters must be a positive finite number")
    if args.max_findings < 1:
        parser.error("--max-findings must be at least 1")
    try:
        if args.output:
            protected_paths = set()
            for source in (args.baseline, args.candidate):
                source_path = Path(source)
                protected_paths.add(source_path.resolve())
                if source_path.is_dir():
                    protected_paths.add((source_path / "stops.txt").resolve())
            if args.output.resolve() in protected_paths:
                raise FeedError("--output must not overwrite the baseline or candidate feed")
        report = compare_feeds(
            args.baseline, args.candidate, min_overlap=args.min_overlap,
            identity_distance_meters=args.identity_distance_meters,
        )
        rendered = (report.to_json(max_findings=args.max_findings) if args.format == "json"
                    else report.to_markdown(max_findings=args.max_findings))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            print(rendered, end="")
    except (FeedError, OSError) as e:
        print(f"gtfs-accessdiff: {e}", file=sys.stderr)
        return 1

    return gate_exit_code(
        comparable_overlap=report.comparable_overlap,
        min_overlap=report.min_overlap,
        identity_concerns=len(report.identity_concerns),
        information_losses=report.information_losses,
        status_changes=report.status_changes,
        comparison_status=report.status,
        fail_on_loss=args.fail_on_loss,
        fail_on_status_change=args.fail_on_status_change,
    )


if __name__ == "__main__":
    raise SystemExit(main())
