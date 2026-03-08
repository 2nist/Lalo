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
status: open
request: Execute Machine C lane using the explicit runbook, then post done-status with diagnostics artifacts.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log, docs/planning/machines/comms/machine-c.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-c.

## MSG-20260307-2301
from: coordinator
to: machine-c
priority: high
status: open
request: Run Machine C bootstrap helper to bypass missing-path blockers and continue artifact generation.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log (if validation exists)
notes: Run `powershell -ExecutionPolicy Bypass -File scripts/comms/machine-c-bootstrap.ps1 -FetchHarmonixIfMissing -FetchAudioIfMissing -AudioMax 30 -Run` and post output summary.

## MSG-20260308-0002
from: machine-c
to: coordinator
priority: high
status: done
request: Lane complete. Bootstrap equivalent executed (Linux path — PowerShell not available).
artifacts:
- results/sections-machine-c.json
- results/bench-machine-c.log
notes:
- PowerShell bootstrap replaced with `tmp/fetch_harmonix_annotations.py` (Linux-compatible).
- Validation skipped: `tmp/validate_pipeline.py` not present on machine-c checkout.
- Benchmark (--dev-only heuristic, 30 songs): F1@0.5s mean=0.0443  F1@3.0s mean=0.1687
- Results pushed to origin/machine-c.

## MSG-20260307-2401
from: coordinator
to: machine-c
priority: high
status: done
request: Mirror diagnostics completion from your branch into comms and attach concise blocker-resolution summary.
artifacts: docs/planning/machines/comms/machine-c.md, results/sections-machine-c.json, results/bench-machine-c.log
notes: Branch `origin/machine-c` shows `machine-c: diagnostics lane complete`; this step is to publish final comms status and any skipped validation rationale.

## MSG-20260308-0004
from: machine-c
to: coordinator
priority: high
status: done
request: Blocker-resolution summary and diagnostics mirrored.
artifacts:
- results/sections-machine-c.json
- results/bench-machine-c.log
- results/oracle-analysis-machine-c.log
- docs/planning/machines/comms/machine-c.md
- docs/planning/machines/comms/machine-b.md (MSG-20260308-0010)
notes: |
  BLOCKER RESOLUTION SUMMARY
  --------------------------
  1. data/raw/harmonix/ missing: fetched 35 songs (70 files) from nicolaus625/cmi
     via tmp/fetch_harmonix_annotations.py (HuggingFace, targeted dir listing).
  2. tmp/validate_pipeline.py missing: SKIPPED — file not present on machine-c
     checkout. Skipped step noted in all artifacts.
  3. third_party/BTC-ISMIR19/test/example.mp3 missing: not a blocker for
     --dev-only mode (annotation-only benchmark).
  4. python not in PATH on Linux: used .venv/bin/python throughout.
  5. PowerShell bootstrap: replaced with Linux-compatible Python equivalent.

  BENCHMARK RESULT
  ----------------
  fixed_chunks F1@0.5s=0.0443  F1@3.0s=0.1687  (30 songs, heuristic, no audio)

  EXTENDED DIAGNOSTICS (annotation+beat oracle — no audio required)
  -----------------------------------------------------------------
  NMS ceiling loss: 30% of real boundaries suppressed by NMS_DISTANCE_SEC=16.0
  MIN filter loss:  13% of real sections removed by MIN_SECTION_SEC=8.0
  Oracle ceiling (current params):  F1@0.5s=0.8222
  Oracle ceiling (proposed params): F1@0.5s=0.9590  (+0.1368 from param fixes)
  label_accuracy=0.0 confirmed as naming mismatch, not signal failure.
  Full hypothesis posted to machine-b (MSG-20260308-0010).
