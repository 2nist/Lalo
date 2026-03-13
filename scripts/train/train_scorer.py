#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import joblib
import numpy as np
import json
from pathlib import Path
from typing import List

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedShuffleSplit

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


def _load_dataset(path: Path) -> np.ndarray:
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    if not rows:
        raise ValueError("No rows found in dataset.")
    X = np.array([[float(row[col]) for col in FEATURE_COLUMNS] for row in rows])
    y = np.array([int(row["label"]) for row in rows])
    return X, y


def _compute_sample_weights(y: np.ndarray) -> np.ndarray:
    unique, counts = np.unique(y, return_counts=True)
    freq = {cls: cnt for cls, cnt in zip(unique, counts)}
    weights = np.array([len(y) / freq[val] for val in y])
    return weights


def main() -> None:
    parser = argparse.ArgumentParser(description="Train GradientBoosting scorer.")
    parser.add_argument("--data", type=Path, required=True, help="Candidate CSV path.")
    parser.add_argument("--out", type=Path, required=True, help="Output model path.")
    args = parser.parse_args()

    X, y = _load_dataset(args.data)
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, val_idx = next(sss.split(X, y))
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    sample_weight = _compute_sample_weights(y_train)

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train, sample_weight=sample_weight)

    train_pred = model.predict(X_train)
    val_pred = model.predict(X_val)
    train_f1 = f1_score(y_train, train_pred)
    val_f1 = f1_score(y_val, val_pred)

    importances = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.out)

    print(f"train f1: {train_f1:.4f}")
    print(f"val f1: {val_f1:.4f}")
    print("top features:")
    for name, score in importances:
        print(f"  {name}: {score:.4f}")


if __name__ == "__main__":
    import csv  # ensure csv imported when running as script

    main()
