# Purrtocol Expansion Event Schema

Canonical machine-readable schema:

`data/pakenya_event_schema.json`

Two statuses are allowed:

~~~text
implemented
concept
~~~

`implemented` means the artifact exists in the repository and has commit-backed
`timestamp_utc` and `source_commit`.

`concept` is reserved for future adjacent ideas such as Purrtocol University,
Evidence Court, the 3D model, or any other not-yet-built surface. Concept nodes
must leave `timestamp_utc` and `source_commit` null.

Only implemented timestamped events are eligible for the compound-growth and
Hawkes event-time fits.

Evidence boundary:

~~~text
commit timestamp             = repository observation
parent_event_id              = editorial lineage annotation
adjacent_ideas_generated     = author annotation
exponential / Hawkes fit     = descriptive model
quadratic singularity        = scenario
observation hazard           = illustrative unless instrumented
Earth saturation             = NOT YET OBSERVED
~~~

The joke may be sloppy; the schema may not be sloppy.
