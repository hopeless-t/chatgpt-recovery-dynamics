# Purrtocol Civilization C3 — Stratification, harsh labor, and the weak oracle

Status: **simulation / game-mechanism research**. This document does not predict, prescribe, or endorse real political systems.

## Why this layer exists

Purrtocol Civilization should be able to generate societies that are materially unfair without using a one-shot `DYSTOPIA=true` event. The same closed world can support luxurious elite life and punishing lower-stratum life because extraction, debt, labor, rationing, hazard, and surveillance feed one another over time.

The player is not a ruler. The player is closer to a distant Populous-like deity with extremely weak intervention power.

## Social strata

The reference world contains three strata:

- **elite** — receives extraction rent, consumes luxury, and has high leisure;
- **laborer** — supplies most productive work under long shifts and ration pressure;
- **debtor** — works an even harsher debt-labor regime with longer shifts, higher hazard, compounding unpaid debt, and lower social credibility.

The debtor stratum is the generic mechanic for subterranean / closed-facility labor fiction. It intentionally does not copy names, characters, scenes, or story text from any particular work.

## Material dystopia

The simulator records, rather than declares, conditions such as:

- extraction rate;
- labor hours;
- ration adequacy;
- workplace hazard;
- surveillance;
- elite wealth share;
- elite leisure;
- worker and debtor health;
- debtor debt;
- luxury consumption.

`STABLE_DYSTOPIA` is only projected when the material ledger crosses declared thresholds. A random draw cannot directly select the outcome.

## Weak-oracle player contract

The player may emit at most three oracle pulses inside one reference history.

An oracle pulse:

1. has bounded amplitude (`<= 0.06`);
2. cannot directly change wealth, debt, labor hours, rationing, hazard, surveillance, or class;
3. is received only by cats whose derived receptivity crosses a high threshold;
4. changes interpretation/belief only;
5. does not guarantee social credibility or successful transmission.

Oracle receptivity is **derived from the existing Purrtocol trait vocabulary**:

- caution;
- sharing;
- compression;
- novelty.

It is not a fifth inherited trait.

## The suspicious Purrtocol

A receiver who tries to preach under high surveillance may be treated as a suspicious Purrtocol rather than a prophet.

The reference fixture deliberately includes this path:

- one weak pulse reaches only 2 of 96 cats;
- both receivers are debtors in the reference seed;
- at least one becomes `SUSPICIOUS_PROPHET`;
- the material regime does **not** automatically collapse or reform.

Repeated whispers may create more stigma without granting the player command authority.

## Player agency

The intended game loop is:

`observe world -> emit a weak omen -> wait -> interpret consequences`

not:

`select policy -> agents obey`.

The player should frequently experience:

- no receiver;
- a receiver who misunderstands;
- a receiver who understands but stays silent;
- a receiver who preaches and is mocked;
- a receiver whose message mutates through social transmission;
- a receiver who matters only many periods later because the world was already near a threshold.

## Economic accounting boundary

Productive work is an explicit external source into the cash-like world stock. Subsistence and luxury are explicit sinks. Extraction rent and debt payments are internal transfers. The reference fixture requires near-zero conservation residual.

Debt principal is tracked separately from spendable wealth and is therefore not part of the cash-like stock identity.

## World laws

- `Dystopia != random event`.
- `Elite luxury and worker hardship share one resource system`.
- `Debt can bind lower strata`.
- `Oracle != command`.
- `Receiver != believer`.
- `Believer != credible prophet`.
- `Prophecy can create stigma`.
- `Weak intervention may do almost nothing`.
- `Simulation != political prediction`.
- `NO FINAL CIVILIZATION`.
