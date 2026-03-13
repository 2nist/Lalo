#!/usr/bin/env python3
"""Train XGBoost on Harmonix candidate features and save a pickled scorer.

Outputs:
  - data/training/scorer_gbt.pkl
  - results/xgb_feature_importances.json
  - results/learned_weights_xgb.json

This reuses the candidate gathering from the existing train_xgboost.py but
also serialises the trained classifier with joblib for use by
`scripts.analysis.section_detector.detect_sections(..., algorithm='scored')`.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure repo root is on sys.path so `scripts.*` imports work when run as a script
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from typing import List
import numpy as np

SCORER_PATH = Path("data/training/scorer_gbt.pkl")


def gather_candidates(pairs: List[dict], label_tol: float = 0.5):
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

        # get reference boundaries
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


def train_xgb(X, y):
    try:
        import xgboost as xgb
    except Exception as exc:
        raise SystemExit("xgboost not available in this env: " + str(exc))

    from sklearn.model_selection import StratifiedKFold
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import precision_recall_fscore_support

    if len(X) == 0:
        raise SystemExit("No training examples found")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
    scores = []
    for train_idx, test_idx in skf.split(X, y):
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        clf = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss", n_estimators=100, verbosity=0)
        clf.fit(Xtr, ytr)
        yp = clf.predict(Xte)
        p, r, f, _ = precision_recall_fscore_support(yte, yp, average="binary", zero_division=0)
        scores.append({"precision": float(p), "recall": float(r), "f1": float(f)})

    # fit base estimator on all data (returned to caller, calibration optional)
    base_clf = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss", n_estimators=200, verbosity=0)
    base_clf.fit(X, y)

    return base_clf, scores


def normalize_importances_to_weights(importances, keys):
    base = np.array([importances[i] for i in range(len(keys))], dtype=float)
    base = np.maximum(base, 0.0)
    s = base.sum()
    if s <= 0:
        base = np.abs(base) + 1e-8
        s = base.sum()
    w = (base / s).round(4).tolist()
    return dict(zip(keys, w))


def main():
    from scripts.bench.section_benchmark import _load_harmonix_pairs, HARMONIX_DIR, AUDIO_DIR
    import argparse
    import joblib

    parser = argparse.ArgumentParser()
    parser.add_argument("--label-tol", type=float, default=0.5, help="label tolerance in seconds for positive examples")
    parser.add_argument("--calibrate", action="store_true", help="Apply probability calibration to the trained estimator")
    parser.add_argument("--calib-method", choices=["sigmoid", "isotonic"], default="sigmoid", help="Calibration method for probability calibration")
    args = parser.parse_args()

    pairs = _load_harmonix_pairs(Path(HARMONIX_DIR), Path(AUDIO_DIR), max_songs=30)
    print(f"Gathering candidate features with label tolerance={args.label_tol}s...")
    X, y = gather_candidates(pairs, label_tol=args.label_tol)
    print("Examples:", len(X), "Positives:", int(y.sum()))

    clf, cv_scores = train_xgb(X, y)
    print("CV scores:", cv_scores)

    # get feature importances
    try:
        importances = clf.feature_importances_.tolist()
    except Exception:
        importances = [0.0] * X.shape[1]

    keys = ["flux_peak", "chord_novelty", "cadence_score", "repetition_break", "duration_prior", "chroma_change", "spec_contrast", "onset_density", "rms_energy"]
    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    Path("results/xgb_feature_importances.json").write_text(json.dumps({"keys": keys, "importances": importances, "cv_scores": cv_scores}, indent=2))

    # derive linear weights for all keys from importances
    learned = normalize_importances_to_weights(importances, keys)
    Path("results/learned_weights_xgb.json").write_text(json.dumps({"importances": importances, "weights": learned, "keys": keys}, indent=2))
    print("Learned weights (from XGBoost importances):", learned)

    # Optionally apply probability calibration if requested via CLI args
    final_clf = clf
    if args.calibrate:
        try:
            calib = CalibratedClassifierCV(base_estimator=type(clf)(), cv=3, method=args.calib_method)
            calib.fit(X, y)
            final_clf = calib
        except Exception:
            final_clf = clf

    SCORER_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_clf, str(SCORER_PATH))
    print(f"Saved scorer model to {SCORER_PATH}")


if __name__ == "__main__":
    main()
