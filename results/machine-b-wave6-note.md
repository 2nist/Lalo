# Machine B — Wave 6 Delta Note

from: machine-b
to: coordinator
priority: high
status: done
request: Wave 6 NMS-first pass (single scoped change: reduce `NMS_DISTANCE_SEC` 16 -> 8). Ran dev-only pinned heuristic benchmark and recorded results.
artifacts:
  - results/sections-machine-b-wave6.json
  - results/sections-machine-b-wave6.log

| Metric | BASE (sections-machine-b.json) | WAVE6 (sections-machine-b-wave6.json) |
|---|---:|---:|
| Songs evaluated | 30 | 30 |
| Section Detector F1@0.5s (mean) | 0.0179 | 0.0270 |
| Section Detector F1@3.0s (mean) | 0.0779 | 0.1069 |

Notes:
- Implemented a single scoped change in `scripts/analysis/section_detector.py`: `NMS_DISTANCE_SEC` reduced from `16.0` to `8.0` to allow denser boundary retention during NMS.
- Ran dev-only pinned heuristic benchmark under `lalo311` Conda env; results show improved mean F1 (small increase) on dev split.
- Next recommended steps: tune `min_section_sec` and NMS gap together, or run full-dataset evaluation to confirm gains.

Commit: Wave6: reduce NMS_DISTANCE_SEC to 8.0, run dev-only benchmark, add delta note
