#!/usr/bin/env python3
"""Wave15 run with duration_prior = wave9 + 0.12 and min_avg_spec_onset=0.40.

Runs A/B (prob=0.50 and 0.25) and writes results/sections-machine-b-wave15d12-*.json
"""
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

wave9_path = Path('results/sections-machine-b-wave9.json')
if not wave9_path.exists():
    raise SystemExit('Missing baseline results/sections-machine-b-wave9.json')
wave9 = json.loads(wave9_path.read_text())
weights = wave9.get('weights') or {}
per = wave9.get('per_song', [])
audio_list = [p.get('audio') for p in per if p.get('audio')]

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
pair_map = {p.get('audio'): p for p in pairs if p.get('audio')}
with_audio = [pair_map[a] for a in audio_list if a in pair_map]

# override duration_prior to +0.12 from baseline
weights['duration_prior'] = round(weights.get('duration_prior', 0.0) + 0.12, 4)

nms=8.0
min_sec=4.0
beat=0.0
downbeat_confidence=0.4
min_avg_gate=0.40

runs = [
    {'name':'wave15d12a','prob_threshold':0.50},
    {'name':'wave15d12b','prob_threshold':0.25},
]

Path('results').mkdir(parents=True,exist_ok=True)
seed = 42
for r in runs:
    prob_threshold = r['prob_threshold']
    tot_tp=tot_fp=tot_fn=0
    tot_preds=0
    per_song=[]
    trace_dir = Path(f'results/traces/{r["name"]}')
    trace_dir.mkdir(parents=True, exist_ok=True)
    for p in with_audio:
        audio=Path(p['audio'])
        ref=_parse_harmonix_sections(Path(p['sections_file']))
        trace_path = trace_dir / f"{audio.stem}.trace.json"
        res=detect_sections(audio,chords=None,weights=weights,min_section_sec=min_sec,nms_gap_sec=nms,beat_snap_sec=beat,algorithm='heuristic',prob_threshold=prob_threshold,random_seed=seed,trace_path=trace_path,downbeat_confidence_thresh=downbeat_confidence,min_avg_spec_onset=min_avg_gate)
        det_raw=res.get('sections',[])
        det=[]
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s=float(s['start_ms'])/1000.0
                end_s=start_s+float(s['duration_ms'])/1000.0
                det.append({'start_s':start_s,'end_s':end_s})
        b=_boundary_f1(ref,det,0.5)
        tot_tp+=b['tp']; tot_fp+=b['fp']; tot_fn+=b['fn']; tot_preds+=b.get('pred_boundaries',0)
        per_song.append({'song':p.get('song_id') or p.get('sections_file'), 'tp':b['tp'],'fp':b['fp'],'fn':b['fn'],'pred_boundaries':b.get('pred_boundaries',0)})

    precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
    recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
    avg_pred=round(tot_preds/len(with_audio),3) if len(with_audio)>0 else 0.0
    out={'prob_threshold':prob_threshold,'nms_gap_sec':nms,'min_section_sec':min_sec,'beat_snap_sec':beat,'downbeat_confidence_thresh':downbeat_confidence,'min_avg_spec_onset':min_avg_gate,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred,'per_song':per_song}
    fname = f'results/sections-machine-b-{r["name"]}.json'
    Path(fname).write_text(json.dumps(out,indent=2))
    print('Wrote',fname,'traces->',trace_dir)
