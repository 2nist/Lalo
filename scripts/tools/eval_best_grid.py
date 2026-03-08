#!/usr/bin/env python3
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _parse_harmonix_sections, _boundary_f1, HARMONIX_DIR, AUDIO_DIR

best = json.load(open('results/grid_search_weights.best.json'))
weights = best.get('weights')
print('Best grid weights:', weights)

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
wave9 = json.load(open('results/sections-machine-b-wave9.json'))
wave9_per = wave9.get('per_song', [])
wave9_audio_list = [p.get('audio') for p in wave9_per if p.get('audio')]
pair_map = {p.get('audio'): p for p in pairs if p.get('audio')}
with_audio = [pair_map[a] for a in wave9_audio_list if a in pair_map]

nms=8.0
min_sec=4.0
beat=0.0

out = {}
for prob in (0.5, 0.25, 0.15):
    tp=fp=fn=0
    preds=0; cnt=0
    for p in with_audio:
        audio = Path(p['audio'])
        ref = _parse_harmonix_sections(Path(p['sections_file']))
        res = detect_sections(audio, chords=None, weights=weights, min_section_sec=min_sec, nms_gap_sec=nms, beat_snap_sec=beat, algorithm='heuristic', prob_threshold=prob, random_seed=42)
        det_raw = res.get('sections', [])
        det = []
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s = float(s['start_ms'])/1000.0
                end_s = start_s + float(s['duration_ms'])/1000.0
                det.append({'start_s': start_s, 'end_s': end_s})
        b = _boundary_f1(ref, det, 0.5)
        tp += b['tp']; fp += b['fp']; fn += b['fn']; preds += b.get('pred_boundaries', 0); cnt += 1
    precision = round(tp/(tp+fp),4) if (tp+fp)>0 else 0.0
    recall = round(tp/(tp+fn),4) if (tp+fn)>0 else 0.0
    avg_pred = round(preds/cnt,3) if cnt>0 else 0.0
    out[str(prob)] = {'tp':tp,'fp':fp,'fn':fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred}

Path('results/grid_search_weights.best_eval.json').write_text(json.dumps(out, indent=2))
print('Wrote results/grid_search_weights.best_eval.json')
print(json.dumps(out, indent=2))
