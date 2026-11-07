"""Command-line entry point for GTFS AccessDiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import FeedError, compare_feeds


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
        "--min-overlap",
        type=float,
        default=0.75,
        help="Minimum common stop-ID overlap ratio for a conclusive result (default: 0.75)",
    )
    parser.add_argument(
        "--fail-on-loss",
        action="store_true",
        help="Exit 2 for information loss, or 3 if overlap is inconclusive; otherwise exit 0",
    )
    args = parser.parse_args(argv)
    if not 0 <= args.min_overlap <= 1:
        parser.error("--min-overlap must be between 0 and 1")
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
        report = compare_feeds(args.baseline, args.candidate, min_overlap=args.min_overlap)
        rendered = report.to_json() if args.format == "json" else report.to_markdown()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            print(rendered, end="")
    except (FeedError, OSError) as e:
        print(f"gtfs-accessdiff: {e}", file=sys.stderr)
        return 1

    if args.fail_on_loss:
        if report.status == "inconclusive_low_id_overlap":
            return 3
        if report.information_losses:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
