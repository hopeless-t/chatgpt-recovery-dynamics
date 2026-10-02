# Methodology

## Source captures

Two HAR captures were supplied from the same affected workflow.

- Capture A: 345 entries
- Capture B: 1,705 entries
- 341 Capture-A entries matched entries in Capture B using a strict signature of start time, method, URL, response status, duration and content size.

Capture A was therefore treated as an almost-entirely nested earlier capture. Quantitative analysis uses Capture B only to avoid double counting.

## Retained event classes

The public dataset retains only four coarse classes:

- `conversation_snapshot`
- `stream_status`
- `conversation_resume`
- `websocket`

Exact hosts, paths and resource identifiers are not exported.

## Pairing rule

A `stream_status` event and `conversation_snapshot` event are paired when their start times differ by no more than 50 ms. Each snapshot can be used only once.

Observed pairs:

- 108 total
- 48: `(200, 200)` — labeled `accessible`
- 60: `(no_http_response, 429)` — labeled `blocked`
- 0 mixed pairs

The labels are descriptive shorthand for the capture, not claims about server internals.

## Timing

All public timestamps are converted to seconds relative to the first retained event.

Absolute timestamps are deliberately removed.

## Payload size

Response payload size is rounded to the nearest 4 KiB before publication.

Request/response bodies are never copied.

## Transition statistics

Transitions are computed on the ordered sequence of paired observations.

`P(Blocked next | Blocked now)` is the empirical fraction of transitions out of a blocked observation that lead to another blocked observation.

## Limitations

HAR status `0` is represented as `no_http_response`. It is a client-side observation, not an HTTP status code.

Network capture timing can be affected by browser instrumentation, aborted requests, local scheduling and implementation details.

No server-side logs were available.
