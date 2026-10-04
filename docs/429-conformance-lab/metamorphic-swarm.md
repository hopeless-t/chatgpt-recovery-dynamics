# HTTP 429 Metamorphic Kitten Swarm

> Status: FIRST SWARM OBSERVATION PENDING

The frozen eight-case conformance baseline is intentionally left unchanged.

This experiment expands the **input space**, not the historical reference.

A deterministic generator creates 30 loopback-only cases in five equal
families:

```text
Retry-After floor          6
fast-fail start anchor     6
draft zero-window hint     6
Retry-After precedence     6
bounded retry budget       6
                          --
                          30
```

The generated scenario file is ephemeral CI output and is not committed.

Promotion CI runs the same generated swarm through:

- Python standard library implementation
- Node standard library implementation
- Go standard library implementation

Then it compares:

- Python vs Node
- Python vs Go

Pass criteria:

- 30/30 scenarios pass in every implementation;
- both semantic comparisons have zero errors;
- generator family counts remain fixed;
- all logical operation IDs are unique;
- safety remains loopback-only with no production traffic.

This is metamorphic contract testing, not production load testing and not a
provider-behavior claim.

Preflight intentionally runs only generator + Python swarm in addition to the
existing base checks. Full three-runtime swarm execution stays in promotion CI
to limit observer cost.
