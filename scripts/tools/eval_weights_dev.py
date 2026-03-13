#!/usr/bin/env python3
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)

# Use Wave9 audio list
wave9 = json.load(open('results/sections-machine-b-wave9.json'))
wave9_per = wave9.get('per_song', [])
wave9_audio_list = [p.get('audio') for p in wave9_per if p.get('audio')]
pair_map = {p.get('audio'): p for p in pairs if p.get('audio')}
with_audio = [pair_map[a] for a in wave9_audio_list if a in pair_map]

grid = json.load(open('results/grid_search_dev.json'))
best = max(grid.get('results',[]), key=lambda r: r.get('mean_f1_0.5',0))
weights = best.get('weights')

print('Evaluating best dev weights:', weights)

nms=8.0
min_sec=4.0
beat=2.0
runs = [
    {'name':'dev_eval_a','prob_threshold':0.50},
    {'name':'dev_eval_b','prob_threshold':0.25},
    {'name':'dev_eval_c','prob_threshold':0.15},
]

Path('results').mkdir(parents=True,exist_ok=True)
all_out={}
for r in runs:
    prob_threshold=r['prob_threshold']
    tot_tp=tot_fp=tot_fn=0
    tot_preds=0
    count=0
    per_song=[]
    for p in with_audio:
        audio=Path(p['audio'])
        ref=_parse_harmonix_sections(Path(p['sections_file']))
        res=detect_sections(audio,chords=None,weights=weights,min_section_sec=min_sec,nms_gap_sec=nms,beat_snap_sec=beat,algorithm='heuristic',prob_threshold=prob_threshold,random_seed=42,downbeat_confidence_thresh=0.0)
        det_raw=res.get('sections',[])
        det=[]
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s=float(s['start_ms'])/1000.0
                end_s=start_s+float(s['duration_ms'])/1000.0
                det.append({'start_s':start_s,'end_s':end_s,'label':s.get('label','')})
        b=_boundary_f1(ref,det,0.5)
        tot_tp+=b['tp']; tot_fp+=b['fp']; tot_fn+=b['fn']; tot_preds+=b.get('pred_boundaries',0); count+=1
        per_song.append({'song':p.get('song_id') or p.get('sections_file'), 'tp':b['tp'],'fp':b['fp'],'fn':b['fn'],'pred_boundaries':b.get('pred_boundaries',0)})

    precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
    recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
    avg_pred=round(tot_preds/count,3) if count>0 else 0.0
    out={'prob_threshold':prob_threshold,'nms_gap_sec':nms,'min_section_sec':min_sec,'beat_snap_sec':beat,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred,'per_song':per_song}
    fname=f'results/dev_eval_{r["name"]}.json'
    Path(fname).write_text(json.dumps(out,indent=2))
    all_out[r['name']]=out
    print('Wrote',fname)

print('Dev evaluation summary:')
print(json.dumps({k:{'tp':v['tp'],'fp':v['fp'],'fn':v['fn'],'precision':v['precision'],'recall':v['recall'],'avg_pred_per_song':v['avg_pred_per_song']} for k,v in all_out.items()},indent=2))
