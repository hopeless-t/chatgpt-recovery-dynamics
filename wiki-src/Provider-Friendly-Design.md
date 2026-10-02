# Provider Friendly Design

The constructive question is:

> How can a client recover more reliably while making a popular service do less unnecessary work?

## Ordering

```text
1. suppress duplicate recovery
2. cheap observation
3. Retry-After + jitter
4. one retry owner
5. bounded queue / early load shedding
6. protect useful foreground work
7. transport acceleration last
```

## Abstract local stress model

At base `rho = 0.90`:

```text
naive completion        18.54x retry amplification
server-friendly stack    3.98x retry amplification
```

Those are local simulation outputs, **not OpenAI production telemetry**.

At sustained `rho >= 1`, retry policy cannot create missing capacity. Some work must wait, degrade, or be shed.

Full design: [server-friendly congestion control](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/server-friendly-congestion-control.md)