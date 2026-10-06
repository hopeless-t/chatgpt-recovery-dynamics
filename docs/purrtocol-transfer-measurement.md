# Purrtocol Transfer Measurement Contract / 転送計測契約

Status: **engineering observation — diagnostic only**

This lane measures a deterministic compressed-transfer proxy for generated GLB assets. It is intentionally narrower than a network model.

## Contract

For one immutable asset byte string:

```text
raw_bytes  = len(asset)
gzip_bytes = len(gzip.compress(asset, compresslevel=9, mtime=0))
```

The receipt records raw/gzip SHA-256, byte counts, compression ratio, and the exact proxy contract.

The same asset measured twice must produce byte-identical JSON receipts.

## What this does *not* mean

`gzip_bytes` is **not** actual network load. Real transfer cost depends on protocol framing, caches, CDN behavior, retransmission, retries, fanout, connection reuse, congestion, transport, and many other effects.

In particular:

```text
one compressed transfer != recovery traffic
small gzip payload != low outage risk
compression ratio != semantic quality
```

The 2026-09-29 OpenAI cross-product incident is a useful warning: repeated background checks and connection creation can amplify shared infrastructure load. A future network model therefore needs retry/fanout/connection-capacity terms in addition to payload size.

## Anti-Goodhart counterexample

CI measures a synthetic highly-compressible filler payload. It may achieve fewer `gzip_bytes` than valid Purrtocol GLBs while carrying no renderer semantics at all.

Therefore transfer proxy measurements stay **diagnostic-only** in Renderer Arena v0. Invalid or meaningless payloads cannot become candidates merely by compressing well.

## Promotion rule

A new network-related Arena objective may be promoted only after all of these exist:

1. a deterministic measurement contract,
2. a semantic/provenance gate,
3. at least one counterexample showing how the metric can be gamed,
4. a statement of what the proxy does not measure,
5. a bounded model for retry/fanout amplification if the objective claims to approximate recovery-time network pressure.

Until then:

```text
Measurement != fitness.
Compressed bytes != network load.
Local efficiency != global recovery safety.
```
