# Evidence and hypothesis ledger

This document separates what the repository directly observes from what it
infers, simulates, or proposes.

## Directly observed / reconstructed from the public trace

### O1 — paired Accessible / Blocked regimes

~~~text
108 pairs
48 Accessible
60 Blocked
0 mixed
max canonical pair skew = 9 ms
~~~

### O2 — fast-fail timing

Blocked snapshot latency is dramatically lower than Accessible snapshot latency.

### O3 — state persistence

Within active epochs:

~~~text
A -> A: 38
A -> B: 10
B -> A:  8
B -> B: 50
~~~

### O4 — history-dependent rebound

~~~text
B -> E -> B : 8
B -> E -> H : 0
~~~

### O5 — latency change point

The best one-change-point fit to service time equals the first Blocked
observation in both active epochs.

### O6 — temporal residual dependence

The cycle law leaves AR-like residual memory:

~~~text
phi ~= 0.524
~~~

and post-completion wait has:

~~~text
phi_W ~= 0.676
~~~

## Recomputed / robustness-checked

### R1 — pairing threshold

The canonical 108/48/60/0 pairing is stable from 10 ms through 100 ms.

### R2 — epoch threshold

The corrected transition matrix is stable from 20 s through 600 s.

### R3 — cross-epoch cycle-law prediction

A cycle law fitted on either active epoch predicts the other with about
0.25–0.26 s RMSE.

### R4 — cross-epoch history model

A Jeffreys-posterior H/E/B transition model trained on one epoch predicts the
other better than a first-order A/B model in both directions.

### R5 — numerical precision

The small timing regression is well conditioned and binary64 agrees with
high-precision recomputation at the displayed digits.

## Strong within-capture model evidence

### S1 — completion-coupled cadence amplification

Strongly supported as a description of observed cycle timing.

### S2 — provisional recovery state E

Strongly supported within the capture.

The first successful observation after Blocked behaves differently from
established Accessible state.

### S3 — one-step timing memory

Supported by BIC and persists after controlling for state and epoch.

A direct residual-model competition adds an important qualification:

~~~text
same-sample BIC:
  HMM-2  ~= -15.99
  AR(1)  ~= -10.10

cross-epoch held-out mean NLL:
  epoch 1 -> 2: AR(1) 0.0191  < HMM-2 0.3678
  epoch 2 -> 1: AR(1) -0.2203 < HMM-2 -0.0337
~~~

So a two-state Gaussian HMM compresses the pooled residuals better in-sample,
while AR(1) transfers better between the two active epochs in both directions.

This supports one-step predictive memory while weakening any temptation to name
the HMM's two statistical states as physical controller modes.

The physical implementation of this memory is unknown.

## Compatible causal hypotheses, not identified mechanisms

### C1 — retry pressure contributes to 429 persistence

Compatible with the trace and useful in stress models.

Not directly observed.

### C2 — byte/work-weighted recovery pressure

Useful alternative stress model.

Production rate-limit weights are unknown.

### C3 — slow latent capacity/headroom state

Motivated by epoch-level entry differences and pressure models.

Not observed directly.

### C4 — transport/recovery dissociation

Compatible with local trace and public reports.

The internal service architecture is unknown.

## Design proposals

### D1 — start-to-start retry anchor

Derived from observed healthy-cycle timing and Monte Carlo robustness.

### D2 — single-flight recovery owner

Reduces duplicate offered work in simulations.

### D3 — cheap observe before snapshot materialization

Reduces payload/materialization cost and is especially valuable when work cost
is not purely request-count based.

### D4 — recovery hysteresis

Directly motivated by B -> E -> B observations.

### D5 — bounded admission / load shedding

General provider-friendly overload design, tested in local server simulation.

### D6 — transport profile

~~~text
HTTP/2      baseline
HTTP/1.1    correctness-preserving fallback
HTTP/3      optional path-survival acceleration
WebSocket   optional realtime observation
~~~

Transport choice is not treated as canonical recovery truth.

## Weak external historical evidence

Reddit/Hacker News reports are retained as provenance-preserving archaeology.

They can:

- document recurrence;
- constrain overly simple explanations;
- motivate replication targets.

They cannot:

- establish production prevalence;
- identify a shared root cause;
- be treated as IID telemetry.

## Explicitly not established

The repository does not establish:

- OpenAI internal root cause;
- rate-limit scope;
- exact capacity;
- free-vs-paid traffic share;
- production HTTP version;
- production queue sizes;
- that resume 404 causes 429;
- that WebSocket failure initiates the problem;
- that the AR(1) residual state is a specific scheduler or timer;
- that the HMM's two latent states correspond to two physical controller/backend states;
- that local simulation parameters correspond to production values.

## Falsification priorities

The highest-value future evidence would be:

1. an independent capture reproducing the cycle law;
2. an independent capture reproducing B -> E -> B rebound;
3. a different client showing or rejecting the same residual timing memory;
4. passive evidence that request suppression changes or does not change
   recovery duration;
5. additional active epochs to test the repeated 34-observation morphology.

The model should be simplified or rejected when those observations disagree.

## Meta-observation: the research conversation itself hit 429

While this repository was being built and discussed, the author reported that
the active ChatGPT conversation used for the work itself encountered a
**429 / Too Many Requests** error.

Classification:

~~~text
source:
  contemporaneous author report during repository construction

status:
  real-world anecdotal meta-observation

included in original 108-pair quantitative dataset:
  no

used to recompute transition/timing statistics:
  no

used as proof of OpenAI internal root cause:
  no
~~~

This event is preserved because it is historically relevant and unusually
self-referential, but it does not upgrade or alter the evidentiary status of the
original capture.

> **Meta-observation != primary dataset.**

## Satirical side-study — Purrtocol Expansion Dynamics

Purrtocol mascot proliferation is analyzed separately from the primary recovery evidence base.

~~~text
selected Purrtocol-related Git commit timestamps:
  repository-observed

parent/child lineage:
  editorial project archaeology; not causal proof

adjacent_ideas_generated marks:
  author annotation; not a measured branching process

exponential growth fit / Hawkes fit:
  descriptive models over a short, curated, bursty event window

quadratic finite-time singularity:
  illustrative scenario; coupling parameter not fitted

Sam/Tibo observation hazard:
  illustrative scenario; not instrumented

Earth saturation:
  NOT YET OBSERVED

forecast of planetary Purrtocol coverage:
  NOT ESTABLISHED
~~~

The selected 10-event sequence gives a descriptive exponential doubling time of
about **3.758 hours** and a grid-fit Hawkes branching ratio of about **0.85**,
classified as **subcritical**. The manually annotated adjacent-idea mark averages
**3.3 ideas/event**; that number is not a Hawkes branching ratio.

The joke is allowed to outrun common sense. It is not allowed to outrun the evidence boundary.


### Purrtocol measurement backaction checkpoint

Operationalizing the Purrtocol expansion side-study produced **12 additional
Purrtocol-related repository artifacts in 183 seconds** after the original
10-event selected cohort.

~~~text
primary cohort:
  events = 10
  Hawkes n ~= 0.85
  classification = subcritical

observer-inclusive checkpoint:
  events = 22
  Hawkes n ~= 1.00
  classification = near-critical

checkpoint:
  ec25244a024f2049cfc7851c7fafd421d35a113c

causal generalization:
  NOT ESTABLISHED

Earth saturation:
  NOT YET OBSERVED
~~~

Classification: **measurement-associated repository backaction**. Building the
measurement/communication apparatus added artifacts to the measured project
surface. This does not establish a universal observer-effect law or a forecast
of runaway mascot growth.
