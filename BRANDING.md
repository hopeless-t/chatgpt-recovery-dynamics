# Branding and visual identity

This document is intentionally excessive.

## Project name
**ChatGPT Conversation Recovery Dynamics**

Short forms:
- Recovery Dynamics
- CRD

## Primary motto
> **Recover. Don't amplify.**

## Evidence motto
> **Visualization != Evidence.**

## Mascot
**Purrtocol** - the Recovery Cat.

Japanese nickname:
**パープロトコル / パケにゃ**

Role:
- sits between many noisy local triggers and one calm recovery owner;
- dislikes duplicate retries;
- likes tiny observation packets;
- refuses to call the first success "Healthy";
- carries exactly one snapshot when recovery is stable.

Mascot motto:
> **Retry less. Observe more.**

Purrtocol is a visual metaphor only and is therefore, naturally, not evidence.

## Palette
- Night background: #07111F
- Panel: #0D1B2D
- Observation cyan: #4CDAEB
- Healthy green: #4CD384
- Recovering amber: #F6BB44
- Retry red: #EF5F6C
- Transport blue: #658DFF

## State colors
~~~text
B / Blocked      red
E / Recovering   amber
H / Healthy      green
Observe/probe    cyan
Transport        blue
~~~

Color is explanatory only. Text labels remain authoritative.

## Visual language
Preferred motifs:
- packet trails;
- single-flight convergence;
- B -> E -> H state progression;
- dark grid / observability console;
- rounded network nodes;
- explicit evidence disclaimers.

Avoid:
- claiming an internal OpenAI topology;
- depicting speculative components as confirmed;
- visualizing exact production capacity.

## Logo / mascot assets
- docs/assets/purrtocol.svg
- docs/assets/recovery-network.gif

## Tone
Technically serious, visually unnecessary, epistemically conservative.


## Local TV commercial mode

An intentionally retro promotional mode is part of the visual identity.

Reference implementation:

- `docs/cm/index.html`

Design target:

> a local television commercial that only airs after 23:30 in one prefecture.

Required properties:

- overconfident primary colors;
- slightly too many borders;
- a mascot that appears to have been approved by a committee;
- one unnecessary jingle;
- a disclaimer that is more rigorous than the advertisement;
- no degradation of the evidence boundary.

Canonical slogan:

> **Retry 0回増量中。※増やしていません**

The local-TV mode is intentionally uncool.

That is considered a feature.


## Canonical Purrtocol design bible

Character, narrative, and 3D work should use:

- `docs/purrtocol-design-bible.md`
- https://hopeless-t.github.io/chatgpt-recovery-dynamics/purrtocol/

The canonical character function is:

> **An anthropomorphic error model for recovery systems.**

Canonical production rule:

> **The joke may be sloppy; the footnote may not be sloppy.**

The canonical 3D First Light asset now preserves B/E/H state legibility, tiny-observation vs heavy-snapshot semantics, and the rule that Purrtocol is an observer/recovery-side character rather than an omniscient backend mascot. Future rigs and visual refinements inherit that semantic contract.

3D First Light:
- `docs/assets/purrtocol/purrtocol.glb`
- `docs/purrtocol-3d/index.html`
- 7,672 bytes / 21 nodes / 6 named semantic animation clips
