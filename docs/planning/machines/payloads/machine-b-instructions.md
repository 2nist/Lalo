# Machine B: Benchmark payload and run instructions

Files provided for Machine B:

- `docs/planning/machines/payloads/machine-b-payload.json` — contains `song_slug`, `audio_relative_path`, `backend`, `algorithm`, benchmark command, and artifact targets.

Purpose: give Machine B exact benchmark settings and artifact outputs so section benchmarking is reproducible across machines.

Exact recommended (PowerShell) commands to follow after cloning `coordination/wave-1` and creating your worker branch:

```powershell
# ensure coordination branch
git fetch origin
git checkout coordination/wave-1
git pull --ff-only origin coordination/wave-1

# create your worker branch
git checkout -b worker/machine-b

# confirm payload
cat docs/planning/machines/payloads/machine-b-payload.json

# create artifact directory
mkdir -Force results

# run pinned heuristic benchmark and capture log
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-b.json *> results/bench-machine-b.log

# commit and push benchmark artifacts
git add results/sections-machine-b.json results/bench-machine-b.log
git commit -m "worker/machine-b: add heuristic benchmark artifacts"
git push -u origin HEAD
```

Notes:
- `algorithm` is pinned to `heuristic` for this lane.
- Backend in payload is `reference` as the active consistency anchor for runtime behavior on coordination runner.
- The payload includes a sample `song_slug` path (`third_party/BTC-ISMIR19/test/example.mp3`) for reproducible local diagnostics if needed.

When Machine B reports back, include:
- exact benchmark command used,
- artifact paths,
- summary metrics from `results/sections-machine-b.json`,
- decision: gain | neutral | regression | inconclusive.
