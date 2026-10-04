# Cross-language HTTP 429 conformance

> Status: FIRST CROSS-LANGUAGE BASELINE OBSERVED

NET-429-001 now has two independent standard-library implementations:

- Python reference implementation
- Node.js independent implementation

They share only the repository contract and scenario JSON.

The Node implementation does **not**:

- import the Python scheduler;
- invoke the Python scheduler;
- use third-party retry packages;
- accept remote target URLs;
- generate production traffic.

Both implementations run the same eight loopback scenarios.

After both reports are produced, a separate comparator checks semantic parity for:

- terminal recovery action;
- start-to-start retry timing;
- Retry-After floor behavior;
- experimental RateLimit zero-window hint behavior;
- bounded retry budget;
- UNKNOWN non-idempotent POST -> REOBSERVE;
- stable `operation_id` across authorized retries;
- changing `attempt_id`;
- side-effect counts under the explicit lab idempotency contract.

Implementation-specific transport error names and descriptive classification labels
are intentionally excluded from equality.

The first CI run is observation-before-freeze. This document does not claim
cross-language parity until the observed result is read and frozen.

Passing this experiment would mean:

> two independent implementations reproduced the same repository contract
> semantics in the shared local fire drill.

It would **not** mean:

- universal provider behavior;
- production reliability;
- formal RFC certification;
- absence of all retry amplification bugs;
- proof about any particular service's internal limiter.


## First observed result

Source:

```text
workflow run 37192562631
job          111407652075
head         6e8547c1c5dceacd3d1824ad7fd1f4e26e0f8635
Node         24.21.0
```

Observed:

```text
shared scenarios            8
Python pass                 8 / 8
Node pass                   8 / 8
semantic parity             true
comparison errors           0
absolute float tolerance    1e-9
```

Implementation-specific transport error names and descriptive classification
labels were intentionally excluded from semantic equality.

The first cross-language baseline therefore supports:

> **The repository's HTTP 429 Survival Plane semantics are reproducible across
> two independent standard-library implementations in the shared loopback lab.**

This remains local/mock evidence.

It does not establish provider behavior, production reliability, or formal RFC
certification.

Frozen receipt:

- `data/http_429_cross_language_reference.json`
