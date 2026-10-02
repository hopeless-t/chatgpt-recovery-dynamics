# Methodology

## Source captures

Two HAR captures were supplied from the same affected workflow.

- Capture A: 345 entries
- Capture B: 1,705 entries
- 341 Capture-A entries matched entries in Capture B using a strict signature of
  start time, method, URL, response status, duration and content size.

Capture A was therefore treated as an almost-entirely nested earlier capture.
Quantitative analysis uses Capture B only to avoid double counting.

## Retained event classes

The public dataset retains only four coarse classes:

- conversation_snapshot
- stream_status
- conversation_resume
- websocket

Exact hosts, paths and resource identifiers are not exported.

## Pairing rule

A stream_status event and conversation_snapshot event are paired when their
start times differ by no more than 50 ms. Each snapshot can be used only once.

For each stream-status event, the public reproduction script selects the closest
unused snapshot within the 50 ms window.

Observed pairs:

- 108 total
- 48: (200, 200) — labeled accessible
- 60: (no_http_response, 429) — labeled blocked
- 0 mixed pairs
- maximum observed start-time skew: 9 ms

The labels are descriptive shorthand for the capture, not claims about server
internals.

The pairing can be reproduced directly from data/session_b_events.jsonl with:

~~~bash
python3 scripts/analyze_public_data.py
~~~

## Timing

All public timestamps are converted to seconds relative to the first retained
event.

Absolute timestamps are deliberately removed.

## Payload size

Response payload size is rounded to the nearest 4 KiB before publication.

Request/response bodies are never copied.

All aggregate payload totals reported in the public analysis are now computed
from this rounded public field so that third parties can reproduce them exactly.
Earlier source-level aggregate values differed slightly because they were
calculated before the 4 KiB rounding step.

## Active-epoch sessionization

The paired-observation sequence contains one approximately 775.640 s inactive
gap. Treating the observations on each side of that gap as an ordinary
state-to-state transition would imply continuity that was not observed.

For transition and cycle-time analysis, a start-to-start gap greater than 60 s
is therefore treated as an **epoch boundary** and the cross-boundary transition
is censored.

In this capture, that rule excludes exactly one cross-epoch transition.

This threshold is an analysis convention, not a claim about ChatGPT session
semantics. Future datasets should report sensitivity to the chosen threshold
when multiple candidate gaps exist.

## Transition statistics

Transitions are computed only within active epochs.

Observed active-epoch transitions:

- Accessible -> Accessible: 38
- Accessible -> Blocked: 10
- Blocked -> Accessible: 8
- Blocked -> Blocked: 50

Therefore:

~~~text
P(Blocked next | Accessible) = 10 / 48 = 0.208333
P(Blocked next | Blocked)    = 50 / 58 = 0.862069
~~~

Wilson 95% intervals are reported by the public analysis script.

Blocked runs that terminate at the end of an active epoch are treated as
right-censored for interpretation. There are two such runs in this capture.

## Cycle-time decomposition

For each within-epoch transition from paired observation n to n+1:

~~~text
Delta_n = start_(n+1) - start_n
~~~

The pair's observed service/failure time is approximated as the slower of the
two paired request latencies:

~~~text
S_n = max(stream_latency_n, snapshot_latency_n)
~~~

This choice is motivated by the fact that the two requests start almost
simultaneously and the observed next-cycle timing is most strongly associated
with completion of the slower member.

The residual wait is:

~~~text
W_n = Delta_n - S_n
~~~

A simple one-predictor least-squares fit is then applied:

~~~text
Delta_n = beta_0 + beta_1 * S_n + epsilon_n
~~~

The public fit uses 106 within-epoch transitions and yields approximately:

~~~text
beta_0 = 5.6164 s
beta_1 = 0.9566
R^2    = 0.99136
~~~

This is an observational timing relation. It does not identify a specific
client timer or implementation.

## Observation-count versus time occupancy

Because the two regimes have different cycle lengths, the fraction of retained
observations in a state is not the same as the fraction of active wall-clock
time assigned to that state.

The repository therefore reports both:

- blocked fraction by observation count;
- blocked fraction by within-epoch start-to-start active time.

This avoids interpreting a faster-sampled state as if it necessarily occupied
the same fraction of time.

## Resume episodes

For each conversation_resume 404, the analysis finds the first later
conversation_snapshot 429 and counts successful snapshot-200 events in between.

Payload totals are summed from the public 4 KiB-rounded field.

The ordering is descriptive and does not establish that the resume response
caused the later 429.

## Numerical validation

The published cycle-time regression is small and well conditioned. High
precision arithmetic reproduces the displayed coefficients, so floating-point
roundoff is not a material uncertainty source for this analysis.

The dominant uncertainties are observational:

- HAR timing precision and instrumentation;
- omitted/non-retained request classes;
- unknown server-side state;
- epoch boundaries;
- a single user/session sample;
- possible client scheduling behavior not visible in the HAR.

## Limitations

HAR status 0 is represented as no_http_response. It is a client-side
observation, not an HTTP status code.

Network capture timing can be affected by browser instrumentation, aborted
requests, local scheduling and implementation details.

No server-side logs were available.

The retained event classes are a deliberately narrow projection of the full
network trace. Request pressure inferred from them should not be interpreted as
total account-, edge-, or service-level traffic.
