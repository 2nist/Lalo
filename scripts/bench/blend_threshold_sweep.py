#!/usr/bin/env python3
"""Sweep blended heuristic weights × probability thresholds on Harmonix dev.

Writes: results/blend_threshold_sweep.json and per-combo outputs.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import DEFAULT_WEIGHTS
from scripts.bench.section_benchmark import _load_harmonix_pairs, _parse_harmonix_sections, _boundary_f1

LEARNED = Path('results/learned_weights_xgb.json')
OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]
THRESHOLDS = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]


def load_learned():
    if not LEARNED.exists():
        raise SystemExit('Missing learned weights: results/learned_weights_xgb.json')
    data = json.loads(LEARNED.read_text(encoding='utf-8'))
    return data.get('weights', {})


def blend(w_promoted, w_learned, alpha: float):
    out = {}
    keys = [
        'flux_peak','chord_novelty','cadence_score','repetition_break','duration_prior',
        'chroma_change','spec_contrast','onset_density','rms_energy'
    ]
    for k in keys:
        p = float(w_promoted.get(k, 0.0))
        l = float(w_learned.get(k, 0.0))
        out[k] = (1.0 - alpha) * p + alpha * l
    return out


def eval_harmonix(weights_map, threshold: float, max_songs: int = 30):
    pairs = _load_harmonix_pairs(ROOT / 'data' / 'raw' / 'harmonix', ROOT / 'data' / 'audio', max_songs=max_songs)
    vals = []
    per_song = []
    from scripts.analysis.section_detector import detect_sections
    for p in pairs:
        if not p.get('audio'):
            continue
        try:
            res = detect_sections(p['audio'], chords=None, weights=weights_map, algorithm='heuristic', prob_threshold=threshold)
        except Exception as exc:
            print('detector error', p['id'], exc)
            continue
        det_raw = res.get('sections', [])
        # normalize detector output to sections with start_s/end_s
        det = []
        for s in det_raw:
            if 'start_ms' in s and 'duration_ms' in s:
                start_s = float(s['start_ms']) / 1000.0
                end_s = start_s + float(s['duration_ms']) / 1000.0
                det.append({'start_s': start_s, 'end_s': end_s, 'label': s.get('label', '')})
            elif 'start_s' in s:
                det.append(s)
        ref = _parse_harmonix_sections(Path(p['sections_file']))
        f = _boundary_f1(ref, det, 3.0)
        vals.append(f['f1'])
        per_song.append({'id': p['id'], 'f1': f['f1']})
    return {'threshold': threshold, 'mean_f1_3.0': mean(vals) if vals else 0.0, 'per_song': per_song}


def main():
    learned = load_learned()
    promoted = {
        'flux_peak': DEFAULT_WEIGHTS.get('flux_peak', 0.0),
        'chord_novelty': DEFAULT_WEIGHTS.get('chord_novelty', 0.0),
        'cadence_score': DEFAULT_WEIGHTS.get('cadence_score', 0.0),
        'repetition_break': DEFAULT_WEIGHTS.get('repetition_break', 0.0),
        'duration_prior': DEFAULT_WEIGHTS.get('duration_prior', 0.0),
        'chroma_change': DEFAULT_WEIGHTS.get('chroma_change', 0.0),
        'spec_contrast': DEFAULT_WEIGHTS.get('spec_contrast', 0.0),
        'onset_density': DEFAULT_WEIGHTS.get('onset_density', 0.0),
        'rms_energy': DEFAULT_WEIGHTS.get('rms_energy', 0.0),
    }

    results = []
    for a in ALPHAS:
        blended = blend(promoted, learned, a)
        for t in THRESHOLDS:
            print(f'Alpha={a} Threshold={t}')
            h = eval_harmonix(blended, t)
            Path(OUT / f'harmonix_blend_alpha_{a:.2f}_th_{t:.2f}.json').write_text(json.dumps(h, indent=2))
            results.append({'alpha': a, 'threshold': t, 'mean_f1_3.0': h['mean_f1_3.0'], 'out': f'results/harmonix_blend_alpha_{a:.2f}_th_{t:.2f}.json'})
            print('  mean F1@3.0 =', h['mean_f1_3.0'])

    Path(OUT / 'blend_threshold_sweep.json').write_text(json.dumps(results, indent=2))
    print('Wrote results/blend_threshold_sweep.json')


if __name__ == '__main__':
    main()
