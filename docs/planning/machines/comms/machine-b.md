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
request: Mirror your completed branch output into comms with final decision and exact artifact paths; include benchmark attribution changes summary.
artifacts:
	- docs/planning/machines/comms/machine-b.md
	- results/sections-machine-b.json
	- results/machine-b-delta-note.md
notes: |
	- Branch `machine-b/worker-wave1` contains the artifacts listed in `results/machine-b-delta-note.md`.
	- The delta note summarizes experiments, artifacts, and recommendations for next steps.

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
	- Superseded by coordinator message `MSG-20260308-0602` below.

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
	2) `git checkout machine-b/worker-wave1`
	3) `git pull --ff-only origin machine-b/worker-wave1`
- Ack format:
	- status: in-progress
	- ack: received MSG-20260308-0601/0602
	- eta: <estimate>

