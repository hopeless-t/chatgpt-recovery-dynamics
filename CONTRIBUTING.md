# Contributing

Independent replication is welcome.

Please contribute only sanitized, derived telemetry.

## Never upload

- raw HAR files
- session secrets or browser credentials
- conversation/message content
- user, account, project or conversation identifiers
- full request/response bodies

## Suggested contribution

1. Run `scripts/extract_public_events.py` locally.
2. Manually inspect the JSONL.
3. Add a short metadata note describing only non-identifying conditions, such as client family and whether the failure was naturally observed.
4. Open a pull request with the sanitized derivative and analysis.

Please distinguish observation from inference and avoid claiming an OpenAI internal root cause without server-side evidence.


## Responsible testing

Before contributing, read [RESPONSIBLE_TESTING.md](RESPONSIBLE_TESTING.md).

Do not generate synthetic load, retry storms, deliberate 429s, or coordinated
recovery traffic against production OpenAI services for the purpose of this
repository.

Prefer passive observation of naturally occurring failures and local
simulation.

Contributions that reduce duplicate/retry/provider work are especially welcome.


## Purrtocol variants

Forked and derivative Purrtocols are welcome.

Read [PURRTOCOL_VARIANTS.md](PURRTOCOL_VARIANTS.md), start from
[examples/purrtocol-variant.example.json](examples/purrtocol-variant.example.json),
and use the Purrtocol Variant pull-request template if you want upstream lineage
indexing.

A fork does not need upstream approval to exist. Upstream indexing records
provenance; it does not imply endorsement, ranking, or empirical validation.

Please keep lineage and third-party asset licensing explicit.
