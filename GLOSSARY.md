# Glossary

## A / Accessible
A paired observation in which the relevant stream-status and conversation snapshot observations are both accessible.

## B / Blocked
A paired observation representing the blocked regime in the public trace.

## E / Recovering / provisional recovery
The first Accessible observation immediately after Blocked. It is modeled separately because its next-state behavior differs from established Accessible state in this capture.

## H / Healthy
Established Accessible state after stable confirmation.

## Recovery hysteresis
The rule that one success is not enough to reset failure history or declare stable recovery.

## Single-flight
Coalescing many local recovery triggers into one logical network recovery owner.

## Cheap observation
A conceptual small state/version check used before expensive snapshot materialization.

## Snapshot materialization
Fetching/building the readable conversation representation required to reconcile the UI.

## Start-anchored retry
Retry scheduling based on start-to-start spacing so a fast failure cannot automatically shorten the next retry interval.

## Retry amplification
~~~text
network recovery attempts / logical recovery demand
~~~

## Pressure knee
The load region where latency, rejection, or recovery behavior changes sharply.

## rho / utilization
In local congestion simulations:
~~~text
rho = exogenous foreground offered work / nominal service capacity
~~~
before adding recovery traffic.

## Trace-preserving replay
Counterfactual accounting that holds the observed state sequence fixed while changing only what would have been materialized/transferred. It is not a causal production estimate.

## Posterior predictive check
A Bayesian check asking how likely an observed pattern is under a fitted model.

## Change point
A statistically selected position where a time-series mean or other property changes.

## AR(1)
A one-step autoregressive residual model:
~~~text
u_n = phi * u_(n-1) + epsilon_n
~~~

## DCS / dissociated control state
A systems-engineering framing in which partially independent subsystems can be in different operational states simultaneously.

## Transport Survival Plane
The recovery principle that durable application state survives changes in transport attempts or connections.

## Provider-friendly recovery
A recovery architecture that attempts to improve user recovery while reducing avoidable duplicate work, retries, bytes, queue growth, and materialization cost.

## Visualization != Evidence
A repository-wide rule: design visuals explain; they do not upgrade a hypothesis into observed fact.
