# Public Analysis Observer Routing / META-003

> Status: SHADOW OBSERVATION ONLY

The repository currently runs the full `Validate public analysis` workflow on
every pull request. That workflow launches 13 jobs, including three Python
compatibility jobs plus Monte Carlo, archaeology, transition, transport,
congestion, deep-validation, latent-timing, Purrtocol, repository-surface and
Recovery Helper checks.

Recent source-proximate HTTP 429 pull requests already had dedicated promotion
workflows, but the full 13-job public-analysis matrix still ran as well.

META-003 asks a narrower question:

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

That includes:

- unknown paths;
- science/model paths;
- shared Observatory state;
- global portal/discovery surfaces;
- mixed safe-island + shared-surface changes.

## Historical specimens

The predeclared regression set contains real PR path lists:

| PR | Classification | Candidate public-analysis jobs |
|---|---|---:|
| #47 429 composition metamorphic | `http-429-isolated` | 4 / 13 |
| #45 429 + shared Observatory state | `full-fail-closed` | 13 / 13 |
| #31 Peace Bridge + global portal | `full-fail-closed` | 13 / 13 |
| #9 latent-timing science | `full-fail-closed` | 13 / 13 |

PR #47 actually launched all 13 public-analysis jobs. Under the shadow policy,
9 of those jobs are candidate avoidable work. This is **not yet a measured
runtime saving**, because no job is skipped during META-003.

## Authority boundary

The router has no execution authority.

```text
candidate route != permission to skip
shadow PASS      != workflow optimization promoted
unknown          -> FULL
mixed surface    -> FULL
```

The full public-analysis workflow remains authoritative during the shadow phase.
Existing source-proximate promotion gates also remain unchanged.

## Promotion path

Before any real skip proposal:

1. run the router in shadow mode on live PRs;
2. compare every candidate route with the still-executed full result;
3. accumulate both isolated and fail-closed cases;
4. investigate any failure the candidate route would have missed;
5. keep unknown/mixed surfaces fail-closed;
6. make job-skipping a separate, reversible promotion change.

This is observer-hygiene research, not a request to weaken evidence.
