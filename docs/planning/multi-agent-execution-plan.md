# Multi-Agent Execution Plan

## Purpose

This repo can support multiple agents working in parallel, but only if they do not optimize against different targets.

The coordination rule is:

- chord runtime stability first
- benchmarked section gains second
- YouTube analysis last and only as smoke-test feedback

The goal is not maximum parallelism. The goal is low-regression parallelism.

## Shared Operating Model

Every agent works in one of four lanes:

1. `runtime-stability`
2. `section-benchmarking`
3. `single-song-diagnostics`
4. `docs-and-tooling`

Each lane has a different success criterion.

### Lane 1: runtime-stability

Scope:

- `audioanalysis/btc_runtime/`
- `audioanalysis/chord_pipeline.py`
- `tmp/validate_pipeline.py`
- setup and health checks for BTC and beat dependencies

Success means:

- no regression in reference BTC output parity
- no widening of the app-facing chord contract
- no mixing of runtime migration and section scoring changes in one task

### Lane 2: section-benchmarking

Scope:

- `scripts/analysis/section_detector.py`
- `scripts/bench/section_benchmark.py`
- `scripts/bench/grid_search_weights.py`
- detector-related API wiring only when required

Success means:

- benchmark improves or remains neutral on the pinned backend
- detector output clearly records which backend/algorithm was requested and used
- changes are explainable from candidate logs or benchmark deltas

### Lane 3: single-song-diagnostics

Scope:

- YouTube or local-song analysis review
- candidate log inspection
- audio health inspection
- failure classification for one song

Success means:

- produces diagnosis, not a tuning decision by itself
- outputs reproducible notes with exact audio slug, algorithm, backend, and artifact paths
- does not directly rewrite defaults without benchmark confirmation

### Lane 4: docs-and-tooling

Scope:

- workflow docs
- prompts
- regression gates
- setup guidance
- repo memory and benchmark metadata

Success means:

- reduces coordination cost
- improves reproducibility across machines
- does not change live model behavior indirectly

## Hard Rules

1. Never combine chord runtime changes and section scoring changes in the same work item.
2. Never treat a YouTube result as the primary proof of improvement.
3. Never change defaults without recording the benchmark command and result.
4. Always pin the detector backend when benchmarking.
5. Always identify whether the run used reference BTC or owned BTC.
6. Always keep artifacts for any claimed gain under `data/output/` or another explicit path.

## Machine Coordination

Use one machine role per active branch when possible.

Recommended roles:

1. `Machine A`: runtime/parity work
2. `Machine B`: section benchmarking and detector tuning
3. `Machine C`: single-song diagnostics and repro collection

If only two machines are available:

1. `Machine A`: runtime/parity
2. `Machine B`: benchmark + diagnostics

Do not run the same tuning experiment independently on multiple machines unless the inputs are identical and intentionally duplicated for verification.

## Branching Model

Use one integration branch plus short-lived worker branches.

Recommended pattern:

- integration branch: `coordination/<wave-name>`
- worker branches merged into it: one per machine or lane

Example:

- `coordination/wave-1`
- `runtime/btc-reference-pin`
- `sections/heuristic-weight-sweep`
- `diagnostics/youtube-failure-catalog`

Do not have all machines commit directly to the same integration branch. That removes attribution and creates avoidable conflicts.

Use short-lived worker branches with explicit lane prefixes:

- `runtime/<topic>`
- `sections/<topic>`
- `diagnostics/<topic>`
- `tooling/<topic>`

Examples:

- `runtime/btc-reference-pin`
- `sections/heuristic-weight-sweep`
- `diagnostics/youtube-boundary-failure-notes`
- `tooling/regression-gate`

## Task Contract

Every agent task should start by declaring:

- lane
- files expected to change
- benchmark or parity command to use
- forbidden side-effects
- expected artifacts

Minimum contract template:

```text
Lane: section-benchmarking
Files: scripts/analysis/section_detector.py, scripts/bench/section_benchmark.py
Proof: python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic
Do not touch: audioanalysis/chord_pipeline.py, audioanalysis/btc_runtime/
Artifacts: data/output/section_benchmark.json
```

## Definition Of Done

### Runtime-stability

- parity command run
- backend used is explicit
- fallback behavior explained
- health reporting remains correct

### Section-benchmarking

- benchmark run against pinned backend
- before/after delta captured
- single-song smoke test, if used, is labeled as diagnostic only

### Single-song-diagnostics

- audio source identified
- algorithm/backend identified
- failure mode categorized
- recommendation sent back to benchmark lane, not directly applied

### Docs-and-tooling

- instructions stored in repo
- prompts are reusable without hidden context
- cross-machine assumptions are stated explicitly

## Recommended Near-Term Sequence

1. Pin chord work to reference BTC as the consistency anchor.
2. Keep owned-runtime work behind parity checks only.
3. Run section gains only on the heuristic detector with pinned benchmark backend.
4. Add regression gating before changing defaults again.
5. Use YouTube runs after benchmark success to inspect whether the gain generalizes perceptually.

## What Counts As A Gain

A change is a gain only if:

1. the primary benchmark does not regress
2. the change is attributable to one lane
3. the result can be reproduced on another machine with the same command

If any of those are missing, the result is exploratory, not a gain.
