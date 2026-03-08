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

