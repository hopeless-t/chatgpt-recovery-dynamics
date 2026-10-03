# Provider-friendly recovery checklist

A compact operator/design checklist derived from the repository's observations,
models, and local simulations.

This is not a description of OpenAI internals.

## Client / edge

- [ ] One logical conversation recovery has one retry owner.
- [ ] Multiple local tabs/windows coalesce recovery work.
- [ ] Fast failure does not shorten start-to-start retry spacing.
- [ ] 429 / Retry-After increases or preserves spacing.
- [ ] Retry-After is treated as a lower bound, not a jitter center.
- [ ] Herd jitter is nonnegative after server-directed timing floors.
- [ ] Retry budget is bounded.
- [ ] First successful observation enters Recovering, not Healthy.
- [ ] Stable confirmation is required before backoff/failure history is reset.
- [ ] Last-known-good readable UI is preserved while recovery is uncertain.
- [ ] Cheap state/version observation happens before full materialization.
- [ ] Full snapshot is fetched once per stable recovery epoch when possible.
- [ ] Delta/conditional synchronization is preferred when sufficient.
- [ ] Transport failure triggers re-observation, not blind re-execution.

## Frontend / admission

- [ ] Queue size is bounded.
- [ ] Overload is rejected early and cheaply.
- [ ] Recovery traffic has an explicit work budget.
- [ ] Foreground useful work is protected during real saturation.
- [ ] Cheap recovery observations cannot be starved indefinitely.
- [ ] Expensive snapshots cannot monopolize capacity.
- [ ] Admission reasons are visible in metrics.
- [ ] Retry guidance is explicit enough for clients to reduce pressure.
- [ ] Duplicate same-conversation work is coalesced when feasible.
- [ ] Hot users/conversations cannot consume an unbounded share.

## Work-aware scheduling

Do not assume every request has equal cost.

Track approximate cost dimensions such as:

~~~text
request count
bytes transferred
CPU time
database/cache work
memory footprint
materialization cost
fan-out
~~~

A conceptual request cost is:

~~~text
c_i =
    w_request
  + w_bytes * bytes_i
  + w_cpu * cpu_i
  + w_db * db_i
  + w_memory * memory_i
~~~

The exact weights are deployment-specific.

## Deadline and cancellation hygiene

- [ ] Client deadlines propagate through backend work where appropriate.
- [ ] Work that is no longer useful can be cancelled before expensive completion.
- [ ] A stale queued snapshot is not completed merely because it entered the queue first.
- [ ] Late/older snapshot responses cannot overwrite newer reconciled state.
- [ ] Recovery operations are idempotent or have stable logical identities.

This matters because overload can otherwise spend scarce capacity finishing work
whose client has already retried or moved on.

## Adaptive concurrency

Static rate limits are not the only possible control.

A service may also cap in-flight expensive work and adapt the cap based on
observed latency/queue pressure.

Conceptually:

~~~text
if queue_delay rises:
    concurrency_limit decreases

if service is stable and queue_delay is low:
    concurrency_limit increases cautiously
~~~

The repository does not prescribe a production algorithm.

The design goal is to keep the system away from the high-latency positive
feedback region rather than discovering overload only after queues are deep.

## Graceful degradation ladder

A provider-friendly degradation order is:

~~~text
Healthy:
  normal recovery path

Pressure:
  single-flight
  cheap observe
  start anchoring
  jitter

High pressure:
  stronger backoff
  snapshot budget
  bounded queues
  coalescing

Saturation:
  foreground-first
  defer expensive recovery materialization
  preserve stale-but-readable UI
  shed reconstructible/background work

Recovery:
  provisional success
  stable confirmation
  materialize once
  reattach realtime
~~~

## Fairness

A popular service should avoid letting one hot key dominate.

Possible fairness scopes include:

~~~text
account/user
conversation
project/workspace
client session
request class
backend shard
~~~

Fairness and rate-limit scope are deployment decisions.

The repository deliberately does not infer which scope OpenAI uses.

## Metrics to expose internally

Useful operator metrics for this failure family would include:

~~~text
base foreground offered work
recovery offered work
retry amplification
recovery attempts per logical recovery
duplicate/coalesced recovery requests
full snapshot materializations
cheap observation requests
queue work by class
queue delay by class
429 / overload rejection rate
Retry-After distribution
recovery time to stable Healthy
E/Recovering rebound rate
bytes per successful recovery
cancelled stale work
~~~

These metrics make it possible to distinguish:

~~~text
not enough capacity
vs
avoidable duplicate work
vs
bad retry control
vs
expensive recovery representation
vs
transport instability
~~~

## Transport

Use transport features to improve survival and efficiency, not to store
canonical truth.

Suggested profile:

~~~text
HTTP/2      default multiplexed request path
HTTP/1.1    correctness-preserving fallback
HTTP/3      optional migration/path-survival acceleration
WebSocket   optional realtime observation/notification
~~~

Application state remains recoverable without requiring one particular
connection to survive.

## Research safety

- [ ] No intentional production retry storms.
- [ ] No deliberate production 429 generation.
- [ ] No rate-limit bypass.
- [ ] No raw authenticated HAR publication.
- [ ] Overload experiments run locally.
- [ ] Public reports retain provenance and uncertainty.
- [ ] Simulation parameters are never presented as OpenAI production values.

See [RESPONSIBLE_TESTING.md](../RESPONSIBLE_TESTING.md).

## Design principle

The central provider-friendly rule is:

> **Do the least expensive observation that can answer the current question,
> and do expensive reconstruction only once the system has evidence that it
> will be useful.**


## Standards-aware client reference

See [HTTP 429 Survival Kit](429-survival-kit/index.md) for the stable-RFC vs
active/expired-draft boundary, retry authorization, and executable scenarios.
