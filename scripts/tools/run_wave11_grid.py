#!/usr/bin/env python3
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
with_audio = [p for p in pairs if p.get('audio')]
learned=json.load(open('results/learned_weights_xgb.json'))
weights = learned.get('weights') if isinstance(learned, dict) and learned.get('weights') else learned

thresholds=[0.05,0.1,0.15,0.25]
# reuse previous params
nms=6.0
min_sec=4.0
beat=2.0

results=[]
for thr in thresholds:
    tot_tp=tot_fp=tot_fn=0
    tot_preds=0
    count=0
    for p in with_audio:
        audio=Path(p['audio'])
        ref=_parse_harmonix_sections(Path(p['sections_file']))
        res=detect_sections(audio,chords=None,weights=weights,min_section_sec=min_sec,nms_gap_sec=nms,beat_snap_sec=beat,algorithm='heuristic',prob_threshold=thr)
        det_raw=res.get('sections',[])
        det=[]
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s=float(s['start_ms'])/1000.0
                end_s=start_s+float(s['duration_ms'])/1000.0
                det.append({'start_s':start_s,'end_s':end_s,'label':s.get('label','')})
        b=_boundary_f1(ref,det,0.5)
        tot_tp+=b['tp']; tot_fp+=b['fp']; tot_fn+=b['fn']; tot_preds+=b.get('pred_boundaries',0); count+=1
    precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
    recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
    avg_pred=round(tot_preds/count,3) if count>0 else 0.0
    results.append({'prob_threshold':thr,'nms_gap_sec':nms,'min_section_sec':min_sec,'beat_snap_sec':beat,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred})

Path('results').mkdir(parents=True,exist_ok=True)
Path('results/grid_wave11_thresholds.json').write_text(json.dumps({'results':results},indent=2))
# csv
import csv
with open('results/grid_wave11_thresholds.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['prob_threshold','nms_gap_sec','min_section_sec','beat_snap_sec','tp','fp','fn','precision','recall','avg_pred_per_song'])
    w.writeheader()
    for r in results:
        w.writerow(r)
print('Wrote results/grid_wave11_thresholds.json and .csv')
print(json.dumps(results,indent=2))
