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
artifacts: results/sections-machine-b-wave13a.json, results/sections-machine-b-wave13b.json, results/machine-b-wave13-note.md, results/wave13.run.log, results/wave13_wave13a.log, results/wave13_wave13b.log, docs/planning/machines/comms/machine-b.md
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
summary: Wave 13 runs committed in `7582529`. Results:

- Run A (repro parity, prob=0.50): TP 2, FP 34, FN 126, precision 0.0556, recall 0.0156, avg_pred_per_song 2.25.
- Run B (ablation, prob=0.25): TP 2, FP 33, FN 126, precision 0.0571, recall 0.0156, avg_pred_per_song 2.188.

validations:
- Wave13a reproduces Wave9: false (expected TP=3, FP=29, F1@0.5s approx 0.0383).
- Monotonic FP check (FP_B >= FP_A): false (33 >= 34 -> false).
- Monotonic pred check (pred_B >= pred_A): false (2.188 >= 2.25 -> false).

conclusion: Repro parity not achieved; ablation did not show monotonic threshold behavior. Recommend investigating nondeterminism sources (candidate ordering, beat tracking variability, or feature extraction timing) and then re-running a parity replay with deterministic seeds and full trace of intermediate candidate scores.
