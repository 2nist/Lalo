#!/usr/bin/env python3
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

# Load Wave9 baseline
wave9_path = Path('results/sections-machine-b-wave9.json')
if not wave9_path.exists():
    raise SystemExit('Missing baseline results/sections-machine-b-wave9.json')
wave9 = json.loads(wave9_path.read_text())
weights = wave9.get('weights') or {}
per = wave9.get('per_song', [])
ids = [p.get('id') for p in per if p.get('id')]

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
# map by id
pair_map = {p.get('id'): p for p in pairs if p.get('id')}
with_audio = [pair_map[i] for i in ids if i in pair_map]

print('with_audio_count', len(with_audio))

prob_thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]

nms=8.0
min_sec=4.0
beat=0.0
seed=42

Path('results').mkdir(parents=True,exist_ok=True)
results_out = []
for pt in prob_thresholds:
    tot_tp=tot_fp=tot_fn=0
    tot_preds=0
    count=0
    for p in with_audio:
        audio_path = p.get('audio')
        if not audio_path:
            continue
        try:
            audio = Path(audio_path)
        except Exception:
            continue
        try:
            ref = _parse_harmonix_sections(Path(p['sections_file']))
        except Exception:
            continue
        try:
            res = detect_sections(audio, chords=None, weights=weights, min_section_sec=min_sec, nms_gap_sec=nms, beat_snap_sec=beat, algorithm='heuristic', prob_threshold=pt, random_seed=seed, downbeat_confidence_thresh=0.4)
        except Exception as e:
            print('error detect_sections for id', p.get('id'), e)
            continue
        det_raw=res.get('sections',[])
        det=[]
        for ss in det_raw:
            if 'start_ms' in ss and 'duration_ms' in ss:
                start_s=float(ss['start_ms'])/1000.0
                end_s=start_s+float(ss['duration_ms'])/1000.0
                det.append({'start_s':start_s,'end_s':end_s})
        b=_boundary_f1(ref,det,0.5)
        tot_tp+=b['tp']; tot_fp+=b['fp']; tot_fn+=b['fn']; tot_preds+=b.get('pred_boundaries',0); count+=1
    precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
    recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
    f1=round((2*precision*recall)/(precision+recall),4) if (precision+recall)>0 else 0.0
    avg_pred=round(tot_preds/count,3) if count>0 else 0.0
    results_out.append({'prob_threshold':pt,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'f1':f1,'avg_pred_per_song':avg_pred})
    print(f"pt={pt} tp={tot_tp} fp={tot_fp} avg_pred={avg_pred} f1={f1}")

Path('results/sweep_prob_threshold_fine.json').write_text(json.dumps(results_out,indent=2))
print('Wrote results/sweep_prob_threshold_fine.json')
