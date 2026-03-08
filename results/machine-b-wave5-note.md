# Machine B — Wave 5 Delta Note

from: machine-b
to: coordinator
priority: high
status: done
request: Wave 5 candidate-generator pass (single scoped change: lower `prominence` 0.20 → 0.18). Ran dev-only pinned heuristic benchmark and recorded results.
artifacts:
  - results/sections-machine-b-wave5.json
  - results/sections-machine-b-wave5.log

| Metric | BASE (sections-machine-b.json) | WAVE5 (sections-machine-b-wave5.json) |
|---|---:|---:|
| Songs evaluated | 30 | 30 |
| Section Detector F1@0.5s (mean) | 0.0179 | 0.0179 |
| Section Detector F1@3.0s (mean) | 0.0779 | 0.0779 |

Notes:
- Implemented a single scoped change in `scripts/analysis/section_detector.py`: `prominence` default lowered to `0.18` to increase primary peak sensitivity.
- Ran dev-only pinned heuristic benchmark under `lalo311` Conda env; results unchanged on the dev split (no improvement in mean F1).
- Next recommended steps: try a complementary candidate change (reduce `min_sec` or lower `sub_prominence` further), or run a full-dataset evaluation to check for non-dev improvements.

Commit: Wave5: lower prominence default to 0.18, run dev-only benchmark, add delta note
