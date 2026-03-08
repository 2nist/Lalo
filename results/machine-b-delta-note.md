Machine B delta note
====================

Summary of changes pushed in branch machine-b/worker-wave1:

- Ran dev-only heuristic benchmark and produced: results/sections-machine-b.json
- Added per-song error analysis: results/false_pos_neg_per_song.csv
- Trained supervised logistic weights: results/learned_weights.json and benchmarked: results/section_bench.learned_weights.json
- Extended detector with richer candidate features and produced: results/sections-machine-b.richer.json
- Trained XGBoost (label-tol=0.5 and label-tol=3.0), saved importances and learned weights:
  - results/xgb_feature_importances.json
  - results/learned_weights_xgb.json
  - results/learned_weights_xgb_hyperparam.json
  - results/xgb_hyperparam_results.json
- Benchmarks from XGBoost-derived weights:
  - results/section_bench.learned_weights_xgb.json
  - results/section_bench.best_weights.json
  - results/sections-machine-b-wave2.json

Notes on attribution and changes:
- Most learned-weight experiments collapsed to `flux_peak` as the dominant feature. This aligns with earlier feature-importance outputs.
- The training set was small and imbalanced; widening labeling tolerance to ±3.0s increased positives (95 examples → 34 positives) and enabled meaningful CV during hyperparameter search.
- Recommendation: improve the candidate generator to increase recall before further model tuning; run full-dataset evaluation after that.

Branch: machine-b/worker-wave1
