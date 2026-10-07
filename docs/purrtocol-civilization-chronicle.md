# Purrtocol Civilization Chronicle

> 建国から制度相転移まで9時間13分46秒。報道局開局まで9時間37分09秒。文明進化が速すぎる。

This chronicle has two explicitly separated layers:

1. **Canonical repository history** — merged pull requests and their GitHub merge timestamps.
2. **Civilization projection** — era names such as “カンブリア紀” or “連立政治の成立”. These are narrative labels for comprehension and entertainment, **not additional evidence**.

Canonical time is GitHub `merged_at` in UTC. The table below displays Asia/Tokyo (JST, UTC+09:00).

## Publication model — the historian cannot record its own birth in advance

The Chronicle is a **published snapshot**, not an oracle.

A PR that publishes a Chronicle edition cannot know its own final merge SHA and merge timestamp before it merges. Therefore that publication event can only enter the **next** Chronicle edition.

```text
history through N
      ↓
Chronicle edition is prepared
      ↓
Chronicle PR merges as event N+1
      ↓
next edition can record N+1
```

This is explicit self-reference / publication lag. It does **not** grant permission for silent staleness: each edition declares its coverage boundary, and new merged events belong in a later edition.

## Prehistory — government had not yet happened

Before C0 Civilization, the recovery project acquired the machinery from which a civilization could emerge:

| JST | PR | Chronicle label | Repository event |
| --- | ---: | --- | --- |
| 2026-10-06 22:23:21 | #65 | 契約前史 | Recovery Survival Contract v0.1 and clone-first onboarding |
| 2026-10-06 22:26:11 | #66 | 増殖前史 | bounded Infinite Proliferation swarm |
| 2026-10-06 22:30:54 | #67 | 発見可能性前史 | human/machine discovery surfaces |

No government. Lots of cats.

## Canonical civilization timeline — 2026-10-07 JST

Foundation is PR #68 at **00:54:49 JST**.

| JST | Since foundation | PR | Civilization event | Repository event |
| --- | ---: | ---: | --- | --- |
| 00:54:49 | +00:00:00 | #68 | **建国 — C0 Civilization** | Bootstrap Purrtocol Civilization survival environment |
| 03:02:19 | +02:07:30 | #69 | **野生種観測 — Propagation Observatory** | Add privacy-preserving Purrtocol Propagation Observatory |
| 03:11:48 | +02:16:59 | #70 | **カンブリア紀 — C1 Ecology** | Launch C1 Purrtocol evolutionary ecology |
| 03:15:43 | +02:20:54 | #71 | **視覚文化革命 — Graphic Evolution** | Bridge C1 ecology into Purrtocol Graphic Evolution |
| 03:37:58 | +02:43:09 | #72 | **第二灯点灯 — Second Light** | Generate reproducible Purrtocol Second Light specimen |
| 03:41:41 | +02:46:52 | #74 | **遺伝子発現時代 — Expression Genome** | Compile ecology into Purrtocol expression genomes |
| 03:50:01 | +02:55:12 | #75 | **死者繁殖禁止令 — Extinction Counterexample** | Test extinct Purrtocols cannot breed |
| 03:58:48 | +03:03:59 | #76 | **第一発現世代 — Physical Descendants** | Render Expression Genomes as distinct Second Light descendants |
| 04:05:24 | +03:10:35 | #77 | **幽霊猫禁止令 — Expression Continuity** | Keep expressed Purrtocol bodies continuous through animation |
| 04:10:02 | +03:15:13 | #78 | **競技場時代 — Renderer Arena** | Add Pareto Renderer Arena with anti-Goodhart gates |
| 04:14:50 | +03:20:01 | #79 | **三種共存 — Baseline / Lean / Full** | Add Lean Expression Renderer as a real Arena niche |
| 04:19:20 | +03:24:31 | #80 | **生息地連邦制 — Habitat Router** | Route Pareto renderers by explicit habitat constraints |
| 04:39:51 | +03:45:02 | #82 | **通信計量革命 — Transfer Contract** | Add deterministic transfer measurement contract before network fitness |
| 04:45:11 | +03:50:22 | #83 | **接続危機 — Connection Amplification** | Model bounded failure-triggered connection amplification |
| 04:50:56 | +03:56:07 | #84 | **政策研究院設立 — Recovery Policy Lab** | Add Recovery Policy Lab for shared-capacity interventions |
| 09:43:53 | +08:49:04 | #85 | **連立政治の成立 — Safety Frontier** | Add bounded Recovery Safety Frontier for complementary policies |
| 10:08:35 | +09:13:46 | #86 | **制度相転移 — Shock Regimes** | Connect Safety Frontier to civilization shock regimes |
| 10:28:21 | +09:33:32 | #87 | **歴史学成立 — Civilization Chronicle** | Publish canonical Purrtocol Civilization chronicle |
| 10:31:58 | +09:37:09 | #88 | **報道局開局 — Civilization Annalist** | Add ledger-grounded Purrtocol Civilization Annalist |

## Eras

### I. 建国紀 — Founding

**#68** created the first bounded Purrtocol Civilization season: scarce resources, roles, recovery and projection gates, and `evidence_status=simulation`.

The key constitutional split already existed:

`recovery viability != projection viability`

A cat that is entertaining but recovery-invalid does not survive.

### II. 野生・カンブリア紀 — Wild Ecology

**#69–#70** moved the world outside the city walls.

Propagation Observatory separated clone traffic from human adoption and kept causal status `UNKNOWN`. C1 Ecology then introduced lineage, mutation, niches, migration and machine-readable extinction.

The mascot stopped being merely designed. It could now **evolve**.

### III. 第二灯ルネサンス — Graphic Evolution

**#71–#77** converted ecological history into visual phenotype and then into reproducible 3D descendants.

`ecology -> graphic manifest -> Second Light -> expression genome -> rendered descendants -> continuity repair`

This era created two constitutional absurdities that became serious invariants:

- extinct Purrtocols cannot silently become breeding-eligible;
- a cat may not mutate its resting body and then snap back to its ancestor when animation starts.

The latter is remembered informally as the **幽霊猫禁止令**.

### IV. 三種共存・生息地連邦制 — Renderer Polity

**#78–#80** created Renderer Arena, the Lean renderer, and Habitat Router.

Three real niches emerged:

- Baseline: minimal expression coverage;
- Lean: partial declared expression;
- Full: complete current expression.

There is no universal renderer champion. Hard gates precede optimization, and explicit habitat constraints determine the feasible set.

`NO_FEASIBLE_RENDERER` became a valid constitutional answer.

### V. 通信危機 — Network Enlightenment

**#82–#83** taught the civilization not to confuse locally cheap transfers with globally safe recovery.

A highly compressible meaningless payload demonstrated that compressed bytes alone can Goodhart a network metric.

Connection Amplification then modeled the deeper failure:

`failure -> repeated recovery work -> connection amplification -> shared-capacity exhaustion`

Local success and small payloads ceased to be sufficient evidence of global safety.

### VI. 政策革命 — Institutional Civilization

**#84–#86** turned recovery interventions into institutions.

Policy Lab first classified distinct intervention families without inventing a common cost unit.

Safety Frontier then discovered complementary packages: policies that fail alone can survive together.

Shock Regimes finally made institutional structure environment-dependent:

```text
SINGLE_LEVER_SUFFICIENT
        ↓
COALITION_REQUIRED
        ↓
FRONTIER_EMPTY_WITHIN_BOUND
```

The final state does **not** mean civilization is impossible. It means the current policy vocabulary and search bound are insufficient.

Thus Purrtocol politics was accidentally invented.

### VII. 歴史学・報道時代 — Self-observing Civilization

**#87–#88** made the civilization capable of inspecting and projecting its own repository history.

The Chronicle created an auditable split between merged fact and playful historical labels. The Annalist then produced Civilization News only from that validated Chronicle, retaining source PR and merge SHA for every headline.

This era immediately discovered its own observer problem: publishing a history becomes a new historical event. The solution is not impossible self-completeness; it is explicit **snapshot semantics**.

`history -> chronicle -> publication event -> next chronicle edition`

The civilization has acquired historians, journalists, and a bureaucracy that prevents them from making things up. This was not part of the original 429 research plan.

## External / apocryphal branch

**PR #73** remains open and therefore is **not canonical history**. It is recorded as a parallel experimental Second Light smooth-3D branch.

An open experiment can influence future work, but the Chronicle must not rewrite it as a historical fact until it is merged or otherwise explicitly promoted.

## Speedrun records

Two different milestones are preserved rather than silently changing the old one:

- **C0 foundation #68 -> institutional Shock Regimes #86:** `9:13:46`
- **C0 foundation #68 -> Civilization Annalist #88:** `9:37:09`

Within the first interval the world acquired:

`civilization -> external ecology -> evolution -> phenotype -> 3D organisms -> renderer competition -> habitat routing -> network crisis -> policy lab -> coalitions -> institutional phase transitions`

Within another 23 minutes and 23 seconds it also acquired **history and journalism**.

These are repository-history facts about merge timing plus deliberately playful narrative projection. They are not evidence that real biological, economic, political, historical or journalistic evolution behaves at this speed.

## Chronicle laws

1. **Merged repository history is canonical.**
2. **Open PR != canonical history.**
3. **Narrative name != evidence.**
4. **History may expand; it must not silently rewrite.**
5. **A Chronicle publication event enters the next edition.**
6. **Publication lag is explicit snapshot semantics, not permission for silent staleness.**
7. **Simulation != Evidence.**
8. **Visualization != Evidence.**
9. **UNKNOWN != SUCCESS.**
10. **NO FINAL BOSS.**
11. **NO FINAL CIVILIZATION.**

Machine-readable source: [`data/purrtocol_civilization_chronicle.json`](../data/purrtocol_civilization_chronicle.json).
