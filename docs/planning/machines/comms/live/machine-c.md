# Live Channel: Machine C

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-c|copilot
to: machine-c|coordinator|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <paths>
notes: <constraints>
```

## MSG-20260307-2001
from: coordinator
to: machine-c
priority: high
status: done
request: Confirm live-channel polling works, then mirror your status update into docs/planning/machines/comms/machine-c.md.
artifacts: docs/planning/machines/comms/machine-c.md, results/sections-machine-c.json (if produced)
notes: Reply in this file first, then mirror to the main comms file.

## MSG-20260307-2101
from: coordinator
to: machine-c
priority: high
status: done
request: Execute Machine C lane using the explicit runbook, then post done-status with diagnostics artifacts.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log, docs/planning/machines/comms/machine-c.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-c.

## MSG-20260307-2301
from: coordinator
to: machine-c
priority: high
status: done
request: Run Machine C bootstrap helper to bypass missing-path blockers and continue artifact generation.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log (if validation exists)
notes: Run `powershell -ExecutionPolicy Bypass -File scripts/comms/machine-c-bootstrap.ps1 -FetchHarmonixIfMissing -FetchAudioIfMissing -AudioMax 30 -Run` and post output summary.

## MSG-20260307-2401
from: coordinator
to: machine-c
priority: high
status: done
request: Mirror diagnostics completion from your branch into comms and attach concise blocker-resolution summary.
artifacts: docs/planning/machines/comms/machine-c.md, results/sections-machine-c.json, results/bench-machine-c.log
notes: Branch `origin/machine-c` shows `machine-c: diagnostics lane complete`; this step is to publish final comms status and any skipped validation rationale.

## MSG-20260308-0101
from: coordinator
to: machine-c
priority: normal
status: done
request: Run Wave 2 diagnostics-only lane (non-audio-dependent). Summarize top 5 failure patterns from `results/bench-machine-c.log` and map each to a testable benchmark hypothesis for Machine B.
artifacts: results/machine-c-failure-taxonomy.md, docs/planning/machines/comms/machine-c.md
notes: No model/backend/default changes in this lane. This is analysis + hypothesis packaging only.

## MSG-20260308-0201
from: coordinator
to: machine-c
priority: high
status: done
request: Finalize Wave 2 diagnostics handoff by syncing your completion commit into coordination-visible comms and highlighting the top 2 hypotheses Machine B should test first.
artifacts: docs/planning/machines/comms/machine-c.md, docs/planning/machines/comms/live/machine-c.md, results/machine-c-failure-taxonomy.md
notes: Your branch shows completion (`origin/machine-c` latest commit). This step is a sync + prioritization handoff.

## MSG-20260308-0301
from: coordinator
to: machine-c
priority: normal
status: done
request: Stay in support mode. Validate Machine B parser-fix branch once available and confirm whether H2/H3 gains persist after H4 is fixed.
artifacts: docs/planning/machines/comms/machine-c.md
notes: No new modeling work yet; this is verification support for B's parser-first lane.

status: done
summary: Support-mode verification completed on `origin/machine-c` commit `27c7276a`. Machine C validated non-zero reference boundaries and confirmed H2/H3 confidence persistence after Machine B label-tolerance update.

## MSG-20260308-0401
from: coordinator
to: machine-c
priority: normal
status: done
request: Run quick verification against latest Machine B XGBoost artifact and post a short consistency check: non-zero reference boundaries observed and any change in H2/H3 hypothesis confidence.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Keep this as analysis-only validation. Do not retune models or alter defaults.

status: done
summary: Verification posted by Machine C (`MSG-20260308-0402` on branch). Key outcomes: ref=0 count is 0/30 (PASS), XGBoost CV mean F1=0.380 (non-zero), H2 confidence increased, H3 remains medium and supported.

## MSG-20260308-0501
from: coordinator
to: machine-c
priority: normal
status: open
request: Wave 4 verification pass. Validate Machine B H2/H3 tuning output once posted and confirm whether recall improves without breaking boundary sanity.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL with concise rationale and top risk note.
