#!/usr/bin/env python3
"""
SALAMI Section Detection Benchmark — McGill Billboard subset.

Evaluates the section detector against SALAMI ground-truth annotations.
Annotation format:
{
  "title": "...",
  "artist": "...",
  "sections": [
    {"id": "A1", "sectionType": "Intro", "start_ms": 73, "duration_ms": 22273}
  ]
}

Metrics:
  F1 @ 0.5s tolerance
  F1 @ 3.0s tolerance

Usage:
  python scripts/bench/salami_benchmark.py --max-songs 20
  python scripts/bench/salami_benchmark.py --algorithm heuristic --out results/salami.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Optional, Tuple

import mir_eval.segment as mir_segment

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DEFAULT_ANN_DIR = ROOT / "datasets" / "mcgill" / "mcgill_jcrd_salami_Billboard"
DEFAULT_AUDIO_DIR = ROOT / "data" / "salami_audio"

# Candidate pruning defaults (can be overridden via CLI)
GLOBAL_MIN_SECTION_SEC = 4.0
GLOBAL_NMS_GAP_SEC = 8.0
GLOBAL_CAND_PROMINENCE = 0.18
GLOBAL_CAND_SUB_PROMINENCE = 0.3


# ---------------------------------------------------------------------------
# Metrics (copied verbatim from section_benchmark.py)
# ---------------------------------------------------------------------------

def _boundary_f1(
    ref_sections: List[Dict],
    pred_sections: List[Dict],
    tolerance_s: float,
) -> Dict:
    """Compute boundary precision/recall/F1 at given tolerance."""

    def _boundaries(sections: List[Dict]) -> List[float]:
        if not sections:
            return []
        all_starts = sorted(set(round(s["start_s"], 3) for s in sections))
        first = min(s["start_s"] for s in sections)
        return [t for t in all_starts if t > first + 0.1]

    ref_b = _boundaries(ref_sections)
    pred_b = _boundaries(pred_sections)

    used: set = set()
    tp = 0
    for p in pred_b:
        best_i = None
        best_d = float("inf")
        for i, r in enumerate(ref_b):
            if i in used:
                continue
            d = abs(p - r)
            if d <= tolerance_s and d < best_d:
                best_d = d
                best_i = i
        if best_i is not None:
            used.add(best_i)
            tp += 1

    fp = len(pred_b) - tp
    fn = len(ref_b) - tp
    precision = tp / len(pred_b) if pred_b else 0.0
    recall = tp / len(ref_b) if ref_b else 0.0
    denom = precision + recall
    f1 = (2 * precision * recall) / denom if denom else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "ref_boundaries": len(ref_b),
        "pred_boundaries": len(pred_b),
    }


def _label_accuracy(
    ref_sections: List[Dict],
    pred_sections: List[Dict],
) -> float:
    """Duration-weighted canonical label accuracy."""
    if not ref_sections or not pred_sections:
        return 0.0
    total_dur = sum(s["end_s"] - s["start_s"] for s in ref_sections)
    if total_dur <= 0:
        return 0.0
    correct = 0.0
    for ref in ref_sections:
        dur = ref["end_s"] - ref["start_s"]
        best_overlap = 0.0
        best_pred = None
        for pred in pred_sections:
            ov = max(
                0,
                min(ref["end_s"], pred["end_s"])
                - max(ref["start_s"], pred["start_s"]),
            )
            if ov > best_overlap:
                best_overlap = ov
                best_pred = pred
        if best_pred and (ref.get("label") == best_pred.get("label", "")):
            correct += dur
    return round(correct / total_dur, 4)


# ---------------------------------------------------------------------------
# SALAMI helpers
# ---------------------------------------------------------------------------

def _parse_salami_sections(path: Path) -> List[Dict]:
    """Parse SALAMI annotation file -> [{start_s, end_s, label}]."""
    data = json.loads(path.read_text(encoding="utf-8"))
    sections = []
    for s in data.get("sections", []):
        start_s = float(s.get("start_ms", 0.0)) / 1000.0
        dur_s = float(s.get("duration_ms", 0.0)) / 1000.0
        if dur_s <= 0:
            continue
        sections.append({
            "start_s": start_s,
            "end_s": start_s + dur_s,
            "label": s.get("sectionType", "Section"),
        })
    sections = sorted(sections, key=lambda x: x["start_s"])
    return sections


def _find_annotation(ann_dir: Path, salami_id: str) -> Optional[Path]:
    pat = f"{int(salami_id):04d}_*.json"
    matches = sorted(ann_dir.glob(pat))
    return matches[0] if matches else None


def _load_salami_pairs(
    ann_dir: Path,
    audio_dir: Path,
    max_songs: Optional[int] = None,
) -> List[Dict]:
    pairs: List[Dict] = []
    audio_files = sorted(audio_dir.glob("[0-9]*.m4a"), key=lambda p: int(p.stem))
    for audio_path in audio_files:
        salami_id = audio_path.stem
        ann_path = _find_annotation(ann_dir, salami_id)
        if not ann_path:
            continue
        pairs.append({
            "id": salami_id,
            "audio": str(audio_path),
            "annotation": str(ann_path),
        })
        if max_songs and len(pairs) >= max_songs:
            break
    return pairs


# ---------------------------------------------------------------------------
# Baseline methods
# ---------------------------------------------------------------------------

def _predict_fixed_chunks(
    song_duration_s: float, chunk_s: float = 32.0
) -> List[Dict]:
    sections = []
    t = 0.0
    i = 1
    while t < song_duration_s:
        end = min(t + chunk_s, song_duration_s)
        sections.append({"start_s": t, "end_s": end, "label": f"Section {i}"})
        t = end
        i += 1
    return sections


def _run_detector(
    audio_path: Path,
    chords: Optional[List[Dict]],
    weights: Dict,
    algorithm: str,
) -> Optional[Dict]:
    try:
        from scripts.analysis.section_detector import detect_sections

        result = detect_sections(
            audio_path,
            chords=chords,
            weights=weights,
            beat_snap_sec=0,
            algorithm=algorithm,
            downbeat_confidence_thresh=0.0,
            min_section_sec=GLOBAL_MIN_SECTION_SEC,
            nms_gap_sec=GLOBAL_NMS_GAP_SEC,
            cand_prominence=GLOBAL_CAND_PROMINENCE,
            cand_sub_prominence=GLOBAL_CAND_SUB_PROMINENCE,
        )
        sections = []
        for s in result.get("sections", []):
            start_s = s["start_ms"] / 1000.0
            dur_s = s["duration_ms"] / 1000.0
            sections.append({
                "start_s": start_s,
                "end_s": start_s + dur_s,
                "label": s.get("label", "Section"),
            })
        return {
            "sections": sections,
            "meta": result.get("meta", {}),
            "candidates": result.get("candidates", []),
        }
    except Exception as exc:
        print(f"    detector error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

def run_benchmark(
    pairs: List[Dict],
    weights: Dict,
    tolerances: Tuple[float, ...] = (0.5, 3.0),
    algorithm: str = "heuristic",
) -> List[Dict]:
    results: List[Dict] = []
    n = len(pairs)
    print(
        f"\nRunning SALAMI section detection benchmark on {n} songs "
        f"(algorithm={algorithm})..."
    )
    cols = (
        f"{'#':>3}  {'ID':>6}  {'Det@0.5':>7}  {'Det@3.0':>7}  "
        f"{'Fixed@0.5':>9}  {'Time':>5}"
    )
    print(cols)
    print("-" * len(cols))

    for i, pair in enumerate(pairs):
        t0 = time.time()
        song_id = pair["id"]
        audio_path = Path(pair["audio"])
        ann_path = Path(pair["annotation"])

        try:
            ref_sections = _parse_salami_sections(ann_path)
        except Exception as exc:
            print(f"{i+1:>3}  {song_id:>6}  skip  (parse error: {exc})")
            continue

        if not ref_sections:
            print(f"{i+1:>3}  {song_id:>6}  skip  (no ref sections)")
            continue

        ref_intervals = [
            [s["start_s"], s["end_s"]] for s in ref_sections
        ]
        ref_labels = [s.get("label", "Section") for s in ref_sections]

        song_duration_s = ref_sections[-1]["end_s"]
        entry: Dict = {
            "id": song_id,
            "audio": str(audio_path),
            "annotation": str(ann_path),
            "ref_sections": len(ref_sections),
            "song_duration_s": round(song_duration_s, 2),
        }

        fixed_pred = _predict_fixed_chunks(song_duration_s, chunk_s=32.0)
        entry["fixed_chunks"] = {
            str(tol): _boundary_f1(ref_sections, fixed_pred, tol)
            for tol in tolerances
        }

        det_pred = _run_detector(
            audio_path,
            chords=None,
            weights=weights,
            algorithm=algorithm,
        )
        if det_pred is not None:
            det_sections = det_pred.get("sections", [])
            det_meta = det_pred.get("meta", {})
            det_candidates = det_pred.get("candidates", [])

            entry["detector"] = {
                str(tol): _boundary_f1(ref_sections, det_sections, tol)
                for tol in tolerances
            }
            entry["detector"]["label_accuracy"] = (
                _label_accuracy(ref_sections, det_sections)
            )
            entry["detector"]["pred_sections"] = len(det_sections)
            entry["detector"]["algorithm"] = det_meta.get("algorithm") or algorithm
            entry["detector"]["meta"] = det_meta
            entry["detector"]["candidates"] = det_candidates

            est_intervals = [
                [s["start_s"], s["end_s"]] for s in det_sections
            ]
            est_labels = ["S"] * len(est_intervals)
            pairwise_f1 = None
            mean_deviation_s = None
            if ref_intervals and est_intervals:
                try:
                    pairwise_f1 = mir_segment.pairwise(
                        ref_intervals,
                        ref_labels,
                        est_intervals,
                        est_labels,
                    )[2]
                except Exception:
                    pairwise_f1 = None
                try:
                    mean_deviation_s = mir_segment.deviation(
                        ref_intervals,
                        est_intervals,
                    )[0]
                except Exception:
                    mean_deviation_s = None
            entry["detector"]["pairwise_f1"] = (
                round(pairwise_f1, 4) if pairwise_f1 is not None else None
            )
            entry["detector"]["mean_deviation_s"] = (
                round(mean_deviation_s, 4) if mean_deviation_s is not None else None
            )

        elapsed = time.time() - t0
        entry["time_s"] = round(elapsed, 1)

        det_f1 = entry.get("detector", {}).get("0.5", {}).get("f1", "-")
        det_f1_coarse = entry.get("detector", {}).get("3.0", {}).get("f1", "-")
        fixed_f1 = entry["fixed_chunks"]["0.5"]["f1"]

        print(
            f"{i+1:>3}  {song_id:>6}  {str(det_f1):>7}  {str(det_f1_coarse):>7}"
            f"  {fixed_f1:>9.3f}  {elapsed:>5.1f}s"
        )
        results.append(entry)

    return results


def _summarise(results: List[Dict], tolerances: Tuple[float, ...]) -> Dict:
    summary = {}
    for method in ("detector", "fixed_chunks"):
        method_f1: Dict = {}
        for tol in tolerances:
            vals = [
                r[method][str(tol)]["f1"]
                for r in results
                if isinstance(r.get(method), dict)
                and str(tol) in r[method]
                and r[method][str(tol)].get("f1") is not None
            ]
            if vals:
                method_f1[f"F1@{tol}s"] = {
                    "mean": round(mean(vals), 4),
                    "median": round(median(vals), 4),
                    "n": len(vals),
                }
        label_accs = [
            r[method].get("label_accuracy")
            for r in results
            if isinstance(r.get(method), dict)
            and r[method].get("label_accuracy") is not None
        ]
        if label_accs:
            method_f1["label_accuracy"] = {
                "mean": round(mean(label_accs), 4),
                "median": round(median(label_accs), 4),
                "n": len(label_accs),
            }
        if method_f1:
            summary[method] = method_f1
    return summary


def main() -> None:
    p = argparse.ArgumentParser(
        description="Section detection benchmark (SALAMI McGill Billboard subset)"
    )
    p.add_argument(
        "--ann-dir",
        default=str(DEFAULT_ANN_DIR),
        help="Directory with SALAMI annotation JSON files",
    )
    p.add_argument(
        "--salami-audio-dir",
        default=str(DEFAULT_AUDIO_DIR),
        help="Directory with SALAMI audio .m4a files",
    )
    p.add_argument(
        "--max-songs", type=int, default=None, help="Limit songs (quick test)"
    )
    p.add_argument(
        "--out",
        default="results/salami_benchmark.json",
        help="Output JSON path",
    )
    p.add_argument(
        "--algorithm",
        default="heuristic",
        choices=[
            "heuristic",
            "auto",
            "msaf_scluster",
            "msaf_sf",
            "scored",
        ],
        help="Detector backend to benchmark",
    )
    p.add_argument("--nms_gap_sec", type=float, default=GLOBAL_NMS_GAP_SEC)
    p.add_argument("--min_section_sec", type=float, default=GLOBAL_MIN_SECTION_SEC)
    p.add_argument("--prominence", type=float, default=GLOBAL_CAND_PROMINENCE)
    p.add_argument("--sub_prominence", type=float, default=GLOBAL_CAND_SUB_PROMINENCE)
    p.add_argument("--weight-flux", type=float, default=0.35)
    p.add_argument("--weight-chord", type=float, default=0.30)
    p.add_argument("--weight-cadence", type=float, default=0.15)
    p.add_argument("--weight-repetition", type=float, default=0.15)
    p.add_argument("--weight-duration", type=float, default=0.05)
    p.add_argument("--weight-chroma", type=float, default=0.0)
    p.add_argument("--weight-spec-contrast", type=float, default=0.0)
    p.add_argument("--weight-onset-density", type=float, default=0.0)
    p.add_argument("--weight-rms", type=float, default=0.0)
    args = p.parse_args()

    # Apply CLI overrides to detector globals via globals() to avoid scope issues
    globals().update({
        "GLOBAL_MIN_SECTION_SEC": float(args.min_section_sec),
        "GLOBAL_NMS_GAP_SEC": float(args.nms_gap_sec),
        "GLOBAL_CAND_PROMINENCE": float(args.prominence),
        "GLOBAL_CAND_SUB_PROMINENCE": float(args.sub_prominence),
    })

    weights = {
        "flux_peak": args.weight_flux,
        "chord_novelty": args.weight_chord,
        "cadence_score": args.weight_cadence,
        "repetition_break": args.weight_repetition,
        "duration_prior": args.weight_duration,
        "chroma_change": args.weight_chroma,
        "spec_contrast": args.weight_spec_contrast,
        "onset_density": args.weight_onset_density,
        "rms_energy": args.weight_rms,
    }

    ann_dir = Path(args.ann_dir)
    audio_dir = Path(args.salami_audio_dir)
    if not ann_dir.exists():
        print(f"SALAMI annotation dir not found: {ann_dir}")
        sys.exit(1)
    if not audio_dir.exists():
        print(f"SALAMI audio dir not found: {audio_dir}")
        sys.exit(1)

    pairs = _load_salami_pairs(ann_dir, audio_dir, max_songs=args.max_songs)
    print(f"Found {len(pairs)} matched SALAMI pairs")
    if not pairs:
        sys.exit(1)

    tolerances = (0.5, 3.0)
    results = run_benchmark(
        pairs,
        weights=weights,
        tolerances=tolerances,
        algorithm=args.algorithm,
    )
    summary = _summarise(results, tolerances)

    output = {
        "benchmark_date": time.strftime("%Y-%m-%d %H:%M"),
        "songs_evaluated": len(results),
        "algorithm": args.algorithm,
        "weights": weights,
        "summary": summary,
        "per_song": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("SECTION DETECTION BENCHMARK (SALAMI) RESULTS")
    print("=" * 60)
    labels = {
        "detector": "Section Detector (new)",
        "fixed_chunks": "Fixed 32s Chunks (naive)",
    }
    for method in ("detector", "fixed_chunks"):
        s = summary.get(method)
        if not s:
            continue
        print(f"\n{labels[method]}:")
        for metric, vals in sorted(s.items()):
            print(
                f"  {metric}: mean={vals['mean']:.4f}"
                f"  median={vals['median']:.4f}  n={vals['n']}"
            )

    print(f"\nWrote: {out_path}")


if __name__ == "__main__":
    main()
