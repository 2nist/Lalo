#!/usr/bin/env python3
"""Oracle upper-bound analysis for Machine C diagnostics.

Simulates what F1 scores would be achievable if:
  - Oracle-perfect: detector places boundaries at exact true positions
  - Oracle-NMS-limited: perfect boundaries but current NMS_DISTANCE_SEC applied
  - Oracle-min-filtered: perfect boundaries but MIN_SECTION_SEC filter applied
  - Combo: both filters applied together

This isolates how much ceiling NMS and MIN_SECTION_SEC suppress, without audio.
"""
from __future__ import annotations
from pathlib import Path
from statistics import mean, median, stdev
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
HARMONIX_DIR = ROOT / "data" / "raw" / "harmonix"

# Current detector parameters
NMS_DISTANCE_SEC = 16.0
MIN_SECTION_SEC = 8.0
MAX_SECTION_SEC = 90.0

# Benchmark tolerances
TOLERANCES = [0.5, 3.0]


def parse_sections(path: Path):
    rows = []
    with open(path) as f:
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
        sections.append({"start_s": row["start_s"], "end_s": end_s, "label": row["label"]})
    return sections


def boundaries(sections):
    if not sections:
        return []
    all_starts = sorted(set(round(s["start_s"], 3) for s in sections))
    first = min(s["start_s"] for s in sections)
    return [t for t in all_starts if t > first + 0.1]


def boundary_f1(ref_sections, pred_sections, tol):
    ref_b = boundaries(ref_sections)
    pred_b = boundaries(pred_sections)
    used = set()
    tp = 0
    for p in pred_b:
        best_i, best_d = None, float("inf")
        for i, r in enumerate(ref_b):
            if i in used:
                continue
            d = abs(p - r)
            if d <= tol and d < best_d:
                best_d, best_i = d, i
        if best_i is not None:
            used.add(best_i)
            tp += 1
    fp = len(pred_b) - tp
    fn = len(ref_b) - tp
    p = tp / len(pred_b) if pred_b else 0.0
    r = tp / len(ref_b) if ref_b else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}


def apply_nms(sections, min_gap):
    """Greedy NMS: keep highest-scoring (here: longest) with minimum gap."""
    if not sections:
        return sections
    scored = sorted(sections, key=lambda s: s["end_s"] - s["start_s"], reverse=True)
    kept = []
    for s in scored:
        mid = (s["start_s"] + s["end_s"]) / 2
        if all(abs(mid - (k["start_s"] + k["end_s"]) / 2) >= min_gap for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: s["start_s"])


def apply_length_filter(sections, min_s, max_s):
    return [s for s in sections if (s["end_s"] - s["start_s"]) >= min_s
            and (s["end_s"] - s["start_s"]) <= max_s]


section_files = sorted(HARMONIX_DIR.glob("*_sections.txt"))
print(f"Analyzing {len(section_files)} songs\n")

results = {
    "oracle_perfect":       {"0.5": [], "3.0": []},
    "oracle_nms_limited":   {"0.5": [], "3.0": []},
    "oracle_min_filtered":  {"0.5": [], "3.0": []},
    "oracle_combo":         {"0.5": [], "3.0": []},
    "fixed_chunks":         {"0.5": [], "3.0": []},
    "nms_suppressed_pct":   [],
    "min_filtered_pct":     [],
}

for sf in section_files:
    ref = parse_sections(sf)
    if len(ref) < 2:
        continue

    song_dur = ref[-1]["end_s"]

    # Fixed-chunk baseline (32s)
    t, chunks, i = 0.0, [], 1
    while t < song_dur:
        end = min(t + 32.0, song_dur)
        chunks.append({"start_s": t, "end_s": end, "label": f"Section {i}"})
        t, i = end, i + 1

    # Oracle: use ref sections as predictions
    oracle_all = ref  # perfect predictions
    oracle_nms = apply_nms(ref, NMS_DISTANCE_SEC)
    oracle_min = apply_length_filter(ref, MIN_SECTION_SEC, MAX_SECTION_SEC)
    oracle_combo = apply_nms(apply_length_filter(ref, MIN_SECTION_SEC, MAX_SECTION_SEC), NMS_DISTANCE_SEC)

    pct_nms_lost = 1.0 - len(oracle_nms) / len(ref) if ref else 0
    pct_min_lost = len([s for s in ref if (s["end_s"]-s["start_s"]) < MIN_SECTION_SEC]) / len(ref) if ref else 0
    results["nms_suppressed_pct"].append(pct_nms_lost)
    results["min_filtered_pct"].append(pct_min_lost)

    for tol in TOLERANCES:
        k = str(tol)
        results["oracle_perfect"][k].append(boundary_f1(ref, oracle_all, tol)["f1"])
        results["oracle_nms_limited"][k].append(boundary_f1(ref, oracle_nms, tol)["f1"])
        results["oracle_min_filtered"][k].append(boundary_f1(ref, oracle_min, tol)["f1"])
        results["oracle_combo"][k].append(boundary_f1(ref, oracle_combo, tol)["f1"])
        results["fixed_chunks"][k].append(boundary_f1(ref, chunks, tol)["f1"])

print("=" * 62)
print("ORACLE UPPER-BOUND ANALYSIS  (annotation-only, no audio)")
print("=" * 62)
print(f"{'Method':<28}  F1@0.5s  F1@3.0s")
print("-" * 62)

for key, label in [
    ("oracle_perfect",      "Oracle: perfect predictions"),
    ("oracle_nms_limited",  f"  - after NMS (gap={NMS_DISTANCE_SEC}s)"),
    ("oracle_min_filtered", f"  - after MIN filter ({MIN_SECTION_SEC}s)"),
    ("oracle_combo",        f"  - after BOTH filters"),
    ("fixed_chunks",        "Fixed-32s baseline (current)"),
]:
    f05 = mean(results[key]["0.5"])
    f30 = mean(results[key]["3.0"])
    print(f"  {label:<26}  {f05:.4f}   {f30:.4f}")

print()
nms_pct = mean(results["nms_suppressed_pct"]) * 100
min_pct = mean(results["min_filtered_pct"]) * 100
print(f"NMS suppresses on average {nms_pct:.0f}% of true sections per song")
print(f"MIN filter removes on average {min_pct:.0f}% of true sections per song")

print()
print("=" * 62)
print("RECOMMENDED PARAMETER CHANGES FOR MACHINE B")
print("=" * 62)
print(f"  NMS_DISTANCE_SEC:  {NMS_DISTANCE_SEC} -> 8.0  (median true gap is ~19.5s,")
print( "                              but 30% of boundaries are <16s apart)")
print(f"  MIN_SECTION_SEC:   {MIN_SECTION_SEC} -> 4.0  (13% of true sections are <8s)")
print()

# Simulate what oracle_combo looks like with new params
results2 = {"oracle_combo_new": {"0.5": [], "3.0": []}}
for sf in section_files:
    ref = parse_sections(sf)
    if len(ref) < 2:
        continue
    oracle_combo_new = apply_nms(apply_length_filter(ref, 4.0, MAX_SECTION_SEC), 8.0)
    for tol in TOLERANCES:
        k = str(tol)
        results2["oracle_combo_new"][k].append(boundary_f1(ref, oracle_combo_new, tol)["f1"])

f05_new = mean(results2["oracle_combo_new"]["0.5"])
f30_new = mean(results2["oracle_combo_new"]["3.0"])
f05_old = mean(results["oracle_combo"]["0.5"])
f30_old = mean(results["oracle_combo"]["3.0"])
print(f"  Oracle ceiling with current params:  F1@0.5s={f05_old:.4f}  F1@3.0s={f30_old:.4f}")
print(f"  Oracle ceiling with new params:      F1@0.5s={f05_new:.4f}  F1@3.0s={f30_new:.4f}")
print(f"  Ceiling gain from param fix alone:   F1@0.5s=+{f05_new-f05_old:.4f}  F1@3.0s=+{f30_new-f30_old:.4f}")
print()
print("  label_accuracy=0.0 is structurally guaranteed:")
print("  Detector emits 'Section 1/2/..' — ground truth uses 'verse/chorus/...'")
print("  Fix: add a post-hoc label classifier (repetition-based or rule-based)")
print("  This is Machine B scope — zero weight changes can fix a naming mismatch.")
