# Start Here

You cloned `chatgpt-recovery-dynamics`. This page is the shortest path to understanding what you now have.

> **Recover. Don't amplify.**

## In 30 seconds

This repository studies failure recovery when repeated attempts can make a degraded system worse.

The core idea is simple:

```text
failure or ambiguity
        ↓
observe durable state first
        ↓
separate operation identity from attempt identity
        ↓
retry only when policy and evidence permit it
        ↓
confirm stable recovery before declaring Healthy
```

This is a client-side research and reference implementation. It does **not** claim to reveal OpenAI's internal architecture or root cause.

## Pick your path

### I just want to run something

Go to [QUICKSTART.md](QUICKSTART.md).

You can run the loopback-only HTTP 429 fire drill locally without sending production traffic.

### I want to adopt the recovery semantics in my own system

Go to [ADOPT.md](ADOPT.md).

It extracts the reusable rules without requiring you to copy the entire research repository.

### I want the smallest stable contract

Read [Recovery Survival Contract v0.1](RECOVERY_SURVIVAL_CONTRACT_V0_1.md).

It defines the first intentionally small interoperability surface for operation identity, retry authorization, observation, replay safety, and recovery confidence.

### I want the evidence and mathematics

Start with:

- `docs/evidence-ledger.md`
- `docs/methodology.md`
- `docs/deep-validation.md`
- the main [README](README.md)

### I came for the cats

Excellent.

- [Purrtocol Variant Protocol](PURRTOCOL_VARIANTS.md)
- [Purrtocol Genome Nursery](https://hopeless-t.github.io/chatgpt-recovery-dynamics/purrtocol-nursery/)
- `docs/purrtocol-design-bible.md`

Purrtocol is the communication layer for the recovery ideas. The mascot may mutate freely; the evidence boundary may not.

> **Visualization != Evidence.**

## Six invariants worth carrying home

1. **Attempt != Operation.** A retry is another attempt at the same semantic operation, not automatically a new operation.
2. **UNKNOWN != retry permission.** Ambiguous completion must be re-observed before a non-idempotent action is replayed.
3. **Re-observation != re-execution.** Cheap state inspection and expensive side effects are different actions.
4. **Retry-After is a floor, not a suggestion to retry immediately.**
5. **First success != Healthy.** Recovery confidence needs confirmation/hysteresis.
6. **Recover. Don't amplify.** Recovery work itself must not become a new source of load.

## What to do after cloning

```bash
python scripts/http_429_conformance_lab.py \
  --output /tmp/http-429-conformance.json
```

Then read [QUICKSTART.md](QUICKSTART.md) to interpret the result.

No production endpoint is required.

## Contributing

You do not need upstream permission to experiment, fork, remix, or implement a derivative under the repository license.

If you want a change or Purrtocol lineage indexed upstream, see [CONTRIBUTING.md](CONTRIBUTING.md) and [PURRTOCOL_VARIANTS.md](PURRTOCOL_VARIANTS.md).

Keep provenance clear. Keep evidence claims narrower than the artifacts that illustrate them.
