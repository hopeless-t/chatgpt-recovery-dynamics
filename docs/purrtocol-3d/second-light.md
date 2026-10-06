# Purrtocol 3D Second Light / 第二灯

Status: **experimental implemented visualization — not canonical**

Second Light is the first generated 3D specimen after the C1 Ecology → Graphic Evolution bridge. It does **not** replace `purrtocol.glb`; First Light remains the stable semantic baseline.

## Why this exists

First Light proved that a tiny GLB could preserve the recovery-state contract. Second Light asks a narrower next question:

> How much smoother, more organic, and more expressive can Purrtocol become while remaining deterministic, web-light, provenance-safe, and semantically compatible?

The current generator uses only Python's standard library and produces a GLB with:

```text
bytes        18,500
nodes        30
animations   6
channels     31
CUBICSPLINE  15
triangles    168 shared sphere primitive
textures     0
```

The six canonical semantic clips remain:

- `idle_observe`
- `blocked_429`
- `provisional_step_E`
- `stable_snapshot_carry_H`
- `duplicate_retry_attempt`
- `director_neck_scruff_stop`

The geometry shifts from shared voxel cubes toward an organic shared sphere primitive. Smoothness comes mainly from timing, secondary transform motion, and interpolation rather than from brute-force polygon count.

## Reproducibility rule

The generator is the source of truth for this experiment:

```text
scripts/generate_purrtocol_second_light.py
```

CI generates the GLB twice and requires byte-identical output before uploading the specimen and receipt as a workflow artifact. This intentionally avoids manually editing binary GLB chunks.

## Projection candidate

The current Graphic Evolution lane includes a candidate presentation regime:

```text
serious-midnight-commercial
production_intent = play-straight
```

That is a production hypothesis, not a measured human-response result. Humor, comprehension, replay value, and propagation remain `UNKNOWN` until observed.

## World laws retained

```text
Simulation != Evidence
Visualization != Evidence
Generated variant != Canon
UNKNOWN != SUCCESS
Technical quality != humor
```

Second Light is therefore a **breedable experimental organism**, not a new canonical mascot. Future descendants may mutate silhouette, motion grammar, props, material response, and presentation while the Recovery Survival semantics remain upstream constraints.
