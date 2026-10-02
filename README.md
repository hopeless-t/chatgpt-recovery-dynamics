# ChatGPT Conversation Recovery Dynamics

A sanitized, client-side case study of a ChatGPT conversation-loading failure.

This repository does **not** claim to identify OpenAI's internal root cause.
It publishes sanitized derivative telemetry, a reproducible timing analysis,
a falsifiable mathematical model, and a client-side recovery proposal.

## Start here

- [Mathematical model](docs/model.md)
- [Independent validation / model audit](docs/validation.md)
- [Recovery design proposal](docs/recovery-design.md)
- [Robust Monte Carlo stress test](docs/monte-carlo.md)
- [Methodology](docs/methodology.md)
- [Public quantitative summary](data/summary.json)

## Main finding

The central observation is not simply “HTTP 429 happened.”

In the captured session, stream-status observation and conversation-snapshot
access switched together between two regimes:

- Accessible: stream 200 + snapshot 200
- Blocked: stream had no HTTP response + snapshot 429

The most important result after re-analysis is a timing relation:

~~~text
next-cycle gap ~= 5.616 s + 0.957 * current service/failure time
R^2 = 0.991
~~~

This means the higher attempt cadence in the blocked regime does **not** require
the client to deliberately choose a more aggressive retry policy.

A simpler mechanism is enough:

~~~text
request completes/fails
 -> roughly fixed post-completion wait
 -> next observation cycle
~~~

When a successful snapshot takes about 5 seconds, the cycle is roughly
10 seconds. When a blocked request fails in roughly 0.3 seconds, the same
post-completion wait produces a cycle near 6 seconds.

That is a **completion-coupled fast-fail cadence amplifier**.

If those additional attempts consume a constrained request/rate-limit budget,
a positive feedback loop becomes possible:

~~~text
throttling / blocked response
 -> failure completes faster
 -> observation cycles happen more often
 -> request-attempt pressure may rise
 -> throttling can become harder to escape
~~~

The first three arrows are directly compatible with the public timing data.
The final pressure/causality arrow remains a hypothesis.

## Why this is interesting

A UI that cannot render a conversation does not necessarily imply that the
canonical conversation is gone.

The capture contains states consistent with:

- conversation snapshots returning successfully while a resume request returns
  404;
- later transitions into a paired blocked regime;
- blocked observations occurring at a faster cadence than accessible ones;
- brief accessible excursions inside longer blocked periods;
- a later successful long-lived resume after WebSocket reconnection activity.

This suggests a useful systems principle:

> **Observed failure != global system failure.**

Conversation availability, snapshot accessibility, stream observability,
recovery attachment and user-visible readability should not automatically be
collapsed into one WORKING/BROKEN bit.

## Dataset

Raw HAR files are **not** included.

Only derivative fields are published:

- relative time from the first retained event;
- coarse event class;
- HTTP/transport status;
- request latency;
- payload size rounded to 4 KiB.

Excluded data includes:

- private session material;
- request/response headers;
- request/response bodies;
- account, user, project and conversation identifiers;
- exact URLs and query strings;
- absolute timestamps;
- message content.

See [docs/privacy.md](docs/privacy.md).

## Observed session

Two HAR captures were available. Capture A contained 345 entries; 341 matched
entries in the larger 1,705-entry Capture B.

To avoid double counting, quantitative analysis uses **Capture B only**.

Among retained recovery-related events:

| Event class | Count |
|---|---:|
| stream status observations | 122 |
| conversation snapshots | 114 |
| WebSocket attempts | 14 |
| conversation resume attempts | 3 |
| **total** | **253** |

## Coupled accessible / blocked regimes

A stream-status observation and conversation snapshot are paired when their
start times differ by no more than 50 ms.

The public JSONL reproduces:

| Regime | stream status | snapshot | Count |
|---|---|---|---:|
| Accessible | HTTP 200 | HTTP 200 | 48 |
| Blocked | no HTTP response | HTTP 429 | 60 |
| Mixed | any other combination | — | **0** |

Maximum observed pair-start skew is 9 ms.

The absence of mixed pairs is consistent with a shared latent regime affecting
multiple client-visible observations. It does not identify that regime's
server-side implementation.

## Cadence and latency shift

Median time until the next paired observation:

- Accessible: **10.272 s**
- Blocked: **5.998 s**

That corresponds to about a **1.71x higher median observation-cycle rate** in
the blocked regime.

Median latency:

| Metric | Accessible | Blocked |
|---|---:|---:|
| stream-status latency | 3570.987 ms | 340.994 ms |
| snapshot latency | 5099.195 ms | 325.632 ms |

The blocked snapshot path fails about **15.7x faster** by median latency.

### Cycle-time decomposition

For each within-epoch transition, define service time as the slower latency of
the paired stream/snapshot requests.

Across 106 active transitions:

~~~text
gap_s ~= 5.6164 + 0.9566 * service_s
R^2 = 0.99136
~~~

A robust Theil-Sen fit is also close:

~~~text
gap_s ~= 5.7017 + 0.9220 * service_s
~~~

Median inferred post-completion wait:

- Accessible: **5.383 s**
- Blocked: **5.647 s**

Adding a blocked-state indicator after service time contributes essentially
nothing to fit (about -0.0066 s).

See [docs/validation.md](docs/validation.md).

## Persistence and epoch boundary

The paired sequence contains one approximately **775.640 s** inactive gap.
That cross-gap adjacency is treated as an epoch boundary rather than a normal
state transition.

Within active epochs:

- Accessible -> Accessible: 38
- Accessible -> Blocked: 10
- Blocked -> Accessible: 8
- Blocked -> Blocked: 50

Therefore:

~~~text
P(Blocked next | Accessible) = 0.208333
P(Blocked next | Blocked)    = 0.862069
~~~

The blocked state is persistent in this capture.

There are 10 blocked runs. Two terminate at active-epoch boundaries and are
right-censored.

## Observation-count bias

Blocked cycles are shorter, so they produce more observations per unit time.

- blocked fraction by observation count: **55.6%**
- blocked fraction across active start-to-start time: **40.2%**

This is why the timing layer is better treated as a Markov renewal /
semi-Markov observation process rather than interpreting pair counts as
wall-clock occupancy.

## Resume observations

Two resume attempts returned HTTP 404 before later snapshot-429 periods.

Episode 1:

- first later snapshot 429: **349.013 s**
- successful snapshots first: **32**
- public rounded snapshot payload first: **146.375 MiB**

Episode 2:

- first later snapshot 429: **87.853 s**
- successful snapshots first: **8**
- public rounded snapshot payload first: **36.594 MiB**

A later resume attempt returned HTTP 200 and remained active for about
**135.8 s**.

These timings weaken a simple “429 always causes resume failure” story.
They do **not** prove that a resume 404 causes a later 429.

The very different successful-count / payload totals also do not support a
simple fixed snapshot-count or fixed-byte threshold from this sample.

## DCS-inspired mathematical model

The model separates client-visible state:

~~~text
x_t = (C_t, A_t, O_t, R_t, P_t, Theta_t, U_t)
~~~

where the variables represent canonical conversation availability, snapshot
accessibility, observability, recovery attachment, latent pressure, an
effective threshold/capacity state and user-visible utility.

The key revised mechanism is:

~~~text
Delta_n = S_n + W_n
X ~= 1 / (S + W)
~~~

combined with a conditional pressure model:

~~~text
dP/dt = alpha * X(t) - delta * P(t) + xi(t)

Pr(429) = sigmoid(P(t) - Theta(t))
~~~

If higher pressure produces earlier rejection, so that service time falls as
pressure rises, a completion-coupled loop can acquire positive feedback.

The full derivation and falsification conditions are in
[docs/model.md](docs/model.md).

## Recovery proposal

The proposed client-side recovery rule is:

> **Do not let a fast failure automatically shorten start-to-start retry
> spacing.**

A conceptual scheduler is:

~~~text
next_start =
    max(
        last_start + minimum_period,
        now + error_backoff(error_class, consecutive_failures)
    )
~~~

The proposal also includes:

- exponential backoff + jitter for throttling;
- a bounded retry budget / circuit breaker;
- cheap re-observation before expensive full snapshots;
- single-flight snapshot recovery;
- preserving the last-known-good readable UI;
- atomic snapshot/version reconciliation;
- stream reattachment after state reconciliation;
- recovery hysteresis so one brief success does not reset all backoff state.

See [docs/recovery-design.md](docs/recovery-design.md).

## Robust Monte Carlo stress test

Because the production causal mechanism is not identified, the recovery policy
is also stress-tested against **three deliberately different models**:

1. an attempt-driven embedded Markov model, where waiting cannot make recovery
   progress;
2. a latent wall-clock clearing model, where polling only changes detection
   delay;
3. a hypothetical pressure-feedback model, where attempts consume a decaying
   pressure budget.

A 30,000-resample bootstrap puts the Accessible median cycle at approximately:

~~~text
95% bootstrap interval: 10.002 s .. 10.987 s
median:                 10.272 s
~~~

This makes a **~10 s start-to-start anchor** a data-derived conservative
controller rather than an arbitrary constant.

In the CI reference run (5,000 trials per policy/model), the 10 s anchor:

- preserves 99.96% recovery in the deliberately adverse attempt-driven model;
- reduces mean blocked probes from 6.85 to 4.32 in the latent wall-clock model,
  with p95 detection delay increasing from 5.79 s to 9.53 s;
- raises recovery rate from 52.68% to 69.10% in the hypothetical
  pressure-feedback stress model.

Stronger exponential backoff performs much better under pressure feedback, but
can perform much worse if the causal model is wrong. The robust core is
therefore:

> **first prevent fast failure from increasing start-to-start attempt rate;
> escalate backoff only with stronger evidence.**

See [docs/monte-carlo.md](docs/monte-carlo.md) and
[data/monte_carlo_reference.json](data/monte_carlo_reference.json).

## Reproduce from public data

The public event stream can be re-analyzed without a raw HAR:

~~~bash
python3 scripts/analyze_public_data.py
~~~

The script reconstructs the 108 pairs, censors the inactive epoch boundary and
recomputes the timing / transition statistics using only Python's standard
library.

To sanitize your own local HAR first:

~~~bash
python3 scripts/extract_public_events.py input.har output.jsonl
python3 scripts/analyze_public_data.py output.jsonl
~~~

**Do not publish raw HAR files.** They can contain private session and account
material.

Review derivative output manually before publishing it.

## Numerical precision check

The cycle-time fit is small and well conditioned:

- design-matrix condition number: about **5.62**
- normal-matrix condition number: about **31.6**

An 80-digit recomputation agrees with ordinary binary64 at all displayed OLS
coefficient digits.

Accurate matrix-multiplication methods such as the Ozaki scheme are therefore
not needed for this fit: observation/model uncertainty dominates floating-point
roundoff.

See [docs/validation.md](docs/validation.md) for the numerical audit.

## Files

- data/session_b_events.jsonl — sanitized relative event stream
- data/paired_observations.csv — 108 paired observations
- data/summary.json — quantitative summary
- data/monte_carlo_reference.json — CI Monte Carlo reference output
- docs/model.md — revised DCS / feedback model
- docs/validation.md — independent recomputation and model audit
- docs/recovery-design.md — concrete client-side recovery proposal
- docs/monte-carlo.md — robust policy stress test under causal-model uncertainty
- docs/methodology.md — pairing, sessionization and analysis rules
- docs/privacy.md — sanitization policy
- scripts/extract_public_events.py — HAR -> public event extractor
- scripts/analyze_public_data.py — public JSONL -> reproduced statistics
- scripts/monte_carlo_recovery.py — bootstrap + three-model policy stress test

## Scope and limitations

This is one observed user session, not a population study.

The data can show ordering, coupling, persistence, timing relations, cadence
changes and compatibility with hypotheses.

It cannot establish:

- OpenAI's internal implementation;
- the semantic meaning of a particular 404;
- whether a rate limiter is account-, endpoint-, edge-, or service-scoped;
- whether WebSocket failure is the initiating cause;
- whether increased observation traffic causes the 429 state;
- whether the same mechanism applies to every reported ChatGPT
  conversation-loading failure.

The right next step is replication across independent users, clients,
conversation sizes and network conditions.

## Responsible disclosure / privacy

This repository intentionally publishes **derived telemetry, not credentials or
raw traffic**.

If you want to contribute a capture, publish only sanitized derivative events.

Do not attach raw HAR files to public GitHub issues.

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

Independent observational research. Not affiliated with or endorsed by OpenAI.
