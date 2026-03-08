# Machine B — Wave 7 Delta Note

from: machine-b
to: coordinator
priority: high
status: done
request: Wave 7 H3 pass — set `MIN_SECTION_SEC` 8 -> 4 and fix feature-weight CLI alignment. Ran dev-only pinned heuristic benchmark and recorded results.
artifacts:
  - results/sections-machine-b-wave7.json
  - results/sections-machine-b-wave7.log

| Metric | BASE (Wave6) | WAVE7 |
|---|---:|---:|
| Section Detector F1@0.5s (mean) | 0.0270 | 0.0270 |
| Section Detector F1@3.0s (mean) | 0.1069 | 0.1267 |

Notes:
- Implemented two changes together:
  1. `MIN_SECTION_SEC` reduced from 8.0 -> 4.0 (H3 change).
  2. Exposed CLI weights for `chroma_change`, `spec_contrast`, `onset_density`, and `rms_energy` and included them in the `weights` mapping so learned/hand-set weights are applied correctly.
- Ran dev-only heuristic benchmark under `lalo311` Conda env; results show increased F1@3.0s mean.
- Commit: pending (will be recorded when changes are committed and pushed).

Recommendation: re-run XGBoost / weight-learning with the expanded candidate set and weight alignment; tune `min_section_sec` together with NMS gap for further gains.
