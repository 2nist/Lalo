#!/usr/bin/env python3
"""Train an XGBoost classifier on candidate features and derive linear weights.

Outputs:
  - results/xgb_feature_importances.json
  - results/learned_weights_xgb.json
  - results/section_bench.learned_weights_xgb.json (benchmark with weights derived)

Runs best inside the `lalo311` Conda env so audio deps import correctly.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np


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

    # fit on all data
    clf = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss", n_estimators=200, verbosity=0)
    clf.fit(X, y)

    return clf, scores


def normalize_importances_to_weights(importances, keys):
    # take importances for original 5 keys and normalise
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

    parser = argparse.ArgumentParser()
    parser.add_argument("--label-tol", type=float, default=0.5, help="label tolerance in seconds for positive examples")
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

    # run benchmark with these weights
    # build benchmark command passing explicit weights for all features
    cmd = (
        f"./miniconda3/envs/lalo311/bin/python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic "
        f"--weight-flux {learned.get('flux_peak', 0.0)} --weight-chord {learned.get('chord_novelty', 0.0)} "
        f"--weight-cadence {learned.get('cadence_score', 0.0)} --weight-repetition {learned.get('repetition_break', 0.0)} "
        f"--weight-duration {learned.get('duration_prior', 0.0)} "
        f"--weight-chroma {learned.get('chroma_change', 0.0)} --weight-spec-contrast {learned.get('spec_contrast', 0.0)} "
        f"--weight-onset-density {learned.get('onset_density', 0.0)} --weight-rms {learned.get('rms_energy', 0.0)} "
        f"--out results/section_bench.learned_weights_xgb.json"
    )
    print("Running benchmark with XGB-derived weights...")
    import subprocess
    subprocess.run(cmd, shell=True, check=True)
    print("Wrote results/section_bench.learned_weights_xgb.json")


if __name__ == "__main__":
    main()
