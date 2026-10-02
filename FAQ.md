# FAQ

## Is this repository claiming to know OpenAI's internal root cause?

No. It publishes sanitized client-side observations, reproducible calculations,
compatible models, and design proposals. The evidence ledger explicitly marks
what is not established.

## What is the core observed pattern?

In the public paired trace there are 108 paired observations:

~~~text
48 Accessible
60 Blocked
0 mixed
~~~

The Blocked regime is persistent and fast-failing.

## Why introduce Recovering / E?

Because the first Accessible observation after Blocked rebounded immediately to Blocked in 8/8 observed cases in the active trace.

## Does that mean the rebound probability is always 100%?

No. Eight observations are a small within-capture sample. The design uses hysteresis because history is predictive here, not because a universal 100% law has been established.

## Why not just switch everything to HTTP/3?

Transport efficiency does not solve offered work above capacity, retry storms, or ambiguous application state. HTTP/3 is treated as optional path-survival acceleration, not as the recovery truth layer.

## Why a cheap observation before a snapshot?

Because using a multi-MiB snapshot merely to ask whether recovery is stable can be expensive. A small version/state check can answer a narrower question more cheaply if such a primitive exists.

## Is the 4 KiB probe a real OpenAI endpoint?

No. It is a simulation assumption used to compare architectures.

## Is the Recovery Helper an official OpenAI product?

No. It is a community research tool. Official OpenAI guidance always takes precedence.

## Does the Recovery Helper send anything?

No automatic network request is used by the Helper. It has no telemetry, cookies, local/session storage, external JavaScript, WebSocket, or background API calls. Explicit official links navigate only when clicked.

## Should I upload a raw authenticated HAR publicly?

No. Raw HAR files can contain sensitive session/account material. This project publishes sanitized derivative telemetry only.

## Is it safe to hammer refresh to collect more data?

No. The repository explicitly avoids production load testing and synthetic retry storms.

## What does "Visualization != Evidence" mean?

The neon diagrams explain the proposed design. They do not claim to reproduce OpenAI's internal topology.

## Why is there a cat mascot?

Because the repository already became far too serious for a problem that started with "my conversation will not load." The mascot is not evidence either.
