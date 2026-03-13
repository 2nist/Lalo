#!/usr/bin/env python3
"""
Grid search over `scripts.analysis.section_detector` signal weights.

Defaults to a small sweep varying `flux_peak` and `duration_prior` multipliers
to keep runtime reasonable. Use `--vary all` to expand to the full grid.

Outputs `results/grid_search_weights.json` and a CSV summary.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Dict, List

# Ensure project root is on sys.path so imports like
# `from scripts.bench.section_benchmark import ...` work when run from CLI
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description="Grid-search section detector weights")
    ap.add_argument("--dev-only", action="store_true", help="Use first 30 Harmonix songs")
    ap.add_argument("--out", default="results/grid_search_weights.json")
    ap.add_argument("--vary", choices=("flux_duration", "all"), default="flux_duration",
                    help="Which dimensions to sweep: small (flux+duration) or all signals")
    ap.add_argument("--max-combos", type=int, default=0,
                    help="Stop after this many combos (0=unlimited)")
    args = ap.parse_args()

    # Local import to reuse benchmark helpers
    from scripts.bench.section_benchmark import (
        _load_harmonix_pairs,
        run_benchmark,
        _summarise,
        HARMONIX_DIR,
        AUDIO_DIR,
    )

    # Base multipliers
    if args.vary == "flux_duration":
        mult_flux = [0.5, 0.75, 1.0, 1.25, 1.5]
        mult_dur = [0.5, 0.75, 1.0, 1.25, 1.5]
        mult_small = [1.0]
    else:
        # Larger full sweep (may be many combos)
        mult_flux = [0.5, 0.75, 1.0, 1.25, 1.5]
        mult_dur = [0.5, 0.75, 1.0, 1.25, 1.5]
        mult_small = [0.5, 1.0, 1.5]

    combos = list(itertools.product(mult_flux, mult_small, mult_small, mult_small, mult_dur))
    total = len(combos)
    if args.max_combos and args.max_combos > 0:
        total = min(total, args.max_combos)

    harmonix_dir = Path(HARMONIX_DIR)
    audio_dir = Path(AUDIO_DIR)
    max_songs = 30 if args.dev_only else None
    pairs = _load_harmonix_pairs(harmonix_dir, audio_dir, max_songs=max_songs)
    with_audio = [p for p in pairs if p.get("audio")]
    if not with_audio:
        raise SystemExit("No Harmonix songs with audio found for sweeping")

    results: List[Dict] = []
    start = time.time()
    seen = 0
    for i, (mf, mc, mca, mr, md) in enumerate(combos, start=1):
        if args.max_combos and seen >= args.max_combos:
            break
        weights = {
            "flux_peak": round(1.0 * mf, 4),
            "chord_novelty": round(1.0 * mc, 4),
            "cadence_score": round(1.0 * mca, 4),
            "repetition_break": round(1.0 * mr, 4),
            "duration_prior": round(1.0 * md, 4),
        }

        print(f"[{i}/{len(combos)}] Testing weights: {weights}")
        # run benchmark on dev split (pairs already limited)
        res = run_benchmark(with_audio, weights=weights, tolerances=(0.5, 3.0), algorithm="heuristic")
        summary = _summarise(res, (0.5, 3.0))
        det_summary = summary.get("detector", {})
        f1_05 = det_summary.get("F1@0.5s", {}).get("mean")

        results.append({
            "weights": weights,
            "mean_f1_0.5": f1_05,
            "summary": det_summary,
            "per_song_count": len(res),
        })

        seen += 1

    dur = time.time() - start
    outp = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "sweep_count": len(results),
        "dev_only": args.dev_only,
        "vary": args.vary,
        "results": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(outp, indent=2), encoding="utf-8")
    # Also write CSV summary
    import csv
    csv_path = out_path.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["mean_f1_0.5", "flux_peak", "chord_novelty", "cadence_score", "repetition_break", "duration_prior"])
        for r in results:
            w.writerow([
                r.get("mean_f1_0.5"),
                r["weights"]["flux_peak"],
                r["weights"]["chord_novelty"],
                r["weights"]["cadence_score"],
                r["weights"]["repetition_break"],
                r["weights"]["duration_prior"],
            ])

    print(f"Sweep complete: {len(results)} combos in {dur:.1f}s")
    print(f"Wrote: {out_path} and {csv_path}")


if __name__ == "__main__":
    main()
