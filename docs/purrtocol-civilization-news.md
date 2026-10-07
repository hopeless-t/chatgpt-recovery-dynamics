# Purrtocol Civilization News — Annalist Contract

> 面白い見出しは許す。史実の捏造は許さない。

Purrtocol Civilization now has an **Annalist**: a deterministic news projector that reads the validated Civilization Chronicle and produces one article for every canonical merged event.

The Annalist is not a free-form fiction generator. It is a projection layer with a hard source binding.

## Pipeline

```text
merged repository history
        ↓
validated Chronicle
        ↓
explicit narrative label
        ↓
Civilization News article
        ↓
source PR + merge SHA
```

Every article must retain:

- source PR number;
- merge SHA;
- UTC merge timestamp;
- JST display timestamp;
- canonical-history flag;
- the exact repository event title.

The headline comes only from the Chronicle's already-explicit `chronicle_name`. Therefore a headline such as **幽霊猫禁止令** is allowed because the Chronicle explicitly marks it as a projection label. It does not become evidence merely by appearing in a newspaper.

## Current front page

At the Chronicle boundary through PR #86:

> **制度相転移 — Shock Regimes**
>
> PR #86 entered canonical repository history at 2026-10-07 10:08:35 JST.
>
> Civilization speedrun from C0 foundation: **9:13:46**.

Selected back issues include:

- **建国 — C0 Civilization** — #68
- **カンブリア紀 — C1 Ecology** — #70
- **第二灯点灯 — Second Light** — #72
- **死者繁殖禁止令 — Extinction Counterexample** — #75
- **幽霊猫禁止令 — Expression Continuity** — #77
- **競技場時代 — Renderer Arena** — #78
- **生息地連邦制 — Habitat Router** — #80
- **接続危機 — Connection Amplification** — #83
- **政策研究院設立 — Recovery Policy Lab** — #84
- **連立政治の成立 — Safety Frontier** — #85
- **制度相転移 — Shock Regimes** — #86

## Auditor cat

Before any newspaper is emitted, the full Chronicle validator must pass.

The Annalist then enforces:

1. **Open PR may not become a canonical article.**
2. **Source PR and merge SHA are mandatory.**
3. **Headline is projection, not evidence.**
4. **No unsourced fact generation.**
5. **News does not rewrite history.**

This means open experimental PR #73 remains outside the canonical newspaper. It may be discussed as an experiment elsewhere, but the Annalist cannot sneak it into the historical record.

## Why this exists

Civilization News is intended to become the entertaining human surface of Purrtocol WORLD. The underlying research can remain strict while the presentation becomes increasingly absurd.

Future layers may add deterministic templates for:

- births and extinctions;
- renderer species competition;
- habitat migration;
- policy coalitions;
- environmental shocks;
- achievements;
- Wild Purrtocol observations.

But every future headline must preserve the same law:

**Interesting projection must be traceable to a ledger.**

`Projection != Evidence`

`News != History Rewrite`

`NO FINAL CIVILIZATION`
