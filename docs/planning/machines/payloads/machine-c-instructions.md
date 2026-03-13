# Machine C: Diagnostic payload and run instructions

Files provided for Machine C:

- `docs/planning/machines/payloads/machine-c-payload.json` — contains `song_slug`, `audio_relative_path`, `backend`, and `algorithm`.

Purpose: give Machine C an exact song slug and the pinned backend/algorithm to run single-song diagnostics reproducibly.

Exact recommended (PowerShell) commands to follow after cloning `coordination/wave-1` and creating your worker branch:

```powershell
# ensure coordination branch
git fetch origin
git checkout coordination/wave-1
git pull --ff-only origin coordination/wave-1

# create your worker branch
git checkout -b worker/machine-c

# confirm payload
cat docs/planning/machines/payloads/machine-c-payload.json

# Create results dir
mkdir -Force results

# Run the validation (does not change defaults):
python tmp/validate_pipeline.py

# Run the heuristic benchmark (dev-only) to capture sections for the slug
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --output results/sections-machine-c.json

# Commit and push results
git add results/sections-machine-c.json
git commit -m "worker/machine-c: add heuristic diagnostic results for payload song"
git push -u origin HEAD
```

Notes:
- The provided `song_slug` points to `third_party/BTC-ISMIR19/test/example.mp3`. If your machine stores the Harmonix dataset in a different location, update the `audio_relative_path` in the payload or run the benchmark with the correct `--song`/path flag if supported.
- Backend: `reference` (the coordination runner shows owned runtime not implemented). Algorithm: `heuristic` (the pinned detector for benchmarking).

When you push the results, include the artifact path `results/sections-machine-c.json` and the exact commands you ran in the PR description.
