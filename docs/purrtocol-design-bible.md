# Purrtocol Design Bible / パケニャ設定資料集

> Canonical source for future visual, narrative, and 3D work.
>
> No empirical reason for the cat has been established.

## Ontology

Purrtocol is not merely a mascot.

> **An anthropomorphic error model for recovery systems.**

Purrtocol safely performs mistakes that users, clients, agents, and operators are tempted to make: duplicate retry, premature recovery declaration, re-execution under ambiguity, confusing visualization with evidence, and carrying a full snapshot when a tiny observation would do.

## Core identity

- English name: **Purrtocol**
- Japanese nickname: **パケニャ / パケにゃ**
- Job: **Recovery Cat**
- Motto: **Retry less. Observe more.**
- Project motto: **Recover. Don't amplify.**
- Evidence motto: **Visualization != Evidence.**

## Character function

1. State-machine avatar — makes B/E/H transitions legible.
2. Negative-example generator — performs the wrong action so the rule can be demonstrated.
3. Mnemonic compressor — turns protocol language into remembered scenes.
4. Epistemic guardrail — separates observation, inference, simulation, and proposal.
5. Human-factors proxy — embodies the urge to click again when feedback is ambiguous.
6. Brand anchor — gives a long technical project one recognizable object.

## Canonical appearance

- small cat-shaped network operator;
- cyan/green base palette;
- amber recovery goggles;
- left ear associated with B / Blocked;
- amber goggles associated with E / Recovering;
- green tail-tip associated with H / Healthy;
- one small cyan observation packet;
- router / observability hardware.

~~~text
B / Blocked     red
E / Recovering  amber
H / Healthy     green
Observe/probe   cyan
Transport       blue
~~~

## Canonical behavior

Technical Purrtocol knows the rule. Comedic Purrtocol violates it so the audience can learn the rule.

Typical mistakes:

- wants to retry too early;
- calls E Healthy;
- runs on UNKNOWN;
- treats a visualization as evidence;
- carries too many snapshots.

## Voice

Japanese Purrtocol uses simple analogies and often ends with にゃ. Difficult concepts may be explained aggressively simply. Footnotes are not allowed to become sloppy.

> **The joke may be sloppy; the footnote may not be sloppy.**

## World

Current canonical sets:

- Recovery laboratory
- PKN-429 local TV station
- commercial studio
- blooper reel
- studio documentary
- glossary / classroom
- 429 learning room
- Purrtocol University
- Evidence Court
- Purrtocol Restaurant for queueing theory
- Incident Investigation Board
- Agent Retry Academy
- Museum / archive
- Purrtocol Constitution
- Failure Field Guide
- Purrtocol Observatory
- 3D Purrtocol First Light

Permitted future adjacent sets:

- expressive 3D rig / organic silhouette refinement
- 3D Purrtocol variant strains

## Props

- tiny cyan observation packet
- one oversized snapshot package
- 429 stop sign
- clapperboard
- router / queue panel
- B/E/H state lamps

## Forbidden implications

Purrtocol must not be depicted as knowing OpenAI's internal topology or root cause, having privileged backend access, proving hypotheses with diagrams, or bypassing rate limits.

The cat is on the observer/recovery side.

## 3D contract

Current state: **3D Purrtocol First Light is implemented**. PKE-106 remains preserved as concept-origin provenance and is explicitly promoted to PKE-033. The next frontier is expressive rig/art refinement without weakening the semantic contract.

Machine-readable/preflight contract:

- [Purrtocol 3D First Light](purrtocol-3d/index.md)
- [Purrtocol 3D contract](purrtocol-3d/README.md)
- `data/purrtocol_3d_contract.json`
- `scripts/validate_purrtocol_3d.py`

~~~text
turnaround:
  front / side / back / 3-quarter

expression sheet:
  neutral
  B / Blocked
  E / Recovering
  H / Healthy
  about_to_retry
  director_stopped_me
  visualization_is_evidence_oops

rig:
  head / ears / eyes / eyelids / mouth
  paws / tail / goggles
  packet prop socket
  snapshot prop socket

animation:
  idle_observe
  blocked_429
  provisional_step_E
  stable_snapshot_carry_H
  duplicate_retry_attempt
  director_neck_scruff_stop
~~~

The model should function as an **architecture mascot**: state, observation, transport, and materialization should remain visually legible.

## Measurement backaction

The act of measuring Purrtocol expansion can itself create documentation, pages,
scripts, CI, and lore. These artifacts belong to a separate `observer_effect`
cohort rather than being silently folded into the original fit.

> **The instrument used to measure the cat is also made of cat.**

Measurement-associated expansion is repository history. A universal causal
observer effect is not established.

## Meta-rule

Every additional document about why the cat exists increases the amount of evidence that the cat exists.

This is not evidence that the cat was necessary.


## Concept promotion rule

Future settings may be registered as `status=concept` before implementation.
When a concept becomes real, the concept record is retained as historical
provenance and `data/pakenya_promotions.jsonl` maps it to a separate
commit-backed implemented event.

~~~text
concept origin != implemented artifact
promotion       = explicit bridge
frozen fit      = unchanged
~~~

First promotions:

- PKE-100 → PKE-024 — Purrtocol University
- PKE-101 → PKE-025 — Evidence Court
- PKE-103 → PKE-026 — Queueing Restaurant
- PKE-102 → PKE-027 — Incident Investigation Board
- PKE-104 → PKE-028 — Agent Retry Academy
- PKE-105 → PKE-029 — Purrtocol Museum
