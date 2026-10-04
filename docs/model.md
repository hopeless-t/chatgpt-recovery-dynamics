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

## H6 — external archaeological constraint set

The repository also preserves public Reddit / Hacker News reports as a separate
weak-evidence plane.

These reports are not used to estimate production incidence or to fit the HAR
timing model. Instead, they act as **historical constraint cases**.

The current curated archive contains:

- 15 public-report artifacts;
- 13 reports in the default weak-evidence subset;
- 12 distinct 2026 report dates spanning 185 days;
- a 1,301-day archaeology span including the oldest retained HN artifact.

Within the default subset:

~~~text
Too Many Requests                                  9
Unable to load conversation                        5
temporary recovery                                 5
state-dissociation signature                       7
transport-recovery signature                       2
Unable-to-load AND Too-Many-Requests              4
Too-Many-Requests AND local trigger association   5
~~~

After removing three reports that overlap or sit adjacent to confirmed official
incident windows, the remaining 10-report sensitivity subset still contains:

~~~text
Unable-to-load AND Too-Many-Requests              3
Too-Many-Requests AND local trigger association   4
state-dissociation signature                       6
transport-recovery signature                       1
~~~

This does not prove a common root cause.

It does provide falsification pressure against overly simple models.

### Constraint C1 — pure canonical data loss is insufficient

Public reports exist where:

- history/sidebar disappears while a retained direct conversation remains
  accessible;
- one client cannot retrieve an old conversation while another client can;
- refresh/wait/restart temporarily restores access.

Those observations are difficult to represent as irreversible canonical data
loss alone.

### Constraint C2 — one global WORKING/BROKEN state is insufficient

Cross-client disagreement and mixed recovery outcomes are compatible with the
DCS state vector and inconsistent with treating the whole product as one
synchronous binary state.

### Constraint C3 — rate-pressure coupling remains plausible

Several reports associate Too Many Requests with:

- multiple open tabs;
- archive/delete/rename/organize actions;
- suspected conversation-list/sidebar refresh behavior.

These are uncontrolled self-reports. They do not identify a rate limiter or
prove that list/recovery traffic caused 429. They are nevertheless compatible
with a constrained request-budget model and motivate controlled replication.

### Constraint C4 — transport/recovery deserves its own state

Public technical reports include:

- stream recovery polling timeout;
- conversation/resume 404;
- stream_status continuing to report streaming;
- WebSocket/client state desynchronization.

These observations are compatible with R_t / O_t being dissociable from
canonical conversation availability.

### Negative control

The archive intentionally keeps a 2024 Hacker News case where the visible
"Unable to load conversation" string arose from use of a non-share/private URL.

Therefore:

~~~text
error-string match != mechanism match
~~~

The external corpus should be matched on **symptom morphology and
co-occurrence**, not on one UI string.

No Bayes factor is reported for the social corpus because its sampling process,
independence and reporting probabilities are unknown.

See [external evidence archaeology](external-evidence.md).

## H7 — provisional recovery state and history-dependent hazard

The A -> B transition biopsy suggests that the binary Accessible/Blocked label
is too coarse for recovery control.

Define:

~~~text
H = established/stable Accessible
E = first Accessible observation immediately after Blocked
B = Blocked
~~~

Observed active-epoch transitions:

~~~text
H -> H: 38
H -> B:  2

B -> E:  8
B -> B: 50

E -> B:  8
E -> H:  0
~~~

Thus:

~~~text
P(next B | E) = 1.00 observed
P(next B | H) = 0.05 observed
~~~

with a one-sided Fisher exact value of approximately:

~~~text
1.19e-7
~~~

The Jeffreys posterior for the E -> B probability is:

~~~text
p_EB | data ~ Beta(8.5, 0.5)
~~~

whose posterior-predictive mean is:

~~~text
E[p_EB | data] = 8.5 / 9 ~= 0.944
~~~

This is the basis of the approximately 94.5% naive-first-success rebound rate
in the transport stress simulation.

The result should be interpreted as:

> current transport success is insufficient state; recovery history carries
> additional predictive information.

A small-sample model competition gives the reentry-history partition a
leave-one-out log loss of about 0.199 versus about 0.533 for a constant
A -> B hazard.

The history-aware H/E/B transition model improves the first-order A/B model by:

~~~text
Delta AIC ~= -31.25
Delta BIC ~= -28.58
~~~

within this capture.

This motivates a recovery controller that enters E after the first success and
requires independent/stable confirmation before resetting failure history or
declaring H.

See:

- [A -> B transition biopsy](transition-biopsy.md)
- [transition model competition](transition-model-competition.md)
- [fixed-point recovery correspondence / REC-FP-001](fixed-point-recovery-correspondence.md)

## H8 — recovery-path cost model

The earlier pressure equation counted observation throughput X(t). A transport
redesign needs to distinguish request count from per-request work.

Let recovery request i carry abstract cost:

~~~text
c_i =
    w_request
  + w_bytes * bytes_i
  + w_work * server_work_i
~~~

and define total recovery load rate:

~~~text
L(t) = sum_i c_i / time
~~~

Then a more general latent pressure model is:

~~~text
dP/dt = alpha * L(t) - delta * P(t) + xi(t)
~~~

Two limiting cases are useful stress models.

### Request-count dominated

~~~text
w_request >> w_bytes, w_work
~~~

A cheap status probe and a full snapshot can have similar rate-limit cost.

In this case, observe-before-snapshot mainly saves transfer/materialization
cost; start anchoring and single-flight provide the pressure benefit.

### Byte/work dominated

~~~text
w_bytes or w_work is material
~~~

Repeated multi-MiB snapshot materialization can contribute more pressure than a
small state/version observation.

In this case, separating observation from materialization can improve both
traffic cost and pressure dynamics.

The production values of these weights are unknown.

Therefore the transport simulation evaluates both regimes rather than assuming
one.

## H9 — transport survival invariants

The mathematical model suggests the following correctness invariants:

~~~text
transport failure != canonical conversation loss
transport attempt != logical recovery
re-observation != re-execution
first success != stable recovery
UNKNOWN != retry permission
~~~

A robust recovery path therefore keeps stable application-level identity across
transport changes:

~~~text
recovery_id stays fixed
operation_id stays fixed when logical work exists
attempt_id changes per network attempt
conversation_version is reconciled monotonically
~~~

The proposed network path is:

~~~text
single-flight recovery owner
 -> cheap observe/version request
 -> bounded start-anchored retry
 -> E / Recovering
 -> stable confirmation
 -> one full snapshot
 -> atomic reconcile
 -> optional realtime reattachment
~~~

HTTP/2, HTTP/1.1, HTTP/3 and WebSocket are transport choices around this state
machine, not sources of canonical truth.

See [transport and recovery-path redesign](transport-recovery-redesign.md).

## H10 — server-side congestion and retry amplification

The earlier pressure model can be embedded in a conventional server-capacity
model.

Let:

~~~text
lambda_0(t) = exogenous foreground arrival rate
lambda_r(t) = recovery/retry arrival rate
C(t)        = available service capacity
~~~

For heterogeneous request cost, define offered work:

~~~text
A(t) = sum_i c_i
~~~

where c_i is the abstract cost from H8.

Base utilization before recovery traffic is:

~~~text
rho_0(t) = foreground_work(t) / C(t)
~~~

and effective utilization is:

~~~text
rho_eff(t) =
    (foreground_work(t) + recovery_work(t))
    / C(t)
~~~

Retry amplification therefore consumes the same headroom needed for useful
foreground work.

A bounded work queue evolves approximately as:

~~~text
Q_(t+1) =
    max(
        0,
        Q_t + A_t - C_t
    )
~~~

and admission can be represented as:

~~~text
accept_i =
    1[ Q_t + c_i <= Q_max ]
~~~

possibly refined by priority/class/fairness.

This yields an important limit:

~~~text
rho_0 >= 1
=> retry control cannot create missing capacity
~~~

At that point the control problem changes from "recover everything quickly" to
"preserve the highest-value useful work while shedding/degrading reconstructible
work safely."

### Provider-friendly objective

A server-friendly recovery controller can be written as a multi-objective cost:

~~~text
J_provider =
    w_F * foreground_failures
  + w_L * foreground_latency
  + w_R * retry_amplification
  + w_Q * queued_work
  + w_B * recovery_bytes
  + w_D * duplicate_work
  + w_T * recovery_time
~~~

The weights are deployment-specific and are not identified here.

The important structural result is that client-side duplicate suppression
reduces several terms simultaneously before server scheduling begins.

### Pressure-knee simulation

A local stress simulator varies base rho from 0.70 to 1.10 while injecting the
same logical recovery workload.

The CI reference found:

~~~text
sampled operational knee
  naive completion-coupled recovery: rho ~= 0.98
  provider-friendly paths:          rho ~= 1.00
~~~

using the conservative threshold:

~~~text
foreground success >= 0.99
AND
recovery completion >= 0.99
~~~

At rho = 0.90:

~~~text
retry amplification:
  naive                   18.54x
  Retry-After + jitter     6.24x
  single-flight + observe  4.16x
  server-friendly stack    3.98x
~~~

At rho = 1.00:

~~~text
recovery completion:
  naive                   0.8896
  server-friendly stack   1.0000

retry amplification:
  naive                   62.91x
  server-friendly stack    7.49x
~~~

These are abstract simulation results, not production estimates.

Their role is to demonstrate a mechanism:

> avoidable retry/recovery work can consume enough residual capacity to move an
> overload knee earlier.

See [server-friendly congestion control](server-friendly-congestion-control.md).

## H11 — latent timing/controller memory

The first-order cycle model is:

~~~text
Delta_n = beta_0 + beta_1 S_n + u_n
~~~

with:

~~~text
beta_0 ~= 5.6164
beta_1 ~= 0.9566
~~~

and R² ~= 0.99136.

However, the remaining residual is not independent noise.

Within active epochs, an AR residual competition gives:

~~~text
u_n = phi u_(n-1) + epsilon_n

phi ~= 0.524
~~~

and reduces residual SSE by about 27.4%.

BIC:

~~~text
independent residuals  -290.26
AR(1)                  -319.58
AR(2)                  -318.22
AR(3)                  -311.24
AR(4)                  -306.53
~~~

Among AR orders 0–4, the best tested residual model is AR(1).

A later competition against a qualitatively different two-state Gaussian HMM
changes the interpretation without overturning the one-step-memory result:

~~~text
same-sample BIC:
  HMM-2  ~= -15.99
  AR(1)  ~= -10.10

held-out epoch prediction:
  epoch 1 -> 2: AR(1) mean NLL ~=  0.0191
                HMM-2 mean NLL ~=  0.3678

  epoch 2 -> 1: AR(1) mean NLL ~= -0.2203
                HMM-2 mean NLL ~= -0.0337
~~~

Thus the HMM is a stronger pooled descriptive fit, but AR(1) is the stronger
tested portable predictive representation across the two active epochs.

The correct update is **not** “the system has two hidden modes.” The HMM labels
remain unnamed statistical states.

Directly analyzing post-completion wait:

~~~text
W_n = Delta_n - S_n
~~~

gives an even larger lag-1 coefficient:

~~~text
phi_W ~= 0.676
~~~

A refined timing model is:

~~~text
Delta_n = S_n + mu + z_n + epsilon_n

z_n = phi z_(n-1) + eta_n
~~~

where z_n is an unobserved slowly varying timing/controller state.

Possible sources include client scheduling, timer state, event-loop effects,
transport/recovery state, or another omitted variable.

The public trace does not identify the physical implementation of z_n.

## H12 — latency change point coincides with Blocked onset

Within each active epoch, fit one unconstrained mean change point to:

~~~text
S_n = max(stream latency, snapshot latency)
~~~

Epoch 1:

~~~text
first Blocked index       = 32
best service change point = 32
mean before ~= 5.570 s
mean after  ~= 1.025 s
SSE reduction ~= 65.8%
~~~

Epoch 2:

~~~text
first Blocked index       = 8
best service change point = 8
mean before ~= 5.475 s
mean after  ~= 0.947 s
SSE reduction ~= 58.7%
~~~

A 5,000-permutation CI reference gives add-one Monte Carlo p ~= 0.00020 for a
maximum change-point reduction at least this large in each epoch.

Therefore the A/B boundary is not only a status-label transition. It coincides
with an independently detectable latency-regime shift in both active epochs.

This does not determine whether rate limiting caused the latency change.

## H13 — analysis-threshold robustness

The main paired-observation result is stable across pairing windows:

~~~text
10 ms through 100 ms:
108 pairs = 48 Accessible + 60 Blocked + 0 mixed
~~~

The maximum canonical pair skew is 9 ms.

The active-epoch transition matrix is unchanged for every tested epoch-gap
threshold from 20 s through 600 s:

~~~text
A -> A: 38
A -> B: 10
B -> A:  8
B -> B: 50
~~~

Only a 900 s threshold deliberately bridges the observed 775.640 s inactive
period and recreates the older B -> A count of 9.

The primary conclusions therefore do not depend on choosing exactly 50 ms or
60 s.

## H14 — history-free posterior predictive failure

Under a history-free A-origin transition model with Jeffreys posterior:

~~~text
p_AB | data ~ Beta(10.5, 38.5)
~~~

the posterior-predictive probability that all eight Accessible observations
immediately following Blocked would all return to Blocked is:

~~~text
P(8/8 rebound | history-free A/B)
~= 2.31e-5
~~~

This complements the Fisher exact analysis and further disfavors collapsing E
(provisional recovery) into ordinary H/Accessible state.

## H15 — trace-preserving materialization accounting

From the first Blocked observation onward, the two active epochs each contain:

~~~text
34 observations
30 Blocked
4 transient Accessible
~~~

There are no two consecutive Accessible observations in either tail.

The eight transient successful snapshots represent:

~~~text
36.59375 MiB
~~~

of public rounded snapshot payload.

Holding the observed state sequence fixed, a hypothetical 4 KiB state probe
with full materialization only after two consecutive Accessible observations
would transfer:

~~~text
68 probes * 4 KiB = 0.265625 MiB
full materializations = 0
~~~

for an accounting reduction of about 99.27%.

This is **not** a causal production estimate. Suppressing requests could alter
the trajectory.

Its purpose is narrower:

> using a multi-MiB full snapshot as a recovery-health probe is intrinsically
> expensive when successful observations are transient.

See [deep validation](deep-validation.md).

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
