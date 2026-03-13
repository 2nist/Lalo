#!/usr/bin/env python3
import json
from pathlib import Path
import time
from statistics import mean, median

ROOT = Path('.').resolve()
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections
from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1, _label_accuracy

OUT = Path('results') / 'salami_validate_combo.json'

weights = {
    'flux_peak': 0.4118,
    'chord_novelty': 0.0588,
    'cadence_score': 0.0588,
    'repetition_break': 0.15,
    'duration_prior': 0.4118,
    'msaf_vote': 0.05,
    'chord_ngram_rep': 0.0,
    'chroma_change': 0.05,
    'spec_contrast': 0.05,
    'onset_density': 0.05,
    'rms_energy': 0.05,
}

pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=20)
print('Validating on', len(pairs), 'songs')

results = []
for p in pairs:
    audio = Path(p['audio'])
    ann = Path(p['annotation'])
    ref_sections = _parse_salami_sections(ann)
    t0 = time.time()
    res = detect_sections(
        audio,
        chords=None,
        weights=weights,
        beat_snap_sec=0,
        algorithm='heuristic',
        downbeat_confidence_thresh=0.0,
        min_section_sec=4.0,
        nms_gap_sec=8.0,
        cand_prominence=0.18,
        cand_sub_prominence=0.3,
    )
    det_sections = [
        {'start_s': s['start_ms']/1000.0, 'end_s': (s['start_ms']+s['duration_ms'])/1000.0}
        for s in res.get('sections', [])
    ]
    entry = {
        'id': p['id'],
        'detector': {
            '0.5': _boundary_f1(ref_sections, det_sections, 0.5),
            '3.0': _boundary_f1(ref_sections, det_sections, 3.0),
        },
        'time_s': round(time.time()-t0, 2),
        'cand_count': len(res.get('candidates', [])),
    }
    results.append(entry)
    print('id', p['id'], 'cand', entry['cand_count'], 'F1@3.0', entry['detector']['3.0']['f1'])

summary = {}
for tol in ('0.5','3.0'):
    vals = [r['detector'][tol]['f1'] for r in results]
    summary[f'F1@{tol}s'] = {'mean': round(mean(vals),4), 'median': round(median(vals),4), 'n': len(vals)}

out = {'benchmark_date': time.strftime('%Y-%m-%d %H:%M'), 'weights': weights, 'summary': summary, 'per_song': results}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out, indent=2), encoding='utf-8')
print('Wrote', OUT)
