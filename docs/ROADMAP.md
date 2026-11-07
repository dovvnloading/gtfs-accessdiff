# Incremental GitHub roadmap

Our rule is to merge small, reviewable PRs. Every feature needs a synthetic
counterexample, an expected report, a passing test and explicit limitations.

## Milestone 0 — working research prototype (implemented locally)

- [x] Document problem, competitors, scope and assumptions.
- [x] Local ZIP/directory loader for `stops.txt`.
- [x] Compare unchanged stop IDs and resolve inherited wheelchair metadata.
- [x] Distinguish information loss, status change and gain.
- [x] Report low ID overlap as inconclusive and keep CI gating opt-in.
- [x] Stable Markdown/JSON outputs, synthetic examples and unit tests.
- [x] MIT license, contribution guidance and a CI test workflow.

## Milestone 1 — harden before public pilot

1. **Issue 1: Handle arbitrary GTFS ID churn.** Add a human-reviewable
   matching report, never silently join ambiguous stops; cover duplicate names
   and nearby stops. Start with tests, not geographic guesses.
2. **Issue 2: Add GTFS input robustness tests.** **In progress:** duplicate headers, extra CSV columns, malformed quotes, invalid UTF-8, NUL bytes, empty feeds, and accidental source overwrites are tested. Still to cover: CRC errors, extreme compression and output-size handling.
3. **Issue 3: Report causes of inherited changes.** Group many child losses
   under the parent whose value disappeared, retaining full per-stop evidence.
4. **Issue 4: Validate 3 archived feed pairs.** Check licenses; run publicly
   reproducible audits; maintain a manual review log; do not invent an impact
   metric based on unverified inputs. See `docs/PILOT.md`.

## Milestone 2 — meaningful data coverage

5. **Issue 5: Compare trip-level `wheelchair_accessible`.** First establish
   trip identity stability; do not treat new/retimed trips as physical access
   changes or compare unrelated trip IDs.
6. **Issue 6: Compare station Pathways graphs.** Detect loss of previously
   published accessible connections; test cycles, one-way paths and elevators.
7. **Issue 7: Compare text-to-speech fields.** Flag loss of existing
   `tts_stop_name` content for human review; avoid claiming missing optional
   values are always wrong.

## Milestone 3 — adoption and upstream collaboration

8. **Issue 8: Minimal GitHub Action / reusable workflow.** Run in read-only
   contexts; pin dependencies; generate a review artifact; never execute
   untrusted feed contents as code. Keep blocking behavior optional.
9. **Issue 9: Schema interoperability.** Discuss integrating findings with the
   existing GTFS Diff specification and MobilityData validator reports.
10. **Issue 10: Documentation and feedback from pilot maintainers.** Keep a
    public false-positive log and maintain structured, versioned JSON output.

## Open-source quality bar

- New data rule → specification link, test that fails without the change,
  negative test, Markdown/JSON example and limitation note.
- New output → stable schema with version number and snapshot test.
- CI integration → least-privilege permissions and safe handling of untrusted
  PR content; no secret-bearing `pull_request_target` execution.
- Substantial new rules → user feedback or an upstream issue demonstrating
  demand before implementation.

## First user-facing success criterion

One feed publisher can run a comparison entirely locally, understand the
exact `stop_id` and field responsible for a loss, and decide whether to
correct their GTFS export. **This has not been user-tested yet.**
