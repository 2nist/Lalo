# LALO Agent Coordination

This file defines how coding agents should operate in this repo.

## Core Priorities

1. Preserve chord runtime consistency.
2. Make section detector gains benchmark-first.
3. Treat YouTube analysis as diagnostic, not proof.

## Architecture Guardrails

- The app-facing chord boundary is `audioanalysis/btc_runtime/` plus `audioanalysis/chord_pipeline.py`.
- `third_party/` is reference material, not the active architectural surface.
- Reference BTC is the consistency anchor until owned-runtime parity is repeatedly demonstrated.
- Section tuning must stay isolated from chord runtime migration.

## Work Lanes

Choose exactly one lane per task:

1. `runtime-stability`
2. `section-benchmarking`
3. `single-song-diagnostics`
4. `docs-and-tooling`

If the request crosses lanes, split it into separate tasks.

## Required Start-of-Task Declaration

At the start of substantial work, state:

- lane
- target files
- validation command
- files or systems that must not change

Example:

```text
Lane: runtime-stability
Target files: audioanalysis/btc_runtime/runtime.py, tmp/validate_pipeline.py
Validation: python tmp/validate_pipeline.py
Do not change: scripts/analysis/section_detector.py
```

## Runtime Rules

- Do not widen direct imports from `third_party/BTC-ISMIR19`.
- Prefer changes behind `audioanalysis/btc_runtime/`.
- When consistency matters, pin BTC to the reference backend.
- Any owned-runtime change must preserve parity evidence.

## Section Rules

- Benchmark with an explicit detector backend.
- Do not tune on a single YouTube song.
- Log artifacts for any claimed gain.
- Record requested and actual algorithm/backend in outputs when available.

## Diagnostic Rules

- Single-song analysis is for failure classification.
- Report exact audio slug/path, backend, algorithm, and output artifact.
- Convert observations into benchmark hypotheses before changing defaults.

## Coordination Rules For Multiple Machines

- Use one integration branch as the merge target and one worker branch per machine or lane.
- Do not have multiple machines commit directly to the same active branch head.
- Do not let two agents change the same subsystem concurrently unless one is read-only.
- Share exact commands and artifact paths, not paraphrases.
- If a run depends on local models or optional Windows dependencies, say so explicitly.

## Preferred Validation Commands

- Runtime parity: `python tmp/validate_pipeline.py`
- Section benchmark: `python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic`
- Section weight sweep: `python scripts/bench/grid_search_weights.py --max-songs 20`
- Syntax check for edited Python files: `python -m py_compile <files>`

## Default Decision Policy

- If parity is uncertain, prefer the reference BTC backend.
- If benchmark evidence is missing, do not claim a section gain.
- If a task touches both runtime and section scoring, stop and split the work.
