#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


FEATURE_COLUMNS = [
    "flux_peak",
    "chord_novelty",
    "cadence_score",
    "repetition_break",
    "duration_prior",
    "chroma_change",
    "spec_contrast",
    "onset_density",
    "rms_energy",
    "msaf_vote",
]


def _load_benchmark(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _salami_boundaries(ann_path: Path) -> List[float]:
    data = json.loads(ann_path.read_text(encoding="utf-8"))
    sections = data.get("sections", [])
    boundaries = sorted([float(s.get("start_ms", 0.0)) / 1000.0 for s in sections])
    unique = []
    for t in boundaries:
        if not unique or abs(t - unique[-1]) > 1e-3:
            unique.append(t)
    return unique


def _label_candidate(time_s: float, boundaries: List[float], tol: float = 0.5) -> int:
    return 1 if any(abs(time_s - b) <= tol for b in boundaries) else 0


def _choose_best_run(paths: List[Path]) -> Path:
    best_path: Optional[Path] = None
    best_f1 = float("-inf")
    for p in paths:
        if not p.exists():
            continue
        data = _load_benchmark(p)
        detector = data.get("summary", {}).get("detector", {})
        f1_info = detector.get("F1@3.0s", {})
        f1 = float(f1_info.get("mean", 0.0))
        if f1 > best_f1:
            best_f1 = f1
            best_path = p
    if best_path is None:
        raise FileNotFoundError("No SALAMI benchmark outputs found.")
    return best_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract SALAMI candidate training data from benchmark output."
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=None,
        help="Path to SALAMI benchmark JSON (defaults to best F1@3.0 run).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="CSV destination path.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.5,
        help="Boundary tolerance in seconds.",
    )
    args = parser.parse_args()

    candidate_paths = [
        Path("results/salami-baseline-heuristic.json"),
        Path("results/salami-step5-full.json"),
        Path("results/salami-step7-final.json"),
    ]
    benchmark_path = args.benchmark or _choose_best_run(candidate_paths)
    print(f"Using benchmark: {benchmark_path}")
    benchmark = _load_benchmark(benchmark_path)

    header = FEATURE_COLUMNS + ["label"]
    rows: List[List[str]] = []
    positives = 0

    for song in benchmark.get("per_song", []):
        ann_path = song.get("annotation")
        if not ann_path:
            continue
        boundaries = _salami_boundaries(Path(ann_path))
        candidates = song.get("detector", {}).get("candidates", [])
        for cand in candidates:
            features: Dict[str, float] = cand.get("features", {})
            time_s = float(cand.get("time_s", 0.0))
            label = _label_candidate(time_s, boundaries, tol=args.tolerance)
            if label == 1:
                positives += 1
            feature_values = [
                features.get(name, 0.0 if name == "msaf_vote" else 0.0)
                for name in FEATURE_COLUMNS
            ]
            rows.append([f"{float(val):.6f}" for val in feature_values] + [str(label)])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)

    total = len(rows)
    pct = round(100 * positives / total, 2) if total else 0.0
    print(
        f"Total rows: {total}, positives: {positives}, "
        f"class balance (% positive): {pct}"
    )


if __name__ == "__main__":
    main()
