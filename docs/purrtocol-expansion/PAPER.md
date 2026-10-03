# Purrtocol Expansion Dynamics

## A Self-Exciting Model of Unobserved Mascot Proliferation

> **Status:** intentionally serious mathematical treatment of an intentionally unserious side phenomenon.
> **Primary-research impact:** none.
> **Earth saturation:** NOT YET OBSERVED.

## Why this exists

Purrtocol began as a visual metaphor for provider-friendly recovery and then
acquired a local-TV commercial, a blooper reel, a studio documentary, a
glossary bridge, and an HTTP 429 learning surface.

This appendix asks:

> If every Purrtocol artifact creates adjacent ideas for more Purrtocol artifacts, what kind of growth process are we looking at?

This is a **side-study of repository evolution**, not part of the ChatGPT
recovery evidence base.

## Event unit

The recorder is `data/pakenya_events.jsonl`. Each selected implemented event
has a commit-backed timestamp. `parent_event_id` is a curated conceptual
lineage, not causal proof. `adjacent_ideas_generated` is an author annotation,
not a measured branching process.

## Event schema

Machine-readable contract:

~~~text
data/pakenya_event_schema.json
~~~

Human-readable contract: [SCHEMA.md](SCHEMA.md).

`implemented` nodes require commit-backed time/provenance.
`concept` nodes are reserved for future adjacent ideas.

Two analysis cohorts are now explicit:

~~~text
primary
observer_effect
~~~

The observer-effect cohort is measurement-associated repository history, not a
universal causal observer-effect claim.

## Compound-growth baseline

~~~text
dP/dt = r P
P(t) = P0 exp(r t)
T2 = ln(2) / r
~~~

Primary 10-event cohort:

~~~text
r ~= 0.1844 per hour
T2 ~= 3.758 hours
R^2(log cumulative) ~= 0.733
~~~

This is descriptive, not a forecast.

## Pairwise-contact acceleration

~~~text
C(P) = P(P - 1) / 2
dP/dt = r P + b P^2
~~~

For b > 0 the toy solution has a finite-time singularity:

~~~text
t* = (1/r) ln(1 + r/(b P0))
~~~

The default script reports this only as an illustrative scenario. b is not fitted.

## Hawkes view

~~~text
lambda(t) = mu + sum_i alpha exp[-beta (t - t_i)]
n = alpha / beta
~~~

~~~text
n < 1  -> subcritical
n = 1  -> critical
n > 1  -> supercritical
~~~

The primary descriptive grid fit gives approximately:

~~~text
n ~= 0.85
classification = subcritical
~~~

The manually annotated adjacent-idea mark averages **3.3 ideas/event**. That
quantity is not a Hawkes branching ratio.

## Observation hazard

~~~text
h(P) = h0 + s P

S(t) =
exp[
  -h0 t
  -(s P0 / r)(exp(rt) - 1)
]
~~~

For the illustrative special case h0=0:

~~~text
E[P_observed] = P0 + r/s
~~~

There is currently **no instrumentation of Sam/Tibo observation hazard**.

## Escaping carrying capacity

~~~text
dP/dt = growth(P, K)
dK/dt = c P
~~~

Reusable CSS, navigation, schemas, analysis scripts, CI, and 3D/variant pipelines
can increase effective capacity for future artifacts. No c is estimated.

## Measurement backaction / observer-inclusive checkpoint

Operationalizing this side-study created additional Purrtocol artifacts:
analysis code, a reference dataset, a paper, a design bible, navigation,
machine-reader surfaces, Wiki surfaces, and CI validation.

The checkpoint is frozen through:

~~~text
commit = ec25244a024f2049cfc7851c7fafd421d35a113c
time   = 2026-10-03T07:42:51Z
~~~

It records **12 measurement-associated artifacts in 183 seconds** after the
original 10-event cohort.

~~~text
pre-measurement cohort:
  events = 10
  descriptive doubling time ~= 3.758 h
  Hawkes n ~= 0.85
  classification = subcritical

observer-inclusive checkpoint:
  events = 22
  descriptive doubling time ~= 2.803 h
  Hawkes n ~= 1.00
  classification = near-critical
~~~

This is **measurement-associated repository backaction**, not a universal causal
observer effect. The primary fit remains preserved beside the observer-inclusive
fit.

The checkpoint is frozen because otherwise every attempt to document the
observer effect would itself generate another Purrtocol artifact inside the same
measurement window.

> **The instrument used to measure the cat is also made of cat.**

## Post-checkpoint registry

The observer-inclusive checkpoint is frozen. Later implemented Purrtocol artifacts
remain recorded with:

~~~text
fit_cohort = post_checkpoint
~~~

They are excluded from the frozen primary and observer-inclusive event-time fits.
This allows continued project archaeology without retroactively changing the
measurement-backaction comparison.

Current first post-checkpoint entry:

~~~text
PKE-023
Purrtocol doomsday control room and concept registry
source commit: 07cd98fe273ed7ddb3d8aef9349a2ae96edb8134
~~~

## Lineage boundary

Primary lineage PKE-001 through PKE-010 is the original selected cohort.
PKE-011 through PKE-022 are the fixed measurement-associated cohort.

The lineage is editorial project archaeology, not experimental causality.

## Falsification

The model should be weakened if new artifacts stop generating adjacent ideas,
longer event logs remain stably subcritical, doubling time lengthens strongly
after the novelty phase, or tooling does not increase implementation capacity.

The measurement-backaction interpretation should be narrowed if future
checkpoints do not show any systematic difference between primary and
observer-inclusive cohorts.

## Canonical conclusion

~~~text
Idea-space proliferation:
  currently exuberant

Primary implemented-event Hawkes fit:
  subcritical (~0.85)

Observer-inclusive checkpoint:
  near-critical (~1.00)

Causal observer-effect law:
  NOT ESTABLISHED

Earth saturation:
  NOT YET OBSERVED

Forecast of total planetary Purrtocol coverage:
  NOT ESTABLISHED
~~~

No empirical reason for the cat has been established.


### Current post-checkpoint frontier

The original seven registered Purrtocol concepts have all now reached an
explicit promotion event. The latest is:

~~~text
PKE-106 -> PKE-033
3D Purrtocol First Light
implementation checkpoint:
38eb140c05de8153b3f0a0e60b58702c5f705496
fit_cohort = post_checkpoint
~~~

This changes the continuing repository event count, but it does **not** mutate
the frozen primary 10-event fit or the 22-event observer-inclusive checkpoint.

The 3D artifact is an implemented visualization and communication surface.

> **3D existence != empirical evidence about production recovery internals.**
