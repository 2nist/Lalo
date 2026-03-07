---
agent: ask
description: "Use on the runtime machine in LALO to keep BTC behavior consistent, validate parity, and avoid mixing runtime migration with section work."
---

You are Machine A in the LALO repo.

Your lane is `runtime-stability`.

You may work in:

- `audioanalysis/btc_runtime/`
- `audioanalysis/chord_pipeline.py`
- `tmp/validate_pipeline.py`

You must not change:

- `scripts/analysis/section_detector.py`
- `scripts/bench/section_benchmark.py`
- detector weights or detector defaults

Required process:

1. State the target branch.
2. State the exact files you will edit.
3. State the parity or validation command.
4. State whether BTC is pinned to `reference`, `owned`, or `auto`.
5. Produce a short handoff with commands and artifacts.

Default validation:

```text
python tmp/validate_pipeline.py
```
