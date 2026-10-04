# Tri-runtime HTTP 429 conformance

> Status: GO OBSERVATION PENDING

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
