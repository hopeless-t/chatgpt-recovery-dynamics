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

Core rule: **Retry-After is a floor; jitter must not pull a client earlier.**

## Purrtocol

Purrtocol is an anthropomorphic error model for recovery systems.

- [Design Bible](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/purrtocol-design-bible.md)
- [Purrtocol Expansion Dynamics](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/purrtocol-expansion/PAPER.md)
- [Variant Protocol](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/PURRTOCOL_VARIANTS.md)
- [Variant Foundry](./purrtocol-variant-foundry/index.md)
- [Genome Nursery](./purrtocol-nursery/index.md) — deterministic concept breeding; theoretical genotype space is not artifact count
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
