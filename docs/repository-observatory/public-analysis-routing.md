# Public Analysis Observer Routing / META-003 + MIL-004

> Status: SHADOW OBSERVATION ONLY / TRIGGER-COVERAGE HARDENED

The repository currently runs the full `Validate public analysis` workflow on
every pull request. That workflow launches 13 jobs, including three Python
compatibility jobs plus Monte Carlo, archaeology, transition, transport,
congestion, deep-validation, latent-timing, Purrtocol, repository-surface and
Recovery Helper checks.

Recent source-proximate HTTP 429 pull requests already had dedicated promotion
workflows, but the full 13-job public-analysis matrix still ran as well.

The observer-routing experiment asks:

> Can the repository identify a conservative candidate subset of public-analysis
> jobs for isolated 429 changes without weakening the source-proximate promotion
> gates that make that reduction defensible?

## Two-stage fail-closed shadow policy

A changed path set must pass **both** stages before it can even become a reduced
route candidate.

### Stage 1 — safe-island membership

Every changed path must belong to the narrow 429 island:

- `.github/workflows/validate-http-429*`
- `data/http_429_*`
- `scripts/http_429_*`
- `docs/429-conformance-lab/*`
- `docs/purrtocol-429-peace-bridge/*`
- `data/preflight_routes.json`

Anything mixed, unknown, global, scientific, or shared-state routes `FULL`.

### Stage 2 — actual source-gate trigger coverage

Safe-island membership is **not enough**.

For every changed path, the router reads the current repository's actual:

```text
.github/workflows/validate-http-429*.yml
```

and extracts each workflow's `pull_request.paths`.

A reduced route remains eligible only when **every changed path matches at least
one real source-proximate 429 workflow trigger**.

If even one path is uncovered:

```text
safe-island match        yes
source-gate coverage     no
final route              FULL
coverage_fail_closed     true
jobs actually skipped    false
```

This is deliberately stricter than file-name classification.

## Candidate public-analysis subset

For a fully covered isolated 429 path set:

```text
repository-surface
+ validate (3.11), validate (3.12), validate (3.13) when Python changed
```

The router still has no execution authority.

## Historical + live specimens

| PR | First-stage island | Trigger coverage | Final candidate route |
|---|---|---|---:|
| #47 429 composition metamorphic | yes | yes | `http-429-isolated`, 4 / 13 |
| #51 live routing probe | yes | **no** | `FULL`, 13 / 13 |
| #45 429 + shared Observatory state | no | n/a | `FULL`, 13 / 13 |
| #31 Peace Bridge + global portal | no | n/a | `FULL`, 13 / 13 |
| #9 latent-timing science | no | n/a | `FULL`, 13 / 13 |

### Why PR #51 matters

The first live shadow probe exposed a real second-order mismatch:

```text
router island       scripts/http_429_*
dedicated triggers explicit narrower path lists
```

The new probe script was therefore recognizable as "429" by the router without
being guaranteed to start a source-proximate 429 workflow.

The hardened router now treats that exact historical path set as a negative
regression and fails closed to the full public-analysis matrix.

## Authority boundary

```text
candidate route != permission to skip
coverage PASS  != permission to skip
shadow PASS    != workflow optimization promoted
unknown        -> FULL
mixed surface  -> FULL
uncovered path -> FULL
```

The full public-analysis workflow remains authoritative during this phase.
Existing source-proximate promotion gates remain unchanged.

## Promotion path

Before any real skip proposal:

1. keep the full 13-job matrix running;
2. retain PR #51 as the uncovered-path negative regression;
3. obtain another **live isolated 429 PR whose entire path set has verified
   source-gate trigger coverage**;
4. compare its reduced candidate route with the still-executed full result;
5. investigate any failure the candidate route would have missed;
6. make job-skipping a separate, reversible promotion change;
7. unknown/mixed/uncovered paths remain permanently fail-closed.

This is observer-hygiene research, not a request to weaken evidence.
