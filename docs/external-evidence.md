# External public-report archaeology

This archive preserves public reports that may be relevant to ChatGPT
conversation-loading and recovery failures.

The purpose is historical and model-comparison oriented:

> a public self-report is evidence that a symptom was publicly observed and
> described at that time; it is not automatically evidence that the reporter
> identified the correct mechanism.

## Evidence planes

The repository deliberately separates three evidence planes.

### Plane A — local instrumented evidence

HAR-derived sanitized telemetry from the local case.

This is the strongest quantitative evidence in the repository.

### Plane B — external public observations

Reddit / Hacker News reports.

These may preserve useful historical symptom morphology:

- Unable to load conversation
- Too Many Requests
- blank/unavailable history
- cross-client disagreement
- temporary recovery after refresh/wait/restart
- stream recovery timeout
- resume 404
- backend/client state disagreement

They are not assumed to be independent, truthful, complete or sampled without
selection bias.

### Plane C — official incident context

OpenAI Status incidents are archived separately.

They establish that service-level conversation incidents existed at particular
times, but they do not prove that an individual Reddit/HN report had the same
root cause.

## Archaeological result

The current curated archive contains:

- 15 public-report artifacts;
- 1 explicit negative control;
- 1 possible overlap with the local case, excluded by default from independent
  corroboration counts;
- 13 reports in the default weak-evidence subset;
- 13 distinct report dates;
- a 1,301-day span from the oldest retained HN artifact to the newest;
- 12 distinct 2026 report dates across a 185-day span from March 28 to
  September 29.

This is **recurrence evidence**, not prevalence evidence.

The corpus cannot tell us what fraction of ChatGPT users were affected.

## Symptom morphology

Within the 13-report default subset:

- Too Many Requests: 9
- Unable to load conversation: 5
- temporary recovery: 5
- history/sidebar unavailable: 3
- multi-client symptom differences: 3
- conversation mutation association: 3
- apparent canonical conversation presence despite UI failure: 2
- transport-recovery anomaly: 2
- resume 404: 1
- stream recovery polling timeout: 1

Observed co-occurrence:

- Unable-to-load + Too-Many-Requests: 4
- Too-Many-Requests + local trigger association: 5
- state-dissociation signature: 7
- transport-recovery signature: 2

After removing three reports overlapping or adjacent to known official
incidents, the 10-report sensitivity subset still contains:

- Unable-to-load + Too-Many-Requests: 3
- Too-Many-Requests + trigger association: 4
- state-dissociation signature: 6
- transport-recovery signature: 1

The pattern therefore does not disappear when obvious incident-confounded
reports are removed.

## Model constraints

The external archive is used as a **constraint set**, not as a synthetic
population sample.

### Pure canonical-data-loss model

A pure data-loss explanation has difficulty with reports where:

- history/sidebar is unavailable while a direct conversation remains
  accessible;
- browser/desktop retrieval fails while another client retrieves the same old
  conversation;
- refresh/wait/restart temporarily restores access.

Those reports are compatible with a dissociated accessibility/client-state
problem without requiring canonical deletion.

### Global single-state outage model

A single global WORKING/BROKEN bit has difficulty explaining:

- browser failure while iPhone access remains available;
- different error morphology across clients;
- one conversation surface failing while another path can still observe the
  conversation.

This motivates the DCS-style state vector.

### Completion-coupled / rate-pressure model

The public archive contains several reports associating Too Many Requests with:

- multiple tabs;
- archiving/deleting/renaming/organizing chats;
- suspected sidebar/list refresh behavior.

These reports do not prove retry amplification, but they are qualitatively
compatible with a model where observation/list/recovery traffic contributes to
a constrained request budget.

### Recovery-plane model

Technical reports containing:

- stream recovery polling timeout;
- conversation/resume 404;
- stream-status still indicating streaming;
- WebSocket failure / client desynchronization

are compatible with a recovery-plane failure distinct from canonical
conversation storage.

## Negative control

The archive intentionally retains a 2024 Hacker News case where the visible
string "Unable to load conversation" occurred because a private/non-share URL
was used incorrectly.

This is important.

It demonstrates:

> **error text alone is not a mechanism signature.**

The model should require morphology/co-occurrence, not string matching.

## Why no Bayes factor is reported

The Reddit/HN corpus is a convenience sample with unknown:

- reporting probability;
- duplication probability;
- account/client distribution;
- deletion/moderation history;
- incident overlap;
- independence between reporters;
- accuracy of technical interpretation.

Treating the posts as IID Bernoulli samples and producing a posterior
probability of the production root cause would create false precision.

Instead, the archive is used for:

1. historical recurrence;
2. symptom co-occurrence;
3. model falsification constraints;
4. candidate replication targets;
5. provenance-preserving archaeology.

## Source files

- `data/external_observations.jsonl`
- `data/external_summary.json`
- `data/official_incidents.jsonl`

The archive stores source URLs, dates, evidence class, caveats and manually
coded symptom features.

Public posts may be edited or deleted later. Keeping the structured provenance
record is part of the archaeological purpose.
