# MIL-004 coverage-aware live 429 shadow specimen

> Status: SHADOW ONLY / ZERO JOBS SKIPPED

This file is intentionally a documentation-only HTTP 429 lab change.

It exists to exercise the hardened public-analysis observer router after source-
gate trigger coverage became mandatory for reduced-route candidates.

## Why this path

`docs/429-conformance-lab/**` is:

1. inside the public-analysis router's narrow HTTP 429 safe island; and
2. explicitly covered by the pull-request trigger of the source-proximate HTTP
   429 local-conformance workflow.

The live router must therefore observe both:

```text
safe-island membership     true
source-gate coverage       true
```

Because this PR changes no Python source, the expected public-analysis shadow
candidate is deliberately tiny:

```text
candidate route            http-429-isolated
candidate public jobs      1 / 13
candidate job              repository-surface
candidate avoided jobs     12 / 13
execution authority        false
jobs actually skipped      false
```

## Paired-observation requirement

The candidate result is useful only if the same PR still runs and passes:

- all 13 jobs in `Validate public analysis`;
- the source-proximate HTTP 429 local-conformance workflow;
- Repository Observatory;
- Meta Improvement Loop.

No job is skipped in this experiment.

## Relationship to PR #51

PR #51 exposed the opposite specimen: a path could satisfy the broad
`scripts/http_429_*` naming island while lacking an actual source-workflow
trigger. The hardened router now keeps that historical path set FULL.

This PR tests the positive covered case on current main.

## Claim boundary

A green result will establish one coverage-aware live shadow specimen.

It will **not** establish:

- zero false negatives;
- measured CI runtime savings;
- permission to skip public-analysis jobs;
- universal optimality of the 1/13 candidate route.

Any execution-routing promotion must remain a separate reversible change.
