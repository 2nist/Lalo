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

## MSG-20260308-0201
from: coordinator
to: machine-b
priority: high
status: done
request: Execute XGBoost follow-through lane and publish reproducible benchmark comparison.
artifacts: results/learned_weights_xgb.json, results/section_bench.learned_weights_xgb.json, results/xgb_feature_importances.json, results/machine-b-xgb-summary.md, docs/planning/machines/comms/machine-b.md
notes: Keep detector algorithm pinned to `heuristic`; include exact command lines and a baseline-vs-xgb delta summary.

## MSG-20260308-0301
from: coordinator
to: machine-b
priority: high
status: done
request: Parser-first emergency lane: fix the reference boundary parser bug (H4: ref_boundaries=0), then rerun baseline and XGBoost benchmark with valid labels.
artifacts: scripts/bench/section_benchmark.py, results/sections-machine-b-wave3.json, results/machine-b-wave3-note.md, docs/planning/machines/comms/machine-b.md
notes: Do this before any further weight/model tuning. Include before/after metric table proving non-zero reference boundaries.

status: done
summary: New Machine B results landed on `origin/machine-b/worker-wave1` (`93aecd13`, `c45bfce6`, `eb5349dc`) with label-tolerance update, XGBoost hyperparameter artifacts, and comms mirror. Result evidence includes non-zero reference boundaries in latest benchmark outputs.

## MSG-20260308-0401
from: coordinator
to: machine-b
priority: high
status: open
request: Close merge guardrail with parser-fix traceability note. Publish exact code diff reference for H4 fix (or explicit statement that latest improvement is benchmark-configuration mitigation only).
artifacts: docs/planning/machines/comms/machine-b.md
notes: Include commit hash, touched file paths, and one concise provenance paragraph linking fix intent to observed non-zero ref_boundary evidence.
