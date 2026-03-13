#!/usr/bin/env python3
"""Compare two section benchmark JSON outputs and write per-song deltas as CSV.

Usage:
  python scripts/tools/compare_section_runs.py \
    --old results/sections-machine-b.json \
    --new results/sections-machine-b-promote-wave15-full.json \
    --out results/per_song_delta.csv
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Any


def load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_entry_map(data: Dict[str, Any]) -> Dict[str, Dict]:
    m = {}
    for e in data.get("per_song", []):
        m[e.get("id")] = e
    return m


def get_f1(entry: Dict, tol: str) -> float | None:
    if not entry:
        return None
    det = entry.get("detector")
    if not isinstance(det, dict):
        return None
    v = det.get(tol)
    if not isinstance(v, dict):
        return None
    return v.get("f1")


def get_pred_sections(entry: Dict) -> int | None:
    if not entry:
        return None
    det = entry.get("detector")
    if not isinstance(det, dict):
        return None
    return det.get("pred_sections")


def get_candidate_counts(entry: Dict) -> tuple[int | None, int | None]:
    if not entry:
        return (None, None)
    det = entry.get("detector")
    if not isinstance(det, dict):
        return (None, None)
    meta = det.get("meta", {}) or {}
    cand = meta.get("candidate_count")
    kept = meta.get("kept_count")
    return (cand, kept)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    p.add_argument("--out", default="results/per_song_delta.csv")
    args = p.parse_args()

    old = load(Path(args.old))
    new = load(Path(args.new))
    old_map = get_entry_map(old)
    new_map = get_entry_map(new)

    ids = sorted(set(list(old_map.keys()) + list(new_map.keys())))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline='', encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "id",
            "old_f1_3.0",
            "new_f1_3.0",
            "delta_f1_3.0",
            "old_f1_0.5",
            "new_f1_0.5",
            "delta_f1_0.5",
            "old_pred_sections",
            "new_pred_sections",
            "old_candidate_count",
            "new_candidate_count",
            "new_kept_count",
        ])

        for sid in ids:
            o = old_map.get(sid)
            n = new_map.get(sid)
            of3 = get_f1(o, "3.0")
            nf3 = get_f1(n, "3.0")
            of05 = get_f1(o, "0.5")
            nf05 = get_f1(n, "0.5")
            delta_f3 = (nf3 - of3) if (of3 is not None and nf3 is not None) else None
            delta_f05 = (nf05 - of05) if (of05 is not None and nf05 is not None) else None
            opred = get_pred_sections(o)
            npred = get_pred_sections(n)
            ocand, okept = get_candidate_counts(o)
            ncand, nkept = get_candidate_counts(n)
            writer.writerow([
                sid,
                "" if of3 is None else f"{of3:.4f}",
                "" if nf3 is None else f"{nf3:.4f}",
                "" if delta_f3 is None else f"{delta_f3:.4f}",
                "" if of05 is None else f"{of05:.4f}",
                "" if nf05 is None else f"{nf05:.4f}",
                "" if delta_f05 is None else f"{delta_f05:.4f}",
                "" if opred is None else str(opred),
                "" if npred is None else str(npred),
                "" if ocand is None else str(ocand),
                "" if ncand is None else str(ncand),
                "" if nkept is None else str(nkept),
            ])

    print(f"Wrote per-song delta CSV: {out_path}")


if __name__ == '__main__':
    main()
