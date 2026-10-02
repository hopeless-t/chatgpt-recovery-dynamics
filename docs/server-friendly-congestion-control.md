# Server-friendly congestion control

## Purpose

This document turns the client-side recovery findings into a **popular-server
overload design**.

The objective is deliberately provider-friendly:

> recover readable conversation state while adding as little avoidable work,
> queue growth, duplicate materialization, and retry amplification as possible.

This is an architecture proposal and stress model.

It does **not** estimate OpenAI's production request rate, capacity, queue
length, rate-limit scope, infrastructure, or implementation.

---

## 1. The capacity problem

Let:

~~~text
lambda_0(t) = exogenous foreground request/work arrival rate
lambda_r(t) = recovery/retry arrival rate
C(t)        = service capacity
~~~

Then the effective offered load is:

~~~text
lambda_eff(t) = lambda_0(t) + lambda_r(t)
~~~

For heterogeneous requests, count work rather than raw requests:

~~~text
A(t) = sum_i c_i
~~~

with abstract request cost:

~~~text
c_i =
    w_request
  + w_bytes * bytes_i
  + w_cpu * cpu_i
  + w_db * db_i
  + w_memory * memory_i
~~~

A convenient base-load ratio is:

~~~text
rho = foreground_offered_work / nominal_capacity
~~~

The critical distinction is that this rho is defined **before recovery
traffic**.

A system at rho = 0.98 has very little headroom even if ordinary foreground
traffic still appears healthy.

No retry algorithm can create missing capacity when sustained useful work
already exceeds service capacity.

---

## 2. Retry amplification

The local capture showed completion-coupled cadence amplification:

~~~text
Delta ~= 5.616 + 0.957 * service_time
~~~

so fast failure can shorten the observation cycle.

At server scale, retry traffic changes the capacity equation:

~~~text
rho_eff =
    (foreground_work + retry_work)
    / capacity
~~~

A small foreground error rate can therefore create a much larger effective load
if every failure causes one or more quick retries.

Define recovery amplification:

~~~text
R_amp =
    recovery_network_attempts
    / logical_recovery_conversations
~~~

The server-friendly objective is not merely to reduce 429 count.

It is to keep R_amp bounded while preserving useful foreground work.

---

## 3. Bounded queue dynamics

A simple discrete work-queue model is:

~~~text
Q_(t+1) =
    max(
        0,
        Q_t + A_t - C_t
    )
~~~

An infinite queue is not a resilience feature.

When the server cannot sustain incoming work, queue growth converts overload
into:

- memory consumption;
- latency inflation;
- expired/dead work;
- user refresh/retry traffic;
- further positive feedback.

The proposal therefore uses bounded admission:

~~~text
accept_i =
    1
    if Q_t + c_i <= Q_max
    else 0
~~~

with error-aware feedback to the client.

HTTP 429 may include Retry-After; RFC 6585 explicitly permits this and leaves
the server free to define the counting scope.

Reference:
https://www.rfc-editor.org/rfc/rfc6585.html

---

## 4. Provider-friendly control stack

The ordering matters.

### Layer A — suppress duplicate work at the source

~~~text
many local tabs/windows
        |
        v
one per-conversation recovery owner
~~~

Single-flight/coalescing is preferred to accepting duplicate work and trying to
schedule it efficiently later.

The cheapest server request is the duplicate request never sent.

### Layer B — observe cheaply before materializing

~~~text
small state/version observation
        |
        +-- still unavailable -> bounded retry
        |
        +-- provisional success -> Recovering
        |
        +-- stable success -> snapshot/delta only if required
~~~

Repeated multi-MiB snapshot materialization should not be the health check.

### Layer C — server-directed retry spacing

On overload/throttling:

~~~text
next_start =
    max(
        previous_start + normal_period,
        Retry-After,
        local_backoff_with_jitter
    )
~~~

A client should not convert a fast 429 into a higher request rate.

Jitter prevents synchronized clients from returning as a new herd.

### Layer D — small queues and early load shedding

Once useful work exceeds sustainable capacity:

~~~text
cheap early rejection
    >
long queue
    >
late failure after expensive work
~~~

This follows the general overload principle that a server should protect itself
from queues that only add latency and memory pressure.

### Layer E — protect useful foreground work

Recovery traffic is important, but during genuine saturation it is usually
better to preserve active useful work and defer background/reconstructible
recovery work.

The emergency mode is therefore:

~~~text
foreground first
cheap recovery probes allowed in a tiny bounded lane
expensive recovery snapshots use residual capacity
~~~

This is graceful degradation, not recovery failure.

### Layer F — cost-aware admission

A 4 KiB version probe and a multi-MiB snapshot need not have the same server
work cost even when both are one HTTP request.

Where the implementation exposes useful cost signals, admission/scheduling
should reason about work rather than only request count.

The repository deliberately tests both limiting cases:

~~~text
request-count dominated
byte/work dominated
~~~

because the production weights are unknown.

---

## 5. Five stress-test policies

The simulator compares:

### P0 — naive_completion

- each tab/window may recover independently;
- full snapshot attempts;
- 6 s completion-coupled retry;
- no jitter/coalescing.

### P1 — retry_after_jitter

- full snapshot attempts remain;
- server-directed approximately 10 s retry spacing;
- jitter reduces synchronization.

### P2 — singleflight_observe

- one recovery owner per logical conversation;
- cheap observation;
- two successful observations before stable recovery;
- one snapshot materialization.

### P3 — server_friendly_stack

P2 plus:

- bounded per-class and global queues;
- tiny observation lane;
- foreground-priority scheduling;
- small recovery snapshot reserve;
- bounded admission.

### P4 — foreground_first

Emergency overload mode:

- bounded cheap probes remain;
- foreground traffic consumes capacity first;
- expensive recovery snapshots use only residual capacity.

P4 intentionally trades recovery latency/completion for foreground protection.

---

## 6. Pressure-knee experiment

The simulator varies base foreground load:

~~~text
rho =
0.70, 0.80, 0.90, 0.95,
0.98, 1.00, 1.05, 1.10
~~~

before adding recovery traffic.

For every rho/policy it records:

~~~text
foreground success fraction
foreground p95 latency
recovery completion fraction
recovery p95 time
recovery request count
recovery rejection count
retry amplification
recovery payload
maximum queued work
duplicate recovery work
~~~

The conservative sampled operational knee is the first rho where either:

~~~text
foreground success < 0.99
OR
recovery completion < 0.99
~~~

This is an engineering threshold, not a claim about a production SLO.

---

## 7. CI reference results

The GitHub Actions reference run uses 12 common-world trials per rho/policy.

At base rho = 0.90:

| Policy | Retry amplification | Recovery payload | Recovery rejects | Foreground p95 |
|---|---:|---:|---:|---:|
| naive completion | **18.54x** | 847.4 MiB | 1298.2 | 2.0 s |
| Retry-After + jitter | 6.24x | 474.2 MiB | 395.9 | 2.0 s |
| single-flight + observe | 4.16x | **366.6 MiB** | 92.8 | 2.0 s |
| server-friendly stack | **3.98x** | **366.6 MiB** | **78.3** | **1.0 s** |

At base rho = 0.98:

~~~text
naive:
  foreground success  = 0.9869
  retry amplification = 45.42x
  recovery rejects    = 3464.5

server-friendly:
  foreground success  = 0.9921
  retry amplification = 6.04x
  recovery rejects    = 243.3
~~~

At base rho = 1.00:

~~~text
naive recovery completion          = 0.8896
server-friendly recovery completion = 1.0000

naive retry amplification          = 62.91x
server-friendly retry amplification = 7.49x
~~~

The sampled operational knee moves from:

~~~text
naive completion:       rho ~= 0.98
provider-friendly paths: rho ~= 1.00
~~~

under the conservative threshold used by this simulator.

This should not be read as a production capacity claim.

It means that, in this abstract model, avoidable recovery traffic consumes
enough spare capacity to move the failure knee earlier.

At rho = 1.05 the base foreground demand itself exceeds nominal capacity. The
simulator then shows the fundamental limit:

~~~text
no retry policy restores 100% foreground service
~~~

The correct response is graceful degradation / load shedding, not more retries.

Reference JSON:
[data/server_congestion_reference.json](../data/server_congestion_reference.json)

---

## 8. Main qualitative result

The simulator is designed to test a simple proposition:

> overload protection works best when avoidable recovery work is removed
> **before** it reaches the expensive server path.

At high but sub-saturation load, the expected ordering is:

~~~text
naive completion
    > Retry-After + jitter
    > single-flight + cheap observation
    >= bounded server-friendly scheduling
~~~

when the metric is retry amplification / unnecessary recovery work.

Server scheduling is still valuable, but it cannot recover capacity already
consumed by duplicated client traffic.

At rho >= 1, the simulation intentionally refuses to produce a magic answer:

~~~text
sustained foreground demand >= nominal capacity
=> some work must wait, degrade, or be shed
~~~

The server-friendly choice is then to preserve the highest-value useful work
and defer reconstructible recovery.

---

## 9. Why this is friendly to the provider

The proposed design minimizes avoidable provider work in several places:

~~~text
duplicate tabs
    -> single-flight

failure detection
    -> tiny observe request

first success
    -> Recovering, not immediate repeated materialization

stable recovery
    -> one snapshot/delta

429
    -> explicit spacing, not fast retry

true overload
    -> bounded queue + early shedding

foreground saturation
    -> defer expensive recovery work
~~~

This also improves the client's odds: a recovery loop that does not amplify
server pressure is less likely to make its own recovery environment worse.

---

## 10. Transport is secondary to congestion semantics

HTTP/2 and HTTP/3 can improve transport behavior, multiplexing, and path
survival.

They do not change the capacity identity:

~~~text
offered work > service capacity
=> overload
~~~

Therefore the priority order is:

~~~text
1. suppress duplicate/retry work
2. cheap observation
3. server-directed backpressure
4. bounded admission / load shedding
5. cost-aware scheduling
6. transport acceleration
~~~

not the reverse.

---

## 11. Operational safety

This repository does **not** recommend load-testing ChatGPT or any production
OpenAI endpoint.

All overload experiments are local simulations.

Replication against a production service should remain observational and
passive unless the service operator explicitly authorizes active load testing.

That is part of the provider-friendly design.

---

## Reproduce

~~~bash
python3 scripts/simulate_server_congestion.py
~~~

Faster CI-style run:

~~~bash
python3 scripts/simulate_server_congestion.py \
  --trials 12 \
  --output /tmp/server-congestion.json
~~~

See also:

- [transport/recovery redesign](transport-recovery-redesign.md)
- [mathematical model](model.md)
- [recovery design](recovery-design.md)
