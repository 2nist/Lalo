#!/usr/bin/env python3
import json
from pathlib import Path
import sys
ROOT=Path('.').resolve()
sys.path.insert(0,str(ROOT))
from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections
try:
    from scripts.bench.salami_benchmark import _parse_salami_sections
except Exception:
    _parse_salami_sections = None

# Determine pilot set: prefer existing salami_pilot20.json if present
pilot_file = Path('results/salami_pilot20.json')
pairs = []
if pilot_file.exists():
    j = json.loads(pilot_file.read_text())
    per = j.get('per_song', [])
    pairs = [p for p in per if p.get('audio')]
else:
    pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=20)

weights = {}
if Path('results/learned_weights_xgb.json').exists():
    wj = json.loads(Path('results/learned_weights_xgb.json').read_text())
    weights = wj.get('weights') if isinstance(wj, dict) else wj

nms_list = [8.0, 12.0, 16.0]
min_sec_list = [4.0, 6.0, 8.0]
prom_list = [0.18, 0.25, 0.35]
sub_list = [0.3, 0.25, 0.2]

Path('results').mkdir(parents=True, exist_ok=True)
out = []
count_total = len(pairs)
for nms in nms_list:
    for min_sec in min_sec_list:
        for prom in prom_list:
            for sub in sub_list:
                tot_tp=tot_fp=tot_fn=0
                tot_preds=0
                count=0
                for p in pairs:
                    audio = p.get('audio') or p.get('audio_path') or p.get('file')
                    if not audio:
                        continue
                    audio_path = Path(audio)
                    # Parse reference: prefer SALAMI-style annotation if available
                    ann_path = p.get('annotation') or p.get('sections_file') or p.get('sections') or p.get('annotation_file')
                    if ann_path and str(ann_path).lower().endswith('.json') and _parse_salami_sections is not None:
                        try:
                            ref = _parse_salami_sections(Path(ann_path))
                        except Exception:
                            # fallback to harmonix parser
                            try:
                                ref = _parse_harmonix_sections(Path(ann_path))
                            except Exception:
                                continue
                    else:
                        try:
                            ref = _parse_harmonix_sections(Path(ann_path))
                        except Exception:
                            # try fields present in bench loader
                            try:
                                ref = _parse_harmonix_sections(Path(p['sections_file']))
                            except Exception:
                                continue
                    try:
                        res = detect_sections(audio_path, chords=None, weights=weights or None, min_section_sec=min_sec, nms_gap_sec=nms, beat_snap_sec=2.0, algorithm='heuristic', prob_threshold=0.0, random_seed=42, cand_prominence=prom, cand_sub_prominence=sub)
                    except Exception as e:
                        print('detect error', audio_path, e)
                        continue
                    det_raw = res.get('sections', [])
                    det = []
                    for ss in det_raw:
                        if 'start_ms' in ss and 'duration_ms' in ss:
                            start_s = float(ss['start_ms'])/1000.0
                            end_s = start_s + float(ss['duration_ms'])/1000.0
                            det.append({'start_s': start_s, 'end_s': end_s})
                    b = _boundary_f1(ref, det, 0.5)
                    tot_tp += b['tp']; tot_fp += b['fp']; tot_fn += b['fn']; tot_preds += b.get('pred_boundaries', 0); count += 1
                precision = round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
                recall = round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
                f1 = round((2*precision*recall)/(precision+recall),4) if (precision+recall)>0 else 0.0
                avg_pred = round(tot_preds/count,3) if count>0 else 0.0
                rec = {'nms_gap_sec':nms,'min_section_sec':min_sec,'prominence':prom,'sub_prominence':sub,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'f1':f1,'avg_pred_per_song':avg_pred,'songs_evaluated':count}
                out.append(rec)
                print(f"nms={nms} min={min_sec} prom={prom} sub={sub} tp={tot_tp} fp={tot_fp} avg_pred={avg_pred} f1={f1}")

Path('results/sweep_candidate_prune.json').write_text(json.dumps(out, indent=2))
print('Wrote results/sweep_candidate_prune.json')
