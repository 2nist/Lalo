# Machine A: Runtime Stability

## Mission

Protect chord-runtime consistency.

## Lane

`runtime-stability`

## Primary Scope

- `audioanalysis/btc_runtime/`
- `audioanalysis/chord_pipeline.py`
- `tmp/validate_pipeline.py`
- runtime health and setup reporting

## Must Not Touch

- `scripts/analysis/section_detector.py`
- `scripts/bench/section_benchmark.py`
- detector weights or detector defaults

## Success Criteria

1. reference BTC parity remains stable
2. backend choice is explicit
3. fallback behavior is documented if triggered
4. no direct spread of `third_party/BTC-ISMIR19` imports

## Preferred Commands

```text
python tmp/validate_pipeline.py
python -m py_compile audioanalysis/chord_pipeline.py audioanalysis/btc_runtime/runtime.py
```

## Expected Artifacts

- parity notes
- explicit backend used
- any runtime-health output needed for handoff
