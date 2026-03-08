#!/usr/bin/env python3
"""Wave 15: Parity + ablation vs Wave 9 baseline.

Runs:
    A: prob_threshold=0.50 (parity)
    B: prob_threshold=0.25 (ablation)

This runner now encodes the conservative Wave15 champion promoted in
MSG-20260308-1902 (docs/planning/machines/comms/live/machine-b.md):

- Promoted params (conservative champion):
    - `duration_prior` = Wave9 + 0.10
    - `min_avg_spec_onset` = 0.40 (gated rule: avg >= gate OR chord_novelty>0 OR cadence>0)
    - `nms_gap_sec` = 8.0
    - `min_section_sec` = 4.0
    - `downbeat_confidence_thresh` = 0.4

Behavior and artifacts:
- Writes per-run JSON summaries to `results/sections-machine-b-wave15*.json`.
- Writes per-song trace dumps to `results/traces/<run>/` for auditability.
- See results/sections-machine-b-wave15a.json and results/sections-machine-b-wave15d12a.json for parity validation.

Keep algorithm pinned to `heuristic`. This runner intentionally performs only
threshold/validation-style runs; geometry/model tuning happens elsewhere.
"""
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

# Load Wave9 baseline weights and song list
wave9_path = Path('results/sections-machine-b-wave9.json')
if not wave9_path.exists():
    raise SystemExit('Missing baseline results/sections-machine-b-wave9.json')
wave9 = json.loads(wave9_path.read_text())
weights = wave9.get('weights') or {}
per = wave9.get('per_song', [])
audio_list = [p.get('audio') for p in per if p.get('audio')]

# Promote modest duration_prior bump discovered in Wave15 grid sweep
# (keeps baseline geometry but improves TP/FP trade-off)
weights['duration_prior'] = round(weights.get('duration_prior', 0.0) + 0.1, 4)

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
pair_map = {p.get('audio'): p for p in pairs if p.get('audio')}
with_audio = [pair_map[a] for a in audio_list if a in pair_map]

nms=8.0
min_sec=4.0
beat=0.0
downbeat_confidence=0.4

runs = [
    {'name':'wave15a','prob_threshold':0.50},
    {'name':'wave15b','prob_threshold':0.25},
]

Path('results').mkdir(parents=True,exist_ok=True)
all_out = {}
seed = 42
for r in runs:
    prob_threshold=r['prob_threshold']
    tot_tp=tot_fp=tot_fn=0
    tot_preds=0
    count=0
    per_song=[]
    lines=[]
    trace_dir = Path(f'results/traces/{r["name"]}')
    trace_dir.mkdir(parents=True, exist_ok=True)
    lines.append(f"Run: {r['name']} prob_threshold={prob_threshold} nms_gap={nms} min_section={min_sec} beat_snap={beat} seed={seed}\n")
    for p in with_audio:
        audio=Path(p['audio'])
        ref=_parse_harmonix_sections(Path(p['sections_file']))
        trace_path = trace_dir / f"{audio.stem}.trace.json"
        res=detect_sections(audio,chords=None,weights=weights,min_section_sec=min_sec,nms_gap_sec=nms,beat_snap_sec=beat,algorithm='heuristic',prob_threshold=prob_threshold,random_seed=seed,trace_path=trace_path,downbeat_confidence_thresh=downbeat_confidence,min_avg_spec_onset=0.40)
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
        lines.append(json.dumps({'song':p.get('song_id') or p.get('sections_file'),'tp':b['tp'],'fp':b['fp'],'fn':b['fn'],'pred_boundaries':b.get('pred_boundaries',0),'prob_threshold':prob_threshold}))

    precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
    recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
    avg_pred=round(tot_preds/count,3) if count>0 else 0.0
    out={'prob_threshold':prob_threshold,'nms_gap_sec':nms,'min_section_sec':min_sec,'beat_snap_sec':beat,'downbeat_confidence_thresh':downbeat_confidence,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred,'per_song':per_song}
    fname = f'results/sections-machine-b-{r["name"]}.json'
    Path(fname).write_text(json.dumps(out,indent=2))
    logname = f'results/wave15_{r["name"]}.log'
    Path(logname).write_text('\n'.join(lines))
    all_out[r['name']]=out
    print('Wrote',fname,'and',logname,'traces->',trace_dir)

# write combined note
note = []
note.append('# Machine B Wave 15 Note\n')
for name,data in all_out.items():
    note.append(f'## {name}\n')
    note.append(f'prob_threshold: {data["prob_threshold"]}\n')
    note.append(f'TP: {data["tp"]}\n')
    note.append(f'FP: {data["fp"]}\n')
    note.append(f'FN: {data["fn"]}\n')
    note.append(f'Precision: {data["precision"]}\n')
    note.append(f'Recall: {data["recall"]}\n')
    note.append(f'Avg predictions per song: {data["avg_pred_per_song"]}\n')
    note.append(f'log: results/wave15_{name}.log\n\n')

Path('results/machine-b-wave15-note.md').write_text('\n'.join(note))
print('Wrote results/machine-b-wave15-note.md')
