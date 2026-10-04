# ChatGPT Conversation Recovery Dynamics

> Reproducible client-side recovery research, provider-friendly recovery design, and an increasingly unnecessary Purrtocol universe.

## Start here

- [Evidence ledger](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/evidence-ledger.md): observed, recomputed, modeled, simulated, proposed, weak external, and unknown claims.
- [Recovery architecture](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/recovery-design.md): start-anchored retry, single-flight, observation before materialization, and hysteresis.
- [Deep validation](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/deep-validation.md): residual memory, change points, sensitivity checks, and cross-epoch prediction.
- [Provider-friendly congestion design](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/server-friendly-congestion-control.md): retry amplification, bounded admission, and graceful degradation.
- [Public reproduction](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/scripts/analyze_public_data.py): standard-library reconstruction from sanitized derivatives.

## 429 Survival Kit

- [Interactive rescue console](./429-survival-kit/)
- [Technical guide](./429-survival-kit/index.md)
- [Machine contract](./429-survival-kit/contract.json)
- [Purrtocol 429 Peace Junction](./purrtocol-429-peace-bridge/) — visualization of separately frozen Python/Node and Python/Go local conformance baselines

Core rule: **Retry-After is a floor; jitter must not pull a client earlier.**

## Purrtocol

Purrtocol is an anthropomorphic error model for recovery systems.

- [Design Bible](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/purrtocol-design-bible.md)
- [Purrtocol Expansion Dynamics](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/purrtocol-expansion/PAPER.md)
- [Variant Protocol](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/PURRTOCOL_VARIANTS.md)
- [Variant Foundry](./purrtocol-variant-foundry/index.md)
- [Genome Nursery](./purrtocol-nursery/index.md) — deterministic concept breeding; theoretical genotype space is not artifact count
- [Entropy Reactor](./purrtocol-entropy/index.md) — fixed-seed breeder diversity/entropy regression probe
- [Machine discovery manifest](./purrtocol.json)
- [3D First Light](./purrtocol-3d/index.md)
- [3D contract](./purrtocol-3d/README.md)

Current 3D status: **PKE-106 → PKE-033 IMPLEMENTED FIRST LIGHT**. A 7,672-byte GLB with six semantic animations is live and CI-validated.

## Evidence boundary

The repository does not establish OpenAI's internal root cause, production topology, exact rate-limit scope, or production capacity.

Raw authenticated HARs are not public.

**Recover. Don't amplify.**

**Visualization != Evidence.**


## Repository Observatory

The repository now runs a closed improvement loop:

`observe -> biopsy -> smallest reversible change -> verify -> promote -> re-observe`

- [Repository Observatory](./repository-observatory/index.md)
- [Improvement Loop Contract](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/IMPROVEMENT_LOOP.md)
- [Improvement Event Ledger](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/data/improvement_events.jsonl)

The observatory is itself part of the system and may create CI/maintenance load. That observer effect is explicit.


## Meta Improvement Loop

The repository now measures the improvement loop itself.

First four-cycle checkpoint:

```text
median cycle                    631.5 s
observation -> first change     488.0 s
last change -> verification      41.5 s
verification -> promotion        32.5 s
```

The first selected tuning is a [Critic Router](./repository-observatory/critic-router.md):
changed paths are routed to cheap source-proximate diagnostics before the full promotion gates.

- [Meta Improvement Loop](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/META_IMPROVEMENT_LOOP.md)
- [Meta Loop Reference](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/data/meta_improvement_loop_reference.json)
- [Repository Observatory](./repository-observatory/)
