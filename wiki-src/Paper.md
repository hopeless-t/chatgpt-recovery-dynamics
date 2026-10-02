# Paper

The repository builds a paper-style PDF from published derived JSON.

## Live source

- [PAPER.md](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/paper/PAPER.md)
- [Paper build documentation](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/paper/README.md)

## Build principle

The paper reads:

- data/summary.json
- data/transition_biopsy_reference.json
- data/deep_validation_reference.json
- data/server_congestion_reference.json

No raw HAR is used.

The generated PDF is rendered and text-validated in CI before being committed.
