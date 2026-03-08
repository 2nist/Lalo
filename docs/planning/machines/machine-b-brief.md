**Status:** Completed dev-only heuristic benchmark runs on worker branch; installed Conda env and built `madmom` for full detector support.

**Files changed:**
- `scripts/bench/section_benchmark.py` — small improvement: record detector `meta` and whether `candidates` were saved.
- `results/sections-machine-b.madmom.json` — full run with `madmom` available.
- `results/sections-machine-b.conda.json` — earlier conda-assisted run.
- `results/sections-machine-b.full.json` — initial full run attempt (venv, partial).
- `docs/planning/machines/inbox.md` — compatibility questions + import test summary.

**Benchmark command:**
`python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-b.madmom.json`
(run inside Conda env: `conda run -n lalo311 python ...`)

**Artifacts:**
- `results/sections-machine-b.madmom.json` (pushed to `machine-b/worker-wave1`)
- `results/sections-machine-b.conda.json` (pushed)
- `results/sections-machine-b.full.json` (pushed)

**Decision:** inconclusive
- Rationale: detector (heuristic) mean F1@0.5s = 0.0179 (n=16 with audio) vs fixed-chunk baseline mean F1@0.5s = 0.0443 (n=30). On this dev split the heuristic detector did not show an average gain; limited song coverage (16 audio files) and missing prototype module reduce confidence.

**Next step:**
1. Add any missing dataset audio or point the benchmark `--audio-dir` to the correct path so all Harmonix songs have audio available.
2. Re-run full benchmark on the `lalo311` Conda env and compare before/after with consistent `weights` and `algorithm` recorded (I already store `meta` and `weights` in outputs).
3. If you want me to try tuning weights, I can run `scripts/bench/grid_search_weights.py --max-songs 20` next (needs `grid_search_weights.py` present).

If you want, I can now open `results/sections-machine-b.madmom.json` and produce a short table of per-song detector vs fixed scores and highlight the top candidate failures for diagnostic follow-up.
