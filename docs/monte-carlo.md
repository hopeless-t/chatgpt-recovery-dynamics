# Robust Monte Carlo recovery stress test

This experiment asks a design question, not a root-cause question:

> If the exact causal mechanism behind the 429/recovery loop is uncertain, which
> recovery policy is least likely to make things worse?

The simulation intentionally uses **multiple incompatible causal models**. A
policy that only works when one preferred story is true is not considered
robust.

## Why Monte Carlo here?

The public trace is one session. It is enough to estimate timing and transition
structure, but not enough to identify server-side causality.

The robust approach is therefore:

1. bootstrap what is directly observed;
2. vary transition probabilities;
3. vary holding-time / blocked-duration assumptions;
4. introduce a hypothetical pressure-feedback model only as a stress scenario;
5. compare policies across all of them.

Semi-Markov bootstrap methods are well established for empirical transition /
holding-time processes. One relevant reference is:

- Bouzebda & Limnios, *On general bootstrap of empirical estimator of a
  semi-Markov kernel with applications*, Journal of Multivariate Analysis 116
  (2013), 52–62.
  https://doi.org/10.1016/j.jmva.2012.11.008

## Bootstrap result

A 30,000-resample empirical bootstrap of the active-epoch observations gives
the following approximate 95% intervals:

| Quantity | 2.5% | median | 97.5% |
|---|---:|---:|---:|
| Accessible cycle median | 10.002 s | 10.272 s | 10.987 s |
| Blocked cycle median | 5.996 s | 5.998 s | 6.002 s |
| Accessible post-completion wait median | 5.067 s | 5.383 s | 5.514 s |
| Blocked post-completion wait median | 5.628 s | 5.647 s | 5.679 s |

This is important for controller design:

> A start-to-start minimum near **10 seconds** is not an arbitrary constant. It
> lies at the conservative lower edge of the observed normal/Accessible cycle
> distribution.

The previously reported cycle-time regression is also stable under bootstrap:
the slope remains close to one and the fit remains near R² = 0.99.

## Three deliberately different causal models

### Model A — attempt-driven embedded chain

This model is deliberately **unfriendly to backoff**.

The state only gets a chance to transition when the client observes again.
Spacing requests cannot make recovery happen sooner; it can only delay the next
chance to discover recovery.

Transition uncertainty is sampled from Jeffreys beta posteriors derived from
the active-epoch counts:

- B -> B: 50
- B -> A: 8
- A -> B: 10
- A -> A: 38

This model asks:

> What if retries do not contribute to the blocked state at all?

A robust controller should not catastrophically fail under this interpretation.

### Model B — latent wall-clock recovery

Here the blocked condition clears independently in wall-clock time.

Completed blocked-run durations are bootstrapped from the capture and perturbed
multiplicatively with log-normal noise.

Requests do not change the underlying clear time. They only determine how soon
the client notices that recovery has occurred.

This model exposes the classic polling tradeoff:

- probe too often -> unnecessary requests;
- probe too slowly -> detection delay.

### Model C — hypothetical pressure feedback

This is **not fitted to OpenAI internals**.

It stress-tests the mathematical feedback idea:

~~~text
attempt -> pressure increment
pressure -> exponential wall-clock decay
pressure above uncertain threshold -> greater blocked probability
~~~

For each trial, parameters are drawn over deliberately broad ranges:

- pressure decay time constant: log-uniform 15–120 s;
- per-attempt pressure increment: 0.05–0.35 normalized units;
- threshold: 0.7–1.3;
- logistic steepness: 4–12;
- initial pressure: threshold + 0.2–0.8.

The goal is not to estimate those quantities. The question is whether a
controller remains useful if this kind of feedback exists.

## Policies

Four policies are tested.

### Baseline

Completion-coupled timing reconstructed from the empirical service/wait
distributions.

### 10-second start anchor

~~~text
next_start >= previous_start + 10 s
~~~

No exponential backoff is added.

This policy attacks only the mechanism directly observed in the trace:
fast failure should not automatically make the loop run faster.

### Moderate backoff

- minimum start period: 10 s;
- backoff begins after the second consecutive blocked result;
- base: 8 s;
- factor: 1.5;
- cap: 30 s;
- ±20% jitter.

### Strong backoff

- minimum start period: 10 s;
- backoff begins after the second consecutive blocked result;
- base: 8 s;
- factor: 2.0;
- cap: 60 s;
- ±20% jitter.

Backoff + jitter is a standard retry-storm mitigation pattern in distributed
systems, but this experiment explicitly tests the cost of applying it too
aggressively.

Reference:
https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_limit_retries.html

## Reference run

The repository CI runs a deterministic 5,000-trial reference for every
policy/model combination.

The exact artifact is published as:

- data/monte_carlo_reference.json

### Recovery rate

| Policy | Attempt-driven | Latent wall-clock | Pressure-feedback |
|---|---:|---:|---:|
| Baseline | 1.0000 | 1.0000 | 0.5268 |
| **10 s anchor** | **0.9996** | **1.0000** | **0.6910** |
| Moderate backoff | 0.9850 | 1.0000 | 0.9156 |
| Strong backoff | 0.9130 | 1.0000 | 0.9718 |

This table demonstrates the model-risk tradeoff directly.

Strong backoff is excellent if pressure feedback is real, but it performs much
worse when recovery opportunities are attempt-driven.

The 10-second anchor changes the mechanism much less and therefore degrades
gracefully when the causal story is wrong.

### Latent-recovery request cost

Mean blocked attempts before recovery detection:

| Policy | Mean blocked attempts |
|---|---:|
| Baseline | 6.85 |
| **10 s anchor** | **4.32** |
| Moderate backoff | 3.63 |
| Strong backoff | 3.32 |

For the 10-second anchor, that is roughly a **37% reduction** in blocked probes
relative to baseline in this model.

The cost is detection latency:

| Policy | p95 detection delay |
|---|---:|
| Baseline | 5.79 s |
| **10 s anchor** | **9.53 s** |
| Moderate backoff | 24.82 s |
| Strong backoff | 36.29 s |

Again, the 10-second anchor sits near the knee of the tradeoff.

### Pressure-feedback stress result

Under the deliberately broad hypothetical pressure model:

- baseline recovery rate: 52.68%;
- **10-second anchor: 69.10%**;
- moderate backoff: 91.56%;
- strong backoff: 97.18%.

Among recovered 10-second-anchor trials, mean blocked attempts fall from about
13.42 to 8.10.

This does **not** establish that ChatGPT has this pressure model. It shows that
the start-anchor design helps if the feedback hypothesis is approximately true
without becoming highly dependent on that hypothesis.

## Robust-design conclusion

The strongest result is not “use exponential backoff.”

It is:

> **First prevent fast failure from increasing start-to-start attempt rate.**

The data-driven robust core is therefore:

~~~text
normal_period ~= robust estimate of healthy cycle period

next_start =
    max(
        previous_start + normal_period,
        server-directed retry time if available
    )
~~~

For this capture:

~~~text
normal_period ~= 10 s
~~~

because the bootstrap 95% interval for the Accessible median begins at about
10.00 seconds.

### Why not make strong backoff the default?

Because the causal mechanism is uncertain.

If recovery progresses independently of attempts or if retries actively
increase pressure, strong backoff can be excellent.

If recovery opportunities are attempt-driven, strong backoff can turn a
recoverable sequence into a long user-visible wait.

That is exactly the kind of model uncertainty a robust design should survive.

## Recommended layered controller

### Layer 1 — always

Anchor start-to-start timing to a normal/healthy period.

~~~text
next_start >= previous_start + T_normal
~~~

Estimate T_normal from successful healthy observations rather than hard-coding
it globally.

### Layer 2 — when explicit throttling is observed

Honor server-provided retry timing when available.

Otherwise use bounded error-aware spacing, jitter and retry budgets.

### Layer 3 — repeated failure

Escalate gradually rather than immediately applying a large exponential
backoff.

Use circuit breaking / sparse probes only after repeated evidence that normal
observation cannot converge.

### Layer 4 — recovery hysteresis

Do not declare the system healthy after one Accessible excursion.

The simulations require two consecutive Accessible observations as a simple
stand-in for a stability window.

The production threshold should be measured independently.

## Reproduce

~~~bash
python3 scripts/monte_carlo_recovery.py
~~~

A faster local run:

~~~bash
python3 scripts/monte_carlo_recovery.py \
  --trials 5000 \
  --bootstrap-trials 10000
~~~

The GitHub Actions workflow also checks qualitative robustness invariants:

- 10-second anchoring beats baseline under the pressure-feedback stress model;
- strong backoff beats anchoring under that same model;
- strong backoff performs worse than anchoring under the attempt-driven model;
- the healthy-cycle bootstrap continues to place the lower interval near
  10 seconds.

If future data violate those conditions, the design claim should be revisited.

## What this experiment does not prove

It does not prove:

- the existence or scope of an OpenAI rate limiter;
- that retries cause the production 429 response;
- that 10 seconds is globally correct for every client or conversation;
- that the pressure parameters correspond to real server parameters;
- that one user's session is representative of the population.

The purpose is narrower:

> find a recovery controller whose behavior remains reasonable when the causal
> model is wrong.
