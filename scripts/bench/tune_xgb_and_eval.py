#!/usr/bin/env python3
"""Tune XGBoost (label_tol × class-weight) and evaluate Harmonix dev for each model.

Saves results to `results/xgb_tune_results.json` and keeps per-model pickles in
`data/training/scorer_gbt_tune_<i>.pkl`. Overwrites the active scorer at
`data/training/scorer_gbt.pkl` before each benchmark run so `--algorithm scored`
uses the intended model.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_recall_fscore_support
import numpy as np

SCORER_ACTIVE = Path("data/training/scorer_gbt.pkl")
OUT_RESULTS = Path("results/xgb_tune_results.json")
OUT_RESULTS.parent.mkdir(parents=True, exist_ok=True)


def gather_candidates(pairs, label_tol=0.5):
    from scripts.analysis.section_detector import detect_sections
    from scripts.bench.section_benchmark import _parse_harmonix_sections

    X = []
    y = []
    for p in pairs:
        audio = p.get("audio")
        if not audio:
            continue
        audio_path = Path(audio)
        try:
            res = detect_sections(audio_path, chords=None, weights=None, beat_snap_sec=0, algorithm="heuristic")
        except Exception as exc:
            print("detector error for", audio, exc)
            continue
        candidates = res.get("candidates", [])
        if not candidates:
            continue

        ref_secs = [s["start_s"] for s in _parse_harmonix_sections(Path(p["sections_file"]))]
        ref_secs = sorted([t for t in ref_secs if t > 0.1])

        for c in candidates:
            t = float(c.get("time_s", 0.0))
            feats = c.get("features", {})
            vec = [
                feats.get("flux_peak", 0.0),
                feats.get("chord_novelty", 0.0),
                feats.get("cadence_score", 0.0),
                feats.get("repetition_break", 0.0),
                feats.get("duration_prior", 0.0),
                feats.get("chroma_change", 0.0),
                feats.get("spec_contrast", 0.0),
                feats.get("onset_density", 0.0),
                feats.get("rms_energy", 0.0),
            ]
            label = 0
            for r in ref_secs:
                if abs(t - r) <= float(label_tol):
                    label = 1
                    break
            X.append(vec)
            y.append(label)
    return np.array(X, dtype=float), np.array(y, dtype=int)


def train_xgb(X, y, scale_pos_weight=None):
    import xgboost as xgb

    if len(X) == 0:
        raise SystemExit("No training examples found")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
    scores = []
    for train_idx, test_idx in skf.split(X, y):
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        params = {"use_label_encoder": False, "eval_metric": "logloss", "n_estimators": 100, "verbosity": 0}
        if scale_pos_weight is not None:
            params["scale_pos_weight"] = float(scale_pos_weight)
        clf = xgb.XGBClassifier(**params)
        clf.fit(Xtr, ytr)
        yp = clf.predict(Xte)
        p, r, f, _ = precision_recall_fscore_support(yte, yp, average="binary", zero_division=0)
        scores.append({"precision": float(p), "recall": float(r), "f1": float(f)})

    # final fit on all
    params = {"use_label_encoder": False, "eval_metric": "logloss", "n_estimators": 200, "verbosity": 0}
    if scale_pos_weight is not None:
        params["scale_pos_weight"] = float(scale_pos_weight)
    clf = xgb.XGBClassifier(**params)
    clf.fit(X, y)
    return clf, scores


def run_benchmark_with_model(model_path: Path, out_json: Path) -> Dict:
    # copy model to active scorer path
    SCORER_ACTIVE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(model_path), str(SCORER_ACTIVE))
    # run section_benchmark.py --dev-only --algorithm scored
    cmd = [sys.executable, "scripts/bench/section_benchmark.py", "--dev-only", "--algorithm", "scored", "--out", str(out_json)]
    subprocess.run(cmd, check=True)
    # load output
    data = json.loads(out_json.read_text(encoding='utf-8'))
    return data


def main():
    from scripts.bench.section_benchmark import _load_harmonix_pairs, HARMONIX_DIR, AUDIO_DIR

    pairs = _load_harmonix_pairs(Path(HARMONIX_DIR), Path(AUDIO_DIR), max_songs=30)

    label_tols = [0.25, 0.5, 1.0]
    use_scale = [False, True]

    results: List[Dict] = []

    for i, lt in enumerate(label_tols):
        print(f"Gathering candidates (label_tol={lt})...")
        X, y = gather_candidates(pairs, label_tol=lt)
        n_pos = int(y.sum())
        n_neg = len(y) - n_pos
        print(f"Examples: {len(X)}, positives: {n_pos}")
        if len(X) == 0:
            continue
        for use_sw in use_scale:
            if use_sw and n_pos > 0:
                sw = max(1.0, float(n_neg) / max(1.0, float(n_pos)))
            else:
                sw = None
            print(f"Training model (label_tol={lt}, scale_pos_weight={sw})...")
            clf, cv_scores = train_xgb(X, y, scale_pos_weight=sw)
            import joblib
            model_path = Path(f"data/training/scorer_gbt_tune_lt{lt}_sw{int(sw) if sw else 0}.pkl")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(clf, str(model_path))
            bench_out = Path(f"results/harmonix_dev_xgb_tune_lt{lt}_sw{int(sw) if sw else 0}.json")
            print("Evaluating Harmonix dev with this model...")
            data = run_benchmark_with_model(model_path, bench_out)
            f1_3 = data.get("summary", {}).get("detector", {}).get("F1@3.0s", {}).get("mean")
            results.append({
                "label_tol": lt,
                "scale_pos_weight": sw,
                "cv_scores": cv_scores,
                "harmonix_summary": data.get("summary"),
                "harmonix_out": str(bench_out),
                "model_path": str(model_path),
            })
            OUT_RESULTS.write_text(json.dumps(results, indent=2))
            print(f"Recorded result: label_tol={lt}, sw={sw}, F1@3.0={f1_3}")

    print("Tuning complete. Results written to", OUT_RESULTS)


if __name__ == "__main__":
    main()
