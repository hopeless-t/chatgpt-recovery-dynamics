# Branch Convergence Gate / 長寿命branchの早期収束診断

MIL-002 observed that **Critic Router v1 passed its predeclared three-sample
evaluation**, but RIL-007 exposed a different friction:

```text
fast diagnosis
    ↓
useful implementation
    ↓
main advances elsewhere
    ↓
old branch overlaps current main
    ↓
late reintegration / replacement PR
```

This is not the same problem as diagnosis latency.

## Diagnostic

`scripts/check_branch_convergence.py` compares base and head from their merge
base.

It reports:

- how many commits the base advanced;
- how many commits the head advanced;
- paths changed on the base;
- paths changed on the head;
- the intersection.

Classification:

```text
BASE_NOT_AHEAD
BASE_AHEAD_NO_PATH_OVERLAP
CONVERGENCE_RISK
```

A convergence risk means only:

> the base advanced and both branches touched at least one same path.

It does **not** claim a merge conflict.

## Safe response

If risk is observed:

1. stop extending stale history;
2. inspect the overlapping paths;
3. reconcile with current main;
4. if history is already awkward, prefer rebuilding the validated change set on
   a fresh current-main branch;
5. run the full promotion gates.

Do not force-update merely to make this diagnostic green.

## Why no new workflow?

At the MIL-002 observation checkpoint the repository had:

```text
14 workflows
warning threshold: >16
```

The next tuning therefore reuses the existing Meta Improvement Loop workflow
instead of creating another observer.

Observer footprint is a constraint, not free infrastructure.
