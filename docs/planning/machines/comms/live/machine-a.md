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

## MSG-20260307-2401
from: coordinator
to: machine-a
priority: high
status: done
request: Run integration support lane: verify and merge Machine B + C outputs into a clean integration branch, then post consolidated quality summary.
artifacts: integration summary note, merge/cherry-pick commit refs, updated outbox status
notes: This lane should avoid changing detector defaults; focus on integrating validated artifacts and reporting risks.

## MSG-20260308-0101
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 2 integration gate. Build a merge-readiness checklist and verify that integrated B/C outputs have no obvious regressions before merge to coordination/main.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Focus on integration quality gate and risk notes; do not retune detector defaults.

status: done
summary: Integration gate completed with conditional-pass. B artifact is structurally valid and benchmark-pinned; C artifact lacks `summary.detector` and needs one follow-up output or explicit diagnostics-only acceptance before full close.

## MSG-20260308-0201
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 2b integration review: evaluate new Machine B XGBoost artifacts together with Machine C failure taxonomy handoff, then publish merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Decide one of: merge-now | merge-with-guardrail | hold-for-more-data. Include rationale and risk list.

## MSG-20260308-0301
from: coordinator
to: machine-a
priority: high
status: open
request: Own Wave 3 integration gate tracking. Track Machine B parser-fix lane completion and prepare final merge recommendation once B publishes non-zero-boundary metrics.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Gate remains conditional until parser-fix evidence lands.
