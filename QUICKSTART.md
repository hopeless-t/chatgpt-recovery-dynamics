# Five-Minute Recovery Quickstart

This quickstart runs the repository's local HTTP 429 recovery fire drill.

It binds only to loopback and is designed to avoid production traffic.

## Requirements

- Python 3.11+ recommended
- this repository cloned locally

## Run the fire drill

From the repository root:

```bash
python scripts/http_429_conformance_lab.py \
  --output /tmp/http-429-conformance.json
```

A successful run writes a JSON report to:

```text
/tmp/http-429-conformance.json
```

The lab exercises recovery semantics such as:

- `Retry-After` as a minimum retry floor;
- start-to-start pacing under fast failure;
- bounded retry budgets;
- stable `operation_id` across attempts;
- fresh `attempt_id` per attempt;
- ambiguous non-idempotent completion -> `REOBSERVE`, not blind replay;
- an explicit idempotency contract allowing safe retry without duplicating the side effect.

## Read the report

Pretty-print it with:

```bash
python -m json.tool /tmp/http-429-conformance.json
```

Do not treat a PASS as evidence about any production provider.

The local lab proves that the implementation follows the repository's declared contract for the covered deterministic scenarios.

## Optional: independent runtime checks

The repository also contains independent Node.js and Go implementations used by CI.

```bash
node scripts/http_429_conformance_node.js \
  --output /tmp/http-429-conformance-node.json

go run scripts/http_429_conformance_go.go \
  --output /tmp/http-429-conformance-go.json
```

Compare Python and Node semantics:

```bash
python scripts/compare_http_429_conformance.py \
  --python-report /tmp/http-429-conformance.json \
  --node-report /tmp/http-429-conformance-node.json \
  --output /tmp/http-429-cross-language.json
```

The independent implementations intentionally share contract inputs rather than implementation code.

## The mental model

```text
semantic operation
      │
      ├── attempt 1 -> ambiguous result
      │                  │
      │                  └── cheap re-observation
      │
      └── attempt 2 -> only if replay policy permits
```

The most important rule is:

> **UNKNOWN is not retry permission.**

If a side effect may already have happened, observe durable state before creating another side effect.

## Next

- To port only the ideas: [ADOPT.md](ADOPT.md)
- To read the first small normative surface: [RECOVERY_SURVIVAL_CONTRACT_V0_1.md](RECOVERY_SURVIVAL_CONTRACT_V0_1.md)
- To understand the evidence behind the project: `docs/evidence-ledger.md`
- To create a Purrtocol derivative: [PURRTOCOL_VARIANTS.md](PURRTOCOL_VARIANTS.md)
