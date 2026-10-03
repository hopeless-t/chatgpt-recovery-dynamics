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

## Analysis cohorts

~~~text
fit_cohort = primary
  original selected Purrtocol artifact cohort

fit_cohort = observer_effect
  measurement-associated artifacts created while operationalizing the side-study
~~~

`measurement_associated=true` is repository provenance, not a universal causal
observer-effect claim.

The first observer-inclusive checkpoint is frozen through:

~~~text
commit = ec25244a024f2049cfc7851c7fafd421d35a113c
time   = 2026-10-03T07:42:51Z
~~~

Later instrumentation is intentionally outside that checkpoint, otherwise every
attempt to document the observer effect would recursively create another event
inside the same measurement window.

Evidence boundary:

~~~text
commit timestamp             = repository observation
parent_event_id              = editorial lineage annotation
adjacent_ideas_generated     = author annotation
fit_cohort                   = analysis selection label
exponential / Hawkes fit     = descriptive model
quadratic singularity        = scenario
observation hazard           = illustrative unless instrumented
Earth saturation             = NOT YET OBSERVED
~~~

The joke may be sloppy; the schema may not be sloppy.
