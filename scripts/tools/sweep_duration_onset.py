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
audio_list = [p.get('audio') for p in per if p.get('audio')]

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
pair_map = {p.get('audio'): p for p in pairs if p.get('audio')}
with_audio = [pair_map[a] for a in audio_list if a in pair_map]

# sweep ranges
duration_offsets = [0.06, 0.08, 0.10, 0.12]
min_avg_spec_onsets = [0.30, 0.35, 0.40, 0.45]

nms=8.0
min_sec=4.0
beat=0.0
prob_threshold=0.50
seed=42

Path('results').mkdir(parents=True,exist_ok=True)
results_out = []
for off in duration_offsets:
    for gate in min_avg_spec_onsets:
        w = dict(weights)
        w['duration_prior'] = round(w.get('duration_prior',0.0) + off,4)
        tot_tp=tot_fp=tot_fn=0
        tot_preds=0
        count=0
        for p in with_audio:
            audio=Path(p['audio'])
            ref=_parse_harmonix_sections(Path(p['sections_file']))
            res=detect_sections(audio,chords=None,weights=w,min_section_sec=min_sec,nms_gap_sec=nms,beat_snap_sec=beat,algorithm='heuristic',prob_threshold=prob_threshold,random_seed=seed,downbeat_confidence_thresh=0.4,min_avg_spec_onset=gate)
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
        avg_pred=round(tot_preds/count,3) if count>0 else 0.0
        results_out.append({'duration_offset':off,'min_avg_spec_onset':gate,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred})
        print(f"off={off} gate={gate} tp={tot_tp} fp={tot_fp} avg_pred={avg_pred}")

Path('results/sweep_duration_onset.json').write_text(json.dumps(results_out,indent=2))
print('Wrote results/sweep_duration_onset.json')
