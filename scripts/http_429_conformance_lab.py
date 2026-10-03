#!/usr/bin/env python3
"""Loopback-only HTTP 429 conformance lab.

This file performs real HTTP I/O only against an ephemeral server bound to
127.0.0.1. It never accepts a remote host or production URL.

The lab combines:
- real local HTTP response/header parsing;
- an injected virtual timeline for deterministic retry scheduling;
- ambiguous POST transport failure after a local side effect;
- an explicit lab-only idempotency contract that demonstrates
  operation_id stability and attempt_id churn.

No production traffic is generated.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import socket
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from http_429_survival import decide

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = ROOT / "data" / "http_429_conformance_scenarios.json"


@dataclass
class LabState:
    scenarios: dict[str, dict[str, Any]]
    scripted_counts: dict[str, int] = field(default_factory=dict)
    request_log: list[dict[str, Any]] = field(default_factory=list)

    ambiguous_post_requests: int = 0
    ambiguous_effects: int = 0

    idempotent_post_requests: int = 0
    idempotent_effects: int = 0
    idempotent_seen: dict[str, dict[str, Any]] = field(default_factory=dict)
    idempotent_drop_done: bool = False


class LabHTTPServer(HTTPServer):
    lab_state: LabState


class Handler(BaseHTTPRequestHandler):
    server_version = "Purrtocol429Lab/1"

    def log_message(self, format: str, *args: Any) -> None:
        # Keep CI output deterministic and quiet.
        return

    @property
    def state(self) -> LabState:
        return self.server.lab_state  # type: ignore[attr-defined]

    def _record(self) -> None:
        self.state.request_log.append(
            {
                "method": self.command,
                "path": urllib.parse.urlparse(self.path).path,
                "operation_id": self.headers.get("X-Lab-Operation-Id"),
                "attempt_id": self.headers.get("X-Lab-Attempt-Id"),
            }
        )

    def _json(self, status: int, body: Any, headers: dict[str, str] | None = None) -> None:
        payload = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status)
        supplied = dict(headers or {})
        lower = {key.lower() for key in supplied}
        for key, value in supplied.items():
            self.send_header(key, value)
        if "content-type" not in lower:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _drop_connection(self) -> None:
        self.close_connection = True
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.connection.close()
        except OSError:
            pass

    def do_GET(self) -> None:
        self._record()
        path = urllib.parse.urlparse(self.path).path

        if path.startswith("/scripted/"):
            scenario_id = path.removeprefix("/scripted/")
            scenario = self.state.scenarios.get(scenario_id)
            if scenario is None:
                self._json(404, {"error": "unknown scenario"})
                return

            count = self.state.scripted_counts.get(scenario_id, 0)
            self.state.scripted_counts[scenario_id] = count + 1
            responses = scenario["responses"]
            response = responses[min(count, len(responses) - 1)]
            self._json(
                int(response["status"]),
                response.get("body", {}),
                {str(k): str(v) for k, v in response.get("headers", {}).items()},
            )
            return

        if path == "/state":
            self._json(
                200,
                {
                    "ambiguous_effects": self.state.ambiguous_effects,
                    "ambiguous_post_requests": self.state.ambiguous_post_requests,
                    "idempotent_effects": self.state.idempotent_effects,
                    "idempotent_post_requests": self.state.idempotent_post_requests,
                },
            )
            return

        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        self._record()
        path = urllib.parse.urlparse(self.path).path

        length = int(self.headers.get("Content-Length", "0") or "0")
        if length:
            self.rfile.read(length)

        if path == "/ambiguous-apply":
            self.state.ambiguous_post_requests += 1
            self.state.ambiguous_effects += 1

            # Apply the local side effect, then lose the response.
            # The client cannot infer "not applied" from the transport failure.
            self._drop_connection()
            return

        if path == "/idempotent-apply":
            self.state.idempotent_post_requests += 1
            operation_id = self.headers.get("X-Lab-Operation-Id")
            if not operation_id:
                self._json(400, {"error": "missing X-Lab-Operation-Id"})
                return

            if operation_id not in self.state.idempotent_seen:
                self.state.idempotent_effects += 1
                self.state.idempotent_seen[operation_id] = {
                    "operation_id": operation_id,
                    "effect_number": self.state.idempotent_effects,
                }

            stored = self.state.idempotent_seen[operation_id]

            if not self.state.idempotent_drop_done:
                self.state.idempotent_drop_done = True
                self._drop_connection()
                return

            self._json(
                200,
                {
                    "ok": True,
                    "deduplicated": True,
                    **stored,
                },
            )
            return

        self._json(404, {"error": "not found"})


class RunningServer:
    def __init__(self, scenarios: dict[str, dict[str, Any]]) -> None:
        self.server = LabHTTPServer(("127.0.0.1", 0), Handler)
        self.server.lab_state = LabState(scenarios=scenarios)
        host, port = self.server.server_address
        if host != "127.0.0.1":
            raise RuntimeError(f"refusing non-loopback bind: {host}")
        self.base_url = f"http://127.0.0.1:{port}"
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )

    @property
    def state(self) -> LabState:
        return self.server.lab_state

    def __enter__(self) -> "RunningServer":
        self.thread.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2.0)


def header(headers: dict[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def request_json(
    *,
    method: str,
    url: str,
    headers: dict[str, str],
    body: dict[str, Any] | None = None,
) -> tuple[int | None, dict[str, str], Any | None, str | None]:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=2.0) as response:
            payload = response.read()
            decoded = json.loads(payload) if payload else None
            return (
                int(response.status),
                dict(response.headers.items()),
                decoded,
                None,
            )
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        decoded = json.loads(payload) if payload else None
        return int(exc.code), dict(exc.headers.items()), decoded, None
    except (
        urllib.error.URLError,
        http.client.RemoteDisconnected,
        ConnectionResetError,
        ConnectionAbortedError,
        BrokenPipeError,
    ) as exc:
        return None, {}, None, type(exc).__name__


def client_settings(scenario: dict[str, Any]) -> dict[str, Any]:
    return scenario["client"]


def run_scripted(
    server: RunningServer,
    scenario: dict[str, Any],
    *,
    base_datetime: dt.datetime,
) -> dict[str, Any]:
    settings = client_settings(scenario)
    operation_id = scenario["operation_id"]
    virtual_start = 0.0
    starts: list[float] = []
    attempts: list[dict[str, Any]] = []
    terminal = "UNSET"

    for attempt_number in range(1, int(settings["retry_budget"]) + 2):
        start = virtual_start
        starts.append(start)
        attempt_id = f"{operation_id}:attempt:{attempt_number}"

        status, headers, body, transport_error = request_json(
            method=scenario["method"],
            url=f"{server.base_url}/scripted/{scenario['scenario_id']}",
            headers={
                "X-Lab-Operation-Id": operation_id,
                "X-Lab-Attempt-Id": attempt_id,
            },
        )

        response_index = min(
            attempt_number - 1,
            len(scenario["responses"]) - 1,
        )
        service_s = float(scenario["responses"][response_index]["service_s"])
        now_s = start + service_s

        event = {
            "attempt_number": attempt_number,
            "operation_id": operation_id,
            "attempt_id": attempt_id,
            "start_s": start,
            "service_s": service_s,
            "status": status,
            "transport_error": transport_error,
            "retry_after": header(headers, "Retry-After"),
            "ratelimit": header(headers, "RateLimit"),
            "body": body,
        }

        if status is not None and 200 <= status < 300:
            event["decision"] = "SUCCESS"
            attempts.append(event)
            terminal = "SUCCESS"
            break

        if status is None:
            event["decision"] = "UNEXPECTED_TRANSPORT_FAILURE"
            attempts.append(event)
            terminal = "UNEXPECTED_TRANSPORT_FAILURE"
            break

        decision = decide(
            status=status,
            method=scenario["method"],
            operation_state="read_only_observation",
            application_idempotency_contract=False,
            attempt_number=attempt_number,
            retry_budget=int(settings["retry_budget"]),
            operation_id=operation_id,
            now_s=now_s,
            previous_start_s=start,
            minimum_period_s=float(settings["minimum_period_s"]),
            retry_after=event["retry_after"],
            draft_ratelimit=event["ratelimit"],
            local_base_s=float(settings["local_base_s"]),
            local_cap_s=float(settings["local_cap_s"]),
            herd_jitter_fraction=float(settings["herd_jitter_fraction"]),
            now_datetime=base_datetime + dt.timedelta(seconds=now_s),
        )
        event["decision"] = decision.action
        event["retry_decision"] = decision.as_dict()
        attempts.append(event)

        if decision.action != "WAIT_THEN_RETRY":
            terminal = decision.action
            break

        assert decision.next_start_s is not None
        virtual_start = decision.next_start_s

    gaps = [
        current - previous
        for previous, current in zip(starts, starts[1:])
    ]
    result = {
        "scenario_id": scenario["scenario_id"],
        "classification": "loopback_real_http_virtual_time",
        "terminal": terminal,
        "operation_id": operation_id,
        "attempts": attempts,
        "start_times_s": starts,
        "start_gaps_s": gaps,
        "server_requests": server.state.scripted_counts.get(
            scenario["scenario_id"],
            0,
        ),
    }
    validate_scripted_result(result, scenario["expect"])
    result["pass"] = True
    return result


def validate_scripted_result(
    result: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    assert result["terminal"] == expected["terminal"], result
    assert result["server_requests"] == expected["requests"], result

    if "min_second_start_s" in expected:
        assert len(result["start_times_s"]) >= 2
        assert result["start_times_s"][1] >= float(
            expected["min_second_start_s"]
        )

    if "min_start_gap_s" in expected:
        assert result["start_gaps_s"]
        assert min(result["start_gaps_s"]) >= float(
            expected["min_start_gap_s"]
        )

    if "draft_floor_s" in expected:
        first = result["attempts"][0]["retry_decision"]
        assert first["draft_ratelimit_floor_s"] == float(
            expected["draft_floor_s"]
        )


def run_unknown_post_reobserve(
    server: RunningServer,
    scenario: dict[str, Any],
    *,
    base_datetime: dt.datetime,
) -> dict[str, Any]:
    settings = scenario["client"]
    operation_id = scenario["operation_id"]
    attempt_id = f"{operation_id}:attempt:1"

    status, _, _, error = request_json(
        method="POST",
        url=f"{server.base_url}{scenario['endpoint']}",
        headers={
            "X-Lab-Operation-Id": operation_id,
            "X-Lab-Attempt-Id": attempt_id,
        },
        body={"action": "apply-once"},
    )
    assert status is None, (status, error)

    decision = decide(
        status=None,
        method="POST",
        operation_state="unknown",
        application_idempotency_contract=False,
        attempt_number=1,
        retry_budget=int(settings["retry_budget"]),
        operation_id=operation_id,
        now_s=0.05,
        previous_start_s=0.0,
        minimum_period_s=float(settings["minimum_period_s"]),
        retry_after=None,
        draft_ratelimit=None,
        local_base_s=float(settings["local_base_s"]),
        local_cap_s=float(settings["local_cap_s"]),
        herd_jitter_fraction=float(settings["herd_jitter_fraction"]),
        now_datetime=base_datetime + dt.timedelta(seconds=0.05),
    )
    assert decision.action == "REOBSERVE"

    state_status, _, state_body, state_error = request_json(
        method="GET",
        url=f"{server.base_url}/state",
        headers={
            "X-Lab-Operation-Id": operation_id,
            "X-Lab-Attempt-Id": f"{operation_id}:observe:1",
        },
    )
    assert state_status == 200, state_error

    result = {
        "scenario_id": scenario["scenario_id"],
        "classification": "loopback_ambiguous_non_idempotent",
        "transport_error": error,
        "decision": decision.as_dict(),
        "reobserved_state": state_body,
        "post_requests": server.state.ambiguous_post_requests,
        "side_effects": server.state.ambiguous_effects,
    }
    expected = scenario["expect"]
    assert result["decision"]["action"] == expected["decision"]
    assert result["post_requests"] == expected["post_requests"]
    assert result["side_effects"] == expected["side_effects"]
    assert state_body["ambiguous_effects"] == expected["reobserve_value"]
    result["pass"] = True
    return result


def run_explicit_contract(
    server: RunningServer,
    scenario: dict[str, Any],
    *,
    base_datetime: dt.datetime,
) -> dict[str, Any]:
    settings = scenario["client"]
    operation_id = scenario["operation_id"]
    attempt_ids = []

    attempt1 = f"{operation_id}:attempt:1"
    attempt_ids.append(attempt1)
    status1, _, _, error1 = request_json(
        method="POST",
        url=f"{server.base_url}{scenario['endpoint']}",
        headers={
            "X-Lab-Operation-Id": operation_id,
            "X-Lab-Attempt-Id": attempt1,
        },
        body={"action": "apply-once"},
    )
    assert status1 is None, (status1, error1)

    decision = decide(
        status=None,
        method="POST",
        operation_state="unknown",
        application_idempotency_contract=True,
        attempt_number=1,
        retry_budget=int(settings["retry_budget"]),
        operation_id=operation_id,
        now_s=0.05,
        previous_start_s=0.0,
        minimum_period_s=float(settings["minimum_period_s"]),
        retry_after=None,
        draft_ratelimit=None,
        local_base_s=float(settings["local_base_s"]),
        local_cap_s=float(settings["local_cap_s"]),
        herd_jitter_fraction=float(settings["herd_jitter_fraction"]),
        now_datetime=base_datetime + dt.timedelta(seconds=0.05),
    )
    assert decision.action == "WAIT_THEN_RETRY"
    assert decision.next_start_s is not None

    attempt2 = f"{operation_id}:attempt:2"
    attempt_ids.append(attempt2)
    status2, _, body2, error2 = request_json(
        method="POST",
        url=f"{server.base_url}{scenario['endpoint']}",
        headers={
            "X-Lab-Operation-Id": operation_id,
            "X-Lab-Attempt-Id": attempt2,
        },
        body={"action": "apply-once"},
    )
    assert status2 == 200, (status2, error2)
    assert body2["operation_id"] == operation_id

    server_operation_ids = [
        row["operation_id"]
        for row in server.state.request_log
        if row["path"] == scenario["endpoint"]
    ]
    server_attempt_ids = [
        row["attempt_id"]
        for row in server.state.request_log
        if row["path"] == scenario["endpoint"]
    ]

    result = {
        "scenario_id": scenario["scenario_id"],
        "classification": "loopback_explicit_application_idempotency",
        "first_transport_error": error1,
        "first_decision": decision.as_dict(),
        "terminal": "SUCCESS",
        "operation_id": operation_id,
        "attempt_ids": attempt_ids,
        "server_operation_ids": server_operation_ids,
        "server_attempt_ids": server_attempt_ids,
        "post_requests": server.state.idempotent_post_requests,
        "side_effects": server.state.idempotent_effects,
        "response": body2,
    }
    expected = scenario["expect"]
    assert result["first_decision"]["action"] == expected["decision"]
    assert result["terminal"] == expected["terminal"]
    assert result["post_requests"] == expected["post_requests"]
    assert result["side_effects"] == expected["side_effects"]
    assert len(set(server_operation_ids)) == 1
    assert len(set(server_attempt_ids)) == 2
    result["pass"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenarios",
        default=str(DEFAULT_SCENARIOS),
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    spec = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    if spec["safety"]["network_scope"] != "loopback_only":
        raise SystemExit("refusing scenario file without loopback_only safety")

    base_datetime = dt.datetime.fromisoformat(
        spec["base_datetime"].replace("Z", "+00:00")
    )
    scripted_map = {
        row["scenario_id"]: row
        for row in spec["scripted"]
    }

    results = []
    with RunningServer(scripted_map) as server:
        assert server.base_url.startswith("http://127.0.0.1:")
        for scenario in spec["scripted"]:
            results.append(
                run_scripted(
                    server,
                    scenario,
                    base_datetime=base_datetime,
                )
            )

    for scenario in spec["ambiguous"]:
        with RunningServer(scripted_map) as server:
            if scenario["application_idempotency_contract"]:
                results.append(
                    run_explicit_contract(
                        server,
                        scenario,
                        base_datetime=base_datetime,
                    )
                )
            else:
                results.append(
                    run_unknown_post_reobserve(
                        server,
                        scenario,
                        base_datetime=base_datetime,
                    )
                )

    output = {
        "schema": "http-429-local-conformance-report/v1",
        "classification": "loopback_only_conformance_not_production_evidence",
        "network_scope": "127.0.0.1 ephemeral local server only",
        "standards_boundary": {
            "stable": [
                "RFC6585-429",
                "RFC9110-Retry-After",
                "RFC9457-Problem-Details",
            ],
            "experimental": [
                "draft-ietf-httpapi-ratelimit-headers-11 simple r=0;t hint"
            ],
            "not_assumed": [
                "universal Idempotency-Key semantics"
            ],
        },
        "results": results,
        "summary": {
            "scenarios": len(results),
            "passed": sum(bool(row.get("pass")) for row in results),
            "failed": sum(not bool(row.get("pass")) for row in results),
        },
        "safety": {
            "production_traffic": False,
            "rate_limit_evasion": False,
            "remote_target_input": False,
        },
    }

    text = json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")

    if output["summary"]["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
