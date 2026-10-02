# ADR-0002: Recovery requires hysteresis

- Status: Accepted
- Date: 2026-10-03

## Context

The active trace contains eight observed provisional Accessible samples immediately following Blocked.

Observed:

~~~text
B -> E -> B : 8
B -> E -> H : 0
~~~

where B = Blocked, E = provisional/Recovering, and H = established Healthy/Accessible.

## Decision

A client recovery state machine should not map the first successful observation directly to Healthy.

Instead:

~~~text
Blocked --success--> Recovering
Recovering --stable confirmation--> Healthy
Recovering --failure--> Blocked
~~~

Stable confirmation can be implementation-specific, but it should not require repeated expensive full snapshot materialization.

## Consequences

- Backoff/failure history is not reset on the first success.
- Temporary reentry is visible as an explicit state.
- The design aligns with the history-aware H/E/B model.
- Recovery may take slightly longer to declare success, trading speed for stability and lower amplification.
