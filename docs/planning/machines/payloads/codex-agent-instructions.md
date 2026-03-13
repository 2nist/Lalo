# Codex Agent: Section Benchmark Run Instructions

Purpose: Provide exact, minimal instructions a Codex-style agent should follow to run SALAMI section benchmarks, produce reproducible artifacts, and run a delta comparison.

Prerequisites
- Activate the project's Python environment (example PowerShell):

  ```powershell
  & ".\.venv\Scripts\Activate.ps1"
  ```

- Ensure the SALAMI annotations and audio are available under `datasets/mcgill/mcgill_jcrd_salami_Billboard` and `data/salami_audio` respectively.

Exact run steps (power user-friendly)

1. Create results directory:

```powershell
mkdir -Force results
```

2. Run the baseline/pinned heuristic benchmark (example artifact name):

```powershell
python scripts/bench/salami_benchmark.py --algorithm heuristic --out results/sections-machine-b.json
```

3. Run the promoted/experiment benchmark (example):

```powershell
python scripts/bench/salami_benchmark.py --algorithm heuristic --out results/sections-machine-b-promote-wave15-full.json
```

4. Generate a per-song delta CSV comparing the two runs:

```powershell
python scripts/tools/compare_section_runs.py --old results/sections-machine-b.json --new results/sections-machine-b-promote-wave15-full.json --out results/per_song_delta.csv
```

What to record in the artifact/PR
- `results/sections-machine-b.json` (baseline run)
- `results/sections-machine-b-promote-wave15-full.json` (new/experiment run)
- `results/per_song_delta.csv` (comparison)
- Any detector candidate outputs if available (detector `meta`/`candidates` fields are included in the JSONs)
- The exact commands used (copy/paste the commands above)

Quick checks a Codex agent should perform before finishing
- Confirm `summary.detector.F1@3.0s.mean` and `summary.detector.F1@0.5s.mean` are present and sensible.
- Confirm `summary.fixed_chunks` remains unchanged (sanity check) and report if detector `n` differs from fixed-chunk `n`.
- Flag runs where `pred_sections` is consistently much larger than `ref_boundaries` (over-segmentation) — pick threshold e.g., `pred_sections/ref_boundaries > 3` on more than 30% of songs.

Optional: quick post-process to reduce false positives
- A simple merge of predictions within 0.5–1.0s can reduce FP at strict tolerance. Implement as a post-processing step in `scripts/tools` if desired and re-run the benchmark to measure effect.

Commit & push
- Add artifacts and a short PR description listing commands, key metrics, and a decision (gain|neutral|regression|inconclusive).

Maintainer note
- Keep instructions minimal and deterministic — prefer explicit `--out` filenames and commit artifacts to the worker branch for traceability.
