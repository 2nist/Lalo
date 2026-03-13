# First Prompts For Active Machines

Use these as the first pasted prompt in each machine after cloning `coordination/wave-1` and creating the machine branch.

## Quick Start (exact commands)

Follow these PowerShell commands on each worker machine. Replace <machine-id> with your machine identifier (e.g. machine-a) and run from the repo root.

- If you do NOT yet have a clone, clone the repo (replace origin URL if needed):

```powershell
git clone https://github.com/2nist/Lalo.git
cd Lalo
```

- Fetch and switch to the coordination branch, then create a worker branch:

```powershell
git fetch origin
git checkout coordination/wave-1
git pull --ff-only origin coordination/wave-1
git checkout -b worker/<machine-id>
```

- Prepare Python environment (Python 3.8+). If you already have an environment, activate it instead.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt || pip install numpy scipy librosa madmom msaf
```

- Run the pinned benchmark (heuristic) and write results to `results/`:

```powershell
mkdir -Force results
python scripts/bench/section_benchmark.py --algorithm heuristic --output results/sections-<machine-id>.json
```

- Inspect results and create a brief worker commit with artifacts and notes:

```powershell
git add results/sections-<machine-id>.json
git commit -m "worker/<machine-id>: add heuristic benchmark results"
git push -u origin HEAD
```

- In your PR or report, include the exact command you ran and the artifact path `results/sections-<machine-id>.json`.

Notes/assumptions:
- This set of commands assumes the Harmonix dataset is available on the machine at the same relative paths used by the benchmark. If datasets are stored elsewhere, set the appropriate environment variables or run the benchmark with dataset path flags.
- If `requirements.txt` is missing in the repo, install the packages manually as shown.


## Machine A

Branch:

`runtime/btc-reference-pin`

Paste this prompt:

```text
You are Machine A in the LALO repo.

Lane: runtime-stability
Target branch: runtime/btc-reference-pin
Target files: audioanalysis/btc_runtime/, audioanalysis/chord_pipeline.py, tmp/validate_pipeline.py
Validation: python tmp/validate_pipeline.py
Do not change: scripts/analysis/section_detector.py, scripts/bench/section_benchmark.py, detector weights, detector defaults
Artifacts: parity notes, backend used, runtime health notes if relevant

Tasks:
1. Read .github/AGENTS.md and docs/planning/machines/machine-a-runtime.md.
2. Inspect the current BTC runtime selector and determine whether reference BTC is effectively the active consistency anchor.
3. Check whether there is already a simple way to pin the backend to reference globally or per call.
4. If the path is ambiguous, propose or implement the smallest safe hardening change behind audioanalysis/btc_runtime/.
5. Do not touch section detection code.

Close with this format:
Status:
Files changed:
Validation run:
Backend behavior:
Risks:
Next step:
```

## Machine B

Branch:

`sections/heuristic-weight-sweep`

Paste this prompt:

```text
You are Machine B in the LALO repo.

Lane: section-benchmarking
Target branch: sections/heuristic-weight-sweep
Target files: scripts/analysis/section_detector.py, scripts/bench/section_benchmark.py, scripts/bench/grid_search_weights.py
Validation: python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic
Do not change: audioanalysis/chord_pipeline.py, audioanalysis/btc_runtime/, BTC backend defaults
Artifacts: benchmark output JSON, candidate logs if used, short before/after delta note

Tasks:
1. Read .github/AGENTS.md and docs/planning/machines/machine-b-sections.md.
2. Confirm the benchmark path is pinned to the heuristic detector and not drifting between backends.
3. Inspect whether the benchmark output is recording enough metadata to compare runs cleanly across machines.
4. If there is a missing low-risk improvement to benchmark attribution or benchmark discipline, implement that first.
5. Do not optimize on a single YouTube song.

Close with this format:
Status:
Files changed:
Benchmark command:
Artifacts:
Decision: gain | neutral | regression | inconclusive
Next step:
```

## Machine C

Branch:

`diagnostics/youtube-failure-catalog`

Paste this prompt:

```text
You are Machine C in the LALO repo.

Lane: single-song-diagnostics
Target branch: diagnostics/youtube-failure-catalog
Target files: diagnostic notes and tooling only; do not change detector defaults or BTC runtime code
Validation: produce a reproducible diagnostic note with exact song slug/path, backend, algorithm, and artifact paths
Do not change: scripts/analysis/section_detector.py defaults, scripts/bench/section_benchmark.py thresholds, audioanalysis/btc_runtime/
Artifacts: candidate log path, sections JSON path, concise repro note, recommendation for benchmark lane

Tasks:
1. Read .github/AGENTS.md and docs/planning/machines/machine-c-diagnostics.md.
2. Review the current single-song analysis path and identify what exact metadata is already captured and what is missing for reproducible diagnosis.
3. If needed, implement only note-taking or diagnostic-output improvements that do not affect benchmark or runtime defaults.
4. Convert one-song observations into benchmark hypotheses, not tuning decisions.

Close with this format:
Song:
Backend:
Algorithm:
Artifacts:
Failure mode:
Recommendation:
```

## Shared Rule

No machine should commit directly to `coordination/wave-1`.

Each machine works only on its own worker branch and hands results back with exact commands and artifact paths.
