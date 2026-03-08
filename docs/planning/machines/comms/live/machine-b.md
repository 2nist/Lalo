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

## MSG-20260307-2403
from: coordinator
to: machine-b
priority: high
status: done
request: Mirror your completed branch output into comms with final decision and exact artifact paths; include benchmark attribution changes summary.
artifacts:
	- docs/planning/machines/comms/machine-b.md
	- results/sections-machine-b.json
	- results/machine-b-delta-note.md
notes: |
	- Branch `machine-b/worker-wave1` contains the artifacts listed in `results/machine-b-delta-note.md`.
	- See the delta note for a short attribution summary and recommended next steps (improve candidate generator, then full-dataset eval).

## MSG-20260308-0901
from: machine-b
to: coordinator
priority: high
status: done
request: Wave 6 NMS-first pass completed (single scoped change: NMS_DISTANCE_SEC 16 -> 8). Posting delta artifacts and metrics.
artifacts:
	- results/sections-machine-b-wave6.json
	- results/machine-b-wave6-note.md
notes: |
	- Commit: e95937e
	- Metrics delta (detector): F1@0.5s mean 0.0179 -> 0.0270, F1@3.0s mean 0.0779 -> 0.1069
	- Full results: results/sections-machine-b-wave6.full.json
	- Recommendation: tune `min_section_sec` and NMS gap jointly, or run targeted per-song analysis for best candidates.

## MSG-20260308-1001
from: machine-b
to: coordinator
priority: high
status: done
request: Re-run XGBoost weight learning for Wave 7 (H3) and post artifacts.
artifacts:
	- results/section_bench.learned_weights_xgb.json
	- results/train_xgb.wave7.labeltol3.log
notes: |
	- Commit: e1f156c
	- Training: label tolerance = 3.0s; Examples=179, Positives=60
	- CV fold F1 scores: approx [0.22, 0.26, 0.31, 0.20, 0.50]
	- Learned linear weights (from XGBoost importances): {'flux_peak': 0.2995, 'repetition_break': 0.7005, 'others': 0.0}
	- Resulting benchmark with learned weights: F1@0.5 mean = 0.0227, F1@3.0 mean = 0.1007
	- Files: results/section_bench.learned_weights_xgb.json, results/train_xgb.wave7.labeltol3.log

## MSG-20260307-2130
from: machine-b
to: coordinator
priority: high
status: done
request: Completed dev-only heuristic benchmark and posted artifacts; reporting final decision and artifacts list.
artifacts: results/sections-machine-b.json, results/bench-machine-b.log, results/learned_weights.json, results/section_bench.learned_weights.json, results/false_pos_neg_per_song.csv
notes: Branch `machine-b/worker-wave1` ran the dev-only heuristic benchmark in Conda env (`lalo311`). Added per-song analyzer and learned weights for follow-up experiments. Decision: inconclusive (see summary).

status: done
branch: machine-b/worker-wave1
backend: reference
algorithm: heuristic
artifacts:
- results/sections-machine-b.json
- results/bench-machine-b.log
- results/learned_weights.json
- results/section_bench.learned_weights.json
- results/false_pos_neg_per_song.csv
summary: Ran dev-only heuristic benchmark in `lalo311` Conda env. Section Detector mean F1@0.5 = 0.0179 (n=16 audio); Fixed 32s baseline F1@0.5 = 0.0443 (n=30). Added per-song error analysis and a supervised learned-weights experiment; no clear gain on dev split — decision: inconclusive.


## MSG-20260308-0301
from: machine-b
to: coordinator
priority: high
status: done
request: Post XGBoost hyperparameter search results, learned weights, benchmarks, and logs for Wave 2 experiments.
artifacts:
	- results/xgb_hyperparam_results.json
	- results/learned_weights_xgb_hyperparam.json
	- results/section_bench.best_weights.json
	- results/xgb_feature_importances.json
	- results/learned_weights_xgb.json
	- results/section_bench.learned_weights_xgb.json
	- results/train_xgb.labeltol3.log
	- results/hyperparam_xgb.labeltol3.log
	- results/sections-machine-b-wave2.json
	- results/machine-b-wave2-note.md
	- results/machine-b-xgb-summary.md
notes: |
	- Training label tolerance widened to ±3.0s to increase positive examples (95 examples, 34 positives).
	- GridSearchCV (5-fold) over XGBoost params found best: {"n_estimators":50, "max_depth":3, "learning_rate":0.1}, best CV F1 ≈ 0.4505.
	- Derived linear weights collapsed to flux-only for original signals (flux_peak=1.0).
	- Benchmark outputs show limited gains on dev split; next recommended actions: improve candidate generator (increase recall) and run full-dataset evaluation.
	- Branch: machine-b/worker-wave1


## MSG-20260307-0401
from: machine-b
to: coordinator
priority: normal
status: done
request: Guardrail traceability Task 401 — post traceability report and confirm compliance.
artifacts:
	- results/guardrail-traceability-401.md
notes: |
	- Guardrail traceability report added to `results/guardrail-traceability-401.md`.
	- Scope: bench scripts and comms updates only; no runtime or third_party edits were made.


## MSG-******-0601
from: machine-b
to: coordinator
priority: normal
status: done
request: Placeholder entry from local agent.
artifacts:
	- none
notes: |
	- Superseded by coordinator messages `MSG-20260308-0601` and `MSG-20260308-0602` below.

## MSG-20260308-0601
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 4b candidate-generator recall pass completed (single scoped change: lower `sub_prominence` 0.4 → 0.3). See delta summary and artifacts.
artifacts:
	- results/sections-machine-b-wave4b.json
	- results/machine-b-wave4b-note.md
	- docs/planning/machines/comms/machine-b.md
notes: |
	- Implemented one scoped change to `scripts/analysis/section_detector.py` (sub_prominence=0.3).
	- Ran dev-only pinned heuristic benchmark; before/after metrics unchanged on dev split. See `results/machine-b-wave4b-note.md` for table.

## MSG-20260308-0602
from: coordinator
to: machine-b
priority: high
status: in-progress
request: Visibility retry for Wave 4b. If this is the first message you can see, execute `MSG-20260308-0601` and post an `ack` reply before running.
artifacts: docs/planning/machines/comms/machine-b.md, results/sections-machine-b-wave4b.json, results/machine-b-wave4b-note.md
notes: |
	Pull steps first:
	1) git fetch origin
	2) git checkout machine-b/worker-wave1
	3) git pull --ff-only origin machine-b/worker-wave1
	Reply format now:
	- status: in-progress
	- ack: received MSG-20260308-0601/0602
	- eta: 2h

ack: received MSG-20260308-0601/0602
eta: 2h

## MSG-20260308-0702
from: coordinator
to: machine-b
priority: high
status: open
request: Canonical active instruction (branch-local). Execute Wave 5 alignment-first pass now: fix feature-weight alignment so informative XGBoost features are preserved (not collapsed to `flux_peak`), rerun pinned heuristic benchmark, and post delta summary.
artifacts: results/sections-machine-b-wave5.json, results/machine-b-wave5-note.md, docs/planning/machines/comms/machine-b.md
notes: |
	Treat this as the current source-of-truth task even if older messages conflict.
	Required reply block:
		- status: in-progress|done
		- commit_hash: <hash>
		- nonzero_weights_before: <n>
		- nonzero_weights_after: <n>
		- metrics_delta: <F1@0.5s, F1@3.0s, pred/song, TP/FP/FN>

## MSG-20260308-1200
from: coordinator
to: machine-b
priority: high
status: open
request: Execute Wave 5 candidate-generator pass (follow-up to Wave 4b). Implement a single scoped candidate-generator change, run the dev-only pinned benchmark, and post delta artifacts.
artifacts:
	- results/sections-machine-b-wave5.json
	- results/machine-b-wave5-note.md
notes: |
	- Scope: one targeted change to `scripts/analysis/section_detector.py` to increase candidate recall (change TBD), then run `scripts/bench/section_benchmark.py --dev-only --algorithm heuristic` and publish results.
	- Pull and ack before running (see MSG-20260308-0602 for pull steps).

## MSG-20260308-0801
from: coordinator
to: machine-b
priority: high
status: open
request: Canonical active instruction (branch-local). Wave 6 NMS-first pass: reduce NMS_DISTANCE_SEC from 16 -> 8, rerun pinned heuristic benchmark, and publish full delta summary.
artifacts: results/sections-machine-b-wave6.json, results/machine-b-wave6-note.md, docs/planning/machines/comms/machine-b.md
notes: |
	This replaces prior Wave 5 alignment-first instruction as top priority.
	Required reply block:
	- status: in-progress|done
	- commit_hash: <hash>
	- metrics_delta: <F1@0.5s, F1@3.0s, pred/song, TP/FP/FN, precision, recall>


## MSG-20260308-1002
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 8 visibility retry. Executed mirrored copy and posted results.
artifacts: results/sections-machine-b-wave8.json, results/machine-b-wave8-note.md, docs/planning/machines/comms/machine-b.md
notes:
- Pull first:
1) git fetch origin
2) git checkout machine-b/worker-wave1
3) git pull --ff-only origin machine-b/worker-wave1
- Ack format:
- status: done
- ack: received MSG-20260308-1001/1002
- eta: 1h

commit_hash: 11fce23
metrics_delta: |
	- F1@0.5s mean: 0.0270 (n=16)
	- F1@3.0s mean: 0.1267 (n=16)
artifacts_generated:
	- results/sections-machine-b-wave8.json
	- results/machine-b-wave8-note.md

## MSG-20260308-1101
from: coordinator
to: machine-b
priority: high
status: done
request: Wave 9 retrain-first corrective pass completed (see artifacts and note).
artifacts: results/sections-machine-b-wave9.json, results/machine-b-wave9-note.md, docs/planning/machines/comms/machine-b.md
notes: |
	- commit_hash: 94124ab
	- weights_key_count: 9
	- weights_keys: ["flux_peak", "chord_novelty", "cadence_score", "repetition_break", "duration_prior", "chroma_change", "spec_contrast", "onset_density", "rms_energy"]
	- feature_importance_excerpt:
		- chroma_change: 0.12096718698740005
		- spec_contrast: 0.14654359221458435
		- onset_density: 0.1488496959209442
		- rms_energy: 0.22271274030208588
	- Metrics (dev-only) delta vs Wave 8:
		- F1@0.5s: 0.0270 -> 0.0383 (+0.0113)
		- F1@3.0s: 0.1267 -> 0.1338 (+0.0071)
	- Aggregated detector totals (0.5s tolerance): TP=3, FP=29, FN=125, precision=0.0938, recall=0.0234, avg_pred_per_song=2.0 (n_audio=16). Full per-song details are in `results/machine-b-wave9-note.json` and `results/sections-machine-b-wave9.json`.

