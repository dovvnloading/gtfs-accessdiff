# Open-source opportunity research

**Research date:** November 6, 2026  
**Question:** What useful, sustainable, collaborative open-source project could
we build in public, in small steps, while avoiding another redundant wrapper?

This is a research-backed *proposal*, not a claim that we have surveyed transit
riders or independently proven demand. Every public source should be revisited
when product assumptions change.

## Method

We compared six candidate areas against five practical criteria: demonstrated
problem, existing-tool coverage, incremental scope, reproducible verification,
and compatibility with collaboration/upstream contributions. We relied on
primary standards and documentation first, then inspected actual repositories,
issue discussions, and 2026 ecosystem reports. We deliberately searched for
competing projects before choosing a direction.

## Decision table

| Area | Evidence of need | Existing solutions | Two-person feasibility | Decision |
| --- | --- | --- | --- | --- |
| CI runtime and energy waste | Strong developer-interest survey | GitHub metrics, Eco CI, cicd-optimizer, Impact Framework | High for niche tooling | Do not duplicate current optimizers |
| Verifying AI-assisted pull requests | Strong maintainer survey + GitHub discussions | proofcheck, PRTruth, CodeDecay, native CI/PR templates | Medium; trust and code-execution boundaries are difficult | Contribute upstream instead of cloning |
| Accessible PDF checking | Standards and public-sector demand | PAC 2026, Horn, OpenADA, pdfa11y, many CI wrappers | Medium, due to complex standards | Too crowded for a generic checker |
| Dependency EOL hygiene | Enterprise maintenance and security needs | Dependabot plus end-of-life checkers, Graveyard Check, EOL services | High for a tiny adapter | Too crowded as a general scanner |
| Single-release transit accessibility quality | GTFS and Caltrans guidance explicitly call out missing data | MobilityData validator, BlinkTag validator, GTFS accessibility auditor | High | Extend ecosystem; don't duplicate validators |
| **Cross-release accessibility-information regression** | GTFS data updates frequently; known data may disappear | Generic GTFS diff specs/tools, but no dedicated tool found in this scan for CI-gating effective wheelchair metadata losses | **High** | **Selected: GTFS AccessDiff** |

These are qualitative judgments, not measured market-size scores. "No dedicated
tool found" describes our bounded search, **not** proof that one doesn't exist.

## Primary evidence

### Why data completeness matters

- The official GTFS accessibility feature guide explains `wheelchair_boarding`
  at locations, `wheelchair_accessible` at trips, and TTS fields:
  https://gtfs.org/getting-started/features/accessibility/
- GTFS Scorecard reports that 1,479 of 1,576 comparison-eligible **feed
  records** (93.8%) were missing wheelchair boarding information as assessed by
  its checker. This supports a *completeness* problem, not the prevalence of
  *between-release regressions*; feed records are not unique agencies and the
  sample may not represent the universe of transit feeds:
  https://gtfsscorecard.org/problems/
- Los Angeles Metro has published proof-of-concept scripts to add missing GTFS
  accessibility information, another practical example of the data-quality
  challenge: https://github.com/LACMTA/gtfs-accessibility
- The GTFS pathways guide says a blank accessibility field leaves riders
  uncertain, even where boarding might be possible:
  https://gtfs.org/documentation/schedule/examples/pathways/
- The GTFS reference describes the important difference between value `0`
  (unknown/inherited), `1` and `2`, including parent-station inheritance:
  https://github.com/google/transit/blob/master/gtfs/spec/en/reference.md
- GTFS guidance stresses that feeds must be complete, accurate, and updated as
  agencies change service, sometimes weekly or daily:
  https://gtfs.org/getting-started/validate/
- The California Transit Data Guidelines emphasize communicating wheelchair
  trip feasibility: https://dot.ca.gov/cal-itp/california-transit-data-guidelines
- Caltrans distinguishes validating the structure of a feed from verifying
  whether its real-world facts are correct. Our tool must make the same
  distinction: https://dot.ca.gov/cal-itp/california-transit-data-guidelines-faqs-v3_0
- U.S. FTA publicly lists GTFS feed links for fixed-route services (published
  dataset updated October 2026), giving a path to pilot agency samples:
  https://catalog.data.gov/dataset/general-transit-feed-specification-weblinks

### Why this must integrate with existing open source

**Snapshot validators already exist:**

- [MobilityData/gtfs-validator](https://github.com/MobilityData/gtfs-validator)
  performs canonical static-feed validation; do not rewrite its rules.
- [BlinkTagInc/gtfs-accessibility-validator](https://github.com/BlinkTagInc/gtfs-accessibility-validator)
  reviews stop, trip, TTS and pathway accessibility fields in one feed.
- [gtfs-accessibility-auditor](https://github.com/DanielCuevas1208/gtfs-accessibility-auditor)
  reports accessible-stop and trip coverage, but explicitly says it checks one
  feed per run.
- [GTFS Scorecard](https://github.com/ChelseaKR/gtfs-scorecard) runs
  existing validators across public feeds and publishes quality history.

**Cross-release diff already exists:**

- [MobilityData GTFS Diff](https://github.com/MobilityData/gtfs-diff)
  specifies general file/row/column changes; it explicitly mentions preserving
  corrections and wheelchair information across schedule updates.
- [GTFS Semantic Diff](https://github.com/niyalist/gtfs-semantic-diff)
  compares feed generations semantically and supports stable ID mapping. Its
  public documentation focuses on routes, schedules, stop changes and fares.
  Our niche is a narrow, explainable accessibility regression *gate* that can
  later integrate with general GTFS Diff formats rather than compete with them.

### Adjacent opportunities we rejected

- GitHub/Yale developer survey (Sept. 2026): 80% of surveyed GitHub users were
  interested in efficient-code tools and 74% in software impact measurement.
  Sample selection was **nonprobability**, so these are respondent preferences,
  not representative global population rates:
  https://github.blog/news-insights/research/developers-want-more-efficient-software-heres-what-over-1000-github-users-told-us-they-need/
- Existing CI solutions already include [GitHub Actions usage and performance
  metrics](https://docs.github.com/en/actions/concepts/metrics),
  [Eco CI](https://docs.gitlab.com/ci/sustainability/), and
  [cicd-optimizer](https://github.com/mrckurz/cicd-optimizer).
- Linux Foundation Research (Oct. 20, 2026) reported maintainer perceptions
  that 25% of incoming pull requests are low quality; **this is a survey
  estimate, not an independently audited percentage of all PRs**:
  https://www.linuxfoundation.org/press/new-lf-research-survey-shows-generative-ai-cuts-open-source-coding-time-in-half-but-25-of-incoming-pull-requests-are-considered-ai-slop
- Existing proof-oriented PR products include
  [proofcheck](https://github.com/bhaskargurram-ai/proofcheck) and
  [PRTruth](https://github.com/eissasoubhi/PRTruth), so another generic PR
  evidence tool is unlikely to add sufficient new value.
- PDF accessibility tooling includes
  [PAC 2026](https://pac.pdf-accessibility.org/en/resources/quickstart-guide/introducing-pdf-accessibility-checker-2026),
  [Horn](https://github.com/focusring/horn), and
  [OpenADA](https://github.com/techcto/openada).
- EOL checking is served by products such as
  [eol-check](https://github.com/endoflife-ai/eol-check) and
  [Graveyard Check](https://graveyard-check-ouxi.vercel.app/).

## Why GTFS AccessDiff is a defensible starting point

- **User-visible impact:** A reviewer can see when accessible-routing metadata
  disappears from a release and request correction before publication.
- **Stable acceptance test:** Feed A `wheelchair_boarding=1`; feed B `0` for the
  same location ID; produce an auditable finding. No AI inference required.
- **Small first release:** Stdlib-only CLI, local ZIPs, no server, no API key.
- **Incremental:** Stop metadata first, then trip-level information, TTS,
  paths, ID changes, CI integration and real-world pilot evaluation.
- **Upstream opportunity:** Sample fixtures and bug findings can be contributed
  to existing validator/diff projects after maintainer agreement.

## Failure modes and how the prototype handles them

| Risk | Approach |
| --- | --- |
| Mistaking missing info for physical inaccessibility | Clearly label the result as metadata only |
| Changes to `stop_id` between releases | Do not match IDs heuristically in v0.1; report overlap and mark low-overlap results inconclusive |
| Valid child stop inherits status from parent | Resolve the parent chain before comparison |
| Service reductions or true stop removal | Count added/removed IDs separately; don't call them information losses |
| Legitimate correction `1 → 2` | Label a review-needed status change, not an automated regression |
| Large, malformed, or untrusted ZIPs | Only read root-level `stops.txt`, enforce a size bound and parse strictly; add fuzz testing before v1 |
| Accidentally claiming GTFS conformance | Require existing validator in production and state this is complementary |
| Data licenses and rider privacy | Publish only synthetic fixtures by default; cite/attribute public feeds and check license before redistributing |
| Unknown real demand | Run pilot interviews with actual feed producers before calling this production-ready |

## Proposed validation study

1. Obtain permission or verify open-data license for two dated releases each of
   3 public transit feeds. Candidate sources include Pittsburgh Regional
   Transit archives (https://data.wprdc.org/en/dataset/gtfs-archive; assess
   both its listed license **and separate WPRDC data-use agreement** before
   accessing or redistributing) and SEPTA's versioned release collection
   (https://catalog.data.gov/dataset/septa-gtfs).
2. Record base/candidate stop-ID overlap, count of lost metadata, and how many
   findings were confirmed by a human reviewing the source records.
3. Ask at least three feed publishers or accessibility-data maintainers whether
   a readable CI report would change their release workflow, and what would
   make a warning actionable.
4. Before expanding scope, log false positives, legitimate data corrections,
   unmatched IDs, and minutes required to review each report.
5. If the needs are better served in an existing project, contribute the test
   corpus or implementation upstream instead of insisting on a new product.

## Uncertainties

We have **not** established that transit agencies would adopt a new tool, that
metadata regressions are frequent, or that the selected name is trademark-free.
A pilot and maintainer outreach are prerequisites for a confident adoption
claim. Real data may need to remain local depending on feed licenses.
