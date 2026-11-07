# Contributing to GTFS AccessDiff

Thanks for helping improve public transit accessibility data.

Please begin with [docs/ROADMAP.md](docs/ROADMAP.md). Open an issue to discuss
substantial features before implementing them, especially GTFS semantics.
Small test cases, documentation corrections, and reproducible bug reports are
always welcome.

## Local setup

Use Python 3.11+:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m gtfs_accessdiff samples/baseline.zip samples/candidate.zip
```

No development dependencies or cloud account are required. Please make each
pull request small enough to understand on its own.

## Pull request checklist

- [ ] A clear problem statement and referenced GTFS specification clause.
- [ ] A minimal synthetic before/after feed test that reproduces the behavior.
- [ ] A test for a harmless counterexample (avoid false positives).
- [ ] No claim about physical accessibility based only on GTFS metadata.
- [ ] Example output or documentation updated for user-visible changes.
- [ ] Tests pass and no real agency datasets are added without license review.
- [ ] If AI tools assisted, verify the resulting code, tests and claims yourself.

If you have a real feed example, please remove personal data and share only
the smallest reproducible portion permitted by the publisher's license.

Be respectful and constructive with contributors and maintainers. Focus on
reproducible evidence, not assumptions about code authorship.
