# Responsible testing

This repository is intended to help reduce avoidable recovery load and improve
conversation-state resilience.

It is **not** a load-testing toolkit for ChatGPT or any other production
service.

## Rules

### 1. Do not actively load-test production OpenAI services

Do not use these scripts to generate high request rates, retry storms, synthetic
429s, or coordinated recovery traffic against ChatGPT, the OpenAI API, or other
production endpoints unless the service operator has explicitly authorized the
test.

The congestion experiments in this repository are local simulations.

### 2. Do not bypass rate limits or backpressure

A 429, Retry-After value, server-directed delay, or other throttling signal
should be treated as a request to reduce pressure.

Do not modify the research tools to evade or defeat those controls.

### 3. Prefer passive observation

For real-service investigation, prefer:

- ordinary user-driven interaction;
- already-occurring failures;
- passive browser/network observation;
- sanitized derivative telemetry.

Do not create artificial production incidents in order to collect a cleaner
trace.

### 4. Never publish raw HAR files from authenticated sessions

Raw HAR files can contain sensitive session/account material.

The repository publishes only sanitized derivative event classes and aggregate
measurements.

Review all derivative outputs manually before sharing them.

### 5. Preserve uncertainty

Do not present:

- an inferred rate limiter as a known production limiter;
- a local simulation capacity as OpenAI capacity;
- a Reddit/Hacker News report as verified server telemetry;
- a client-visible HTTP/transport symptom as proof of backend root cause.

Keep observed facts, compatible mechanisms, simulations, and design proposals
separate.

### 6. Optimize for less provider work

When comparing recovery designs, prefer designs that reduce avoidable:

- duplicate requests;
- retry amplification;
- full snapshot materialization;
- queued work;
- bytes transferred;
- server-side recomputation;
- synchronized client herds.

### 7. Fail closed on ambiguous logical work

Transport ambiguity should trigger re-observation of durable state, not blind
re-execution of a mutating operation.

### 8. Share reproducible, non-sensitive evidence

Useful contributions include:

- sanitized event timelines;
- independent reproductions of timing laws;
- local simulator improvements;
- model falsification;
- alternative recovery state machines;
- public historical reports with provenance and caveats.

## Research intent

The constructive question is:

> How can a client recover more reliably while making a popular service do less
> unnecessary work?

That is the design target for this repository.
