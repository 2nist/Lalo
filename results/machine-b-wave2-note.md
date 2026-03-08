**Machine B — Wave 2 benchmark refinement**

Hypothesis
- XGBoost-derived importances indicate flux-dominant boundaries; running the heuristic detector with XGBoost-derived linear weights (`flux=1.0`, others=0) will change boundary selection and may improve precision on flux-driven candidates.

Commands run
- Wave 2 benchmark (XGB-derived linear weights):
  - `PYTHONPATH=. ./miniconda3/envs/lalo311/bin/python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --weight-flux 1.0 --weight-chord 0 --weight-cadence 0 --weight-repetition 0 --weight-duration 0 --out results/sections-machine-b-wave2.json`

Outcome summary
- Baseline heuristic (default weights) mean F1@0.5: 0.0179 (n=16)
- XGB-derived linear weights (flux-only) mean F1@0.5: 0.0179 (n=16)

Interpretation
- No measurable improvement on the dev split. This aligns with small positive example count and XGBoost CV showing zero F1 in folds (class imbalance). Next steps: increase positive examples and expand candidate recall before retraining.
