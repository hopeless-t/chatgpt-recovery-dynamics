# MIL-004 live 429 observer-routing specimen

> Status: SHADOW ONLY / NO JOB SKIPPING

This pull request is the first live isolated-429 specimen for the public-analysis
observer router.

The changed Python probe reads only frozen local conformance receipts. It sends
no traffic and changes no retry semantics.

Expected shadow route:

```text
route                 http-429-isolated
candidate jobs        4 / 13
candidate avoided     9 / 13
execution authority   false
jobs actually skipped false
```

The full 13-job public-analysis matrix remains authoritative and is expected to
run on the same pull request.

## Trigger-coverage observation

The first live run exposed a second-order mismatch:

```text
router safe island      scripts/http_429_*
existing source gates   explicit 429 path lists
```

The new probe filename was inside the router's safe island but did not itself
match a dedicated HTTP 429 workflow trigger.

This document intentionally lives under `docs/429-conformance-lab/**`, which is
already monitored by the loopback conformance workflow, so the paired live
specimen can include a source-proximate 429 gate.

This does **not** close the trigger-coverage issue.

Before any real public-analysis skipping is proposed, MIL-004 must add a
machine-checkable condition equivalent to:

> every path accepted by a reduced observer route is covered by the required
> source-proximate promotion gates.

Until that inclusion is established, the router remains advisory and
`jobs_actually_skipped=false`.

## Claim boundary

A green live specimen means only that the candidate route did not miss a
failure in this one paired observation while the full matrix still ran.

It does not establish zero false negatives or grant CI-skipping authority.
