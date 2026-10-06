# Purrtocol Connection Amplification Model / 接続増幅モデル

Status: **bounded model / simulation — not provider topology evidence**

This model asks a different question from transfer-size measurement:

> When failures trigger more attempts and each attempt opens more connections, can recovery work itself exhaust shared connection capacity?

The model is motivated by the public 2026-09-29 OpenAI cross-product incident and its reported postmortem shape, but does **not** claim to reproduce OpenAI's exact topology, retry policy, traffic rate, connection lifetime, or capacity.

## State variables

For a scenario:

- `lambda`: baseline request rate, requests/second
- `C`: shared concurrent connection capacity
- `d`: finite maximum retry depth

For each recovery policy:

- `f`: connections opened per attempt
- `p`: probability an attempt takes the failure branch
- `r`: expected retry/check multiplier after a failed attempt
- `tau`: mean connection hold time in seconds
- `B`: payload bytes, diagnostic only
- `s_local`: local success probability, diagnostic only

Define the retry branch factor:

```text
a = p * r
```

The model never assumes an infinite retry tree. With explicit finite depth `d`:

```text
M_d = sum(k=0..d) a^k
attempt_rate = lambda * M_d
connection_open_rate = attempt_rate * f
expected_concurrent_connections = connection_open_rate * tau
utilization = expected_concurrent_connections / C
```

If expected concurrent connections exceed `C`, the global connection-capacity gate fails.

## Why finite depth matters

When `a >= 1`, an infinite geometric extrapolation diverges. Real systems still have budgets, timeouts, queue bounds, process death, cancellation, circuit breakers, or finite observation windows. This model therefore always caps the retry tree and labels `a >= 1` as `NON_DECAYING_BOUNDED` rather than pretending an infinite result is an operational measurement.

## Anti-Goodhart scenario

CI compares two synthetic policies under the same request rate and shared capacity:

- **small-local-hero**: smaller payload and higher local success probability, but high fanout and non-decaying retry amplification,
- **larger-global-safe**: larger payload and lower local success probability, but bounded retry work and low connection occupancy.

The intended counterexample is:

```text
smaller payload + better local success
        DOES NOT imply
safer system-wide recovery
```

At retry depth 0 the aggressive policy can still fit inside shared capacity. With repeated failure-triggered work enabled, the same baseline traffic can exceed capacity. That delta is the modeled **recovery amplification**.

## Evidence boundary

- OpenAI incident existence and cross-product impact: public official status observation.
- Detailed repeated-background-check / connection-exhaustion mechanism: reported public postmortem description supplied for review; keep the linked research case's evidence label until independently re-fetched.
- Equations, scenario values, thresholds, and synthetic policies here: **modeled/simulated**.

## World laws

```text
Failure != permission to amplify work.
Recovery traffic can become outage traffic.
Smaller payload != globally safer recovery.
Higher local success != global safety.
Finite model != exact production topology.
Capacity gate before local optimization.
Recover. Don't amplify.
```
