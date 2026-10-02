# DCS-inspired recovery model

## Motivation

A common debugging shortcut is to assign one global state:

~~~text
WORKING / BROKEN
~~~

The observed capture is more naturally described by partially independent
state variables plus a timing/control loop.

The model below is intentionally client-visible. It does not claim to
reconstruct OpenAI's internal architecture.

## State vector

We model the client-visible system as:

~~~text
x_t = (C_t, A_t, O_t, R_t, P_t, Theta_t, U_t)
~~~

where:

- C_t — canonical conversation availability;
- A_t — snapshot accessibility;
- O_t — stream/realtime observability;
- R_t — recovery/resume attachment;
- P_t — latent request/rate-limit pressure;
- Theta_t — effective throttling/capacity threshold;
- U_t — user-visible utility / readability.

P_t and Theta_t are latent variables. The public trace does not identify the
scope or implementation of any rate limiter.

The term *dissociated control state* is used here in a systems-engineering
sense: sub-systems can occupy different operational states at the same time.

It is **not** a clinical or psychological claim.

## H1 — state dissociation

A successful snapshot and failed resume can coexist.

Therefore:

~~~text
Observed UI failure != proof of canonical data loss
Global state != uniform subsystem state
~~~

This is the most conservative DCS claim in the repository.

## H2 — completion-coupled cadence amplification

The original model assumed that loss of observability might explicitly increase
retry aggressiveness. The public data support a more parsimonious mechanism.

For observation cycle n, define:

- S_n — service/failure time of the slower request in the paired observation;
- W_n — post-completion wait;
- Delta_n — start-to-start time until the next observation cycle.

Then:

~~~text
Delta_n = S_n + W_n
~~~

Across the 106 within-epoch transitions in the public data:

~~~text
Delta_n ~= 5.6164 + 0.9566 * S_n
R^2 = 0.99136
~~~

A robust Theil-Sen fit gives approximately:

~~~text
Delta_n ~= 5.7017 + 0.9220 * S_n
~~~

The median inferred post-completion waits are:

- accessible: about 5.383 s;
- blocked: about 5.647 s.

Adding a blocked-state indicator after service time changes fitted cycle time by
only about -0.0066 s and does not materially improve the fit.

Therefore, the observed cadence increase does **not** require an intentionally
more aggressive blocked-state retry policy. A nearly fixed post-completion wait
plus much faster failure is sufficient.

### Queueing-theory connection

For a closed interactive loop, the response-time law is:

~~~text
N = X * (R + Z)
~~~

For one circulating client loop, N = 1:

~~~text
X ~= 1 / (R + Z)
~~~

Here R corresponds to request/response time and Z to the post-completion wait.
A shorter failure response therefore raises cycle throughput even when Z is
unchanged.

The mean observed start-to-start gap falls from about 10.843 s while accessible
to about 6.036 s while blocked, corresponding to about a 1.80x increase in
pair-initiation rate. The median-gap ratio is about 1.71x.

Reference:
Peter J. Denning, Queueing Networks:
https://denninginstitute.com/pjd/PUBS/ENC/qn08.pdf

## H3 — conditional positive feedback

Cadence amplification alone does not prove that the added attempts cause 429.
To express the causal hypothesis without assuming the missing internal state,
let effective pressure evolve in continuous time as:

~~~text
dP/dt = alpha * X(t) - delta * P(t) + xi(t)
~~~

where:

- X(t) is observation/recovery attempt throughput;
- delta is pressure decay;
- xi(t) is unobserved/exogenous request or service load.

Let throttling probability be:

~~~text
Pr(429 at t) = sigmoid(P(t) - Theta(t))
~~~

Theta(t) is allowed to vary because service capacity, account-level headroom,
edge policy, and other unobserved factors are not known from the HAR.

If higher pressure causes requests to be rejected earlier, then service time can
fall as pressure rises:

~~~text
dS/dP < 0
~~~

With a completion-coupled loop:

~~~text
X(P) ~= 1 / (W + S(P))
~~~

so:

~~~text
dX/dP = -S'(P) / (W + S(P))^2
~~~

which is positive whenever S'(P) is negative.

A local self-amplifying loop becomes possible when the induced gain exceeds
pressure decay:

~~~text
alpha * (-S'(P)) / (W + S(P))^2 > delta
~~~

This gives a precise version of the fast-fail feedback hypothesis:

~~~text
pressure / rejection rises
 -> failures complete faster
 -> completion-coupled cycles start more often
 -> attempt throughput rises
 -> pressure may rise further
~~~

The capture is compatible with this mechanism. It does **not** measure P(t),
Theta(t), or S'(P) directly, so the inequality is a falsifiable hypothesis, not
an identified internal causal law.

## H4 — Markov renewal / semi-Markov observation process

The paired observations form an embedded two-state sequence:

- A — accessible: stream 200 + snapshot 200;
- B — blocked: no stream HTTP response + snapshot 429.

One approximately 775.640 s inactive gap separates two active epochs. Treating
that gap as a normal B -> A transition is inappropriate, so it is censored.

The active-epoch transition counts are:

~~~text
A -> A: 38
A -> B: 10
B -> A:  8
B -> B: 50
~~~

giving:

~~~text
P(B next | A) = 0.2083
P(B next | B) = 0.8621
~~~

The corresponding Wilson 95% intervals are approximately:

~~~text
P(B next | A): [0.117, 0.343]
P(B next | B): [0.751, 0.928]
~~~

The blocked state is therefore persistent in this capture.

### Why not use only a discrete Markov chain?

The state-dependent holding time matters:

- blocked fraction by observation count: 55.6%;
- blocked fraction across active start-to-start wall-clock time: about 40.2%.

Blocked cycles generate more observations per unit time because they complete
faster. The embedded state sequence and the time spent in each state are
therefore different objects.

A Markov renewal / semi-Markov framing is more appropriate when discussing
continuous-time occupancy:

~~~text
state Z_n
   +
holding time Delta_n
   ->
next state Z_(n+1)
~~~

With only eight uncensored B -> A exits, the current data do not establish a
duration-dependent escape law. The completed blocked-run mean is 7.0
observations, close to the geometric mean implied by the fitted exit
probability (about 7.25 observations). A first-order Markov model is therefore
not rejected for the embedded state sequence.

## H5 — slow latent entry state

The two active epochs have the same observed blocked persistence:

~~~text
epoch 1: P(B -> B) = 25 / 29 = 0.8621
epoch 2: P(B -> B) = 25 / 29 = 0.8621
~~~

But their accessible-to-blocked entry fractions differ:

~~~text
epoch 1: 5 / 36 = 0.1389
epoch 2: 5 / 12 = 0.4167
~~~

A two-sided Fisher exact comparison is not conclusive with this sample
(p approximately 0.094).

This is therefore only a hint that entry into B may depend on a slower latent
variable such as remaining rate-limit headroom, backend/edge load, or
unobserved traffic. It motivates P_t and Theta_t in the state vector.

## Competing causal models

### M1: rate-limit-first

~~~text
external / latent pressure
 -> 429
 -> snapshot inaccessible
 -> recovery/observation degrades
 -> UI remains stale/unavailable
~~~

### M2: recovery-first

~~~text
recovery/resume anomaly
 -> repeated observation
 -> pressure rises
 -> 429
 -> recovery becomes harder
~~~

### M3: fast-fail-mediated loop

~~~text
blocked / throttled response
 -> failure latency collapses
 -> completion-coupled loop cycles faster
 -> request attempt rate rises
 -> pressure may be maintained or amplified
~~~

M3 is the part most directly supported by the cycle-time decomposition, but the
final arrow remains causal hypothesis rather than observation.

The two resume-404 episodes precede the first later snapshot-429 by 349.013 s
and 87.853 s respectively, with successful snapshots in between. That ordering
is compatible with M2 but is insufficient to reject M1. A 404 may also be a
normal response for a state that cannot or need not be resumed.

## Recovery implication

If completion-coupled fast failure is the main cadence amplifier, the key
control change is straightforward:

~~~text
do not let a fast failure automatically shorten start-to-start spacing
~~~

A safer scheduler anchors the next attempt to both the prior start time and the
error class:

~~~text
next_start =
    max(
        last_start + minimum_period,
        now + error_backoff(error_class, consecutive_failures)
    )
~~~

For the full proposal, including single-flight snapshots, recovery hysteresis,
retry budgets and re-observation before resynchronization, see
docs/recovery-design.md.

## Numerical precision

The two-parameter cycle-time regression is well conditioned:

- design-matrix condition number: about 5.62;
- normal-matrix condition number: about 31.6.

An 80-digit recomputation agrees with ordinary binary64 at all displayed
digits. High-precision GEMM methods such as the Ozaki scheme are therefore not
needed for this small fit; measurement and model uncertainty dominate
floating-point roundoff.

Ozaki reference:
https://doi.org/10.1007/s13160-026-00816-8

## Falsification / replication

Useful next tests include:

1. Does the relation Delta approximately equal service time plus a fixed wait
   reproduce in independent captures?
2. Does a fast 429 response predict a shorter start-to-start cycle even after
   controlling for state?
3. Does anchoring retries to start time remove cadence amplification in a local
   simulator?
4. Does retry cadence predict transition into B after accounting for session
   epoch and other observed traffic?
5. Does blocking persist after user-driven activity stops?
6. Does conversation size change entry hazard or snapshot cost?
7. Do native clients have different transition / holding-time kernels from
   web/PWA?
8. Do independent captures reproduce the perfect paired
   (stream_status, snapshot) coupling?

The model should be updated or rejected when independent traces contradict
these predictions.
