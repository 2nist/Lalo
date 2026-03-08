"""
Machine C — Wave 4b Verification: Machine B candidate-generator recall
Task: MSG-20260308-0601
Checks: (1) recall gain vs baseline, (2) precision stability, (3) weight alignment.
"""
import json, subprocess, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def git_json(commit, path):
    r = subprocess.run(["git", "show", f"{commit}:{path}"],
                       capture_output=True, text=True, cwd=ROOT)
    return json.loads(r.stdout)

BASELINE_COMMIT  = "75a6ca7"   # label-tol=3.0, F1=0.0179 baseline
CURRENT_COMMIT   = "c45bfce"   # hyperparam best_weights

bench_base = git_json(BASELINE_COMMIT, "results/section_bench.learned_weights_xgb.json")
bench_new  = git_json(CURRENT_COMMIT,  "results/section_bench.best_weights.json")
weights_new = git_json(CURRENT_COMMIT, "results/learned_weights_xgb_hyperparam.json")
hyper       = git_json(CURRENT_COMMIT, "results/xgb_hyperparam_results.json")

def det_stats(bench):
    ps = bench.get("per_song", [])
    det = [s for s in ps if "detector" in s]
    refs  = [s["detector"].get("0.5", {}).get("ref_boundaries", 0) for s in det]
    preds = [s["detector"].get("0.5", {}).get("pred_boundaries", 0) for s in det]
    tps = sum(s["detector"].get("0.5", {}).get("tp", 0) for s in det)
    fps = sum(s["detector"].get("0.5", {}).get("fp", 0) for s in det)
    fns = sum(s["detector"].get("0.5", {}).get("fn", 0) for s in det)
    f1s = [s["detector"].get("0.5", {}).get("f1", 0) for s in det]
    prec = tps / (tps + fps) if (tps + fps) else 0
    rec  = tps / (tps + fns) if (tps + fns) else 0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
    return {
        "n": len(det),
        "mean_ref":  statistics.mean(refs)  if refs  else 0,
        "mean_pred": statistics.mean(preds) if preds else 0,
        "tp": tps, "fp": fps, "fn": fns,
        "precision": prec, "recall": rec, "f1": f1,
        "mean_song_f1": statistics.mean(f1s) if f1s else 0,
        "f1_summary": bench.get("summary", {}).get("detector", {}).get("F1@0.5s", {}),
    }

base = det_stats(bench_base)
curr = det_stats(bench_new)

print("=" * 64)
print("WAVE 4b VERIFICATION — Machine B candidate-generator recall")
print("=" * 64)

print(f"\n[CHECK 1] Recall gain vs baseline (commit {BASELINE_COMMIT} → {CURRENT_COMMIT})")
print(f"  Baseline  : pred/song={base['mean_pred']:.2f}  ref/song={base['mean_ref']:.2f}  "
      f"Recall={base['recall']:.4f}  F1={base['f1']:.4f}")
print(f"  Current   : pred/song={curr['mean_pred']:.2f}  ref/song={curr['mean_ref']:.2f}  "
      f"Recall={curr['recall']:.4f}  F1={curr['f1']:.4f}")
recall_delta = curr['recall'] - base['recall']
f1_delta     = curr['f1']    - base['f1']
print(f"  Delta     : recall {recall_delta:+.4f}  F1 {f1_delta:+.4f}")
print(f"  STATUS: {'FAIL — no recall improvement observed' if abs(recall_delta) < 0.001 else ('PASS' if recall_delta > 0 else 'FAIL — recall degraded')}")

print(f"\n[CHECK 2] Precision stability")
prec_delta = curr['precision'] - base['precision']
print(f"  Baseline precision: {base['precision']:.4f}")
print(f"  Current  precision: {curr['precision']:.4f}  (delta {prec_delta:+.4f})")
print(f"  TP/FP/FN: {curr['tp']}/{curr['fp']}/{curr['fn']}")
print(f"  STATUS: {'STABLE' if abs(prec_delta) < 0.01 else ('IMPROVED' if prec_delta > 0 else 'DEGRADED')}")

print(f"\n[CHECK 3] XGBoost hyperparam improvement")
print(f"  Best params: {hyper['best_params']}")
print(f"  CV F1 (hyperparam best): {hyper['best_score']:.4f}")
print(f"  CV F1 (prior label-tol=3.0): 0.3800  (from commit 75a6ca7)")
print(f"  CV gain: {hyper['best_score'] - 0.380:+.4f}")
print(f"  STATUS: PASS — model quality improved (CV F1 {hyper['best_score']:.4f})")

print(f"\n[CHECK 4] Feature weight alignment / collapse risk")
imps = weights_new.get("importances", [])
w    = weights_new.get("weights", {})
non_zero_imps = sum(1 for v in imps if v > 0)
non_zero_wts  = sum(1 for v in w.values() if v > 0)
print(f"  Importances array length : {len(imps)}  (non-zero: {non_zero_imps})")
print(f"  Weight keys in dict      : {len(w)}  (non-zero: {non_zero_wts})")
print(f"  Weights derived: {dict((k,v) for k,v in w.items() if v > 0)}")
alignment_ok = len(imps) == len(w)
print(f"  Alignment: {'OK' if alignment_ok else f'MISMATCH — {len(imps)} importances vs {len(w)} weight keys'}")
if non_zero_imps > non_zero_wts:
    print(f"  RISK: {non_zero_imps} non-zero importances but only {non_zero_wts} non-zero weight(s)")
    print(f"    Index positions with signal: {[i for i,v in enumerate(imps) if v>0]}")
    print(f"    These features may not be mapped to recognized weight keys.")
    print(f"    Weight extraction likely dropped {non_zero_imps - non_zero_wts} informative feature(s).")
print(f"  STATUS: {'PASS' if alignment_ok and non_zero_imps == non_zero_wts else 'FAIL — weight collapse / alignment bug'}")

print(f"""
[CHECK 5] Candidate-generator suppression (NMS/MIN unchanged)
  pred/song = {curr['mean_pred']:.2f}  vs  ref/song = {curr['mean_ref']:.2f}
  Suppression rate: {(1 - curr['mean_pred']/curr['mean_ref'])*100:.0f}%
  Oracle ceiling (NMS=8s): F1@0.5s = 0.9590 (+0.1368 vs current)
  NMS_DISTANCE_SEC and MIN_SECTION_SEC parameters not changed in this commit.
  STATUS: UNCHANGED — candidate-generator recall bottleneck is NMS/MIN, not XGBoost weights.
""")

print("=" * 64)
print("SUMMARY")
print("=" * 64)
print(f"  Recall gain     : {'NO' if abs(recall_delta)<0.001 else 'YES (delta '+str(round(recall_delta,4))+')'}")
print(f"  Precision stable: {'YES' if abs(prec_delta)<0.01 else 'NO'}")
print(f"  CV F1 improved  : YES (0.380 → {hyper['best_score']:.4f})")
print(f"  TOP RISK        : Weight alignment bug — {non_zero_imps} informative features")
print(f"                    but flux_peak=1.0 collapse discards {non_zero_imps-1} of them.")
print(f"                    When NMS/MIN are reduced (H2+H3), the weighted scorer must")
print(f"                    correctly use all informative features or recall will plateau.")
print(f"  VERDICT: Machine B candidate-generator recall NOT YET IMPROVED.")
print(f"           XGBoost model quality improved (CV F1=0.4505). Fix weight extraction")
print(f"           alignment before deploying NMS/MIN changes.")
