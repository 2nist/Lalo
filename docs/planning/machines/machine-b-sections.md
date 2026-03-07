# Machine B: Section Benchmarking

## Mission

Produce section-detector gains without cross-lane regression.

## Lane

`section-benchmarking`

## Primary Scope

- `scripts/analysis/section_detector.py`
- `scripts/bench/section_benchmark.py`
- `scripts/bench/grid_search_weights.py`
- detector-related API wiring when necessary

## Must Not Touch

- `audioanalysis/chord_pipeline.py`
- `audioanalysis/btc_runtime/`
- BTC backend defaults

## Success Criteria

1. benchmark backend is pinned
2. benchmark is improved or neutral
3. single-song review, if used, is diagnostic only
4. artifact paths are recorded for before/after comparison

## Preferred Commands

```text
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic
python scripts/bench/grid_search_weights.py --max-songs 20
python -m py_compile scripts/analysis/section_detector.py scripts/bench/section_benchmark.py
```

## Expected Artifacts

- benchmark JSON output
- any candidate logs needed to explain the change
- short delta summary for handoff
