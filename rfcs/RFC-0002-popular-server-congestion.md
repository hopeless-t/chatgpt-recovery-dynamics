# RFC-0002: Popular-server congestion control for recovery traffic

- Status: Draft
- Scope: local simulation / design guidance only

## Problem

Let:

~~~text
rho_0 = foreground offered work / nominal capacity
~~~

Recovery adds extra work:

~~~text
rho_eff =
  (foreground work + recovery/retry work)
  / capacity
~~~

When sustained foreground work already reaches capacity, retry policy cannot create missing capacity.

## Request cost

Do not assume one request equals one unit of work.

~~~text
c_i =
    w_request
  + w_bytes  * bytes_i
  + w_cpu    * cpu_i
  + w_db     * db_i
  + w_memory * memory_i
~~~

Weights are deployment-specific and unknown here.

## Queue model

~~~text
Q_(t+1) = max(0, Q_t + A_t - C_t)
~~~

Infinite queues convert overload into latency, memory pressure, stale work, and more retries.

## Control stack

1. client-side duplicate suppression;
2. cheap observe-before-materialize;
3. Retry-After + jitter;
4. bounded queues;
5. early load shedding;
6. foreground protection under saturation;
7. fairness and cost-aware scheduling;
8. optional adaptive concurrency.

## Sampled stress result

At abstract base rho=0.90:

~~~text
naive completion       ~18.54x retry amplification
server-friendly stack  ~ 3.98x retry amplification
~~~

These are local simulation outputs, not OpenAI production telemetry.

## Failure mode at rho >= 1

The safe response becomes wait / degrade / shed reconstructible work, not retry harder.

## Non-goals

- estimating OpenAI capacity;
- identifying production queue structure;
- inferring free-vs-paid traffic share;
- active load testing.
