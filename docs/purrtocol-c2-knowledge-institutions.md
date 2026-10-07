# Purrtocol Civilization C2 — Knowledge Institutions

> 学校を作ると知識が増える。知識が増えると生産性も上がる。だが組織力も上がる。では学校を潰せば安全か？ — そんなに簡単ではない。

This is a bounded deterministic **simulation/projection** layer for Purrtocol Civilization. It is not a prediction of real political systems and does not claim that education mechanically causes revolution.

## Why this layer exists

C1 gave Purrtocol WORLD ecology, graphical expression, renderer competition, recovery policy, coalitions, and institutions. C2 now gives institutions something dangerous: **memory**.

Knowledge is modeled as a stock that can accumulate, decay, reproduce through formal education, and—under some conditions—survive school closure through underground learning.

The core game-design question is not:

> Does education cause revolution?

It is:

> How does accumulated knowledge change the feasible policy space of a civilization over time?

## State variables

The bounded model tracks:

- `citizen_knowledge` — socially reproducible public knowledge;
- `elite_knowledge` — elite technical/administrative knowledge;
- `productivity` — productive capacity proxy;
- `elite_capture` — share of institutional surplus retained by the ruling stratum;
- `legitimacy` — acceptance/stability proxy;
- `organization` — citizen coordination capacity;
- `underground` — shadow education/coordination network;
- `repression` — active suppression pressure;
- `education_access` — formal citizen access to education.

All values are synthetic normalized state variables. They are not empirical political measurements.

## Institutions / policy modes

The simulator currently exposes five endogenous policy regimes:

1. `OPEN_UNIVERSITY`
2. `CONTROLLED_SCHOOLING`
3. `ELITE_ACADEMY`
4. `ABOLISH_SCHOOLS`
5. `REFORM_COMPACT`

The ruling institution reacts to a synthetic `elite_threat` measure built from public knowledge, organization, and elite capture. Under pressure it may restrict schooling, abolish formal schooling, or—if the scenario permits adaptive reform—trade some elite capture for legitimacy and continued knowledge growth.

No regime is declared globally optimal.

## Three matched counterfactual histories

The default fixture intentionally demonstrates three different outcomes.

### 1. Late abolition after a knowledge boom

Formal schooling opens first. Citizen knowledge and coordination grow. The ruling stratum later restricts and eventually abolishes schooling.

But abolition occurs **after** the society has accumulated enough knowledge to reproduce learning outside the formal institution. School closure therefore does not reset knowledge to zero. Repression plus closure can grow an underground education network.

In the reference fixture this branch eventually reaches `REVOLUTION`.

Important boundary:

`late abolition -> revolution` is a fixture result, **not a universal law**.

### 2. Adaptive reform before the break

The society begins with the same open-education logic, but the ruling coalition is allowed to respond to a legitimacy or underground crisis with `REFORM_COMPACT`.

The model permits high citizen knowledge and organization to coexist with stability if elite capture is reduced and legitimacy recovers.

The reference fixture reaches `REFORMED_ORDER`.

This is deliberately uncomfortable for a simple oppression/revolution story: the civilization can avoid both elite-maximal extraction and revolutionary collapse.

### 3. Early knowledge lockdown

Formal citizen education is constrained while public knowledge is still low.

The society therefore has little capacity to reproduce an underground learning network. Revolutionary organization remains weak.

But the price is not victory. Knowledge, productivity, and legitimacy fail to develop while elite capture remains high.

The reference fixture reaches `AUTHORITARIAN_STAGNATION`.

The ruling class can suppress the revolution and still lose the civilization.

## The funny-but-serious game loop

This creates a strong Purrtocol Civilization gameplay cycle:

```text
found university
      ↓
knowledge + productivity
      ↓
knowledge also improves organization
      ↓
elite threat perception
      ↓
restrict / abolish / reform
      ↓
formal knowledge, underground learning, legitimacy, capture diverge
      ↓
revolution / reform / stagnation / fragile stability
      ↓
Civilization News explains what the cats just did
```

The important property is delayed consequence.

A player can make a policy that looks locally successful—such as abolishing schools and immediately reducing formal organization—only to discover that accumulated knowledge has already made the society path-dependent.

## World laws

1. **Knowledge != revolution.**
2. **Education can raise both productivity and organization.**
3. **Abolition cannot erase accumulated knowledge.**
4. **Late suppression can feed underground learning.**
5. **Early suppression can trade revolution risk for stagnation.**
6. **Reform can reduce elite capture without erasing knowledge.**
7. **No education policy is a universal winner.**
8. **Simulation != political prediction.**
9. **NO FINAL CIVILIZATION.**

## Why this matters for a game

Purrtocol Civilization should not be a game where the player searches for a hidden correct policy tree.

The stronger design is a **story-generating systems game** where institutions create second-order effects that invalidate yesterday's optimum.

The player should be able to say:

> 学校を廃止したら革命は防げた。文明も死んだ。

or:

> 革命を潰すつもりで学校を潰したら地下大学ができた。

or:

> 特権を少し手放したら文明が一番豊かになってしまった。悔しい。

Those are not scripted endings. They should emerge from bounded, inspectable system interactions.

**Interestingness must remain downstream of the ledger.**
