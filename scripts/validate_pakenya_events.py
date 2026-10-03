#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

required = {
    "event_id", "timestamp_utc", "title", "parent_event_id", "domain",
    "artifact_type", "status", "source_commit", "adjacent_ideas_generated",
}
optional = {"fit_cohort", "measurement_associated", "timestamp_basis", "lineage_basis"}
allowed = required | optional

def check(e):
    assert required <= set(e)
    assert set(e) <= allowed
    assert e["status"] in {"implemented", "concept"}
    assert isinstance(e["adjacent_ideas_generated"], int)
    assert e["adjacent_ideas_generated"] >= 0
    if "fit_cohort" in e:
        assert e["fit_cohort"] in {"primary", "observer_effect", "post_checkpoint"}
    if "measurement_associated" in e:
        assert isinstance(e["measurement_associated"], bool)
    if e["status"] == "implemented":
        assert e["timestamp_utc"] and e["source_commit"]
        datetime.fromisoformat(e["timestamp_utc"].replace("Z", "+00:00"))
    else:
        assert e["timestamp_utc"] is None
        assert e["source_commit"] is None

schema = json.loads(Path("data/pakenya_event_schema.json").read_text(encoding="utf-8"))
assert schema["properties"]["status"]["enum"] == ["implemented", "concept"]
assert schema["properties"]["fit_cohort"]["enum"] == ["primary", "observer_effect", "post_checkpoint"]

events = [
    json.loads(x)
    for x in Path("data/pakenya_events.jsonl").read_text(encoding="utf-8").splitlines()
    if x.strip()
]
concepts = [
    json.loads(x)
    for x in Path("data/pakenya_concepts.jsonl").read_text(encoding="utf-8").splitlines()
    if x.strip()
]
promotions = [
    json.loads(x)
    for x in Path("data/pakenya_promotions.jsonl").read_text(encoding="utf-8").splitlines()
    if x.strip()
]

for e in events + concepts:
    check(e)

assert all(e["status"] == "implemented" for e in events)
assert all(e["status"] == "concept" for e in concepts)

ids = [e["event_id"] for e in events + concepts]
assert len(ids) == len(set(ids))
known = set(ids)
for e in events + concepts:
    if e["parent_event_id"] is not None:
        assert e["parent_event_id"] in known

primary = [e for e in events if e.get("fit_cohort", "primary") == "primary"]
observer = [e for e in events if e.get("fit_cohort") == "observer_effect"]
post = [e for e in events if e.get("fit_cohort") == "post_checkpoint"]
assert len(primary) == 10
assert len(observer) == 12
assert len(post) >= 7
assert all(e.get("measurement_associated") is True for e in observer)
assert all(e.get("measurement_associated") is True for e in post)

assert len(concepts) == 7
assert len(promotions) == 7
by_event = {e["event_id"]: e for e in events}
concept_ids = {e["event_id"] for e in concepts}
seen_concepts = set()
seen_events = set()
for p in promotions:
    assert set(p) == {
        "concept_id", "implemented_event_id", "implementation_commit", "implemented_path"
    }
    assert p["concept_id"] in concept_ids
    assert p["implemented_event_id"] in by_event
    assert by_event[p["implemented_event_id"]]["source_commit"] == p["implementation_commit"]
    assert by_event[p["implemented_event_id"]]["fit_cohort"] == "post_checkpoint"
    assert p["concept_id"] not in seen_concepts
    assert p["implemented_event_id"] not in seen_events
    seen_concepts.add(p["concept_id"])
    seen_events.add(p["implemented_event_id"])

assert seen_concepts == concept_ids
assert all(e["timestamp_utc"] is None and e["source_commit"] is None for e in concepts)

print(
    f"Purrtocol event schema: PASS "
    f"({len(events)} implemented, {len(concepts)} concepts, {len(promotions)} promotions)"
)
