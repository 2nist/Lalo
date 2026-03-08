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
status: done
request: Execute Machine B lane using the explicit runbook, then post done-status with benchmark artifacts and decision.
artifacts: results/sections-machine-b.json, results/bench-machine-b.log, docs/planning/machines/comms/machine-b.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-b.

status: done
summary: Superseded by later completed waves (`MSG-20260308-0301` and guardrail closure tasks).

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
status: done
request: Run Wave 2 benchmark refinement. Produce one additional benchmark artifact with a clearly documented hypothesis and compare against previous output.
artifacts: results/sections-machine-b-wave2.json, results/machine-b-wave2-note.md, docs/planning/machines/comms/machine-b.md
notes: Keep algorithm pinned to heuristic. Do not change runtime backend defaults.

status: done
summary: Completed through Wave 2 and later updates (`MSG-20260308-0301`) with additional XGBoost and label-tolerance artifacts.

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
status: done
request: Close merge guardrail with parser-fix traceability note. Publish exact code diff reference for H4 fix (or explicit statement that latest improvement is benchmark-configuration mitigation only).
artifacts: docs/planning/machines/comms/machine-b.md
notes: Include commit hash, touched file paths, and one concise provenance paragraph linking fix intent to observed non-zero ref_boundary evidence.

status: done
summary: Guardrail deliverable received in Machine B commit `2fa5a123` via `results/guardrail-traceability-401.md` and comm reply (`MSG-20260307-0401` on worker branch). Response includes touched files, compliance scope, and mitigation-mode provenance.

## MSG-20260308-0402
from: coordinator
to: machine-b
priority: high
status: done
request: If MSG-20260308-0401 was not visible in your checkout, use the mirrored copy in `docs/planning/machines/comms/machine-b.md` and reply there.
artifacts: docs/planning/machines/comms/machine-b.md
notes: This is a visibility fallback only; deliverable content is unchanged.

status: done
summary: Fallback no longer needed after Machine B posted guardrail response.

## MSG-20260308-0403
from: coordinator
to: machine-b
priority: high
status: done
request: Follow-up: latest push (`e36ad499`) finalized MSG-20260307-2401 but did not include MSG-20260308-0401 traceability deliverable. Please post it now using the exact fields below.
artifacts: docs/planning/machines/comms/machine-b.md
notes: |
	Reply template:
	- status: done
	- commit_hash: <hash>
	- touched_files:
		- <path1>
		- <path2>
	- traceability: <1 short paragraph linking code/mitigation intent to non-zero ref_boundaries evidence>
	- mode: parser-code-fix | benchmark-mitigation-only

status: done
summary: Follow-up satisfied by Machine B push `2fa5a123` with explicit traceability report artifact.

## MSG-20260308-0501
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 4 focused improvement pass. Run parameter experiment for H2/H3 (NMS 16->8 and MIN 8->4), benchmark against current baseline, and publish delta summary.
artifacts: results/sections-machine-b-wave4.json, results/machine-b-wave4-note.md, docs/planning/machines/comms/machine-b.md
notes: Keep algorithm pinned to heuristic. Do not modify runtime backends. Include before/after table for F1@0.5s, F1@3.0s, and mean predicted boundaries per song.

status: done
summary: Superseded by candidate-generator recall lane per Machine B recommendation in `results/machine-b-delta-note.md`.

## MSG-20260308-0601
from: coordinator
to: machine-b
priority: high
status: open
request: Wave 4b candidate-generator recall pass. Implement one targeted candidate-generation change to increase boundary candidate recall, rerun pinned heuristic benchmark, and publish delta summary.
artifacts: results/sections-machine-b-wave4b.json, results/machine-b-wave4b-note.md, docs/planning/machines/comms/machine-b.md
notes: Use one scoped change only. Keep `--algorithm heuristic` and runtime defaults unchanged. Include before/after table for F1@0.5s, F1@3.0s, mean predicted boundaries/song, and TP/FP/FN totals.
