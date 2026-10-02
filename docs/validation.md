# Validation and model audit

This note records an independent recomputation of the published derivative
telemetry. It intentionally uses the sanitized public JSONL/CSV rather than the
raw HAR files.

## Result

The core observation survives recomputation, but one part of the original
explanation is better replaced by a stronger and more parsimonious mechanism:

> the blocked regime does not need an explicitly more aggressive retry policy to
> produce a higher attempt cadence. Fast failure plus completion-coupled polling
> is sufficient.

The data therefore support **cadence amplification** more directly than they
support the stronger claim that the client deliberately increases retry
aggressiveness when observability falls.

## Recomputed observations

The public JSONL reproduces the published pairing exactly:

- 108 stream/snapshot pairs;
- 48 (200, 200) accessible pairs;
- 60 (no_http_response, 429) blocked pairs;
- 0 mixed pairs;
- maximum observed pair-start skew: 9 ms.

### Session boundary correction

There is one approximately 775.640 s gap between active observation epochs.
Treating the observations immediately before and after that gap as one ordinary
state transition biases the transition matrix slightly.

With that cross-epoch transition treated as censored:

- Accessible -> Accessible: 38
- Accessible -> Blocked: 10
- Blocked -> Accessible: 8
- Blocked -> Blocked: 50

Thus:

- P(Blocked next | Accessible) = 0.208333
- P(Blocked next | Blocked) = 0.862069

The corresponding Wilson 95% intervals are approximately:

- Accessible -> Blocked: [0.117, 0.343]
- Blocked -> Blocked: [0.751, 0.928]

This still shows strong state persistence, but the corrected value should be
used for active-epoch transition analysis.

## The strongest new result: cycle-time decomposition

For every active within-epoch transition, define:

- S_n = the slower of the paired stream/snapshot request latencies;
- Delta_n = start-to-start time until the next pair;
- W_n = Delta_n - S_n = residual post-completion wait.

A least-squares fit on 106 active transitions gives:

~~~text
Delta_n ~= 5.6164 + 0.9566 * S_n
R^2 = 0.99136
~~~

A robust Theil-Sen fit gives approximately:

~~~text
Delta_n ~= 5.7017 + 0.9220 * S_n
~~~

The residual post-completion wait is similar in both regimes:

- Accessible median: about 5.383 s
- Blocked median: about 5.647 s

Adding a blocked-state indicator after service time changes the fitted cycle
time by only about -0.0066 s and does not materially improve fit.

That strongly suggests this public trace is compatible with a
**completion-coupled loop**:

~~~text
request starts
   -> request completes/fails
   -> roughly fixed wait
   -> next observation cycle starts
~~~

rather than requiring a policy that explicitly shortens its configured wait
because the system entered the blocked regime.

## Connection to queueing theory

The pattern is a one-client special case of the interactive response-time law:

~~~text
N = X * (R + Z)
~~~

For one circulating observation loop, N = 1, so:

~~~text
X ~= 1 / (R + Z)
~~~

where R is request/response time and Z is the post-completion delay.

The accessible mean start-to-start gap in active epochs is about 10.843 s,
while the blocked mean is about 6.036 s. That corresponds to an observed
pair-initiation rate increase of about 1.80x. The median-gap ratio is about
1.71x.

Reference: Peter J. Denning, Queueing Networks, response-time law:
https://denninginstitute.com/pjd/PUBS/ENC/qn08.pdf

## Observation-count bias

Because blocked cycles are shorter, counting observations overweights the
blocked regime relative to wall-clock time.

- blocked fraction by pair count: 60 / 108 = 55.6%
- blocked fraction across active start-to-start time: about 40.2%

This is why the process is better described as a **Markov renewal /
semi-Markov observation process** when continuous-time occupancy matters:
the embedded state sequence and the state-dependent holding times carry
different information.

## Markov persistence

After censoring the long inactive gap, the embedded transition matrix is:

~~~text
             next A    next B
current A    0.7917    0.2083
current B    0.1379    0.8621
~~~

There are only eight uncensored exits from blocked runs, so the dataset is too
small to establish a more complicated duration-dependent escape law. The
completed blocked-run mean (7.0 observations) is close to the geometric mean
implied by the fitted exit probability (about 7.25 observations). A plain
first-order Markov model is therefore not rejected for the embedded state
sequence, while the timing layer still benefits from a semi-Markov treatment.

## Two active epochs

The blocked persistence estimate is identical in both active epochs:

- epoch 1: P(B -> B) = 25 / 29 = 0.8621
- epoch 2: P(B -> B) = 25 / 29 = 0.8621

The accessible-to-blocked entry fraction differs:

- epoch 1: 5 / 36 = 0.1389
- epoch 2: 5 / 12 = 0.4167

With this small sample, a two-sided Fisher exact comparison is not conclusive
(p ~= 0.094). It is best treated as a hint that entry hazard may depend on an
unobserved slow state such as rate-limit headroom, account/service load, or
another external variable.

## Resume ordering

The two public resume-404 episodes still precede later snapshot-429 periods:

- 349.013 s with 32 successful snapshots first;
- 87.853 s with 8 successful snapshots first.

Using the published 4 KiB-rounded payload field, those successful snapshots
sum to:

- 146.375 MiB;
- 36.594 MiB.

Earlier README values were calculated from pre-rounding source sizes and could
not be reproduced exactly from the public derivative data. The repository now
uses the public-data-reproducible values.

These episodes are compatible with a recovery-first story, but do not prove
that a resume 404 causes a later 429. They also argue against a simple fixed
successful-snapshot-count or fixed-byte threshold, because the two episodes
reach 429 after very different accumulated counts/bytes.

## Numerical precision audit

The cycle-time regression is numerically well conditioned:

- condition number of the two-column design matrix: about 5.62;
- condition number of the normal matrix: about 31.6.

Recomputing the two-parameter fit with 80-digit arithmetic agrees with ordinary
binary64 at all displayed digits.

The Ozaki scheme is designed for accurate matrix multiplication by decomposing
operands so lower-precision products can be combined with high accuracy. That
is valuable for large or ill-conditioned matrix computations, but it is not the
limiting error source here. The public telemetry is rounded to millisecond /
4 KiB-scale quantities and contains observational uncertainty that dominates
floating-point roundoff.

Reference:
K. Ozaki and T. Koizumi, Fast and accurate algorithms for matrix multiplication
using fused multiply-add and their rounding error analysis (2026):
https://doi.org/10.1007/s13160-026-00816-8

## What is supported vs. not supported

### Directly supported by this capture

- perfect coupling of the two paired observation classes in 108 retained pairs;
- much faster failure latency in the blocked regime;
- higher observation-cycle frequency in the blocked regime;
- strong blocked-state persistence within active epochs;
- cycle time is almost completely explained by service/failure time plus a
  roughly fixed post-completion delay.

### Compatible, but not established

- a recovery-generated observation loop contributes to 429 pressure;
- a latent rate-limit / capacity state drives entry into the blocked regime;
- the same mechanism explains other users or other ChatGPT clients.

### Not established

- OpenAI's internal implementation;
- the scope or exact policy of any rate limiter;
- that resume 404 causes 429;
- that WebSocket failure is the initiating cause;
- that the client intentionally selects a shorter retry delay while blocked.

## Reproduce

Run:

~~~bash
python3 scripts/analyze_public_data.py
~~~

The script starts from data/session_b_events.jsonl, reconstructs the 108 pairs,
censors the long inactive boundary, and emits the public statistics as JSON.


## Deep validation

A separate harness now checks whether the main results depend on analysis
choices or leave structured residual dynamics.

### Threshold sensitivity

Pairing is identical from 10 ms through 100 ms:

~~~text
108 pairs
48 Accessible
60 Blocked
0 mixed
~~~

The active transition matrix is identical for epoch-gap thresholds from 20 s
through 600 s:

~~~text
A -> A: 38
A -> B: 10
B -> A:  8
B -> B: 50
~~~

This means the primary counts are not artifacts of choosing exactly 50 ms and
60 s.

### Cross-epoch timing replication

Fit on epoch 1, test on epoch 2:

~~~text
RMSE ~= 0.259 s
~~~

Fit on epoch 2, test on epoch 1:

~~~text
RMSE ~= 0.251 s
~~~

The approximately-one-for-one service-time coefficient reproduces across the
two active epochs.

### Residual memory

The high-R² cycle law leaves temporally correlated residuals.

AR(1):

~~~text
phi ~= 0.524
Delta BIC vs independent residuals ~= -29.3
SSE reduction ~= 27.4%
~~~

Post-completion wait itself has:

~~~text
phi_W ~= 0.676
~~~

This motivates a latent timing/controller state rather than a perfectly fixed
sleep timer.

### Change points

The optimal one-change-point fit to service time coincides exactly with the
first Blocked observation in both epochs.

~~~text
epoch 1: index 32, SSE reduction ~= 65.8%
epoch 2: index  8, SSE reduction ~= 58.7%
~~~

The CI permutation reference gives p ~= 0.00020 per epoch for a maximum
reduction at least this large.

### Posterior predictive check

Under a history-free A/B transition model:

~~~text
p_AB | data ~ Beta(10.5, 38.5)
~~~

the posterior-predictive probability of all eight reentry Accessible samples
immediately returning to Blocked is:

~~~text
~2.31e-5
~~~

### Fixed-trace materialization accounting

From the first Blocked observation onward, eight transient successful snapshots
represent 36.59375 MiB of rounded payload.

Holding the observed state path fixed, 68 conceptual 4 KiB probes with a
two-success stability rule would transfer 0.265625 MiB and materialize no full
snapshot during those transient excursions.

Accounting reduction:

~~~text
~99.27%
~~~

This is not a causal production estimate. It is fixed-trace accounting.

See [deep-validation.md](deep-validation.md) and
[data/deep_validation_reference.json](../data/deep_validation_reference.json).
