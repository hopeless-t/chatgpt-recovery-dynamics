# Deep validation of the recovery trace

This note collects validation steps that use only the already-published
sanitized trace.

The goal is not to invent another production-root-cause story. It is to ask:

> Which conclusions survive alternative analysis choices, and what structure is
> still left unexplained after the high-R² timing law?

---

## 1. Pairing-window sensitivity

The main analysis pairs stream-status and snapshot observations when their start
times differ by no more than 50 ms.

That threshold is not critical over a broad stable region:

| Pairing window | Pairs | Accessible | Blocked | Mixed |
|---|---:|---:|---:|---:|
| 5 ms | 103 | 44 | 59 | 0 |
| **10 ms** | **108** | **48** | **60** | **0** |
| 20 ms | 108 | 48 | 60 | 0 |
| 50 ms | 108 | 48 | 60 | 0 |
| 100 ms | 108 | 48 | 60 | 0 |
| 250 ms | 109 | 49 | 60 | 0 |

The maximum start skew among the 108 canonical pairs is 9 ms.

Therefore the published 50 ms window lies inside a stable 10–100 ms plateau,
not at a tuned edge.

---

## 2. Active-epoch boundary sensitivity

The primary analysis censors one approximately 775.640 s inactive gap using a
60 s epoch threshold.

The transition matrix is unchanged for every tested threshold from 20 s through
600 s:

~~~text
A -> A: 38
A -> B: 10
B -> A:  8
B -> B: 50
~~~

Only when the threshold reaches 900 s and deliberately bridges the 775.640 s
inactive period does the matrix change:

~~~text
B -> A: 8 -> 9
P(B next | B): 0.8621 -> 0.8475
~~~

The corrected transition result is therefore not sensitive to choosing exactly
60 seconds.

---

## 3. Cross-epoch replication of the timing law

Fit the cycle law separately in each active epoch.

Epoch 1:

~~~text
Delta ~= 5.6661 + 0.9458 S
~~~

Epoch 2:

~~~text
Delta ~= 5.5595 + 0.9749 S
~~~

Training on epoch 1 and predicting epoch 2 gives:

~~~text
RMSE ~= 0.259 s
mean error ~= -0.053 s
~~~

Training on epoch 2 and predicting epoch 1 gives:

~~~text
RMSE ~= 0.251 s
mean error ~= +0.011 s
~~~

So the approximately-one-for-one service-time coefficient is not produced by
only one of the two active epochs.

---

## 4. The high-R² model still leaves temporal structure

The published model is:

~~~text
Delta_n = beta_0 + beta_1 S_n + u_n

beta_0 ~= 5.6164
beta_1 ~= 0.9566
R^2    ~= 0.99136
~~~

A high R² does **not** imply the residuals are independent.

Within active epochs, the residual lag-1 dependence is approximately:

~~~text
phi ~= 0.524
~~~

Adding an AR(1) residual model:

~~~text
u_n = phi u_(n-1) + epsilon_n
~~~

reduces residual SSE by about **27.4%**.

BIC comparison:

| Residual model | BIC |
|---|---:|
| independent residuals | -290.26 |
| **AR(1)** | **-319.58** |
| AR(2) | -318.22 |
| AR(3) | -311.24 |
| AR(4) | -306.53 |

The best tested timing model is therefore the original service-time relation
plus **one-step residual memory**.

Directly analyzing:

~~~text
W_n = Delta_n - S_n
~~~

gives an even stronger lag-1 coefficient:

~~~text
phi_W ~= 0.676
~~~

### Interpretation

The earlier statement:

> roughly fixed post-completion wait

remains useful as a first-order description.

A better second-order model is:

~~~text
Delta_n = S_n + mu + z_n + epsilon_n

z_n = phi z_(n-1) + eta_n
~~~

where z_n is an unobserved slowly varying timing/controller state.

Possible interpretations include client scheduling, timer state, local event-loop
effects, transport/recovery-controller state, or another omitted variable.

The trace does **not** identify which one.

### Competing continuous and discrete latent-state descriptions

A separate executable competition tests whether the same residual structure is
better described as continuous one-step carryover or as a discrete two-state
latent regime.

Same-sample BIC prefers the two-state Gaussian HMM:

~~~text
HMM-2 BIC ~= -15.99
AR(1) BIC ~= -10.10
Delta BIC (HMM - AR1) ~= -5.89
~~~

But cross-epoch prediction reverses the practical ranking:

~~~text
train epoch 1 -> test epoch 2:
  AR(1) NLL ~= 0.0191
  HMM-2 NLL ~= 0.3678

train epoch 2 -> test epoch 1:
  AR(1) NLL ~= -0.2203
  HMM-2 NLL ~= -0.0337
~~~

AR(1) is best in both held-out directions.

The observed A/B-conditioned Gaussian control also does not explain the
structure well enough to replace the temporal model.

The evidence therefore favors this cautious summary:

> pooled residuals admit a strong discrete two-state compression, but continuous
> one-step memory transfers better across the two active epochs.

This is still **within one capture** and does not identify a physical
scheduler/timer/backend state.

See [latent timing model competition](latent-timing-model-competition.md).

---

## 5. Change-point detection

For each active epoch, fit one unconstrained mean-change point to service time:

~~~text
S_n = max(stream latency, snapshot latency)
~~~

### Epoch 1

~~~text
first Blocked index:       32
best latency change point: 32

mean before ~= 5.570 s
mean after  ~= 1.025 s
SSE reduction ~= 65.8%
~~~

### Epoch 2

~~~text
first Blocked index:        8
best latency change point:  8

mean before ~= 5.475 s
mean after  ~= 0.947 s
SSE reduction ~= 58.7%
~~~

Thus the independently fitted one-change-point boundary exactly matches the
first Blocked observation in **both** epochs.

A within-epoch permutation stress test randomizes latency order and re-fits the
best change point. In the 20,000-permutation exploratory run, no permutation in
either epoch matched or exceeded the observed maximum SSE reduction, so the
add-one Monte Carlo bound was:

~~~text
p <= 1 / 20001 ~= 5.0e-5
~~~

The CI uses 5,000 permutations and checks the same qualitative result.

This does not prove a server-side phase transition. It shows that the A/B state
boundary coincides with a large independently detectable latency-regime shift.

---

## 6. Posterior-predictive check of the history-free A/B model

If every Accessible observation shared one history-free A -> B transition
probability, the Jeffreys posterior is:

~~~text
p_AB | data ~ Beta(10.5, 38.5)
~~~

The posterior-predictive probability that **all eight** Accessible observations
immediately following Blocked would then all return to Blocked is:

~~~text
P(8/8 rebound | history-free A/B model)
~= 2.31e-5
~~~

This is a separate check from the Fisher exact contingency analysis.

Both point in the same direction:

> the immediately-post-Blocked Accessible state carries information that the
> first-order A/B label discards.

---

## 7. Epoch morphology

From the first Blocked observation onward, both active epochs contain exactly:

~~~text
34 observations
30 Blocked
4 Accessible
~~~

Sequences:

~~~text
epoch 1:
BBBBABBBBBBBABBBBBBBBBABBBBBBBBABB

epoch 2:
BBBABBBBBBBBBABBBBBBBBABBBBBBBBABB
~~~

They match at 30 of 34 positions.

Accessible positions:

~~~text
epoch 1: 4, 12, 22, 31
epoch 2: 3, 13, 22, 31
~~~

Two of the four positions overlap exactly.

If each epoch independently placed four Accessible observations uniformly among
34 positions, the probability of overlap >= 2 is approximately:

~~~text
p ~= 0.0589
~~~

That is suggestive but not conventionally conclusive.

The correct conclusion is:

> the two epochs show striking descriptive morphology, but independent captures
> are required before claiming a repeated deterministic controller period.

---

## 8. Trace-preserving materialization accounting

This calculation does **not** simulate a changed server.

It holds the observed A/B state sequence fixed and only asks how many bytes a
different materialization policy would have transferred.

From the first Blocked observation onward:

~~~text
epoch 1: 34 observations, 4 transient A
epoch 2: 34 observations, 4 transient A
~~~

There are no two consecutive Accessible observations in either recovery tail.

The actual published successful snapshot payload represented by those eight
transient A observations is:

~~~text
8 * 4684 KiB = 36.59375 MiB
~~~

A hypothetical policy that used 4 KiB state probes and materialized a full
snapshot only after two consecutive A observations would, on the **same fixed
state sequence**, transfer:

~~~text
68 * 4 KiB = 0.265625 MiB
full materializations = 0
~~~

Accounting reduction:

~~~text
~99.27%
~~~

This is deliberately not called a causal performance estimate.

Suppressing requests could change the real trajectory. The value is an upper
bound-style accounting demonstration of how expensive it is to use full
snapshot materialization as a health probe during transient recovery.

---

## 9. Updated dynamic model

The evidence now supports separating three dynamical components:

~~~text
Z_n = recovery state:
      H / established Accessible
      E / provisional reentry
      B / Blocked

S_n = service/failure time

z_n = slowly varying timing/controller residual state
~~~

A compact model is:

~~~text
Delta_n = S_n + mu + z_n + epsilon_n

z_n = phi z_(n-1) + eta_n
phi ~= 0.52   # residual model
~~~

with history-dependent transition kernel:

~~~text
P(Z_(n+1) | Z_n, recovery history)
~~~

rather than:

~~~text
P(Z_(n+1) | simple A/B label only)
~~~

The pressure state P_t remains a **causal hypothesis layer**, not an observed
state.

---

## 10. What remains unexplained

The current trace still cannot identify:

- what physical/client variable creates the AR(1)-like residual memory;
- whether the latency change is caused by rate limiting or merely coincident
  with it;
- whether the two 34-observation recovery tails reflect a real controller
  period;
- whether an independent client/capture reproduces E -> B rebound behavior;
- whether suppressing transient snapshot requests changes recovery time;
- the scope or implementation of production congestion control.

Those are now much narrower unknowns than at the start of the investigation.

---

## Reproduce

~~~bash
python3 scripts/deep_validate_trace.py
~~~

CI-style:

~~~bash
python3 scripts/deep_validate_trace.py \
  --permutations 5000 \
  --output /tmp/deep-validation.json
~~~

The GitHub Actions workflow checks the stable sensitivity plateau, AR(1)
selection, cross-epoch prediction, both change points, history-free posterior
predictive probability, epoch morphology, and fixed-trace accounting.


## 11. State-controlled memory and cross-epoch generalization

Two additional adversarial checks test whether the AR-like timing memory is
merely an omitted A/B-state artifact, and whether the history-aware H/E/B model
generalizes across active epochs.

### Residual memory after state and epoch controls

Adding current Blocked state and epoch as timing covariates does not remove the
AR-like residual dependence:

~~~text
service + Blocked + epoch:
  residual AR(1) phi ~= 0.514
  Delta BIC from adding AR(1) ~= -27.8
~~~

Including the provisional-reentry indicator also leaves strong residual memory.

Within consecutive same-state observations, the base timing residual remains
positively correlated:

~~~text
Accessible-only consecutive pairs: phi ~= 0.738
Blocked-only consecutive pairs:    phi ~= 0.664
~~~

Therefore the timing-memory result is difficult to explain solely as an
unmodeled A/B switch.

It still does not identify the physical source of the memory.

### Cross-epoch transition prediction

Train the transition model on one active epoch and score the other using
Jeffreys-posterior predictive probabilities.

~~~text
train epoch 1 -> test epoch 2:
  H/E/B log loss ~= 0.378
  A/B   log loss ~= 0.544

train epoch 2 -> test epoch 1:
  H/E/B log loss ~= 0.300
  A/B   log loss ~= 0.508
~~~

The history-aware model therefore predicts the held-out active epoch better in
both directions.

This is still replication within one user/session capture, not population
validation.

Reproduce:

~~~bash
python3 scripts/validate_model_generalization.py
~~~
