# HTTP 429 Metamorphic Kitten Swarm

> Status: FIRST SWARM BASELINE OBSERVED

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


## First observed result

Source:

```text
workflow run 37195222630
job          111415574176
head         e0117110f371a8e903b5395c9ccf9d565042fdaa
artifact     11300686289
```

Observed:

```text
generated cases              30
runtime executions           90

Python                       30 / 30
Node                         30 / 30
Go                           30 / 30

Python / Node parity         true
Python / Go parity           true
comparison errors            0 / 0

scenario SHA-256
2886f662e1f635e0ded7195a0007390ae9f1786979eea7d81cb0153ae84c4f05
```

The generator is now run twice in CI and both outputs must be byte-identical.

Raw runtime report bytes are **not** frozen because intentionally dropped
loopback responses can include ephemeral local port numbers in implementation-
specific transport diagnostics. Those strings are outside semantic equality.

Frozen receipt:

- `data/http_429_metamorphic_reference.json`
