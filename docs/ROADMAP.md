# Incremental roadmap (GitHub issue numbers are authoritative)

Prioritize human-reviewable evidence over expanding scope. Every significant rule needs a synthetic before/after test and a documented limitation. We work on feature branches with pull-request review and passing CI.

## Stage 0: Working public baseline (main, v0.2)

- [x] MIT Python CLI: compare known-to-unknown `stops.txt.wheelchair_boarding` changes.
- [x] Parent inheritance, distinct status-change classification and ID-overlap threshold.
- [x] Versioned JSON/Markdown, synthetic fixtures, 28 tests, GitHub Actions unit-test workflow.

## Stage 1: Evidence and safety (merged on main, v0.3)

- [x] **[#2](https://github.com/dovvnloading/gtfs-accessdiff/issues/2):** ID churn samples; quarantine changed location types and large coordinate moves; never fuzzy join.
- [x] **[#3](https://github.com/dovvnloading/gtfs-accessdiff/issues/3):** Explicit/inherited accessibility provenance and root-cause grouping.
- [x] **[#4](https://github.com/dovvnloading/gtfs-accessdiff/issues/4):** Bounded reports, CRC/size tests, Unicode and Markdown-sanitizing tests.
- [x] **[#5](https://github.com/dovvnloading/gtfs-accessdiff/issues/5):** Reusable, opt-in, offline composite GitHub Action with read-only calling workflow.
- [ ] **[#1](https://github.com/dovvnloading/gtfs-accessdiff/issues/1):** Three release comparisons *and* human review, independent canonical validator, and publisher feedback. The 20-release sweep and independent raw/official-validator cross-check of the notable pair are complete; publisher review and broader independent-feed testing remain.

## Stage 1.5: Make review reports actionable (v0.4)

- [x] [#7](https://github.com/dovvnloading/gtfs-accessdiff/issues/7): Exact effective accessibility-status transition matrix, including unchanged values and information gains.
- [x] Distinct, opt-in known-status-change CI gate; shared exit policy and explicit incomplete-review priority.
- [x] Synthetic CLI/Action coverage for 1 ↔ 2 changes; report-only defaults to nonblocking.
- [x] [#9](https://github.com/dovvnloading/gtfs-accessdiff/issues/9): Zero comparable IDs fail closed for opt-in gates even when the overlap threshold is configured to zero.

## Stage 2: After a useful pilot and maintainer feedback

- [ ] Trip-level `wheelchair_accessible` comparisons with conservative trip identity checks.
- [ ] Pathway graph reviews; never confuse static GTFS pathways with live elevator availability.
- [ ] `tts_stop_name` regression checks and translation nuance.
- [ ] Feedback from maintainers; compare actual reviewer time and false-positive rates.
- [ ] Evaluate opportunities to contribute our work upstream rather than building redundant tools.

## Release criteria

- CI tests pass across supported Python versions.
- User-visible outputs have versioned schema and samples.
- Identity-ambiguous comparisons cannot silently claim a clean audit.
- No external provider ZIPs are bundled without redistribution rights.
- A human must review a published-metadata finding before claiming any operational impact.
