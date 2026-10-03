# Latent Timing Model Competition

> Status: **DESIGN + EXECUTABLE MODEL COMPETITION / RESULT NOT YET PROMOTED**

The public recovery trace has a high-R² cycle law:

```text
Delta_n ~= 5.6164 + 0.9566 * service_time_n + u_n
```

but `u_n` is not independent noise. Existing deep validation finds useful one-step
predictive memory, approximately `phi ~= 0.524`.

That does **not** identify a scheduler, timer, transport controller, backend queue,
or any other physical mechanism.

This study asks a narrower question:

> **What small statistical state representation best predicts the remaining timing residual within this capture?**

## Candidate models

### M0 — IID Gaussian residuals

No temporal memory.

```text
u_n ~ Normal(mu, sigma^2)
```

This is the null timing model.

### M1 — observed A/B-conditioned Gaussian

Residual distribution may differ according to the directly observed current
Accessible/Blocked state, but has no extra temporal memory.

This is a confounding control:

> Is apparent memory just another way of rediscovering the observed A/B regime?

It is not a causal model.

### M2 — AR(1) continuous memory

```text
u_n = c + phi * u_(n-1) + epsilon_n
```

This represents a continuously valued one-step latent carryover.

Existing validation already indicates that this family is useful. The new study
puts it in direct competition with a qualitatively different hidden-state model.

### M3 — two-state Gaussian HMM

A discrete latent state switches according to a 2x2 Markov transition matrix,
and each latent state emits residuals from its own Gaussian distribution.

This asks whether a small **discrete regime** can explain the same persistence
that AR(1) captures continuously.

The latent labels are intentionally unnamed.

They are **not** called scheduler mode, timer mode, queue mode, transport state,
or server state.

## Evaluation

Two complementary tests are used.

### Within-capture BIC

All 106 within-epoch transitions are used.

Lower BIC rewards likelihood while penalizing parameter count.

This is descriptive model selection inside the same capture.

### Cross-epoch prediction

The two active epochs are used as two folds:

```text
fit epoch 1 -> score epoch 2
fit epoch 2 -> score epoch 1
```

For each fold:

1. fit the cycle law on the training epoch;
2. compute training and test residuals using that training law;
3. fit each residual model only on training residuals;
4. score held-out residuals by mean negative log-likelihood.

This is stronger than same-sample BIC, but it remains replication **within one
capture**, not population validation.

## HMM fitting

The HMM uses standard-library log-space forward/backward and Baum-Welch EM.

Multiple starts vary:

- initial emission quantiles;
- initial state persistence.

A variance floor prevents a tiny state from collapsing onto an individual point.

State labels are canonicalized by increasing emission mean only for readable
output.

## Interpretation rules

Do not promote any of the following merely because one model wins:

- “there are exactly two physical controller states”;
- “the AR state is the browser event loop”;
- “the HMM state is a server-side rate-limit phase”;
- “the model describes OpenAI internals”.

Allowed conclusion shape:

> **Within this capture, model X is more/less useful than model Y for compressing or predicting residual timing structure under the tested scoring rule.**

If AR(1) wins cross-epoch prediction, the evidence favors a compact continuous
one-step predictive state over the tested discrete alternative.

If HMM wins, the evidence favors a compact discrete latent-regime description
over the tested AR(1) alternative.

If the rankings disagree, that disagreement is itself a result and should weaken
the temptation to name a mechanism.

## Reproduce

```bash
python scripts/latent_timing_model_competition.py \
  --output /tmp/latent-timing-models.json
```

CI initially checks only structural invariants.

**The winner is deliberately not frozen before the first observed CI result.**

## External validity

**NOT ESTABLISHED.**

There are only two active epochs from one sanitized capture.

The highest-value next evidence remains an independent trace from a different
session/client/time period.

**Prediction != mechanism identification.**
