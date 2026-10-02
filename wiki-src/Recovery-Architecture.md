# Recovery Architecture

## State machine

```text
B / Blocked --success--> E / Recovering
E / Recovering --stable confirmation--> H / Healthy
E / Recovering --failure--> B / Blocked
```

The current trace observed:

```text
B -> E -> B : 8
B -> E -> H : 0
```

So one successful observation is not treated as proof of stable recovery.

## Provider-friendly path

```text
local triggers
 -> single-flight owner
 -> cheap state/version observation
 -> start-anchored retry if blocked
 -> E / Recovering
 -> stable confirmation
 -> full snapshot once
 -> atomic reconcile
 -> optional realtime reattach
```

## Transport profile

```text
HTTP/2      baseline
HTTP/1.1    correctness-preserving fallback
HTTP/3      optional path-survival acceleration
WebSocket   optional realtime observation
```

Transport survival is not application truth.

See the [animated view](https://hopeless-t.github.io/chatgpt-recovery-dynamics/network/).