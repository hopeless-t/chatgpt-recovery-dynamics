# Purrtocol Recovery Safety Frontier

Status: **modeled / bounded / synthetic**

This lane extends the Recovery Policy Lab from single interventions to explicit intervention packages.

The goal is not to crown a universal policy winner. It asks a narrower question:

> Which intervention packages restore the modeled shared-capacity gate, and which of those are inclusion-minimal?

## Frontier definition

A package is on the v0 Safety Frontier when:

1. its modeled shared-connection-capacity gate passes; and
2. no proper non-empty subset of the package also passes.

This is an **inclusion-minimal** result only.

`inclusion-minimal != cheapest`

`fewest levers != lowest operational cost`

Different mechanisms do not share an invented unit of cost. A retry-depth cap, fanout cap, connection-hold reduction, failure reduction, and capacity expansion remain different interventions unless a future measurement contract gives them comparable observed costs.

## Why packages matter

The synthetic aggressive policy used by the Connection Amplification model has:

- baseline request rate: 40 req/s
- shared connection capacity: 100
- fanout: 4 connections/attempt
- failure probability: 0.7
- retry multiplier: 1.5
- hold time: 0.5 s
- retry depth: 4

Its modeled expected concurrent connection demand is **442.0505**, far above the capacity gate.

A strong-looking local intervention can still be insufficient. For example, fanout `4 -> 1` leaves expected concurrency at **110.512625**, still above capacity 100.

v0 therefore includes a deliberate complementarity case:

- `fanout-cap`: fanout `4 -> 1` — unsafe alone
- `retry-multiplier-cap`: retry multiplier `1.5 -> 1.0` — unsafe alone
- both together — expected concurrency **55.462**, inside capacity

The frontier records this as structural complementarity in the model. It does **not** claim those exact values describe OpenAI infrastructure.

## Fail-closed package semantics

Each lever owns explicit modeled fields. If two levers in one package attempt to override the same policy or scenario field, the package is rejected rather than applying hidden ordering.

This avoids a misleading result where package meaning depends on arbitrary list order.

## Bounded search

The implementation enumerates finite combinations only:

- at most 12 candidate levers;
- at most 6 levers in one package;
- explicit `max_package_size` in every run;
- no infinite optimization or provider-topology inference.

## Evidence boundary

The public 2026-09-29 OpenAI cross-product incident motivated the research direction, especially the risk that failure-triggered recovery work can consume shared network capacity.

This Safety Frontier is **not** a reconstruction of OpenAI's exact topology, thresholds, retry policies, or remediation costs. Its equations and CI scenarios are synthetic bounded models.

## World laws

- `Capacity gate before policy preference`
- `Safe package != universal winner`
- `Inclusion-minimal != cheapest`
- `Unsafe singletons can form a safe package`
- `Conflicting overrides fail closed`
- `Different mechanisms do not share an invented cost unit`
- `Modeled frontier != provider topology`
- `Recover. Don't amplify.`

## Next evolution

A later lane may add observed or separately calibrated intervention costs and then construct a genuine multi-objective frontier. Until such measurements exist, v0 refuses to manufacture a scalar cost function.
