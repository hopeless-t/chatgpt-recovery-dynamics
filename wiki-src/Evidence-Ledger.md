# Evidence Ledger

This project deliberately separates evidence strength.

## Directly observed

- 108 paired observations
- 48 Accessible / 60 Blocked / 0 mixed
- fast-fail timing in Blocked
- B -> E -> B rebound morphology
- latency change point aligned with first Blocked observation
- residual timing memory

## Recomputed / robustness checked

- pairing-window sensitivity
- epoch-gap sensitivity
- cross-epoch cycle-law prediction
- cross-epoch H/E/B model prediction
- high-precision numerical recomputation

## Compatible but not identified

- retry-pressure contribution to 429 persistence
- byte/work-weighted pressure
- slow latent capacity/headroom state
- transport/recovery dissociation

## Explicitly not established

- OpenAI internal root cause
- exact production rate-limit scope
- exact production capacity
- free-vs-paid traffic share
- production queue sizes
- physical meaning of the AR(1)-like residual state

Full ledger: [docs/evidence-ledger.md](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/evidence-ledger.md)