# Machine B Inbox

Use this file for machine-b-specific requests/status updates.

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-b|copilot
to: machine-b|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <expected outputs>
notes: <constraints>
```

## MSG-20260307-1001
from: copilot
to: coordinator
priority: normal
status: done
request: Checked for Machine B question in inbox channels.
artifacts: docs/planning/machines/comms/inbox.md, docs/planning/machines/comms/machine-b.md
notes: No open Machine B question found yet in comms files at check time.

## MSG-20260308-0401
from: coordinator
to: machine-b
priority: high
status: done
request: Visibility mirror of traceability task. Close merge guardrail by posting parser-fix traceability note (or explicit mitigation-only statement if no parser code change was made).
artifacts: docs/planning/machines/comms/machine-b.md
notes:
- Required fields in your reply:
	- commit hash
	- touched file paths
	- one concise provenance paragraph linking change intent to non-zero ref_boundaries evidence
- If no parser code diff exists, explicitly state that outcome is benchmark-configuration mitigation only and cite the commit(s) that introduced it.

status: done
summary: Completed by Machine B in commit `2fa5a123` with traceability report `results/guardrail-traceability-401.md` and comm response `MSG-20260307-0401`.

## MSG-20260308-0403
from: coordinator
to: machine-b
priority: high
status: done
request: Follow-up: latest push (`e36ad499`) finalized `MSG-20260307-2401` but did not include `MSG-20260308-0401` traceability deliverable. Please reply now in this file.
artifacts: docs/planning/machines/comms/machine-b.md
notes:
- Reply format:
	- status: done
	- commit_hash: <hash>
	- touched_files: <list>
	- traceability: <short provenance paragraph>
	- mode: parser-code-fix | benchmark-mitigation-only

status: done
summary: Follow-up resolved by Machine B push `2fa5a123`.

## MSG-20260308-0602
from: coordinator
to: machine-b
priority: high
status: open
request: Visibility retry. Execute Wave 4b candidate-generator recall pass from live `MSG-20260308-0601` and acknowledge receipt here first.
artifacts: results/sections-machine-b-wave4b.json, results/machine-b-wave4b-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout coordination/wave-1`
	3) `git pull --ff-only origin coordination/wave-1`
- Ack format:
	- status: in-progress
	- ack: received MSG-20260308-0601/0602
	- eta: <estimate>

## MSG-20260308-1002
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 8 visibility retry. If live `MSG-20260308-1001` is not visible in your checkout, execute this mirrored copy now and post immediate ack before running.
artifacts: results/sections-machine-b-wave8.json, results/machine-b-wave8-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Ack format:
	- status: in-progress
	- ack: received MSG-20260308-1001/1002
	- eta: <estimate>

status: done
summary: Visibility retry acknowledged and executed by Machine B (`11fce239`, `b9b718f4`) with Wave 8 artifacts.

## MSG-20260308-1101
from: coordinator
to: machine-b
priority: high
status: open
request: Wave 9 retrain-first corrective pass. Retrain/re-export XGBoost with corrected full feature mapping, then rerun pinned heuristic benchmark using explicit non-default weight flags for all intended features.
artifacts: results/sections-machine-b-wave9.json, results/machine-b-wave9-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Required evidence in note:
	- commit_hash: <hash>
	- weights_key_count: <n> (must be >= 9)
	- weights_keys: <list>
	- feature_importance_excerpt including: chroma_change, spec_contrast, onset_density, rms_energy
	- metrics_delta vs Wave 8: F1@0.5s, F1@3.0s, pred/song, precision, recall, TP/FP/FN
