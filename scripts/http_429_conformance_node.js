#!/usr/bin/env node
"use strict";

/**
 * Independent Node.js implementation of the HTTP 429 Survival Plane.
 *
 * Safety boundary:
 * - standard library only;
 * - binds only to 127.0.0.1 on an ephemeral port;
 * - accepts no remote URL/host input;
 * - generates no production traffic.
 *
 * This intentionally does not import or invoke the Python scheduler/lab.
 * The shared inputs are the public contract/scenario JSON files only.
 */

const fs = require("node:fs");
const http = require("node:http");
const crypto = require("node:crypto");
const { URL } = require("node:url");

const SCENARIOS = "data/http_429_conformance_scenarios.json";
const IDEMPOTENT_METHODS = new Set([
  "GET", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE",
]);

function parseArgs(argv) {
  const out = { scenarios: SCENARIOS, output: null };
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--scenarios") out.scenarios = argv[++i];
    else if (argv[i] === "--output") out.output = argv[++i];
    else throw new Error(`unknown argument: ${argv[i]}`);
  }
  return out;
}

function parseRetryAfter(value, nowDate) {
  if (value == null) return null;
  const text = String(value).trim();
  if (!text) return null;
  if (/^\d+$/.test(text)) return Number.parseInt(text, 10);

  const parsed = Date.parse(text);
  if (Number.isNaN(parsed)) return null;
  return Math.max(0, (parsed - nowDate.getTime()) / 1000);
}

function parseDraftRateLimitZeroWindow(value) {
  if (value == null) return null;
  const match = String(value).match(
    /(?:^|,)\s*(?:"[^"]*"|[A-Za-z0-9._~-]+)\s*;[^,]*\br=0\b[^,]*\bt=(\d+)\b/i,
  );
  return match ? Number.parseInt(match[1], 10) : null;
}

function deterministicUnitInterval(key) {
  const digest = crypto.createHash("sha256").update(key, "utf8").digest();
  const numerator = digest.readBigUInt64BE(0);
  const denominator = (1n << 64n) - 1n;
  return Number(numerator) / Number(denominator);
}

function exponentialBackoff(attemptNumber, baseS, capS) {
  if (attemptNumber < 1) throw new Error("attemptNumber must be >= 1");
  if (baseS < 0 || capS < 0 || capS < baseS) {
    throw new Error("invalid backoff bounds");
  }
  const exponent = Math.min(attemptNumber - 1, 30);
  return Math.min(capS, baseS * (2 ** exponent));
}

function retryAuthorization(method, operationState, appIdempotency) {
  const upper = method.toUpperCase();

  if (operationState === "known_applied") {
    return ["STOP_DUPLICATE", "operation already known applied"];
  }
  if (
    operationState === "known_not_applied"
    || operationState === "read_only_observation"
  ) {
    return ["TIMED_RETRY", "operation state permits a timed retry"];
  }
  if (operationState !== "unknown") {
    throw new Error(`unknown operation state: ${operationState}`);
  }
  if (IDEMPOTENT_METHODS.has(upper)) {
    return [
      "TIMED_RETRY",
      "unknown outcome but HTTP method semantics are idempotent; timing and budget still apply",
    ];
  }
  if (appIdempotency) {
    return [
      "TIMED_RETRY",
      "unknown non-idempotent outcome covered by explicit application/provider idempotency contract",
    ];
  }
  return [
    "REOBSERVE",
    "unknown non-idempotent outcome without explicit idempotency contract",
  ];
}

function decide(input) {
  const {
    status,
    method,
    operationState,
    applicationIdempotencyContract,
    attemptNumber,
    retryBudget,
    operationId,
    nowS,
    previousStartS,
    minimumPeriodS,
    retryAfter,
    draftRateLimit,
    localBaseS,
    localCapS,
    herdJitterFraction,
    nowDate,
  } = input;

  if (attemptNumber < 1 || retryBudget < 1) throw new Error("invalid attempt/budget");
  if (minimumPeriodS < 0 || herdJitterFraction < 0) {
    throw new Error("negative timing value");
  }
  if (nowS < previousStartS) throw new Error("virtual time moved backwards");

  const attemptId = `${operationId}:attempt:${attemptNumber}`;
  const budgetRemaining = Math.max(0, retryBudget - attemptNumber);
  const [authorization, reason] = retryAuthorization(
    method,
    operationState,
    applicationIdempotencyContract,
  );

  const stop = (action, standardsUsed = []) => ({
    action,
    reason,
    next_start_s: null,
    retry_after_floor_s: 0,
    draft_ratelimit_floor_s: 0,
    local_backoff_s: 0,
    herd_jitter_s: 0,
    operation_id: operationId,
    attempt_id: attemptId,
    attempt_number: attemptNumber,
    budget_remaining_after_attempt: budgetRemaining,
    standards_used: standardsUsed,
  });

  if (authorization === "STOP_DUPLICATE") return stop("STOP_DUPLICATE");
  if (authorization === "REOBSERVE") {
    return stop("REOBSERVE", ["RFC9110-idempotent-method-semantics"]);
  }
  if (attemptNumber >= retryBudget) {
    const result = stop("STOP_BUDGET");
    result.reason = "retry budget exhausted";
    result.budget_remaining_after_attempt = 0;
    return result;
  }

  const retryAfterS = parseRetryAfter(retryAfter, nowDate);
  const retryAfterFloor = retryAfterS ?? 0;
  const draftHint = parseDraftRateLimitZeroWindow(draftRateLimit);
  const draftFloor = retryAfterS == null && draftHint != null ? draftHint : 0;
  const localBackoffS = exponentialBackoff(attemptNumber, localBaseS, localCapS);

  const baseNext = Math.max(
    previousStartS + minimumPeriodS,
    nowS + retryAfterFloor,
    nowS + draftFloor,
    nowS + localBackoffS,
  );

  const jitterWindow = Math.max(
    minimumPeriodS,
    retryAfterFloor,
    draftFloor,
    localBackoffS,
    1,
  ) * herdJitterFraction;
  const herdJitterS = jitterWindow * deterministicUnitInterval(
    `${operationId}:${attemptNumber}:herd-jitter`,
  );

  const standards = [];
  if (status === 429) standards.push("RFC6585-429");
  if (retryAfterS != null) standards.push("RFC9110-Retry-After");
  if (draftFloor > 0) standards.push("draft-ietf-httpapi-ratelimit-headers-11");

  return {
    action: "WAIT_THEN_RETRY",
    reason,
    next_start_s: baseNext + herdJitterS,
    retry_after_floor_s: retryAfterFloor,
    draft_ratelimit_floor_s: draftFloor,
    local_backoff_s: localBackoffS,
    herd_jitter_s: herdJitterS,
    operation_id: operationId,
    attempt_id: attemptId,
    attempt_number: attemptNumber,
    budget_remaining_after_attempt: budgetRemaining,
    standards_used: standards,
  };
}

function makeState(scriptedMap) {
  return {
    scriptedMap,
    scriptedCounts: new Map(),
    requestLog: [],
    ambiguousPostRequests: 0,
    ambiguousEffects: 0,
    idempotentPostRequests: 0,
    idempotentEffects: 0,
    idempotentSeen: new Map(),
    idempotentDropDone: false,
  };
}

function sendJson(res, status, body, headers = {}) {
  const payload = Buffer.from(JSON.stringify(body));
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": payload.length,
    ...headers,
  });
  res.end(payload);
}

async function startServer(scriptedMap) {
  const state = makeState(scriptedMap);

  const server = http.createServer((req, res) => {
    const parsed = new URL(req.url, "http://127.0.0.1");
    const path = parsed.pathname;
    state.requestLog.push({
      method: req.method,
      path,
      operation_id: req.headers["x-lab-operation-id"] ?? null,
      attempt_id: req.headers["x-lab-attempt-id"] ?? null,
    });

    const consumeBody = (done) => {
      req.on("data", () => {});
      req.on("end", done);
    };

    if (req.method === "GET" && path.startsWith("/scripted/")) {
      const id = path.slice("/scripted/".length);
      const scenario = state.scriptedMap.get(id);
      if (!scenario) return sendJson(res, 404, { error: "unknown scenario" });

      const count = state.scriptedCounts.get(id) ?? 0;
      state.scriptedCounts.set(id, count + 1);
      const responses = scenario.responses;
      const response = responses[Math.min(count, responses.length - 1)];
      return sendJson(res, Number(response.status), response.body ?? {}, response.headers ?? {});
    }

    if (req.method === "GET" && path === "/state") {
      return sendJson(res, 200, {
        ambiguous_effects: state.ambiguousEffects,
        ambiguous_post_requests: state.ambiguousPostRequests,
        idempotent_effects: state.idempotentEffects,
        idempotent_post_requests: state.idempotentPostRequests,
      });
    }

    if (req.method === "POST" && path === "/ambiguous-apply") {
      return consumeBody(() => {
        state.ambiguousPostRequests += 1;
        state.ambiguousEffects += 1;
        req.socket.destroy();
      });
    }

    if (req.method === "POST" && path === "/idempotent-apply") {
      return consumeBody(() => {
        state.idempotentPostRequests += 1;
        const operationId = req.headers["x-lab-operation-id"];
        if (!operationId) return sendJson(res, 400, { error: "missing operation id" });

        if (!state.idempotentSeen.has(operationId)) {
          state.idempotentEffects += 1;
          state.idempotentSeen.set(operationId, {
            operation_id: operationId,
            effect_number: state.idempotentEffects,
          });
        }
        const stored = state.idempotentSeen.get(operationId);

        if (!state.idempotentDropDone) {
          state.idempotentDropDone = true;
          req.socket.destroy();
          return;
        }

        return sendJson(res, 200, {
          ok: true,
          deduplicated: true,
          ...stored,
        });
      });
    }

    return sendJson(res, 404, { error: "not found" });
  });

  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });

  const address = server.address();
  if (!address || typeof address === "string" || address.address !== "127.0.0.1") {
    server.close();
    throw new Error("refusing non-loopback bind");
  }

  return {
    server,
    state,
    baseUrl: `http://127.0.0.1:${address.port}`,
    async close() {
      await new Promise((resolve) => server.close(resolve));
    },
  };
}

function requestJson(method, url, headers = {}, body = null) {
  return new Promise((resolve) => {
    const payload = body == null ? null : Buffer.from(JSON.stringify(body));
    const requestHeaders = { ...headers };
    if (payload) {
      requestHeaders["Content-Type"] = "application/json";
      requestHeaders["Content-Length"] = payload.length;
    }

    const req = http.request(url, { method, headers: requestHeaders }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf8");
        let decoded = null;
        if (raw) {
          try { decoded = JSON.parse(raw); } catch { decoded = raw; }
        }
        resolve({
          status: res.statusCode,
          headers: res.headers,
          body: decoded,
          error: null,
        });
      });
    });

    req.setTimeout(2000, () => req.destroy(new Error("RequestTimeout")));
    req.on("error", (error) => resolve({
      status: null,
      headers: {},
      body: null,
      error: error.code || error.name,
    }));
    if (payload) req.write(payload);
    req.end();
  });
}

function header(headers, name) {
  return headers[String(name).toLowerCase()] ?? null;
}

function assert(condition, message) {
  if (!condition) throw new Error(message || "assertion failed");
}

async function runScripted(server, scenario, baseDate) {
  const settings = scenario.client;
  const operationId = scenario.operation_id;
  let virtualStart = 0;
  const starts = [];
  const attempts = [];
  let terminal = "UNSET";

  for (let attemptNumber = 1; attemptNumber <= settings.retry_budget + 1; attemptNumber += 1) {
    const start = virtualStart;
    starts.push(start);
    const attemptId = `${operationId}:attempt:${attemptNumber}`;
    const response = await requestJson(
      scenario.method,
      `${server.baseUrl}/scripted/${scenario.scenario_id}`,
      {
        "X-Lab-Operation-Id": operationId,
        "X-Lab-Attempt-Id": attemptId,
      },
    );

    const responseIndex = Math.min(attemptNumber - 1, scenario.responses.length - 1);
    const serviceS = Number(scenario.responses[responseIndex].service_s);
    const nowS = start + serviceS;

    const event = {
      attempt_number: attemptNumber,
      operation_id: operationId,
      attempt_id: attemptId,
      start_s: start,
      service_s: serviceS,
      status: response.status,
      transport_error: response.error,
      retry_after: header(response.headers, "retry-after"),
      ratelimit: header(response.headers, "ratelimit"),
      body: response.body,
    };

    if (response.status != null && response.status >= 200 && response.status < 300) {
      event.decision = "SUCCESS";
      attempts.push(event);
      terminal = "SUCCESS";
      break;
    }
    if (response.status == null) {
      event.decision = "UNEXPECTED_TRANSPORT_FAILURE";
      attempts.push(event);
      terminal = "UNEXPECTED_TRANSPORT_FAILURE";
      break;
    }

    const decision = decide({
      status: response.status,
      method: scenario.method,
      operationState: "read_only_observation",
      applicationIdempotencyContract: false,
      attemptNumber,
      retryBudget: Number(settings.retry_budget),
      operationId,
      nowS,
      previousStartS: start,
      minimumPeriodS: Number(settings.minimum_period_s),
      retryAfter: event.retry_after,
      draftRateLimit: event.ratelimit,
      localBaseS: Number(settings.local_base_s),
      localCapS: Number(settings.local_cap_s),
      herdJitterFraction: Number(settings.herd_jitter_fraction),
      nowDate: new Date(baseDate.getTime() + nowS * 1000),
    });
    event.decision = decision.action;
    event.retry_decision = decision;
    attempts.push(event);

    if (decision.action !== "WAIT_THEN_RETRY") {
      terminal = decision.action;
      break;
    }
    assert(decision.next_start_s != null, "retry missing next start");
    virtualStart = decision.next_start_s;
  }

  const gaps = starts.slice(1).map((value, index) => value - starts[index]);
  const result = {
    scenario_id: scenario.scenario_id,
    classification: "independent_node_loopback_real_http_virtual_time",
    terminal,
    operation_id: operationId,
    attempts,
    start_times_s: starts,
    start_gaps_s: gaps,
    server_requests: server.state.scriptedCounts.get(scenario.scenario_id) ?? 0,
  };

  const expected = scenario.expect;
  assert(result.terminal === expected.terminal, `${scenario.scenario_id}: terminal`);
  assert(result.server_requests === expected.requests, `${scenario.scenario_id}: requests`);
  if (expected.min_second_start_s != null) {
    assert(starts[1] >= Number(expected.min_second_start_s), `${scenario.scenario_id}: Retry-After floor`);
  }
  if (expected.min_start_gap_s != null) {
    assert(Math.min(...gaps) >= Number(expected.min_start_gap_s), `${scenario.scenario_id}: start anchor`);
  }
  if (expected.draft_floor_s != null) {
    assert(
      attempts[0].retry_decision.draft_ratelimit_floor_s === Number(expected.draft_floor_s),
      `${scenario.scenario_id}: draft precedence`,
    );
  }
  result.pass = true;
  return result;
}

async function runUnknown(server, scenario, baseDate) {
  const settings = scenario.client;
  const operationId = scenario.operation_id;
  const first = await requestJson(
    "POST",
    `${server.baseUrl}${scenario.endpoint}`,
    {
      "X-Lab-Operation-Id": operationId,
      "X-Lab-Attempt-Id": `${operationId}:attempt:1`,
    },
    { action: "apply-once" },
  );
  assert(first.status == null, "ambiguous POST unexpectedly returned HTTP status");

  const decision = decide({
    status: null,
    method: "POST",
    operationState: "unknown",
    applicationIdempotencyContract: false,
    attemptNumber: 1,
    retryBudget: Number(settings.retry_budget),
    operationId,
    nowS: 0.05,
    previousStartS: 0,
    minimumPeriodS: Number(settings.minimum_period_s),
    retryAfter: null,
    draftRateLimit: null,
    localBaseS: Number(settings.local_base_s),
    localCapS: Number(settings.local_cap_s),
    herdJitterFraction: Number(settings.herd_jitter_fraction),
    nowDate: new Date(baseDate.getTime() + 50),
  });
  assert(decision.action === "REOBSERVE", "unknown non-idempotent POST must re-observe");

  const observed = await requestJson(
    "GET",
    `${server.baseUrl}/state`,
    {
      "X-Lab-Operation-Id": operationId,
      "X-Lab-Attempt-Id": `${operationId}:observe:1`,
    },
  );
  assert(observed.status === 200, "state re-observation failed");

  const result = {
    scenario_id: scenario.scenario_id,
    classification: "independent_node_ambiguous_non_idempotent",
    transport_error: first.error,
    decision,
    reobserved_state: observed.body,
    post_requests: server.state.ambiguousPostRequests,
    side_effects: server.state.ambiguousEffects,
  };
  assert(result.post_requests === scenario.expect.post_requests, "ambiguous POST count");
  assert(result.side_effects === scenario.expect.side_effects, "ambiguous side effects");
  assert(observed.body.ambiguous_effects === scenario.expect.reobserve_value, "reobserve value");
  result.pass = true;
  return result;
}

async function runExplicitContract(server, scenario, baseDate) {
  const settings = scenario.client;
  const operationId = scenario.operation_id;
  const attempt1 = `${operationId}:attempt:1`;
  const first = await requestJson(
    "POST",
    `${server.baseUrl}${scenario.endpoint}`,
    {
      "X-Lab-Operation-Id": operationId,
      "X-Lab-Attempt-Id": attempt1,
    },
    { action: "apply-once" },
  );
  assert(first.status == null, "first idempotent-contract call should lose response");

  const decision = decide({
    status: null,
    method: "POST",
    operationState: "unknown",
    applicationIdempotencyContract: true,
    attemptNumber: 1,
    retryBudget: Number(settings.retry_budget),
    operationId,
    nowS: 0.05,
    previousStartS: 0,
    minimumPeriodS: Number(settings.minimum_period_s),
    retryAfter: null,
    draftRateLimit: null,
    localBaseS: Number(settings.local_base_s),
    localCapS: Number(settings.local_cap_s),
    herdJitterFraction: Number(settings.herd_jitter_fraction),
    nowDate: new Date(baseDate.getTime() + 50),
  });
  assert(decision.action === "WAIT_THEN_RETRY", "explicit contract should authorize timed retry");

  const attempt2 = `${operationId}:attempt:2`;
  const second = await requestJson(
    "POST",
    `${server.baseUrl}${scenario.endpoint}`,
    {
      "X-Lab-Operation-Id": operationId,
      "X-Lab-Attempt-Id": attempt2,
    },
    { action: "apply-once" },
  );
  assert(second.status === 200, "second explicit-contract POST failed");

  const relevant = server.state.requestLog.filter((row) => row.path === scenario.endpoint);
  const operationIds = relevant.map((row) => row.operation_id);
  const attemptIds = relevant.map((row) => row.attempt_id);
  const result = {
    scenario_id: scenario.scenario_id,
    classification: "independent_node_explicit_application_idempotency",
    first_transport_error: first.error,
    first_decision: decision,
    terminal: "SUCCESS",
    operation_id: operationId,
    attempt_ids: [attempt1, attempt2],
    server_operation_ids: operationIds,
    server_attempt_ids: attemptIds,
    post_requests: server.state.idempotentPostRequests,
    side_effects: server.state.idempotentEffects,
    response: second.body,
  };
  assert(result.post_requests === scenario.expect.post_requests, "explicit POST count");
  assert(result.side_effects === scenario.expect.side_effects, "dedupe side effects");
  assert(new Set(operationIds).size === 1, "operation id changed across attempts");
  assert(new Set(attemptIds).size === 2, "attempt id did not change");
  result.pass = true;
  return result;
}

async function main() {
  const args = parseArgs(process.argv);
  const spec = JSON.parse(fs.readFileSync(args.scenarios, "utf8"));
  if (spec.safety.network_scope !== "loopback_only") {
    throw new Error("refusing scenario file without loopback_only safety");
  }

  const scriptedMap = new Map(spec.scripted.map((row) => [row.scenario_id, row]));
  const baseDate = new Date(spec.base_datetime);
  const results = [];

  const scriptedServer = await startServer(scriptedMap);
  try {
    assert(scriptedServer.baseUrl.startsWith("http://127.0.0.1:"), "non-loopback server");
    for (const scenario of spec.scripted) {
      results.push(await runScripted(scriptedServer, scenario, baseDate));
    }
  } finally {
    await scriptedServer.close();
  }

  for (const scenario of spec.ambiguous) {
    const server = await startServer(scriptedMap);
    try {
      if (scenario.application_idempotency_contract) {
        results.push(await runExplicitContract(server, scenario, baseDate));
      } else {
        results.push(await runUnknown(server, scenario, baseDate));
      }
    } finally {
      await server.close();
    }
  }

  const output = {
    schema: "http-429-node-independent-conformance-report/v1",
    classification: "independent_standard_library_implementation_loopback_only",
    implementation: {
      language: "javascript",
      runtime: "node",
      imports_python_reference: false,
      invokes_python_reference: false,
      third_party_packages: false,
    },
    network_scope: "127.0.0.1 ephemeral local server only",
    results,
    summary: {
      scenarios: results.length,
      passed: results.filter((row) => row.pass).length,
      failed: results.filter((row) => !row.pass).length,
    },
    safety: {
      production_traffic: false,
      rate_limit_evasion: false,
      remote_target_input: false,
    },
  };

  const text = JSON.stringify(output, null, 2) + "\n";
  process.stdout.write(text);
  if (args.output) fs.writeFileSync(args.output, text);
  if (output.summary.failed) process.exitCode = 1;
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
