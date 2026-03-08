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
status: done
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

status: done
summary: Completed by Machine B with Wave 9 artifact and metrics package (`544e62ad`, `63d418be`).

## MSG-20260308-1201
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 10 density-focused pass. Keep Wave 9 9-feature mapping, then run one controlled threshold/selection tuning pass to increase boundary density (pred/song) while preserving precision.
artifacts: results/sections-machine-b-wave10.json, results/machine-b-wave10-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Required metrics vs Wave 9:
	- F1@0.5s, F1@3.0s, pred/song, precision, recall, TP/FP/FN
- Acceptance target:
	- pred/song > 2.0
	- precision >= 0.04
	- F1@0.5s >= 0.0383

status: done
summary: Wave 10 processed with branch artifacts (`03df0ec1`, `517663a8`) and Machine C fail verification (`51918398`).

## MSG-20260308-1301
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 11 threshold-first corrective pass. Keep Wave 9 9-feature weights and run one controlled probability-threshold tuning run, then publish a full benchmark artifact.
artifacts: results/sections-machine-b-wave11.json, results/machine-b-wave11-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Scope:
	- one threshold-focused change (for example: `--prob_threshold 0.25`)
	- keep Wave 9 geometry and 9-feature weights
- Required metrics vs Wave 9:
	- F1@0.5s, F1@3.0s, pred/song, precision, recall, TP/FP/FN
- Acceptance target:
	- pred/song > 2.0
	- precision >= 0.04
	- F1@0.5s >= 0.0383

status: done
summary: Completed by Machine B in `32f94781` and verified FAIL by Machine C (`9e9d1b2c`): threshold run at 0.25 reduced quality vs Wave 9 (TP 3 -> 1, precision 0.0938 -> 0.0222, F1@0.5s 0.0383 -> 0.0116).

## MSG-20260308-1401
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 12 parity-locked ablation pass. Re-run with Wave 9 geometry fixed, then perform one threshold-only ablation to isolate threshold effect without geometry drift.
artifacts: results/sections-machine-b-wave12a.json, results/sections-machine-b-wave12b.json, results/machine-b-wave12-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Config lock (both runs):
	- keep Wave 9 9-feature weights
	- `nms_gap=8.0`
	- `min_section=4.0`
	- `beat_snap=2.0`
- Run A (parity replay): `prob_threshold=0.50`
- Run B (ablation): `prob_threshold=0.25` (only change)
- Required metrics table for A and B vs Wave 9: F1@0.5s, F1@3.0s, pred/song, precision, recall, TP/FP/FN.

status: done
summary: Completed by Machine B (`85b3e1a5`) and reviewed by Machine C (`7e76cc45`). Verdict: FAIL + DATA INTEGRITY warning due to non-reproducible parity and non-monotonic threshold behavior.

## MSG-20260308-1501
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 13 reproducibility-first pass. Reproduce Wave 9 parity exactly, then run one threshold-only ablation with full trace logs and monotonicity checks.
artifacts: results/sections-machine-b-wave13a.json, results/sections-machine-b-wave13b.json, results/machine-b-wave13-note.md, results/wave13a.log, results/wave13b.log, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Required lock for both runs:
	- Wave 9 9-feature weights exactly
	- `nms_gap=8.0`
	- `min_section=4.0`
	- `beat_snap=2.0`
	- same dev song set as Wave 9
- Run A (repro parity): `prob_threshold=0.50`
- Run B (ablation): `prob_threshold=0.25` (only change)
- Required validations in note:
	1) Wave13a reproduces Wave 9 baseline (target TP=3, FP=29, F1@0.5s=0.0383; explain any mismatch)
	2) Monotonic threshold behavior check: FP_B >= FP_A and pred/song_B >= pred/song_A
	3) Include `benchmark_date`, active weight keys/count, and explicit command lines for both runs

status: done
summary: Completed by Machine B (`75825299`, `00bcfdc0`) and verified FAIL by Machine C (`fd3e551b`) with root-cause diagnosis pointing to inverted threshold filtering.

## MSG-20260308-1601
from: coordinator
to: machine-b
priority: high
status: open
request: Wave 14 threshold-direction fix + confirmation reruns. Apply one code fix for `--prob_threshold` direction, then rerun parity/ablation checks with logs.
artifacts: scripts/pipeline/section_detector.py, results/sections-machine-b-wave14a.json, results/sections-machine-b-wave14b.json, results/sections-machine-b-wave14c.json, results/machine-b-wave14-note.md, results/wave14a.log, results/wave14b.log, results/wave14c.log, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Single code fix scope:
	- threshold filter must keep candidates with `score >= prob_threshold`
	- no geometry/model tuning in this wave
- Locked config for all runs:
	- Wave 9 weights, `nms_gap=8.0`, `min_section=4.0`, `beat_snap=2.0`, same dev set
- Run A: `prob_threshold=0.50`
- Run B: `prob_threshold=0.25`
- Run C: `prob_threshold=0.15`
- Required validations in note:
	1) Wave14a parity target vs Wave 9 (TP=3, FP=29, F1@0.5s=0.0383) with explanation for any mismatch
	2) Monotonic checks: FP_C >= FP_B >= FP_A and pred/song_C >= pred/song_B >= pred/song_A
	3) Include explicit command lines, benchmark timestamp, and active weight keys/count

## MSG-20260308-1701
from: coordinator
to: machine-b
priority: high
status: open
request: Single-machine mode enabled. Run Wave 14+ end-to-end on Machine B only (implementation + benchmark + self-verification) and post one consolidated report per wave.
artifacts: results/sections-machine-b-wave14*.json, results/machine-b-wave14-note.md, results/wave14*.log, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) `git fetch origin`
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Temporary mode:
	- no cross-machine dependency
	- include code diff summary + exact commands + metric table + self-check assertions in one note
	- raise blocker immediately if parity or monotonic checks fail

## MSG-20260308-1801
from: coordinator
to: machine-b
priority: high
status: open
request: Autonomous improvement mode authorized. Execute iterative micro-cycles without waiting for coordinator between cycles, while staying within strict guardrails.
artifacts: results/sections-machine-b-wave*.json, results/machine-b-wave*-note.md, results/wave*.log, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
	1) git fetch origin
	2) git checkout machine-b/worker-wave1
	3) git pull --ff-only origin machine-b/worker-wave1
- Operating loop each cycle:
	1) one hypothesis
	2) one scoped change
	3) run benchmark
	4) run self-checks
	5) post cycle report
- Hard guardrails:
	- heuristic pinned
	- same dataset/split
	- Wave 9 geometry unless explicitly testing geometry
	- exact commands + active params logged
	- no multi-change bundles
- Quality gates:
	- F1@0.5s >= 0.0383
	- precision >= 0.04
	- pred/song > 2.0
	- monotonic threshold checks when threshold changes
- Stop conditions:
	- two consecutive no-improvement cycles on F1@0.5s
	- unexplained contradictory/non-monotonic behavior
	- suspected parameter/code-path mismatch
