# Purrtocol Civilization

> **If it cannot project itself as interesting, it does not survive.**

Purrtocol Civilization is an experimental world layered on top of Recovery Dynamics. It studies how bounded recovery agents evolve when compute, memory, bandwidth, retry budget, human attention, and cultural memory are scarce.

This is a simulation/projection surface, not evidence about production systems.

## World law

Every organism must satisfy two independent gates:

1. **Recovery viability** — it must preserve the safety/evidence invariants of the Recovery Survival Contract.
2. **Projection viability** — it must turn what happened into a compact artifact that a human would plausibly choose to inspect again.

An organism that is technically efficient but persistently incomprehensible or boring may lose cultural reproduction opportunities. An organism that is entertaining but breaks recovery/evidence invariants is disqualified rather than rewarded.

`fun != truth`, and `truth != automatically interesting`.

## Scarce resources

Each season has bounded budgets for:

- compute / execution energy
- memory / resident state
- bandwidth
- retry attempts
- latency
- human attention
- cultural-memory capacity

No resource is treated as actually monetary. Currency, prices, bids, and wealth inside this world are simulated accounting units only.

## Organisms

A Purrtocol organism can specialize in one or more ecological roles:

- Observer — spends budget on re-observation and uncertainty reduction.
- Executor — materializes useful work when replay safety permits.
- Cache Keeper — trades memory cost for avoided recomputation.
- Broker — routes tasks/resources between specialists.
- Archivist — preserves cultural knowledge across generations.
- Teacher — compresses discoveries into reusable explanations.
- Projector — turns validated events into interesting human-facing stories.
- Auditor — rejects attractive stories that outrun evidence.

Roles are not hard-coded species. Evolution may discover mixtures or new niches.

## Minimal economy

For organism `i` in environment `e`, start with a deliberately inspectable utility model:

`U_i = value - compute_cost - retry_cost - latency_cost - memory_cost + shared_value`

Survival is multi-objective. Do not collapse everything into one scalar without preserving the component ledger.

The civilization should observe emergent exchange rather than assume that a market is always optimal. Candidate regimes include:

- isolated competition
- reciprocal exchange
- shared commons
- reputation/credit
- auction-like task allocation
- central scheduler
- guild/cooperative specialization
- hybrid institutions

## Projection pressure

A season produces a **Civilization News** artifact. Projection fitness is evaluated separately on:

- novelty
- comprehensibility
- surprise
- explanatory value
- replay value: would the human want another season?

The projector never gets permission to manufacture events. Its source must be the season ledger. The Auditor can veto unsupported claims.

Anti-Goodhart rule: do not optimize raw joke count, cat count, word count, sensationalism, commits, files, views, clones, stars, or forks as a proxy for interestingness.

## Evolution -> culture -> institutions

The long-horizon experiment intentionally separates four clocks:

1. **Genetic/evolution clock** — traits vary across organisms/generations.
2. **Learning clock** — an organism adapts during its own lifetime.
3. **Culture clock** — discoveries persist after an organism disappears.
4. **Institution clock** — the civilization changes rules for allocating scarce resources.

A major target phenomenon is the point where cultural/institutional adaptation becomes faster or more effective than genetic adaptation.

## Civilization self-research

A mature civilization may inspect its own sanitized season ledgers, propose competing institutional changes, fork into bounded counterfactual worlds, and compare outcomes.

`World -> Observer -> Model -> Proposed Policy -> Forked World -> Observation`

Policy proposals never rewrite historical evidence.

## Season output

Every bounded season should eventually emit machine-readable metrics plus a human projection such as:

> **Purrtocol Civilization Chronicle — Season N**
>
> Retry prices spiked after a failure storm. Cache Keepers gained influence, but an Auditor coalition blocked a fashionable explanation unsupported by the ledger. A new Observe-First guild appeared. Three technically successful species went culturally extinct because nobody could understand what they had accomplished.

The exact news must be generated from actual simulation output; the paragraph above is only an illustration.

## Achievement, never ending

Named observers, first external implementations, independent convergent implementations, citations, and unexpected ecosystem events may unlock achievements. No achievement is a shutdown condition.

> **NO FINAL BOSS.**

## Bootstrap phases

### Phase C0 — Environment
- deterministic seeded seasons
- bounded resource ledger
- organism role/trait schema
- explicit recovery and projection gates
- JSON season output

### Phase C1 — Ecology
- mutation / selection
- niches and specialization
- extinction and lineage tracking
- projection fitness measured separately from technical fitness

### Phase C2 — Economy
- exchange, reputation, commons, auctions, scheduler baselines
- inequality/concentration/resource-waste metrics
- retry amplification and rebound-effect metrics

### Phase C3 — Culture
- persistent discoveries
- teaching/compression cost
- forgetting and archive pressure
- cultural mutation and misinformation resistance

### Phase C4 — Institutions
- rule proposals
- bounded counterfactual forks
- institutional selection
- civilization self-research

### Phase C5 — Projection World
- Civilization News generated only from ledgers
- season timeline and achievements
- human-interest survival pressure
- optional 3D/world projection without treating visualization as evidence

The first implementation should remain small, deterministic, inspectable, and cheap enough for CI. Complexity earns its way in only when a simpler model cannot expose the phenomenon under study.