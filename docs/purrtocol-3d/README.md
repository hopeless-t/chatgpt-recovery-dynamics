# Purrtocol 3D Contract / 3Dパケニャ契約

Status: **IMPLEMENTED FIRST LIGHT / PKE-106 → PKE-033**

The original PKE-106 concept is now promoted to implemented event PKE-033. The historical concept row remains unchanged as provenance. First Light is a deliberately tiny procedural voxel implementation that proves the runtime, animation, preview, promotion, and CI pipeline.

> **Concept != implemented artifact.**
>
> **Visualization != Evidence.**

## First Light reference implementation

```text
asset       docs/assets/purrtocol/purrtocol.glb
format      glTF 2.0 / GLB
bytes       7,672
sha256      fc667ad30bd69fb794a876ec0acbb9e9efdbdd9c3a3d3f056c1769f4579c6467
nodes       21
animations  6
textures    0
viewer      docs/purrtocol-3d/index.html
```

This reference is intentionally minimal. It is a semantic/pipeline baseline, not final character art.

## Why 3D exists

The 3D model is not decoration first. It is an **architecture mascot** that should make recovery-state semantics visible in motion:

- B / Blocked must read as Blocked even without relying on red alone.
- E / Recovering must look provisional, cautious, and not yet Healthy.
- H / Healthy may carry exactly one stable snapshot.
- Observe uses a tiny cyan packet.
- Heavy snapshot materialization must look materially different from a cheap observation.
- UNKNOWN never becomes a visual excuse to run the operation again.

The canonical character source remains [Purrtocol Design Bible](../purrtocol-design-bible.md).

## Runtime target

Primary runtime interchange target:

- glTF 2.0 binary (`.glb`)
- right-handed coordinate system
- +Y up
- +Z forward
- meters for linear units

Those coordinate conventions follow the glTF 2.0 specification:
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html

Blender is the preferred authoring tool for the first implementation because its glTF exporter supports armatures, skinning, shape keys/morph targets, and named animation actions:
https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html

The contract is tool-independent: another authoring tool is acceptable if the exported runtime asset satisfies the same semantics.

## Required state readability

| State | Color cue | Non-color cue |
|---|---|---|
| B / Blocked | red | left ear down + blocked pose |
| E / Recovering | amber | recovery goggles + cautious forward step |
| H / Healthy | green | green tail-tip + exactly one stable snapshot |
| Observe | cyan | tiny packet prop |

Color is supplementary. Silhouette, pose, prop, or motion must carry the state meaning as well.

## Required rig surface

Named runtime nodes are reserved for:

```text
root
head
ear_L / ear_R
eye_L / eye_R
eyelid_L / eyelid_R
mouth
paw_FL / paw_FR / paw_BL / paw_BR
tail
goggles
socket_packet
socket_snapshot
```

The exact internal control rig may be richer. The names above are the portable runtime contract.

## Required animation clips

Each clip should export as a self-contained named action:

```text
idle_observe
blocked_429
provisional_step_E
stable_snapshot_carry_H
duplicate_retry_attempt
director_neck_scruff_stop
```

The final one is intentionally ridiculous and technically important.

## Expression intents

The face/pose system must be able to express:

```text
neutral
B / Blocked
E / Recovering
H / Healthy
about_to_retry
director_stopped_me
visualization_is_evidence_oops
```

The implementation may use bones, morph targets, or a combination. The runtime contract does not require one facial-rig technique.

## Lightweight by design

3D Purrtocol should remain web-first and memory-conscious.

No arbitrary triangle, texture, or binary-size threshold is frozen during preproduction. The implementation PR must report measured:

- GLB size;
- mesh/triangle counts;
- texture dimensions and encoded sizes;
- animation count;
- peak/runtime memory observations in the chosen viewer where practical.

Budgets should be set from those measurements and target devices, not invented in advance.

## Promotion gate

PKE-106 was promoted only after the implementation contained all of:

1. a runtime GLB at `docs/assets/purrtocol/purrtocol.glb`;
2. a runtime preview at `docs/purrtocol-3d/index.html`;
3. an explicit `PKE-106` promotion record;
4. CI validation of the runtime asset and required semantic names;
5. a commit-backed implemented event separate from the historical concept record.

The concept record itself remains immutable historical provenance. Promotion is recorded separately in `data/pakenya_promotions.jsonl`.

## CI behavior

`scripts/validate_purrtocol_3d.py` operates in two modes.

Before the model exists:

```text
asset absent
promotion absent
PKE-106 remains concept
=> PREPRODUCTION PASS
```

After the model exists:

```text
GLB 2.0 header valid
required runtime nodes present
required animations present
preview present
promotion present
=> IMPLEMENTATION CONTRACT PASS
```

The validator does not automatically promote the concept.

## Epistemic guardrails

The 3D model must never imply that Purrtocol:

- knows OpenAI's internal topology;
- has privileged backend access;
- has proven a causal hypothesis because a diagram/animation looks convincing;
- can bypass throttling or rate limits.

The cat remains on the observer/recovery side.

> **The joke may be sloppy; the footnote may not be sloppy.**


## Browser observability

A structural GLB check is not enough to prove that a user can see the model.

The first browser-level observation now has two lanes:

```text
live render
  Chrome + SwiftShader
  -> model-viewer defined
  -> GLB load event observed
  -> 6 animations available
  -> screenshot artifact captured

forced viewer failure
  both external viewer CDNs deliberately unavailable
  -> poster fallback remains visible
  -> dark-box-only failure mode does not recur
```

Canonical receipt:

- `BROWSER_OBSERVATION.json`
- workflow run `37147123715`

Observed live status:

```text
GLB loaded · 6 animations · interactive 3D active
```

Observed forced-failure status:

```text
Interactive 3D did not become ready in 8s · poster fallback remains visible
```

The preview also reports WebGL/runtime/GLB state in-page and tries two pinned
viewer CDNs before falling back to the poster.

This browser observation was made on GitHub Actions Chrome/SwiftShader.

It does **not** prove identical behavior in every device/WebView. In particular,
a ChatGPT iOS in-app browser remains a separate device-specific observation.


## Sustained visibility baseline

The first browser observation proved that the GLB could load and render.

A later real-site observation exposed a stricter requirement:

~~~text
first frame visible
!=
sustained visibility
~~~

The reported symptom was:

~~~text
3D appears briefly
-> stage darkens
~~~

The exact live-device root cause remains **NOT ESTABLISHED**.

The preview is now static-first:

- load the GLB;
- do not automatically start the animation loop;
- keep a local poster backstop behind the renderer;
- if `webglcontextlost` is reported, pause/hide the interactive renderer and reveal the backstop;
- preserve explicit retry and user-triggered animation controls.

The strengthened browser gate now requires:

~~~text
external viewer CDN failure -> local backstop still present
static-first render          -> survives >=20s in Chrome/SwiftShader
forced renderer-loss event   -> webglcontextlost fallback
fallback screenshot          -> visible poster, not a dark box
~~~

Canonical sustained-visibility receipt:

- `BROWSER_SURVIVAL_OBSERVATION.json`
- workflow run `37209084331`

Observed statuses:

~~~text
GLB sustained · static-first renderer remained healthy for 20s

3D renderer fallback: webglcontextlost · stable poster remains visible
~~~

The forced loss lane used a synthetic `model-viewer` `webglcontextlost` error
event in CI because that runner did not expose `WEBGL_lose_context`.

That tests the recovery path, not the browser driver's ability to lose a real
context on demand.

This still does **not** prove identical behavior in ChatGPT's iOS in-app WebView.
The repair covers a matching failure class while preserving that uncertainty.
