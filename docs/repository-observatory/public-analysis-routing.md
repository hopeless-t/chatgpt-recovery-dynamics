# Public Analysis Observer Routing / MIL-004

> Status: SHADOW BASELINE IMPLEMENTED / NO JOB SKIPPING

The repository currently runs the full `Validate public analysis` workflow on
every pull request. That workflow launches 13 jobs, including three Python
compatibility jobs plus Monte Carlo, archaeology, transition, transport,
congestion, deep-validation, latent-timing, Purrtocol, repository-surface and
Recovery Helper checks.

MIL-004 asks a narrow observer-hygiene question:

> Can the repository identify a conservative candidate subset of public-analysis
> jobs for isolated 429 changes without actually skipping anything yet?

## Fail-closed shadow policy

The first safe island is intentionally narrow:

- `.github/workflows/validate-http-429*`
- `data/http_429_*`
- `scripts/http_429_*`
- `docs/429-conformance-lab/*`
- `docs/purrtocol-429-peace-bridge/*`
- `data/preflight_routes.json`

A changed path set qualifies only if **every path** belongs to that island.

For an isolated 429 path set the candidate public-analysis subset is:

```text
repository-surface
+ validate (3.11), validate (3.12), validate (3.13) when Python changed
```

Everything else is fail-closed `FULL`.

That includes unknown paths, science/model paths, shared Observatory state,
global portal/discovery surfaces, and mixed safe-island + shared-surface
changes.

## Historical specimens

| PR | Classification | Candidate public-analysis jobs |
|---|---|---:|
| #47 429 composition metamorphic | `http-429-isolated` | 4 / 13 |
| #45 429 + shared Observatory state | `full-fail-closed` | 13 / 13 |
| #31 Peace Bridge + global portal | `full-fail-closed` | 13 / 13 |
| #9 latent-timing science | `full-fail-closed` | 13 / 13 |

PR #47 actually launched all 13 public-analysis jobs. Under the shadow policy,
9 jobs were candidate avoidable work. No job was actually skipped.

## Live paired specimens

PR #50 changed the Meta workflow itself. The live router correctly classified it
as `full-fail-closed` with 13 / 13 candidate jobs.

PR #51 was the first live isolated-429 specimen:

```text
shadow route             http-429-isolated
candidate jobs           4 / 13
candidate avoided jobs   9 / 13
candidate avoided share  69.23%
actual public jobs       13 / 13 PASS
429 local conformance    PASS
Repository Observatory   PASS
Meta Improvement Loop    PASS
jobs actually skipped    0
```

This is a paired shadow observation: the candidate route was computed while the
full matrix still ran and remained authoritative.

## Trigger-coverage finding

The first live #51 commit exposed a second-order mismatch:

```text
router safe island       broad prefixes such as scripts/http_429_*
source workflow triggers explicit enumerated 429 paths
```

A lab documentation path was then added so the paired specimen also exercised
the existing HTTP 429 local-conformance gate. That produced a green paired
sample, but it does **not** prove that every path accepted by the safe island is
covered by the required source-proximate gates.

Therefore the next hard prerequisite is machine-checkable trigger coverage.

## Authority boundary

The router still has no execution authority.

```text
candidate route != permission to skip
shadow PASS      != workflow optimization promoted
unknown          -> FULL
mixed surface    -> FULL
jobs skipped     = 0
```

No runtime saving has been measured because no job has been skipped.
A zero-false-negative claim is also not established from one live isolated
paired specimen.

Frozen receipt:

- `data/public_analysis_observer_routing_reference.json`

## Promotion path

Before any real skip proposal:

1. prove every reduced-route path is covered by its required source-proximate
   promotion gates;
2. accumulate additional live paired observations while the full matrix still
   runs;
3. investigate any failure outside the candidate subset;
4. keep unknown/mixed surfaces fail-closed;
5. repair Meta timing-integrity anomalies before using phase-speed aggregates as
   justification for further optimization;
6. make any real job-skipping change a separate reversible promotion.

This is observer-hygiene research, not permission to weaken evidence.
