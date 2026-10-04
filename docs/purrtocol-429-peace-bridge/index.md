# Purrtocol 429 Peace Bridge

> **Visualization != Evidence.**

PythonPaw and NodePaw are two independent standard-library implementations of
the same local HTTP 429 Survival Plane contract.

First frozen cross-language observation:

```text
shared scenarios     8
Python pass          8 / 8
Node pass            8 / 8
semantic parity      true
comparison errors    0
```

The bridge metaphor encodes:

```text
operation_id  stays stable
attempt_id    changes
429           means backpressure
Retry-After   is a floor
UNKNOWN POST  means re-observe unless an explicit idempotency contract exists
retry budget  is bounded
```

The page does not claim production-provider behavior or RFC certification.

Evidence source:

- [Frozen cross-language receipt](./reference.json)
- [Technical cross-language notes](../429-conformance-lab/cross-language.md)
- [HTTP 429 Survival Kit](../429-survival-kit/)
