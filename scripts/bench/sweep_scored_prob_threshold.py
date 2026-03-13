#!/usr/bin/env python3
"""Sweep scored detector `prob_threshold` on Harmonix dev and run SALAMI pilot if guard met.

Writes: results/prob_threshold_sweep.json and results/salami_pilot_scored_prob_<t>.json
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections
from scripts.bench.section_benchmark import _load_harmonix_pairs, _parse_harmonix_sections, _boundary_f1
from scripts.bench.salami_benchmark import _load_salami_pairs

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

THRESHOLDS = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
HARMONIX_GUARD = 0.284

def eval_harmonix(threshold: float, max_songs: int = 30):
    pairs = _load_harmonix_pairs(ROOT / 'data' / 'raw' / 'harmonix', ROOT / 'data' / 'audio', max_songs=max_songs)
    vals = []
    per_song = []
    for p in pairs:
        if not p.get('audio'):
            continue
        try:
            res = detect_sections(p['audio'], chords=None, weights=None, algorithm='scored', prob_threshold=threshold)
        except Exception as exc:
            print('detector error', p['id'], exc)
            continue
        det_raw = res.get('sections', [])
        # convert detector output (start_ms,duration_ms) -> (start_s,end_s)
        det = []
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s = float(s['start_ms']) / 1000.0
                end_s = start_s + float(s['duration_ms']) / 1000.0
                det.append({'start_s': start_s, 'end_s': end_s, 'label': s.get('label', '')})
            elif 'start_s' in s:
                # already in expected format
                det.append(s)
        ref = _parse_harmonix_sections(Path(p['sections_file']))
        f = _boundary_f1(ref, det, 3.0)
        vals.append(f['f1'])
        per_song.append({'id': p['id'], 'f1': f['f1']})
    return {'threshold': threshold, 'mean_f1_3.0': mean(vals) if vals else 0.0, 'per_song': per_song}


def run_salami_pilot(threshold: float, max_songs: int = 20):
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=max_songs)
    results = []
    for p in pairs:
        audio = p.get('audio')
        if not audio:
            continue
        ref = _parse_salami_sections(Path(p['annotation']))
        try:
            res = detect_sections(audio, chords=None, weights=None, algorithm='scored', prob_threshold=threshold)
        except Exception as exc:
            print('salami detector error', p['id'], exc)
            continue
        det_raw = res.get('sections', [])
        det = []
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s = float(s['start_ms']) / 1000.0
                end_s = start_s + float(s['duration_ms']) / 1000.0
                det.append({'start_s': start_s, 'end_s': end_s, 'label': s.get('label', '')})
            elif 'start_s' in s:
                det.append(s)
        f = _boundary_f1(ref, det, 3.0)
        results.append({'id': p['id'], 'f1_3.0': f['f1'], 'pred_sections': len(det)})
    summary = {'mean_f1_3.0': mean([r['f1_3.0'] for r in results]) if results else 0.0, 'n': len(results)}
    return {'threshold': threshold, 'summary': summary, 'per_song': results}


def main():
    sweep = []
    for t in THRESHOLDS:
        print('Evaluating threshold', t)
        h = eval_harmonix(t)
        print('  mean F1@3.0 =', h['mean_f1_3.0'])
        sweep.append(h)
        Path(OUT / f'prob_threshold_harmonix_{t:.2f}.json').write_text(json.dumps(h, indent=2))

    Path(OUT / 'prob_threshold_sweep.json').write_text(json.dumps(sweep, indent=2))

    # find best threshold that meets guard
    candidates = [s for s in sweep if s['mean_f1_3.0'] >= HARMONIX_GUARD]
    if not candidates:
        print('No threshold met Harmonix guard')
        return
    # choose threshold with max mean
    best = max(candidates, key=lambda x: x['mean_f1_3.0'])
    print('Best threshold meeting guard:', best['threshold'], 'mean F1@3.0', best['mean_f1_3.0'])
    salami_res = run_salami_pilot(best['threshold'])
    Path(OUT / f'salami_pilot_scored_prob_{best["threshold"]:.2f}.json').write_text(json.dumps(salami_res, indent=2))
    print('Wrote SALAMI pilot results for threshold', best['threshold'])

if __name__ == '__main__':
    main()
