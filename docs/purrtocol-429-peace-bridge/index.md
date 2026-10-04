# Purrtocol 429 Peace Junction

> **Visualization != Evidence.**

PythonPaw, NodePaw, and GoPaw visualize three standard-library implementations
of the same local HTTP 429 Survival Plane semantics.

The evidence remains split into two chronological frozen receipts rather than
being retroactively rewritten as a single three-runtime cohort:

```text
Python / Node
  shared scenarios     8
  semantic parity      true
  comparison errors    0

Python / Go
  shared scenarios     8
  semantic parity      true
  comparison errors    0
  observed Go runtime  go1.24.13 linux/amd64
```

The junction metaphor encodes:

```text
operation_id  stays stable
attempt_id    changes
429           means backpressure
Retry-After   is a floor
UNKNOWN POST  means re-observe unless explicit idempotency semantics exist
retry budget  is bounded
transport error names are implementation-specific
```

The visualization does not claim production-provider behavior, capacity, or
formal RFC certification.

Evidence sources:

- [Frozen Python/Node receipt](./reference.json)
- [Frozen Python/Go receipt](./go-reference.json)
- [Tri-runtime technical notes](../429-conformance-lab/tri-runtime.md)
- [HTTP 429 Survival Kit](../429-survival-kit/)
