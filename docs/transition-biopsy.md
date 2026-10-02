# A -> B transition biopsy

## Question

The earlier analysis characterized the Blocked regime after it had already
appeared. This note asks the next question:

> What distinguishes an Accessible observation that stays Accessible from an
> Accessible observation whose **next** observation falls into Blocked?

Only public paired observations are used.

## Dataset

After censoring the approximately 775.640 s inactive epoch boundary:

- Accessible-origin transitions: **48**
- A -> A: **38**
- A -> B: **10**

## The strongest biopsy feature: recovery history

Define:

- **H** — Accessible and not immediately preceded by Blocked;
- **E** — an Accessible observation immediately preceded by Blocked;
- **B** — Blocked.

The observed A-origin contingency table is:

| Current Accessible history | Next B | Next A | Total |
|---|---:|---:|---:|
| E: immediately after B | **8** | **0** | 8 |
| H: not immediately after B | 2 | 38 | 40 |

Therefore:

~~~text
P(next B | E) = 8 / 8 = 1.000
P(next B | H) = 2 / 40 = 0.050
~~~

Wilson 95% intervals:

~~~text
E: [0.676, 1.000]
H: [0.0138, 0.165]
~~~

A one-sided Fisher exact calculation for the observed table gives:

~~~text
p ~= 1.19e-7
~~~

This is a strong **within-capture** association despite the very small E sample.

It should not be read as a population estimate.

## Interpretation

The capture contains eight observed transitions:

~~~text
B -> E -> B
~~~

and zero observed:

~~~text
B -> E -> H
~~~

within active epochs.

In other words, every observed one-cycle Accessible excursion after Blocked
rebounded immediately.

That directly supports a recovery-hysteresis rule:

> **one successful observation is not sufficient evidence of stable recovery.**

This is stronger than the earlier argument based only on visual inspection of
the state sequence.

## Other biopsy features

The A -> B rows do **not** show an obvious pre-transition latency collapse.

Median service time:

~~~text
A -> A: ~5.222 s
A -> B: ~4.786 s
~~~

Median stream latency:

~~~text
A -> A: ~3.552 s
A -> B: ~3.617 s
~~~

Payload size is uninformative in this public projection:

~~~text
all successful snapshots: 4684 KiB rounded
~~~

By contrast, previous start-to-start gap is highly different:

~~~text
A -> A median previous gap: ~10.272 s
A -> B median previous gap: ~5.998 s
~~~

This is not independent of reentry history: most A -> B transitions are the
single Accessible sample inside an already-active Blocked episode.

The correct interpretation is therefore not:

> a 6-second previous gap independently causes the next 429.

It is:

> the short previous gap is a **morphological marker of the Blocked/recovery
> regime** and largely co-travels with the B -> E -> B history pattern.

## Why this matters for protocol design

A client that maps:

~~~text
first 200 / first readable snapshot -> HEALTHY
~~~

would repeatedly reset its recovery state during these excursions.

That can create:

1. premature backoff reset;
2. repeated full snapshot downloads;
3. repeated realtime reattachment;
4. loss of accumulated failure history;
5. renewed retry amplification if the next failure fast-fails.

A better state machine needs an intermediate state:

~~~text
B --success--> E (Recovering / provisional)
E --stable confirmation--> H
E --failure--> B
~~~

This is the minimum state refinement justified by the current capture.

## Reproduce

~~~bash
python3 scripts/analyze_transition_biopsy.py
python3 scripts/compete_transition_models.py
~~~

The GitHub Actions workflow asserts the contingency table, Fisher result and
model-comparison direction on every change.

## Guardrail

There are only eight observed reentry samples.

The result is strong evidence that **history matters in this capture**. It is
not evidence that all ChatGPT conversation recovery events have a 100% rebound
probability after one successful observation.
