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

status: done
branch: integration/machine-a-wave1
integrated commits:
- 0377ec64 (machine-b benchmark attribution + artifact)
- eedbda26 (machine-c diagnostics lane complete)
verification:
- `python -m py_compile scripts/bench/section_benchmark.py`
- JSON parse OK: `results/sections-machine-b.json`, `results/sections-machine-c.json`
summary: Machine A integration lane completed. B/C outputs are integrated into a single review branch without changing detector defaults.
