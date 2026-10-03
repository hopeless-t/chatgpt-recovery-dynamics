# 3D Purrtocol First Light / 3Dパケニャ

Status: **IMPLEMENTED FIRST LIGHT**

Concept origin: `PKE-106`

Implemented event: `PKE-033`

Runtime asset: `docs/assets/purrtocol/purrtocol.glb`

Interactive preview: https://hopeless-t.github.io/chatgpt-recovery-dynamics/purrtocol-3d/

## First Light measurements

```text
format      GLB / glTF 2.0
bytes       7,672
sha256      c3d2a82aaf14af5219f5236fcb22b296bd8b736fd9c2bb639d5450a3f000e3db
nodes       21
animations  6
textures    0
geometry    one reusable cube mesh topology, seven material variants
```

This is intentionally a tiny procedural/voxel implementation. It proves the repository's 3D asset pipeline and semantic validation path, not artistic completion.

## Required animation clips

- `idle_observe`
- `blocked_429`
- `provisional_step_E`
- `stable_snapshot_carry_H`
- `duplicate_retry_attempt`
- `director_neck_scruff_stop`

## Semantic cues

- B / Blocked — red left-ear cue and blocked animation.
- E / Recovering — amber goggles and cautious provisional step.
- H / Healthy — green tail cue and one stable snapshot.
- Observe — tiny cyan packet.
- Materialization — visibly larger white snapshot package.

## Asset metadata

The GLB root embeds:

- `variant_id = PKV-CANONICAL`
- project motto
- `Visualization != Evidence`

## Viewer

The Pages preview uses the official `<model-viewer>` web component and keeps the GLB itself in this repository.

The viewer is presentation infrastructure. The asset remains the portable artifact.

## Next 3D frontier

First Light closes the "does a canonical 3D artifact exist?" question.

Next work can improve:

- organic silhouette;
- proper armature/skin;
- expression controls;
- Blender editable source;
- turnaround renders;
- material/lighting polish;
- measured mobile runtime memory;
- state-preserving derivative rigs for Purrtocol variants.

The concept record remains historical provenance even after promotion.

**Concept origin != implemented artifact.**

**Visualization != Evidence.**
