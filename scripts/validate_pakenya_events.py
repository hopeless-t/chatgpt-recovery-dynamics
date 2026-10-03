#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

required={"event_id","timestamp_utc","title","parent_event_id","domain","artifact_type","status","source_commit","adjacent_ideas_generated"}
optional={"fit_cohort","measurement_associated","timestamp_basis","lineage_basis"}
allowed=required|optional

def check(e):
    assert required <= set(e)
    assert set(e) <= allowed
    assert e["status"] in {"implemented","concept"}
    assert isinstance(e["adjacent_ideas_generated"],int) and e["adjacent_ideas_generated"]>=0
    if "fit_cohort" in e: assert e["fit_cohort"] in {"primary","observer_effect","post_checkpoint"}
    if "measurement_associated" in e: assert isinstance(e["measurement_associated"],bool)
    if e["status"]=="implemented":
        assert e["timestamp_utc"] and e["source_commit"]
        datetime.fromisoformat(e["timestamp_utc"].replace("Z","+00:00"))
    else:
        assert e["timestamp_utc"] is None and e["source_commit"] is None

schema=json.loads(Path("data/pakenya_event_schema.json").read_text())
assert schema["properties"]["status"]["enum"]==["implemented","concept"]
assert schema["properties"]["fit_cohort"]["enum"]==["primary","observer_effect","post_checkpoint"]

events=[json.loads(x) for x in Path("data/pakenya_events.jsonl").read_text().splitlines() if x.strip()]
concepts=[json.loads(x) for x in Path("data/pakenya_concepts.jsonl").read_text().splitlines() if x.strip()]
for e in events+concepts: check(e)

assert all(e["status"]=="implemented" for e in events)
assert all(e["status"]=="concept" for e in concepts)

ids=[e["event_id"] for e in events+concepts]
assert len(ids)==len(set(ids))
known=set(ids)
for e in events+concepts:
    if e["parent_event_id"] is not None:
        assert e["parent_event_id"] in known

primary=[e for e in events if e.get("fit_cohort","primary")=="primary"]
observer=[e for e in events if e.get("fit_cohort")=="observer_effect"]
post=[e for e in events if e.get("fit_cohort")=="post_checkpoint"]
assert len(primary)==10 and len(observer)==12 and len(post)>=1
assert all(e.get("measurement_associated") is True for e in observer)
assert all(e.get("measurement_associated") is True for e in post)
assert len(concepts)==7
assert all(e["timestamp_utc"] is None and e["source_commit"] is None for e in concepts)

print(f"Purrtocol event schema: PASS ({len(events)} implemented, {len(concepts)} concepts)")
