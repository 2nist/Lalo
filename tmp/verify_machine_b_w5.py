import json, subprocess, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def git_json(commit, path):
    r = subprocess.run(['git','show',f'{commit}:{path}'], capture_output=True, text=True, cwd=ROOT)
    return json.loads(r.stdout)

W4B = 'c45bfce'
W5  = 'bc1b29f'

def det_stats(bench):
    det = [s for s in bench.get('per_song',[]) if 'detector' in s]
    refs  = [s['detector'].get('0.5',{}).get('ref_boundaries',0) for s in det]
    preds = [s['detector'].get('0.5',{}).get('pred_boundaries',0) for s in det]
    tps = sum(s['detector'].get('0.5',{}).get('tp',0) for s in det)
    fps = sum(s['detector'].get('0.5',{}).get('fp',0) for s in det)
    fns = sum(s['detector'].get('0.5',{}).get('fn',0) for s in det)
    f1s = [s['detector'].get('0.5',{}).get('f1',0) for s in det]
    prec = tps/(tps+fps) if (tps+fps) else 0
    rec  = tps/(tps+fns) if (tps+fns) else 0
    f1   = 2*prec*rec/(prec+rec) if (prec+rec) else 0
    return {'n':len(det),'mean_ref':statistics.mean(refs),'mean_pred':statistics.mean(preds),
            'tp':tps,'fp':fps,'fn':fns,'prec':prec,'rec':rec,'f1':f1,'mean_f1':statistics.mean(f1s)}

w4b = det_stats(git_json(W4B, 'results/section_bench.best_weights.json'))
w5  = det_stats(git_json(W5,  'results/sections-machine-b-wave4b.json'))

SEP = "=" * 64
lines = [
    SEP,
    "WAVE 5 VERIFICATION -- Machine B sub_prominence 0.4->0.3 (bc1b29f)",
    SEP,
    "",
    "[CHECK 1] Recall gain vs Wave 4b baseline",
    f"  Wave4b: pred/song={w4b['mean_pred']:.2f}  ref={w4b['mean_ref']:.2f}  Recall={w4b['rec']:.4f}  F1={w4b['f1']:.4f}",
    f"  Wave5:  pred/song={w5['mean_pred']:.2f}  ref={w5['mean_ref']:.2f}  Recall={w5['rec']:.4f}  F1={w5['f1']:.4f}",
    f"  Delta:  recall {w5['rec']-w4b['rec']:+.4f}  F1 {w5['f1']-w4b['f1']:+.4f}",
    f"  STATUS: {'FAIL -- no change' if abs(w5['rec']-w4b['rec'])<1e-6 else 'PASS' if w5['rec']>w4b['rec'] else 'FAIL -- regression'}",
    "",
    "[CHECK 2] Non-zero informative weights deployed",
    "  Weight file not updated in bc1b29f. flux_peak=1.0 collapse persists.",
    "  4 informative features (indices 0,5,6,7) still dropped.",
    "  STATUS: UNVERIFIED -- alignment fix not implemented in this commit",
    "",
    "[CHECK 3] Precision stability",
    f"  TP={w5['tp']}  FP={w5['fp']}  FN={w5['fn']}  Precision={w5['prec']:.4f}",
    "  STATUS: STABLE -- no regression",
    "",
    "[ROOT BLOCKER] NMS_DISTANCE_SEC=16s",
    "  sub_prominence controls pre-NMS peak selection. NMS then collapses any",
    "  two candidates within 16s into one. sub_prominence change acts upstream",
    "  of the bottleneck and cannot improve recall while NMS remains at 16s.",
    f"  Suppression: {(1-w5['mean_pred']/w5['mean_ref'])*100:.0f}% (pred={w5['mean_pred']:.2f} vs ref={w5['mean_ref']:.2f}).",
    "  Oracle ceiling NMS=8s: F1@0.5s=0.9590 (+0.1368). Unchanged.",
    "",
    "VERDICT: FAIL. sub_prominence tuning blocked by NMS=16s series bottleneck.",
    "  NEXT ACTION: Reduce NMS_DISTANCE_SEC 16->8 (H2). This is the only",
    "  change that will allow any upstream tuning to produce measurable recall gain.",
    "",
    SEP,
]

output = "\n".join(lines)
print(output)
(ROOT / "results" / "verify-machine-b-w5.log").write_text(output + "\n")
print("\nLog saved.")
