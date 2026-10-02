# ADR-0003: Provider-friendly recovery is the default design objective

- Status: Accepted
- Date: 2026-10-03

## Context

A recovery loop can become part of the incident if failed requests create duplicate retries, repeated multi-MiB snapshot materialization, deep queues, or synchronized client herds.

Local stress simulations show that avoidable recovery traffic can move a sampled overload knee earlier.

## Decision

The default recovery design optimizes for both user recovery and lower provider work.

Priority order:

~~~text
1. suppress duplicate recovery
2. cheap observation
3. server-directed spacing / Retry-After
4. one retry owner + jitter
5. bounded admission / load shedding
6. protect useful foreground work during saturation
7. transport acceleration last
~~~

No production OpenAI endpoint is to be load-tested for this repository.

## Consequences

- Fastest retry is not the primary objective.
- A small observation can be preferable to an expensive snapshot.
- True saturation is handled through graceful degradation rather than pretending retry policy can create capacity.
