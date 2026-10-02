# Transition model competition

## Goal

Do not privilege the current explanation.

Compete simple candidate predictors of:

~~~text
P(next observation is Blocked | current observation is Accessible)
~~~

on the same 48 Accessible-origin transitions.

The dataset is small, so the primary competition uses exact Beta-Bernoulli
models with a Jeffreys prior instead of high-dimensional regression.

## Models

### M0 — constant hazard

One A -> B probability for every Accessible observation.

### M1 — epoch

Separate hazard for active epoch 1 vs epoch 2.

### M2 — reentry history

Separate hazard for:

- current A immediately preceded by B;
- current A not immediately preceded by B.

### M3 — previous gap < 8 s

The 8 s threshold is not optimized from A -> B labels. It is the midpoint
between the previously established ~6 s Blocked cadence and ~10 s Accessible
cadence.

### M4 — service time < 5 s

A coarse latency comparator. This is intentionally weak and is not tuned to
maximize classification.

### M5 — Accessible run length <= 2

A coarse history proxy.

## Scoring

Each Bernoulli stratum uses:

~~~text
p ~ Beta(1/2, 1/2)
~~~

The repository reports:

- exact integrated marginal likelihood;
- leave-one-out posterior predictive log loss;
- leave-one-out Brier score.

This avoids infinite maximum-likelihood coefficients from the observed 8/8
reentry rebounds.

## Result

The current reference run ranks **M2 reentry history** first by leave-one-out
predictive log loss:

| Model | LOO log loss | LOO Brier | log BF vs constant |
|---|---:|---:|---:|
| **M2 reentry history** | **0.199** | **0.0423** | **+15.07** |
| M3 previous gap <8 s | 0.205 | 0.0442 | +15.20* |
| M5 run length <=2 | 0.364 | 0.1069 | +7.84 |
| M1 epoch | 0.515 | 0.1662 | +0.56 |
| M0 constant | 0.533 | 0.1719 | 0 |
| M4 service <5 s | 0.547 | 0.1765 | -1.12 |

* M3 has two missing previous-gap rows and is strongly collinear with reentry
history. Its marginal likelihood must not be read as independent confirmation.

## First-order vs history-aware state model

The original embedded first-order chain was:

~~~text
A -> A: 38
A -> B: 10
B -> A:  8
B -> B: 50
~~~

A history-aware labeling gives:

~~~text
H -> H: 38
H -> B:  2

E -> B:  8
E -> H:  0

B -> E:  8
B -> B: 50
~~~

where E is the one-cycle Accessible excursion after B.

A simple likelihood competition gives approximately:

~~~text
first-order A/B:
  log L ~= -47.83
  AIC   ~=  99.67
  BIC   ~= 104.99

history-aware H/E/B:
  log L ~= -31.21
  AIC   ~=  68.42
  BIC   ~=  76.41

Delta AIC ~= -31.25
Delta BIC ~= -28.58
~~~

The history-aware model uses one additional Bernoulli hazard parameter.

This is a large within-capture improvement.

## Scientific consequence

The strongest current predictor of A -> B is **not the current successful
request latency**.

It is:

> **whether the current success is a reentry sample immediately after the
> Blocked regime.**

This changes the recovery design target.

The client should not only ask:

~~~text
Did this request succeed?
~~~

It should ask:

~~~text
Did this request succeed from a stable state,
or is it only the first provisional success after a Blocked epoch?
~~~

That is a state-estimation problem, not merely an HTTP-status problem.

## Next falsification target

Independent captures should test whether:

~~~text
P(next B | first A after B)
>>
P(next B | established A)
~~~

reproduces.

If the effect disappears in independent captures, the H/E split should be
downgraded or removed.

## Reproduce

~~~bash
python3 scripts/analyze_transition_biopsy.py
python3 scripts/compete_transition_models.py
~~~
