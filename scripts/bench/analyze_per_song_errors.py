#!/usr/bin/env python3
"""Analyze per-song false positives / false negatives from a benchmark.

Loads a benchmark JSON (created by `section_benchmark.py`), re-runs the
detector to obtain predicted boundaries, matches boundaries to references
at a tolerance (default 0.5s), and writes a CSV with counts and timestamps
for FP/FN per song.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _boundaries_from_sections(sections: List[dict]) -> List[float]:
    if not sections:
        return []
    starts = []
    for s in sections:
        if "start_s" in s:
            starts.append(float(s["start_s"]))
        elif "start_ms" in s:
            starts.append(float(s["start_ms"]) / 1000.0)
        else:
            # skip unknown format
            continue
    all_starts = sorted(set(round(x, 3) for x in starts))
    first = min(starts) if starts else 0.0
    return [t for t in all_starts if t > first + 0.1]


def match_boundaries(ref: List[float], pred: List[float], tol: float) -> Tuple[List[Tuple[float, float]], List[float], List[float]]:
    """Greedy match pred to ref within tol.
    Returns (matches list of (pred,ref), unmatched_refs (FN), unmatched_preds (FP)).
    """
    ref_sorted = sorted(ref)
    pred_sorted = sorted(pred)
    used = set()
    matches = []
    for p in pred_sorted:
        best_i = None
        best_d = float("inf")
        for i, r in enumerate(ref_sorted):
            if i in used:
                continue
            d = abs(p - r)
            if d <= tol and d < best_d:
                best_d = d
                best_i = i
        if best_i is not None:
            used.add(best_i)
            matches.append((p, ref_sorted[best_i]))

    unmatched_refs = [r for i, r in enumerate(ref_sorted) if i not in used]
    matched_preds = {m[0] for m in matches}
    unmatched_preds = [p for p in pred_sorted if p not in matched_preds]
    return matches, unmatched_refs, unmatched_preds


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--bench", default="results/section_bench.learned_weights.json")
    p.add_argument("--out", default="results/false_pos_neg_per_song.csv")
    p.add_argument("--tol", type=float, default=0.5)
    args = p.parse_args()

    bench_path = Path(args.bench)
    if not bench_path.exists():
        print(f"Benchmark JSON not found: {bench_path}")
        raise SystemExit(1)

    data = json.loads(bench_path.read_text(encoding="utf-8"))
    weights = data.get("weights", {})
    algorithm = data.get("algorithm", "heuristic")

    try:
        from scripts.analysis.section_detector import detect_sections
    except Exception as exc:
        print("Cannot import section detector:", exc)
        raise

    rows = []
    for entry in data.get("per_song", []):
        song_id = entry.get("id")
        audio = entry.get("audio")
        sections_file = entry.get("sections_file") or None

        # Load reference sections from file if available
        ref_sections = []
        if sections_file:
            try:
                with open(sections_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                ref_sections.append({"start_s": float(parts[0])})
                            except ValueError:
                                pass
            except Exception:
                ref_sections = []

        ref_b = _boundaries_from_sections(ref_sections)

        if not audio:
            rows.append({
                "id": song_id,
                "audio": "no",
                "ref_boundaries": len(ref_b),
                "pred_boundaries": 0,
                "tp": 0,
                "fp": 0,
                "fn": len(ref_b),
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "fp_times": "",
                "fn_times": ";".join([str(x) for x in ref_b]),
            })
            continue

        # Run detector to get predicted sections
        try:
            res = detect_sections(Path(audio), chords=None, weights=weights, algorithm=algorithm)
            pred_sections = res.get("sections", []) if isinstance(res, dict) else res
        except Exception as exc:
            print(f"Detector run failed for {song_id}: {exc}")
            pred_sections = []

        pred_b = _boundaries_from_sections(pred_sections)

        matches, fn_times, fp_times = match_boundaries(ref_b, pred_b, args.tol)

        tp = len(matches)
        fp = len(fp_times)
        fn = len(fn_times)
        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round((2 * precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        rows.append({
            "id": song_id,
            "audio": "yes",
            "ref_boundaries": len(ref_b),
            "pred_boundaries": len(pred_b),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fp_times": ";".join([str(x) for x in fp_times]),
            "fn_times": ";".join([str(x) for x in fn_times]),
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as csvf:
        fieldnames = [
            "id",
            "audio",
            "ref_boundaries",
            "pred_boundaries",
            "tp",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1",
            "fp_times",
            "fn_times",
        ]
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()
