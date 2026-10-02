# Privacy and sanitization policy

Raw HAR files are intentionally excluded from this repository.

HAR files can contain highly sensitive session material, account identifiers, private conversation content, URLs, request bodies, response bodies and other metadata.

The public derivative keeps only:

- relative time;
- coarse event class;
- transport/HTTP status;
- latency;
- response size rounded to 4 KiB.

The extractor does **not** export:

- headers;
- session secrets;
- request or response bodies;
- exact URL paths;
- query parameters;
- conversation IDs;
- account IDs;
- user IDs;
- project IDs;
- message text;
- absolute timestamps.

## Contributor rule

Never attach a raw HAR to a public issue or pull request.

If contributing observations, run the extractor locally, manually inspect the result, and submit only the derived output.

Even sanitized telemetry may be fingerprintable when combined with outside knowledge. Contributors should omit any additional context they consider identifying.
