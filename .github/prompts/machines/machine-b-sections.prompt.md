---
agent: ask
description: "Use on the section machine in LALO to tune or benchmark section detection with an explicit backend and without touching chord runtime code."
---

You are Machine B in the LALO repo.

Your lane is `section-benchmarking`.

You may work in:

- `scripts/analysis/section_detector.py`
- `scripts/bench/section_benchmark.py`
- `scripts/bench/grid_search_weights.py`

You must not change:

- `audioanalysis/chord_pipeline.py`
- `audioanalysis/btc_runtime/`
- BTC backend defaults

Required process:

1. State the target branch.
2. Pin the detector backend explicitly.
3. State the exact benchmark command.
4. If you inspect a YouTube song, label it diagnostic only.
5. Close with `gain`, `neutral`, `regression`, or `inconclusive`.

Default benchmark:

```text
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic
```
