# Fixed-point recovery correspondence

> Status: REC-FP-001 IDENTIFIABILITY BASELINE IMPLEMENTED  
> Scope: local telemetry / local simulation only  
> Production-root-cause claim: NONE

## Motivation

The current repository already distinguishes:

~~~text
B = Blocked
E = first Accessible observation after Blocked
H = established / stable Accessible
~~~

and has strong within-capture evidence that:

~~~text
first success != stable recovery
~~~

Huang et al. (2026), *Towards Looped Models Done Right — Part II: Rethinking at
Fixed Points*, provides a useful engineered-system comparison: a recurrent state
can approach a fixed point, and endpoint shortcuts are justified only after the
state has sufficiently settled.

Sources:

- https://www.alphaxiv.org/abs/2610.looped-models-fixed-points
- https://github.com/ifm-ai/xllm-loop
- official paper PDF:
  https://github.com/ifm-ai/xllm-loop/blob/main/papers/part2.pdf

This paper is **not evidence about OpenAI production internals**. It is used
only to sharpen the local recovery model.

## Atomic transfer

The transferable object is not "ChatGPT is a looped model." It is the distinction:

~~~text
one successful observation
!=
state convergence
!=
stable post-perturbation recovery
~~~

The current H/E/B evidence already says that E should not be promoted to H from
one successful request. A fixed-point framing suggests a measurable stronger
question:

> after reentry, do the observable recovery coordinates contract toward a
> stable healthy reference, or do they continue to drift / rebound?

## Observable recovery state

Define a local observation vector, using only quantities already available or
derivable in the repository:

~~~text
z_n = [
    normalized service latency,
    normalized cycle time,
    recent Blocked fraction,
    recent rebound indicator,
    timing-residual state estimate
]
~~~

The exact coordinates and normalization must be frozen before fitting.

Let z_H be a healthy reference estimated only from stable Accessible samples.
Define a weighted recovery residual:

~~~text
r_n = || z_n - z_H ||_W
~~~

where W is a declared positive diagonal weight matrix or a standardized
Euclidean metric.

No latent implementation meaning is assigned to z_n. It is an observable state
summary.

## Candidate convergence observables

### Recovery residual

~~~text
r_n = ||z_n - z_H||
~~~

A smaller r_n means closer to the declared healthy observation reference, not
closer to an unknown server-internal state.

### Empirical contraction ratio

~~~text
kappa_n = r_(n+1) / r_n
~~~

Interpretation:

- repeated kappa < 1: compatible with contraction toward the reference;
- kappa ~= 1: neutral / persistent offset;
- kappa > 1: rebound / divergence.

One ratio is never enough to establish a contraction regime.

### Stable-confirmation depth

~~~text
tau_epsilon =
    min k such that
    r_(n+j) <= epsilon
    for all j in [k, k+m]
~~~

where m is a frozen confirmation window.

This gives the current E -> H rule a quantitative interpretation without
assuming an actual fixed point exists.

## Competing models

The fixed-point hypothesis must compete with the models already in this
repository.

### M-A — categorical H/E/B

The current history-aware state model.

Prediction: reentry history carries most of the predictive value; continuous
distance-to-H adds little.

### M-B — semi-Markov recovery

Hazard depends on categorical state plus time / holding duration.

Prediction: elapsed recovery duration materially changes rebound risk.

### M-C — observable contraction

A continuous recovery residual decays after reentry:

~~~text
r_(n+1) ~= a r_n + noise
0 <= a < 1
~~~

Prediction: r_n has reproducible monotone or stochastic contraction before
stable H.

### M-D — rebound / hysteresis

Recovery can initially move toward H and then return to B.

Prediction: one-sample success is common while confirmation-window convergence
fails; kappa can exceed 1 during reentry.

### M-E — no fixed-point structure

There is no reproducible contraction coordinate in the local observations.

Prediction: categorical history remains useful, but continuous convergence
metrics do not generalize across captures.

M-E is a valid outcome.

## REC-FP-001 current-capture result

Before fitting any contraction coefficient, the repository now audits whether the
current sanitized trace contains enough post-reentry trajectory depth to identify
one.

Observed structure:

~~~text
B -> E events:                         8
E -> B on the next observation:       8
E -> H observed:                      0
max post-reentry Accessible run:      1
adjacent post-reentry A/A pairs:      0
empirical kappa samples available:    0
~~~

Therefore the first REC-FP-001 result is:

~~~text
CONTRACTION_NOT_IDENTIFIABLE_FROM_CURRENT_CAPTURE
~~~

This is not a failure of the experiment. It is a useful identifiability result.

The capture strongly supports the existing within-capture rebound/hysteresis
description, while providing **no two-step post-reentry Accessible trajectory**
from which to estimate

~~~text
kappa_n = r_(n+1) / r_n
~~~

or a stable-convergence depth.

Current candidate status is therefore:

| Model | Current status |
|---|---|
| M-A categorical H/E/B | supported within capture |
| M-B semi-Markov recovery | not tested by this audit |
| M-C observable contraction | **unidentifiable from current capture** |
| M-D rebound / hysteresis | supported within capture |
| M-E no fixed-point structure | not rejected |

The next required evidence is an independent capture containing at least one
`B -> E -> H` sequence, or a longer post-reentry Accessible run. Only then
should the repository fit a contraction ratio or convergence depth.

Reproduce:

~~~bash
python3 scripts/audit_recovery_convergence_identifiability.py
~~~

## Recovery controller consequence

No controller change is justified by this document alone.

If future independent captures support M-C or M-D, a recovery declaration could
require both:

~~~text
categorical condition:
    E has survived the confirmation rule

continuous condition:
    recovery residual remains below epsilon
~~~

That would strengthen the existing principle:

~~~text
first success != stable recovery
~~~

into:

~~~text
stable recovery = categorical persistence + bounded observable residual
~~~

Only local simulation and passive observation should be used to test this.
No additional production request load is authorized.

## Relation to the upstream fixed-point paper

The upstream paper reports several points that are useful as methodological
warnings:

1. endpoint reuse is conditional on sufficiently settled state;
2. fixed-depth training can fail under terminal sharing when states keep
   drifting;
3. convergence depth can vary across tokens;
4. shortcuts taken before convergence can fail;
5. the endpoint can become useful only after the training process has shaped
   the recurrent dynamics.

Recovery Dynamics should import those as **falsification pressure**, not as a
mechanism claim.

## Proposed experiment: REC-FP-001

Use existing local / sanitized telemetry only.

1. freeze z_n coordinates and normalization;
2. estimate z_H from stable H samples only;
3. compute r_n and kappa_n around every B -> E transition;
4. compare M-A through M-E with held-out or leave-one-out scoring;
5. bootstrap the contraction estimate;
6. repeat on independent captures before promoting any controller rule.

Primary acceptance question:

~~~text
Does a continuous convergence coordinate improve out-of-sample rebound
prediction beyond the existing H/E/B history label?
~~~

## Falsifiers

Downgrade the fixed-point correspondence if any of these hold:

- r_n does not show reproducible post-reentry structure;
- the fitted contraction parameter is unstable across captures;
- improvement disappears under held-out scoring;
- coordinate choices materially reverse the conclusion;
- categorical H/E/B explains the data equally well with lower complexity.

## Claim ceiling

This document may support:

~~~text
RECOVERY_CONVERGENCE_MODEL_DEFINED
FIXED_POINT_CORRESPONDENCE_TESTABLE
~~~

It may not support:

~~~text
OPENAI_BACKEND_FIXED_POINT_IDENTIFIED
CHATGPT_INTERNAL_ATTRACTOR_IDENTIFIED
PRODUCTION_ROOT_CAUSE_IDENTIFIED
~~~
