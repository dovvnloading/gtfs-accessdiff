# Work on GTFS AccessDiff through GitHub

The project is hosted at https://github.com/dovvnloading/gtfs-accessdiff.

## Get the code

```bash
git clone https://github.com/dovvnloading/gtfs-accessdiff.git
cd gtfs-accessdiff
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m gtfs_accessdiff samples/baseline.zip samples/candidate.zip
```

## Open a contribution

1. Check the repository's **Issues** for a small, well-defined task.
2. Fork or branch the repository, and make a targeted change with tests.
3. Run the test suite on Python 3.11+ locally.
4. Open a pull request and document any changes to the interpretation of GTFS wheelchair information.

The GitHub Actions test workflow runs unit tests against Python 3.11–3.13.
See [CONTRIBUTING.md](../CONTRIBUTING.md) for expectations and the
[real-feed pilot](PILOT.md) for how to handle agency data without bundling
possibly restricted feeds into public commits.

## Maintainer checklist

- Keep `main` protected when the GitHub account/repository supports rulesets.
- Require review and CI for release branches when feasible.
- Leave regression-based CI blocking opt-in until data stability is validated.
- Publish aggregate results rather than third-party GTFS archives unless distribution rights are clear.
