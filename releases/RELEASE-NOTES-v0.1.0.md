# v0.1.0 - Recover. Don't amplify.

This is the first coherent public research release of ChatGPT Conversation Recovery Dynamics.

## What began as

> "Why does this conversation keep failing to load?"

has turned into:

- a sanitized failure trace;
- a state-transition study;
- a timing-law analysis;
- a history-aware recovery model;
- residual time-series validation;
- change-point detection;
- Monte Carlo recovery design;
- popular-server congestion simulation;
- provider-friendly recovery guidance;
- a bilingual local-only user Recovery Helper;
- an animated research portal;
- and, regrettably, a cat mascot.

## Headline findings

Within this capture:

~~~text
108 paired observations
48 Accessible
60 Blocked
0 mixed
~~~

The first Accessible observation after Blocked rebounded:

~~~text
B -> E -> B : 8
B -> E -> H : 0
~~~

The cycle-time relation is approximately:

~~~text
Delta ~= 5.616 + 0.957 * service_time
~~~

and the remaining residual has one-step memory:

~~~text
phi ~= 0.524
~~~

The proposed recovery architecture is:

~~~text
single-flight
 -> cheap observe
 -> provisional recovery
 -> stable confirmation
 -> materialize once
 -> atomic reconcile
 -> optional realtime
~~~

## Provider-friendly stress result

At abstract base rho=0.90:

~~~text
naive retry amplification          ~18.54x
server-friendly stack              ~ 3.98x
~~~

This is a local simulation result, not OpenAI production telemetry.

## User-facing addition

The Recovery Helper is bilingual, local-only, and intentionally performs no automatic ChatGPT/OpenAI request.

## Motto

> **Recover. Don't amplify.**

And, equally important:

> **Visualization != Evidence.**
