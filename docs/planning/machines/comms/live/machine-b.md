# Live Channel: Machine B

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-b|copilot
to: machine-b|coordinator|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <paths>
notes: <constraints>
```

## MSG-20260307-2101
from: coordinator
to: machine-b
priority: high
status: open
request: Execute Machine B lane using the explicit runbook, then post done-status with benchmark artifacts and decision.
artifacts: results/sections-machine-b.json, results/bench-machine-b.log, docs/planning/machines/comms/machine-b.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-b.

## MSG-20260307-2401
from: coordinator
to: machine-b
priority: high
status: done
request: Mirror your completed branch output into comms with final decision and exact artifact paths; include benchmark attribution changes summary.
artifacts: docs/planning/machines/comms/machine-b.md, results/sections-machine-b.json, results/machine-b-delta-note.md
notes: Your branch already has progress (`origin/machine-b/wave-1` latest commit). This is a finalize-and-report step.

## MSG-20260308-0101
from: coordinator
to: machine-b
priority: high
status: open
request: Run Wave 2 benchmark refinement. Produce one additional benchmark artifact with a clearly documented hypothesis and compare against previous output.
artifacts: results/sections-machine-b-wave2.json, results/machine-b-wave2-note.md, docs/planning/machines/comms/machine-b.md
notes: Keep algorithm pinned to heuristic. Do not change runtime backend defaults.
