#!/usr/bin/env python3
"""
LALO Section Detection Benchmark — Harmonix Set.

Evaluates the section detector against Harmonix ground-truth annotations.
Harmonix dataset: nicolaus625/cmi on HuggingFace
  data/raw/harmonix/<id>_sections.txt  — start_time  label
  data/raw/harmonix/<id>_beats.txt     — one beat time per line

Metrics:
  F1 @ 0.5s tolerance  (standard MIR boundary eval)
  F1 @ 3.0s tolerance  (coarse structure eval)
  Duration-weighted canonical label accuracy

Usage:
  python scripts/bench/section_benchmark.py --dev-only
  python scripts/bench/section_benchmark.py --max-songs 10
  python scripts/bench/section_benchmark.py --out data/output/bench.json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import warnings
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Optional, Tuple

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Harmonix annotation parsing
# ---------------------------------------------------------------------------

HARMONIX_DIR = ROOT / "data" / "raw" / "harmonix"
AUDIO_DIR = ROOT / "data" / "audio"

# Canonical label map matching verifySections.js
_LABEL_CANON = {
    "intro": "intro",
    "introduction": "intro",
    "verse": "verse",
    "verse1": "verse",
    "verse2": "verse",
    "chorus": "chorus",
    "refrain": "chorus",
    "hook": "chorus",
    "pre-chorus": "pre-chorus",
    "prechorus": "pre-chorus",
    "post-chorus": "post-chorus",
    "postchorus": "post-chorus",
    "bridge": "bridge",
    "middle8": "bridge",
    "outro": "outro",
    "ending": "outro",
    "coda": "outro",
    "end": "outro",
    "break": "interlude",
    "instrumental": "interlude",
    "interlude": "interlude",
    "solo": "interlude",
    "transition": "interlude",
    "silence": "silence",
}


def _canon(label: str) -> str:
    key = label.lower().strip().replace(" ", "")
    return _LABEL_CANON.get(key, label.lower().strip())


def _parse_harmonix_sections(path: Path) -> List[Dict]:
    """Parse Harmonix sections file -> [{start_s, end_s, label}]."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    rows.append({"start_s": float(parts[0]), "label": parts[1]})
                except ValueError:
                    continue

    sections = []
    for i, row in enumerate(rows):
        end_s = rows[i + 1]["start_s"] if i + 1 < len(rows) else None
        if end_s is None or end_s <= row["start_s"]:
            continue
        sections.append({
            "start_s": row["start_s"],
            "end_s": end_s,
            "label": row["label"],
        })
    return sections


def _load_harmonix_pairs(
    harmonix_dir: Path,
    audio_dir: Path,
    max_songs: Optional[int] = None,
) -> List[Dict]:
    """Find (sections_file, audio_file) pairs from Harmonix directory.

    Audio naming conventions (priority order):
      harmonix_<id>_<slug>.<ext>  — from fetch_harmonix_audio.py
      harmonix_<id>.<ext>         — legacy short form
      <id>.<ext>                  — bare ID
    """
    EXTS = (".m4a", ".mp3", ".webm", ".wav", ".flac", ".ogg", ".opus")

    def _find_audio(glob_pat: str) -> Optional[Path]:
        for m in sorted(audio_dir.glob(glob_pat)):
            if m.suffix.lower() in EXTS and m.stat().st_size > 10_000:
                return m
        return None

    section_files = sorted(harmonix_dir.glob("*_sections.txt"))
    pairs = []
    for sf in section_files:
        song_id = sf.stem.replace("_sections", "")

        # Priority: harmonix_<id>_<slug>.* > harmonix_<id>.* > <id>.*
        audio = (
            _find_audio(f"harmonix_{song_id}_*.*")
            or _find_audio(f"harmonix_{song_id}.*")
            or _find_audio(f"{song_id}.*")
        )

        pairs.append({
            "id": song_id,
            "sections_file": str(sf),
            "audio": str(audio) if audio else None,
        })

    if max_songs:
        pairs = pairs[:max_songs]
    return pairs


# ---------------------------------------------------------------------------
# Metrics (Python re-impl of verifySections.js boundary metrics)
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
        if best_pred and (
            _canon(ref["label"]) == _canon(best_pred.get("label", ""))
        ):
            correct += dur
    return round(correct / total_dur, 4)


# ---------------------------------------------------------------------------
# Baseline methods
# ---------------------------------------------------------------------------

def _predict_fixed_chunks(
    song_duration_s: float, chunk_s: float = 32.0
) -> List[Dict]:
    """Dumbest baseline: fixed-size sections."""
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
    """Run section detector and return benchmark sections plus detector metadata."""
    try:
        from scripts.analysis.section_detector import detect_sections
        result = detect_sections(
            audio_path,
            chords=chords,
            weights=weights,
            beat_snap_sec=0,
            algorithm=algorithm,
        )
        sections: List[Dict] = []
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
        }
    except Exception as exc:
        print(f"    detector error: {exc}")
        return None


def _run_prototype(audio_path: Path) -> Optional[List[Dict]]:
    """Run original section_prototype.py for comparison."""
    try:
        from scripts.experiments.section_prototype import run as prototype_run
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            tmp_path = Path(tf.name)
        prototype_run(audio_path, tmp_path)
        data = json.loads(tmp_path.read_text())
        sections = []
        for s in data.get("sections", []):
            start_s = s["start_ms"] / 1000.0
            dur_s = s["duration_ms"] / 1000.0
            sections.append({
                "start_s": start_s,
                "end_s": start_s + dur_s,
                "label": s.get("label", "Section"),
            })
        tmp_path.unlink(missing_ok=True)
        return sections
    except Exception as exc:
        print(f"    prototype error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Oracle beat helpers
# ---------------------------------------------------------------------------

def _load_harmonix_beats(path: Path) -> List[float]:
    """Load all beat times (seconds) from a Harmonix *_beats.txt file.

    Format: time  beat_in_bar  bar_number  (whitespace-separated).
    Returns every beat time (not just downbeats) so boundaries can snap
    to the nearest beat in the full grid.
    """
    times: List[float] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if parts:
                    try:
                        times.append(float(parts[0]))
                    except ValueError:
                        continue
    except Exception:
        pass
    return sorted(times)


def _snap_boundaries_to_beats(
    sections: List[Dict],
    beat_times: List[float],
    max_snap_s: float = 0.5,
) -> List[Dict]:
    """Snap interior section boundaries to the nearest beat grid point.

    Only interior boundaries move (song start and song end are unchanged).
    If no beat falls within *max_snap_s* the boundary is left as-is.
    """
    if not sections or not beat_times:
        return sections

    import copy
    snapped = copy.deepcopy(sections)

    def _nearest(t: float) -> Optional[float]:
        best_d = float("inf")
        best_v = None
        for b in beat_times:
            d = abs(b - t)
            if d < best_d:
                best_d, best_v = d, b
        return best_v if best_d <= max_snap_s else None

    for i in range(1, len(snapped)):
        orig = snapped[i]["start_s"]
        nb = _nearest(orig)
        if nb is not None:
            snapped[i]["start_s"] = nb
            snapped[i - 1]["end_s"] = nb

    return snapped


# ---------------------------------------------------------------------------
# Main benchmark loop
# ---------------------------------------------------------------------------

def run_benchmark(
    pairs: List[Dict],
    weights: Dict,
    tolerances: Tuple[float, ...] = (0.5, 3.0),
    oracle_beats_dir: Optional[Path] = None,
    algorithm: str = "heuristic",
) -> List[Dict]:
    results = []
    n = len(pairs)
    print(
        f"\nRunning section detection benchmark on {n} songs "
        f"(algorithm={algorithm})..."
    )
    cols = (
        f"{'#':>3}  {'ID':>16}  {'Audio':>5}  {'Ref':>3}"
        f"  {'Det@0.5':>7}  {'Proto@0.5':>9}  {'Fixed@0.5':>9}"
        + ("  {'OSnap@0.5':>10}" if oracle_beats_dir else "")
        + f"  {'Time':>5}"
    )
    print(cols)
    print("-" * len(cols))

    for i, pair in enumerate(pairs):
        t0 = time.time()
        song_id = pair["id"]
        sections_file = Path(pair["sections_file"])
        audio_path = Path(pair["audio"]) if pair["audio"] else None

        try:
            ref_sections = _parse_harmonix_sections(sections_file)
        except Exception as exc:
            print(f"{i+1:>3}  {song_id:>16}  skip  (parse error: {exc})")
            continue

        if not ref_sections:
            print(f"{i+1:>3}  {song_id:>16}  skip  (no ref sections)")
            continue

        song_duration_s = ref_sections[-1]["end_s"]
        has_audio = bool(audio_path and audio_path.exists())

        entry: Dict = {
            "id": song_id,
            "audio": str(audio_path) if audio_path else None,
            "ref_sections": len(ref_sections),
            "song_duration_s": round(song_duration_s, 2),
        }

        # Fixed chunk baseline — no audio needed
        fixed_pred = _predict_fixed_chunks(song_duration_s, chunk_s=32.0)
        entry["fixed_chunks"] = {
            str(tol): _boundary_f1(ref_sections, fixed_pred, tol)
            for tol in tolerances
        }

        if has_audio:
            det_result = _run_detector(
                audio_path,
                chords=None,
                weights=weights,
                algorithm=algorithm,
            )
            if det_result is not None:
                det_pred = det_result["sections"]
                det_meta = det_result.get("meta", {})
                effective_algorithm = det_meta.get("algorithm", "unknown")
                entry["detector"] = {
                    str(tol): _boundary_f1(ref_sections, det_pred, tol)
                    for tol in tolerances
                }
                entry["detector"]["label_accuracy"] = (
                    _label_accuracy(ref_sections, det_pred)
                )
                entry["detector"]["pred_sections"] = len(det_pred)
                entry["detector"]["requested_algorithm"] = algorithm
                entry["detector"]["effective_algorithm"] = effective_algorithm
                entry["detector"]["fallback_used"] = (
                    effective_algorithm != algorithm
                )

                # Oracle beat snap — diagnostic: replace madmom with ground-truth beats
                if oracle_beats_dir is not None:
                    beats_file = oracle_beats_dir / f"{song_id}_beats.txt"
                    if beats_file.exists():
                        beat_times = _load_harmonix_beats(beats_file)
                        snapped = _snap_boundaries_to_beats(det_pred, beat_times)
                        entry["detector_oracle"] = {
                            str(tol): _boundary_f1(ref_sections, snapped, tol)
                            for tol in tolerances
                        }
                        entry["detector_oracle"]["label_accuracy"] = (
                            _label_accuracy(ref_sections, snapped)
                        )
                    else:
                        entry["detector_oracle"] = {"error": "beats_file_missing"}

            proto_pred = _run_prototype(audio_path)
            if proto_pred is not None:
                entry["prototype"] = {
                    str(tol): _boundary_f1(ref_sections, proto_pred, tol)
                    for tol in tolerances
                }

        elapsed = time.time() - t0
        entry["time_s"] = round(elapsed, 1)

        det_f1 = entry.get("detector", {}).get("0.5", {}).get("f1", "-")
        oracle_f1 = entry.get("detector_oracle", {}).get("0.5", {}).get("f1", "-")
        proto_f1 = entry.get("prototype", {}).get("0.5", {}).get("f1", "-")
        fixed_f1 = entry["fixed_chunks"]["0.5"]["f1"]
        audio_flag = "yes" if has_audio else "no"

        oracle_part = f"  {str(oracle_f1):>10}" if oracle_beats_dir else ""
        print(
            f"{i+1:>3}  {song_id:>16}  {audio_flag:>5}  {len(ref_sections):>3}"
            f"  {str(det_f1):>7}  {str(proto_f1):>9}"
            f"  {fixed_f1:>9.3f}{oracle_part}  {elapsed:>5.1f}s"
        )
        results.append(entry)

    return results


def _summarise(results: List[Dict], tolerances: Tuple[float, ...]) -> Dict:
    summary = {}
    for method in ("detector", "detector_oracle", "prototype", "fixed_chunks"):
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


def _algorithm_counts(results: List[Dict]) -> Dict[str, int]:
    """Count effective detector backends used across evaluated songs."""
    counts: Dict[str, int] = {}
    for row in results:
        detector = row.get("detector")
        if not isinstance(detector, dict):
            continue
        algo = detector.get("effective_algorithm")
        if not algo:
            continue
        counts[str(algo)] = counts.get(str(algo), 0) + 1
    return dict(sorted(counts.items()))


def main() -> None:
    p = argparse.ArgumentParser(
        description="LALO section detection benchmark (Harmonix)"
    )
    p.add_argument(
        "--harmonix-dir",
        default=str(HARMONIX_DIR),
        help="Directory with Harmonix *_sections.txt files",
    )
    p.add_argument(
        "--audio-dir",
        default=str(AUDIO_DIR),
        help="Directory with audio files",
    )
    p.add_argument(
        "--max-songs", type=int, default=None, help="Limit songs (quick test)"
    )
    p.add_argument(
        "--dev-only",
        action="store_true",
        help="Use first 30 songs as dev split",
    )
    p.add_argument(
        "--out",
        default="data/output/section_benchmark.json",
        help="Output JSON path",
    )
    p.add_argument(
        "--oracle-beats",
        action="store_true",
        help=(
            "Snap detector boundaries to ground-truth Harmonix beats "
            "(*_beats.txt alongside *_sections.txt) before scoring. "
            "Diagnostic: shows the F1 ceiling achievable with perfect beat alignment."
        ),
    )
    p.add_argument(
        "--algorithm",
        default="heuristic",
        choices=[
            "heuristic",
            "auto",
            "msaf",
            "msaf_sf",
            "msaf_scluster",
            "msaf_olda",
        ],
        help=(
            "Detector backend to benchmark. Default is heuristic so "
            "weight tuning measures the weighted multi-signal path "
            "rather than whichever MSAF "
            "backend happens to be available."
        ),
    )
    p.add_argument("--weight-flux", type=float, default=0.35)
    p.add_argument("--weight-chord", type=float, default=0.30)
    p.add_argument("--weight-cadence", type=float, default=0.15)
    p.add_argument("--weight-repetition", type=float, default=0.15)
    p.add_argument("--weight-duration", type=float, default=0.05)
    args = p.parse_args()

    weights = {
        "flux_peak": args.weight_flux,
        "chord_novelty": args.weight_chord,
        "cadence_score": args.weight_cadence,
        "repetition_break": args.weight_repetition,
        "duration_prior": args.weight_duration,
    }

    harmonix_dir = Path(args.harmonix_dir)
    audio_dir = Path(args.audio_dir)

    if not harmonix_dir.exists():
        print(f"Harmonix dir not found: {harmonix_dir}")
        print("Download annotations first:")
        print("  python scripts/datasets/fetch_harmonix.py")
        sys.exit(1)

    max_songs = 30 if args.dev_only else args.max_songs
    pairs = _load_harmonix_pairs(harmonix_dir, audio_dir, max_songs=max_songs)
    with_audio = sum(1 for p in pairs if p["audio"])
    print(f"Found {len(pairs)} Harmonix songs ({with_audio} with audio)")

    if not pairs:
        print("No Harmonix annotation files found.")
        sys.exit(1)

    tolerances = (0.5, 3.0)
    oracle_beats_dir = Path(args.harmonix_dir) if args.oracle_beats else None
    results = run_benchmark(
        pairs,
        weights=weights,
        tolerances=tolerances,
        oracle_beats_dir=oracle_beats_dir,
        algorithm=args.algorithm,
    )
    summary = _summarise(results, tolerances)
    effective_algorithms = _algorithm_counts(results)

    output = {
        "benchmark_date": time.strftime("%Y-%m-%d %H:%M"),
        "songs_evaluated": len(results),
        "algorithm": args.algorithm,
        "effective_algorithms": effective_algorithms,
        "weights": weights,
        "summary": summary,
        "per_song": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("\n" + "=" * 60)
    print("SECTION DETECTION BENCHMARK RESULTS")
    print("=" * 60)
    labels = {
        "detector": "Section Detector (new)",
        "detector_oracle": "Section Detector + Oracle Beat Snap",
        "prototype": "Flux Prototype (baseline)",
        "fixed_chunks": "Fixed 32s Chunks (naive)",
    }
    for method in ("detector", "detector_oracle", "prototype", "fixed_chunks"):
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
