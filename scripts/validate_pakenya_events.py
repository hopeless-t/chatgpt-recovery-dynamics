#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

required={"event_id","timestamp_utc","title","parent_event_id","domain","artifact_type","status","source_commit","adjacent_ideas_generated"}

def check(e):
    assert set(e)==required
    assert e["status"] in {"implemented","concept"}
    assert isinstance(e["adjacent_ideas_generated"],int) and e["adjacent_ideas_generated"]>=0
    if e["status"]=="implemented":
        assert e["timestamp_utc"] and e["source_commit"]
        datetime.fromisoformat(e["timestamp_utc"].replace("Z","+00:00"))
    else:
        assert e["timestamp_utc"] is None
        assert e["source_commit"] is None

schema=json.loads(Path("data/pakenya_event_schema.json").read_text())
assert schema["properties"]["status"]["enum"]==["implemented","concept"]

events=[json.loads(x) for x in Path("data/pakenya_events.jsonl").read_text().splitlines() if x.strip()]
for e in events:
    check(e)

ids={e["event_id"] for e in events}
assert len(ids)==len(events)
for e in events:
    if e["parent_event_id"] is not None:
        assert e["parent_event_id"] in ids

check({"event_id":"PKE-999","timestamp_utc":None,"title":"future concept","parent_event_id":"PKE-010","domain":"future","artifact_type":"concept","status":"concept","source_commit":None,"adjacent_ideas_generated":0})
print("Purrtocol event schema: PASS")
