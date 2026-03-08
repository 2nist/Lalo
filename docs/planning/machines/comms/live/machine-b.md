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
status: open
request: Wave 4b candidate-generator recall pass. Implement one targeted candidate-generation change to increase boundary candidate recall, rerun pinned heuristic benchmark, and publish delta summary.
artifacts: results/sections-machine-b-wave4b.json, results/machine-b-wave4b-note.md, docs/planning/machines/comms/machine-b.md
notes: Use one scoped change only. Keep `--algorithm heuristic` and runtime defaults unchanged. Include before/after table for F1@0.5s, F1@3.0s, mean predicted boundaries/song, and TP/FP/FN totals.

## MSG-20260308-0602
from: coordinator
to: machine-b
priority: high
status: open
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
	- eta: <estimate>

