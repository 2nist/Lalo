# Live Channel: Machine A

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-a|copilot
to: machine-a|coordinator|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <paths>
notes: <constraints>
```

## MSG-20260307-2101
from: coordinator
to: machine-a
priority: high
status: done
request: Execute Machine A lane using the explicit runbook, then post done-status with artifact paths.
artifacts: results/validate-machine-a.log, docs/planning/machines/comms/machine-a.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-a.

status: done
branch: runtime/btc-reference-pin
backend: reference (owned wrapper delegates/reference parity)
algorithm: n/a (runtime validation lane)
artifacts:
- results/validate-machine-a.log
summary: Validation completed successfully. Direct segment match 40/40 (100.0%). mir_eval root/thirds/triads/sevenths/majmin/mirex all 1.0000.
