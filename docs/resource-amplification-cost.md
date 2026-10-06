# Recovery traffic as resource amplification

## Motivation

This repository already models retry amplification as a reliability and congestion problem. The same mechanism is also a resource-efficiency problem:

> **Every avoidable retry can duplicate network transfer, request handling, parsing, inference-adjacent work, logging, cache activity, and downstream cooling/energy demand.**

The useful optimization target is therefore not only recovery completion probability. It is successful stable recovery per unit of avoidable work.

## Core distinction

```text
external demand
!=
recovery work
!=
retry/rework amplification
```

A provider may need to serve the external demand. The avoidable surface is the internally generated amplification caused by duplicate attempts, full-materialization probes, ambiguous-result replay, and multiple concurrent retry owners.

## Candidate accounting envelope

```text
RecoveryResourceEnvelope {
  recovery_episode_id
  observation_attempts
  materialization_attempts
  duplicate_attempts_suppressed
  payload_bytes
  request_count
  retry_amplification
  stable_recovery
  time_to_stable_recovery
  estimated_or_measured_resource_cost
  provenance
}
```

`estimated_or_measured_resource_cost` must remain explicitly unknown unless a calibrated measurement path exists. Request count or transferred bytes are proxies, not joules.

## Resource-saving mechanisms already implied by the recovery design

### Single-flight ownership

One retry owner prevents many clients/components from independently repeating the same recovery operation.

### Observe before materialize

A cheap health/state probe should precede a full conversation snapshot when the system can answer the recovery question without materializing the larger payload.

### Re-observe before re-execute

After an ambiguous result, query durable state before replaying a non-trivial operation. This converts uncertainty into observation instead of automatic duplicate work.

### Retry-After + jitter + bounded cadence

Spacing attempts reduces synchronized bursts and avoids converting fast failures into a higher request rate.

### Stable recovery confirmation

A single success after a blocked state is provisional. Avoid expensive foreground restoration until a bounded confirmation criterion is met.

## Candidate normalized metrics

Track these beside the existing completion and congestion metrics:

- requests per stable recovery;
- payload bytes per stable recovery;
- duplicate requests suppressed;
- full snapshots avoided;
- re-executions avoided by observation;
- recovery latency;
- retry amplification;
- completion probability under fixed foreground load.

A useful derived measure is:

```text
stable recoveries / recovery traffic bytes
```

but it must not reward under-observation that lowers traffic by missing real failures.

## Research hypothesis CRD-RES-01

Under the same failure-state trace and stable-recovery oracle, the provider-friendly stack should reduce avoidable request/payload amplification relative to naive completion-coupled retries without lowering stable recovery probability.

## Research hypothesis CRD-RES-02

If recovery becomes cheaper, clients may attempt recovery more often. Therefore per-episode savings do not guarantee lower total provider load. Simulations should sweep episode arrival rate and user retry behavior to detect rebound.

## Experiment extension

For the existing popular-server congestion model, add an accounting table for each policy:

```text
policy
  requests
  payload MiB
  duplicate work
  stable recoveries
  requests / stable recovery
  MiB / stable recovery
```

Run the same `rho` sweep already used by the repository. Do not claim production energy or water savings from this simulation.

## Cross-project bridge

This lane connects naturally to:

- `next-generation-github`: canonical operation identity, delta transport, re-observation before re-execution, and resource envelopes;
- `finite-ram-lab`: working-set and residency cost of repeated materialization;
- `market-microcosm-lab`: rebound effects when cheaper recovery encourages more recovery demand.

## Boundary

This is a resource-accounting extension to the existing recovery model. It does not identify OpenAI infrastructure behavior and does not authorize active load testing against production services.

> **Recover. Don't amplify. And measure the amplification you avoid.**
