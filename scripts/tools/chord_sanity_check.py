"""
Quick sanity check: import chord pipeline and BTC runtime health.
Writes `results/chord_sanity.json` with health and simple import checks.
"""
from __future__ import annotations
import json
from pathlib import Path

RESULTS = Path("results")
RESULTS.mkdir(parents=True, exist_ok=True)
OUT = RESULTS / "chord_sanity.json"

res = {"health": None, "imports_ok": [], "errors": []}

try:
    import sys
    from pathlib import Path as _P
    # ensure repo root on sys.path
    sys.path.insert(0, str(_P(__file__).resolve().parents[2]))
    from audioanalysis.btc_runtime import get_btc_runtime_health
    res["imports_ok"].append("btc_runtime")
    try:
        health = get_btc_runtime_health()
        res["health"] = health
    except Exception as e:
        res["errors"].append(f"btc_health_error: {e}")
except Exception as e:
    res["errors"].append(f"import_btc_runtime_failed: {e}")

try:
    from audioanalysis.chord_pipeline import load_audio, extract_cqt
    res["imports_ok"].append("chord_pipeline")
except Exception as e:
    res["errors"].append(f"import_chord_pipeline_failed: {e}")

OUT.write_text(json.dumps(res, indent=2))
print(f"wrote {OUT}")
