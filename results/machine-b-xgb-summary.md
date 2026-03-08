# Machine B — XGBoost Follow-through Summary

Files produced
- `results/xgb_feature_importances.json`
- `results/learned_weights_xgb.json`
- `results/section_bench.learned_weights_xgb.json`

Key observations
- Training set: 95 candidate examples, 5 positives (severe class imbalance).
- XGBoost CV (5-fold) reported zero precision/recall/F1 across folds — model unable to generalize with current positives.
- Feature importances concentrated on `flux_peak` and new chroma/onset features; when deriving linear weights for the original 5 signals the result collapsed to `flux_peak=1.0`.

Benchmark comparison (dev split)
- Baseline heuristic (default weights): mean F1@0.5 = 0.0179 (n=16)
- XGBoost-derived linear weights (flux-only): mean F1@0.5 = 0.0179 (n=16)

Short conclusion
- No improvement observed on the dev split. Recommended next experiments:
  1. Increase positive example coverage (widen labeling tolerance to ±3s or aggregate more songs).
  2. Expand candidate recall (lower flux prominence thresholds and/or ensemble detectors).
  3. Retrain XGBoost with balanced sampling / scale_pos_weight and run Optuna hyperparameter tuning.
