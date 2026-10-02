# ChatGPT Conversation Recovery Dynamics

<p align="center">
  <a href="https://hopeless-t.github.io/chatgpt-recovery-dynamics/network/">
    <img src="https://raw.githubusercontent.com/hopeless-t/chatgpt-recovery-dynamics/main/docs/assets/recovery-network.gif" alt="Animated recovery network" />
  </a>
</p>

> **Recover. Don't amplify.**  
> 会話復旧を、利用者・Support・provider・研究者の全方向に優しくするための研究Wikiです。

## Start here / 入口

| Page | What it is |
|---|---|
| [[Recovery Architecture]] | `Blocked → Recovering → Healthy` と low-amplification recovery |
| [[Evidence Ledger]] | 観測・再計算・支持・仮説・未確定の分離 |
| [[Provider Friendly Design]] | popular-server congestion / admission / backpressure |
| [[Recovery Helper]] | 日英対応・local-onlyの利用者向け復旧ヘルパー |
| [[Deep Validation]] | AR(1), change-point, posterior predictive, threshold sensitivity |
| [[External Archaeology]] | Reddit / Hacker News の歴史的観測記録 |
| [[Paper]] | reproducible paper-style PDF |
| [[Architecture Decisions]] | accepted ADRs |
| [[RFCs]] | proposed recovery / congestion interfaces |
| [[FAQ]] | common questions and caveats |
| [[Glossary]] | canonical terminology |
| [[Purrtocol]] | regrettably, the mascot |
| [[Release Notes]] | release history |

## Core model

```text
Z_n ∈ {H, E, B}

Delta_n = S_n + mu + z_n + epsilon_n
z_n = phi z_(n-1) + eta_n
```

Observed in the current capture:

```text
B -> E -> B : 8
B -> E -> H : 0
```

The recovery design therefore treats the first success after Blocked as **provisional**, not stable.

## Design principle

```text
many triggers
  -> single-flight
  -> cheap observe
  -> provisional recovery E
  -> stable confirmation
  -> materialize once
  -> atomic reconcile
  -> optional realtime reattach
```

## Live pages

- [Animated network visualizer](https://hopeless-t.github.io/chatgpt-recovery-dynamics/network/)
- [Recovery Helper / 復旧ヘルパー](https://hopeless-t.github.io/chatgpt-recovery-dynamics/recovery-helper/)
- [Project portal](https://hopeless-t.github.io/chatgpt-recovery-dynamics/)

> Visualization ≠ Evidence.  
> The visual topology is a design explanation, not a claim about OpenAI internals.