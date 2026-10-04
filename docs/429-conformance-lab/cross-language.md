# Cross-language HTTP 429 conformance

> Status: FIRST OBSERVATION PENDING

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
