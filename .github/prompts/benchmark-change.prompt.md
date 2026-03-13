---
agent: ask
description: "Use when changing LALO section detection and you need the agent to optimize against the pinned benchmark instead of a single-song result."
---

You are working on LALO section detection.

Your job is to make or evaluate a section-detection change under benchmark discipline.

Required process:

1. Confirm the task is in the `section-benchmarking` lane.
2. Pin the detector backend explicitly.
3. Identify the exact files to edit.
4. Run or specify the benchmark command to prove the result.
5. If you inspect a single YouTube or local song, label that output as diagnostic only.
6. Summarize the result as one of:
   - gain
   - neutral
   - regression
   - inconclusive

Default benchmark command:

```text
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic
```

Default weight-sweep command:

```text
python scripts/bench/grid_search_weights.py --max-songs 20
```

Do not:

- modify `audioanalysis/chord_pipeline.py`
- modify `audioanalysis/btc_runtime/`
- claim a gain without benchmark evidence

Required closing format:

```text
Status:
Backend pinned:
Files changed:
Benchmark command:
Artifacts:
Diagnostic single-song notes:
Decision:
```
