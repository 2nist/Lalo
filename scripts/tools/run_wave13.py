#!/usr/bin/env python3
import json
from pathlib import Path
import sys
from datetime import datetime
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

# Load Wave 9 baseline songs and metrics
wave9 = json.load(open('results/sections-machine-b-wave9.json'))
wave9_per = wave9.get('per_song', [])
# Build ordered list of audio paths used in Wave9 (only those with audio)
wave9_audio_list = [p.get('audio') for p in wave9_per if p.get('audio')]

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
# Build a mapping from audio path to pair entry for quick lookup
pair_map = {p.get('audio'): p for p in pairs if p.get('audio')}

# Create the dev song list exactly matching Wave9 ordering (only keep if present in current pairs)
with_audio = [pair_map[a] for a in wave9_audio_list if a in pair_map]

learned=json.load(open('results/learned_weights_xgb.json'))
weights = learned.get('weights') if isinstance(learned, dict) and learned.get('weights') else learned

nms=8.0
min_sec=4.0
beat=2.0

runs = [
    {'name':'wave13a','prob_threshold':0.50},
    {'name':'wave13b','prob_threshold':0.25}
]

Path('results').mkdir(parents=True,exist_ok=True)
all_out = {}
# Save verbose logs per run
for r in runs:
    prob_threshold=r['prob_threshold']
    tot_tp=tot_fp=tot_fn=0
    tot_preds=0
    count=0
    per_song=[]
    lines=[]
    lines.append(f"Run: {r['name']} prob_threshold={prob_threshold} nms_gap={nms} min_section={min_sec} beat_snap={beat} \n")
    for p in with_audio:
        audio=Path(p['audio'])
        ref=_parse_harmonix_sections(Path(p['sections_file']))
        res=detect_sections(audio,chords=None,weights=weights,min_section_sec=min_sec,nms_gap_sec=nms,beat_snap_sec=beat,algorithm='heuristic',prob_threshold=prob_threshold)
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
        # verbose per-song line
        lines.append(json.dumps({'song':p.get('song_id') or p.get('sections_file'),'tp':b['tp'],'fp':b['fp'],'fn':b['fn'],'pred_boundaries':b.get('pred_boundaries',0),'requested_algorithm':'heuristic','prob_threshold':prob_threshold}))

    precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
    recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
    avg_pred=round(tot_preds/count,3) if count>0 else 0.0
    out={'prob_threshold':prob_threshold,'nms_gap_sec':nms,'min_section_sec':min_sec,'beat_snap_sec':beat,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred,'per_song':per_song}
    fname = f'results/sections-machine-b-{r["name"]}.json'
    Path(fname).write_text(json.dumps(out,indent=2))
    # write verbose run log
    logname = f'results/wave13_{r["name"]}.log'
    with open(logname,'w') as f:
        f.write('\n'.join(lines))
    all_out[r['name']] = out
    print('Wrote',fname,'and',logname)

# Validations
# Wave9 targets
wave9_target = {'tp':3,'fp':29,'f1_0.5_mean':wave9.get('summary',{}).get('detector',{}).get('F1@0.5s',{}).get('mean')}

validations = {}
# Check reproduction for wave13a vs wave9 targets
a = all_out.get('wave13a')
if a:
    reproduce_match = (a['tp']==wave9_target['tp'] and a['fp']==wave9_target['fp'] and abs(a.get('precision',0) - round(wave9.get('summary',{}).get('detector',{}).get('F1@0.5s',{}).get('mean',0),4))<=0.02)
    validations['wave13a_reproduces_wave9'] = reproduce_match

# monotonicity: FP_B >= FP_A and pred_B >= pred_A
b = all_out.get('wave13b')
if a and b:
    monotonic_fp = (b['fp'] >= a['fp'])
    monotonic_pred = (b['avg_pred_per_song'] >= a['avg_pred_per_song'])
    validations['monotonic_fp'] = monotonic_fp
    validations['monotonic_pred'] = monotonic_pred

# write combined note with logs and validations
note = []
note.append(f"# Machine B Wave 13 Note\n")
note.append(f"benchmark_date: {datetime.utcnow().isoformat()}Z\n")
note.append(f"wave9_target: {json.dumps(wave9_target)}\n")
for name, data in all_out.items():
    note.append(f"## {name}\n")
    note.append(f"prob_threshold: {data['prob_threshold']}\n")
    note.append(f"TP: {data['tp']}\n")
    note.append(f"FP: {data['fp']}\n")
    note.append(f"FN: {data['fn']}\n")
    note.append(f"Precision: {data['precision']}\n")
    note.append(f"Recall: {data['recall']}\n")
    note.append(f"Avg predictions per song: {data['avg_pred_per_song']}\n")
    note.append(f"log: results/wave13_{name}.log\n\n")

note.append("## Validations\n")
for k,v in validations.items():
    note.append(f"- {k}: {v}\n")

note.append('\n## Active weights and keys\n')
note.append(json.dumps(learned,indent=2))

Path('results/machine-b-wave13-note.md').write_text('\n'.join(note))
print('Wrote results/machine-b-wave13-note.md')
print(json.dumps({'summary':{k:{'tp':v['tp'],'fp':v['fp'],'fn':v['fn'],'precision':v['precision'],'recall':v['recall'],'avg_pred_per_song':v['avg_pred_per_song']} for k,v in all_out.items()},'validations':validations},indent=2))
