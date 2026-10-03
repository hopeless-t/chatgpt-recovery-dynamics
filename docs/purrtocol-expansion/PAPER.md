# Purrtocol Expansion Dynamics

## A Self-Exciting Model of Unobserved Mascot Proliferation

> **Status:** intentionally serious mathematical treatment of an intentionally unserious side phenomenon.
> **Primary-research impact:** none.
> **Earth saturation:** NOT YET OBSERVED.

## Why this exists

Purrtocol began as a visual metaphor for provider-friendly recovery and then acquired a local-TV commercial, a blooper reel, a studio documentary, a glossary bridge, and an HTTP 429 learning surface.

This appendix asks:

> If every Purrtocol artifact creates adjacent ideas for more Purrtocol artifacts, what kind of growth process are we looking at?

This is a **side-study of repository evolution**, not part of the ChatGPT recovery evidence base.

## Event unit

The recorder is data/pakenya_events.jsonl. Each selected implemented event has a commit-backed timestamp. parent_event_id is a curated conceptual lineage, not causal proof. adjacent_ideas_generated is an author annotation, not a measured branching process.

## Compound-growth baseline

~~~text
dP/dt = r P
P(t) = P0 exp(r t)
T2 = ln(2) / r
~~~

Initial selected 10-event log:

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

The toy solution has a finite-time singularity for b > 0:

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

The first descriptive grid fit gives approximately n ~= 0.85: **subcritical**.

The manually annotated adjacent-idea mark averages **3.3 ideas/event**, and observed parents have **1.5 implemented children/parent**, but neither quantity is a Hawkes branching ratio. The current selected commit sequence therefore does **not** establish supercritical implementation growth.

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

Reusable CSS, navigation, schemas, analysis scripts, CI, and future 3D pipelines can increase effective capacity for future artifacts. No c is estimated.

## Lineage

~~~text
PKE-001 Canonical identity
├─ PKE-002 SVG
├─ PKE-003 Wiki
└─ PKE-004 Local-TV commercial
   └─ PKE-005 Expanded universe
      └─ PKE-006 Blooper reel
         └─ PKE-007 Studio documentary
            └─ PKE-008 Glossary / education bridge
               ├─ PKE-009 CM-to-glossary link
               └─ PKE-010 429 learning surface
~~~

The lineage is editorial project archaeology, not experimental causality.

## Falsification

The model should be weakened if new artifacts stop generating adjacent ideas, longer event logs remain stably subcritical, doubling time lengthens strongly after the novelty phase, or tooling does not increase implementation capacity.

## Canonical conclusion

~~~text
Idea-space proliferation:
  currently exuberant

Implemented-event Hawkes fit:
  currently subcritical (~0.85)

Earth saturation:
  NOT YET OBSERVED

Forecast of total planetary Purrtocol coverage:
  NOT ESTABLISHED
~~~

No empirical reason for the cat has been established.
