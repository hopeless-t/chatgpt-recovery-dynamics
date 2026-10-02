# DCS-inspired model

## Motivation

A common debugging shortcut is to assign one global state:

```text
WORKING / BROKEN
```

The observed capture is more naturally described by partially independent state variables.

## State vector

We model the client-visible system as:

`x_t = (C_t, A_t, O_t, R_t, L_t, U_t)`

where:

- `C_t` — canonical conversation availability
- `A_t` — snapshot accessibility
- `O_t` — stream/realtime observability
- `R_t` — recovery/resume attachment
- `L_t` — request/rate-limit pressure
- `U_t` — user-visible utility

The term *dissociated control state* is used here in a systems-engineering sense: sub-systems can occupy different operational states at the same time.

It is **not** a clinical or psychological claim.

## Hypothesis H1 — state dissociation

A successful snapshot and failed resume can coexist.

Therefore:

`Observed UI failure != proof of canonical data loss`

and:

`Global state != uniform subsystem state`

## Hypothesis H2 — recovery amplification

Let retry intensity be:

`lambda_t = lambda_0 + k * (1 - O_t)`

If observability falls, the client attempts recovery more aggressively.

Let request pressure evolve as:

`L_(t+1) = rho * L_t + alpha * lambda_t - delta`

and rate limiting occur with:

`P(429) = sigmoid(L_t - theta)`

Then a failed observation/recovery path can create:

```text
O down -> lambda up -> L up -> A down -> O down
```

This is the core positive-feedback hypothesis.

## Hypothesis H3 — fast-fail feedback gain

In the capture, blocked snapshot attempts had a median latency of ~326 ms versus ~5.10 s when accessible.

Fast failure shortens the time before a retry controller can act again. Even if the controller uses the same logical policy, the effective loop gain can increase because failure feedback arrives much sooner.

This creates a second amplification path:

`failure latency down -> controller cycles faster -> request pressure up`

## Hypothesis H4 — metastable blocked regime

The observed estimate

`P(B_(t+1) | B_t) ~= 0.847`

suggests state persistence.

Short one-observation accessible excursions inside longer blocked periods are compatible with a metastable regime in which the system intermittently crosses the accessibility boundary without converging to a stable recovered state.

## Competing causal models

### M1: rate-limit-first

```text
429
 -> snapshot inaccessible
 -> recovery fails
 -> UI remains stale/unavailable
```

### M2: recovery-first

```text
recovery/resume anomaly
 -> repeated observation/retry
 -> request pressure rises
 -> 429
 -> recovery becomes harder
```

The two observed resume-404 episodes preceded the first later snapshot-429 by 349.013 s and 87.853 s respectively, with successful snapshots in between.

That ordering is compatible with M2, but it is not sufficient to reject M1 globally. A 404 may also be a normal response for a state that cannot or need not be resumed.

## Falsification / replication

Useful tests include:

1. Does recovery anomaly consistently precede retry-rate acceleration?
2. Does retry cadence predict transition into the blocked regime?
3. Does blocking persist after user-driven activity stops?
4. Does conversation size change the transition hazard?
5. Do native clients have different transition matrices from web/PWA?
6. Do independent captures show the same `(stream_status, snapshot)` coupling?

The model should be updated or rejected if independent traces contradict these predictions.
