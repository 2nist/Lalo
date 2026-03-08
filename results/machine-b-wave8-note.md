# Wave 8 Note

- Commit: 93aacbc
- Action: Dev-only heuristic benchmark run (Wave 8 visibility retry)
- Command: `PYTHONPATH=. ./miniconda3/envs/lalo311/bin/python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-b-wave8.json`
- Artifacts produced:
  - results/sections-machine-b-wave8.json
  - results/sections-machine-b-wave8.log
- Summary metrics (detector):
  - F1@0.5s mean = 0.0270 (n=16)
  - F1@3.0s mean = 0.1267 (n=16)
- Notes: Some prototype errors reported in per-song run; overall metrics match recent Wave7 dev numbers.
