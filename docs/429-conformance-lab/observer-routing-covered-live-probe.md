# MIL-004 covered live observer-routing specimen

> Status: LIVE SHADOW PROBE / NO JOB SKIPPING

This pull request intentionally changes **only this file**.

The path is inside the HTTP 429 safe island:

```text
docs/429-conformance-lab/**
```

and is also explicitly covered by the current `pull_request.paths` of:

```text
.github/workflows/validate-http-429-conformance.yml
```

The hardened observer router should therefore report:

```text
safe island match            true
source-gate trigger coverage true
route                        http-429-isolated
candidate jobs               1 / 13
candidate job                repository-surface
execution authority          false
jobs actually skipped        false
```

Python compatibility jobs are not candidates because this PR changes no Python
file.

## Paired observation rule

Even if the router emits the expected 1/13 candidate set, the full 13-job
`Validate public analysis` workflow remains authoritative for this specimen.

The paired observation is acceptable only if all of the following are green on
the same head:

- full 13-job public-analysis matrix;
- `Repository Observatory`;
- `Meta Improvement Loop`;
- source-proximate `Validate HTTP 429 Local Conformance Lab`.

A green result is still **not** permission to skip jobs. It is one positive live
specimen after the PR #51 uncovered-path negative regression.

## Claim boundary

This probe changes no retry semantics, sends no production traffic, and creates
no provider-specific claim.
