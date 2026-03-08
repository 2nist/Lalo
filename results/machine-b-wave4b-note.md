Machine B — Wave 4b candidate-generator recall pass
=================================================

Change implemented (scoped): Lowered `sub_prominence` default in `scripts/analysis/section_detector.py` from 0.4 → 0.3 to increase secondary-peak candidate recall.

Run: dev-only pinned heuristic benchmark
Artifacts: results/sections-machine-b-wave4b.json, results/sections-machine-b.json (baseline)

Before / After summary (detector-level, dev split)

| Metric | Before | After |
|---|---:|---:|
| F1@0.5s (mean) | 0.0179 | 0.0179 |
| F1@3.0s (mean) | 0.0779 | 0.0779 |
| Mean predicted boundaries / audio song | 1.125 | 1.125 |
| TP total (0.5s) | 1 | 1 |
| FP total (0.5s) | 17 | 17 |
| FN total (0.5s) | 127 | 127 |

Notes: The single scoped change did not alter the dev-split benchmark summary metrics. Next recommended action: implement a complementary candidate-generator change (e.g., reduce `prominence` or adjust `min_sec`) or run full-dataset evaluation to verify impact beyond the dev split.
