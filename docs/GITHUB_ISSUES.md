# Initial GitHub issue specifications

Each issue is intentionally bounded to a reviewable change. Scope can change
following feedback from maintainers.

## 1. Establish a licensed, reproducible real-feed pilot

**Context:** The CLI currently has synthetic fixtures but no measured
release-to-release validation. See `docs/PILOT.md`.

**Acceptance criteria:** Record one pair of dated releases and license/terms;
run our CLI and the canonical GTFS validator; document exact checksums,
ID overlap, counts and a manual review of all flags. Never commit the
source GTFS archives without explicit distribution rights.

**Out of scope:** Claims about physical accessibility or broad adoption.

**Suggested labels:** `research`, `help wanted`, `documentation`.

## 2. Add stable-ID change review without automatic fuzzy matching

**Context:** `stop_id` can change or be reused, which can make results
misleading. Silent name-based pairing risks comparing different locations.

**Acceptance criteria:** Produce a separate, deterministic human review report
for removed/added IDs and suspicious reused IDs; don't convert them into
regressions without evidence. Add synthetic examples with identical stop names
at different physical locations, and test ambiguous cases.

**Suggested labels:** `enhancement`, `good first issue`.

## 3. Explain inherited wheelchair-data changes

**Context:** One station status changing can affect many child platform
findings via `parent_station` inheritance.

**Acceptance criteria:** Group inherited losses by the effective source parent
in Markdown and JSON while preserving every original affected stop ID;
cover nested parents and direct child overrides in tests.

**Suggested labels:** `enhancement`, `help wanted`.

## 4. Expand input and report robustness

**Context:** The prototype bounds `stops.txt` reads and rejects common malformed
CSV. It needs broader real-feed and adversarial testing.

**Acceptance criteria:** Cover CRC-corrupted ZIPs, invalid headers,
very large compressed members, Unicode text, Markdown special characters,
CSV line breaks and report truncation strategies. Maintain dependency-free
execution and nonzero exits for untrustworthy inputs.

**Suggested labels:** `testing`, `good first issue`.

## 5. Publish a safe, optional GitHub Actions regression gate

**Context:** The CLI offers `--fail-on-loss`, but integrating it securely
requires testing with untrusted inputs and preserving review artifacts.

**Acceptance criteria:** Define explicit least-privilege permissions, avoid
`pull_request_target` execution of untrusted code, expose human-readable
Markdown and versioned JSON, and keep blocking opt-in. Include a runnable
minimal example and documentation for archived baseline management.

**Suggested labels:** `ci`, `enhancement`.
