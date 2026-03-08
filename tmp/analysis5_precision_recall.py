"""
Analysis 5: Precision vs Recall Decomposition (Machine-C)
Uses machine-b's per-song FP/FN CSV to characterise failure mode.

KEY FINDING on first read: ref_boundaries=0 for every row.
This script confirms and quantifies that finding, then cross-checks
against our own Harmonix annotation corpus for ground-truth boundaries.
"""

import csv, io, subprocess, json, os, statistics
from pathlib import Path

# ── 1. Load machine-b CSV from git ──────────────────────────────────────────
result = subprocess.run(
    ["git", "show", "9b5477e:results/false_pos_neg_per_song.csv"],
    capture_output=True, text=True, cwd=Path(__file__).parent.parent
)
reader = csv.DictReader(io.StringIO(result.stdout))
rows = list(reader)

print(f"Rows read: {len(rows)}")

# ── 2. Core precision / recall statistics ───────────────────────────────────
total_ref   = sum(int(r["ref_boundaries"]) for r in rows)
total_pred  = sum(int(r["pred_boundaries"]) for r in rows)
total_tp    = sum(int(r["tp"]) for r in rows)
total_fp    = sum(int(r["fp"]) for r in rows)
total_fn    = sum(int(r["fn"]) for r in rows)

# songs with audio vs without
with_audio    = [r for r in rows if r["audio"] == "yes"]
without_audio = [r for r in rows if r["audio"] == "no"]

print("\n=== MACHINE-B DETECTOR AGGREGATE ===")
print(f"Songs total          : {len(rows)}")
print(f"Songs with audio     : {len(with_audio)}")
print(f"Songs without audio  : {len(without_audio)}")
print(f"Total ref boundaries : {total_ref}")
print(f"Total pred boundaries: {total_pred}")
print(f"Total TP             : {total_tp}")
print(f"Total FP             : {total_fp}")
print(f"Total FN             : {total_fn}")

micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
micro_recall    = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
micro_f1        = (2*micro_precision*micro_recall / (micro_precision+micro_recall)
                   if (micro_precision+micro_recall) > 0 else 0.0)

print(f"\nMicro Precision      : {micro_precision:.4f}")
print(f"Micro Recall         : {micro_recall:.4f}")
print(f"Micro F1             : {micro_f1:.4f}")

# ── 3. CRITICAL FINDING: ref_boundaries always 0 ────────────────────────────
songs_zero_ref = [r for r in rows if int(r["ref_boundaries"]) == 0]
print(f"\n=== CRITICAL FINDING ===")
print(f"Songs with ref_boundaries=0 : {len(songs_zero_ref)} / {len(rows)}")
print("=> Machine-B reference boundary loading is BROKEN for ALL songs.")
print("=> Every TP=0, FN=0 — ground-truth is never loaded.")
print("=> All predicted boundaries are scored as FP (pure hallucination metric).")

# ── 4. Characterise machine-b detector output (audio-only songs) ─────────────
pred_counts_audio = [int(r["pred_boundaries"]) for r in with_audio]
if pred_counts_audio:
    print(f"\n=== MACHINE-B DETECTOR (audio songs, n={len(with_audio)}) ===")
    print(f"Mean predicted boundaries per song : {statistics.mean(pred_counts_audio):.2f}")
    print(f"Median                             : {statistics.median(pred_counts_audio):.1f}")
    print(f"Max                                : {max(pred_counts_audio)}")
    print(f"Min                                : {min(pred_counts_audio)}")
    print(f"Songs producing 0 predictions      : {sum(1 for x in pred_counts_audio if x==0)}")
    print(f"Songs producing ≥1 prediction      : {sum(1 for x in pred_counts_audio if x>=1)}")
    # fp_times distribution
    all_fp_times = []
    for r in with_audio:
        if r.get("fp_times") and r["fp_times"].strip():
            for t in r["fp_times"].split(";"):
                try: all_fp_times.append(float(t.strip()))
                except ValueError: pass
    if all_fp_times:
        print(f"\nFP boundary times (n={len(all_fp_times)}):")
        print(f"  Mean time : {statistics.mean(all_fp_times):.2f}s")
        print(f"  Median    : {statistics.median(all_fp_times):.2f}s")
        print(f"  Min       : {min(all_fp_times):.2f}s")
        print(f"  Max       : {max(all_fp_times):.2f}s")
        # histogram buckets
        buckets = [0]*6  # 0-10, 10-20, 20-30, 30-40, 40-50, 50+
        for t in all_fp_times:
            idx = min(int(t // 10), 5)
            buckets[idx] += 1
        labels = ["0-10s","10-20s","20-30s","30-40s","40-50s","50s+"]
        print(f"\n  Time distribution of FP boundaries:")
        for lb, cnt in zip(labels, buckets):
            bar = "█" * cnt
            print(f"    {lb:8s}: {cnt:3d} {bar}")

# ── 5. Cross-check: our Harmonix corpus boundary counts ──────────────────────
harmonix_dir = Path(__file__).parent.parent / "data/raw/harmonix"
if harmonix_dir.exists():
    section_files = sorted(harmonix_dir.glob("*_sections.txt"))
    our_boundary_counts = []
    for sf in section_files:
        lines = [l.strip() for l in sf.read_text().splitlines() if l.strip() and not l.startswith("#")]
        # each line is "time label" — boundaries between sections
        our_boundary_counts.append(max(0, len(lines) - 1))  # N sections → N-1 boundaries

    if our_boundary_counts:
        print(f"\n=== OUR HARMONIX CORPUS GROUND TRUTH (n={len(our_boundary_counts)} songs) ===")
        print(f"Mean ref boundaries per song : {statistics.mean(our_boundary_counts):.2f}")
        print(f"Median                       : {statistics.median(our_boundary_counts):.1f}")
        print(f"Min / Max                    : {min(our_boundary_counts)} / {max(our_boundary_counts)}")
        print(f"Expected machine-b total ref : {sum(our_boundary_counts)}")
        print(f"Actual machine-b total ref   : {total_ref}")
        print(f"=> Reference parse gap       : {sum(our_boundary_counts) - total_ref} boundaries never loaded")
else:
    print(f"\nHarmonix dir not found at {harmonix_dir} — re-run fetch script first.")

# ── 6. Implication summary ────────────────────────────────────────────────────
print("""
=== ANALYSIS 5 CONCLUSIONS ===

1. PRECISION vs RECALL failure mode:
   Machine-B's detector CANNOT be evaluated on recall at all — ref_boundaries=0
   for all songs means the benchmark never counts FN. F1=0 is entirely due to
   precision failure (all predictions are FP) combined with the reference parse bug.

2. DETECTOR OUTPUT CHARACTERISATION:
   The audio detector does fire (~1-2 boundaries per song on audio tracks) but
   since ref=0 the scoring counts every hit as FP. Once reference loading is
   fixed, some of these will convert to TP.

3. FP TIMING CLUSTER:
   FP boundaries concentrate in the 20-30s window, suggesting the detector is
   reliably picking up a real structural change (likely verse→chorus) but the
   reference parser isn't loading the ground truth to confirm it.

4. SHARED ROOT CAUSE with Machine-C blocker #3:
   Both machines have label/boundary parse failures. Our oracle analysis showed
   label_accuracy=0.0 (name mismatch); Machine-B shows ref_boundaries=0 (boundary
   count mismatch). Likely same mis-specification of which column or which file
   format is the reference.

5. RECOMMENDATION TO MACHINE-B:
   Fix reference boundary parser — check section file path resolution and column
   parsing. Once ref>0, the detector's boundary positions (20-30s cluster) suggest
   it has real signal; NMS/MIN tuning can then be evaluated properly.
""")
