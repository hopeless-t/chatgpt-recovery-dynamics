# Tri-runtime HTTP 429 conformance

> Status: FIRST GO BASELINE OBSERVED

NET-429-001 already has a frozen Python/Node semantic-parity baseline.

This experiment adds a third implementation written in Go using only the Go
standard library.

The Go implementation:

- does not import or invoke the Python implementation;
- does not import or invoke the Node implementation;
- uses no third-party retry package;
- binds only to 127.0.0.1 on an ephemeral port;
- accepts no production target;
- generates no production traffic.

Shared inputs remain the contract/scenario data, not executable retry code.

The same eight local fire drills are executed.

The existing comparator is intentionally generalized so the already frozen
Python/Node output remains backward-compatible while a second comparison checks
Python/Go semantic parity.

This first run is observation-before-freeze. No Go parity result is asserted in
the source before CI observes it.

A pass would strengthen implementation-independence of the repository contract.
It would not establish universal provider behavior, production reliability, or
formal standards certification.


## First observed Go result

Source:

```text
workflow run 37194246111
job          111412674767
head         60d1750324492dea69d042efeb48386ee2ac8b0f
Go           go1.24.13 linux/amd64
```

Observed:

```text
shared scenarios        8
Go pass                 8 / 8
Python-Go parity        true
comparison errors       0
Python-Node baseline    still PASS
```

The intentionally dropped loopback responses surfaced as Go `EOF` transport
errors. Python/Node use different implementation-specific error names. Those
strings remain outside semantic equality.

Frozen Go receipt:

- `data/http_429_go_cross_language_reference.json`

The prior Python/Node receipt remains separately frozen and unchanged.
