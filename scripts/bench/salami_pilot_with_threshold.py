#!/usr/bin/env python3
"""Run a 20-song SALAMI pilot using `algorithm='scored'` with a prob_threshold and explicit weights.

Writes: results/salami_pilot_alpha{a}_th{t}.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)


def run_pilot(weights: Dict[str, float], prob_threshold: float, max_songs: int = 20):
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=max_songs)
    from scripts.analysis.section_detector import detect_sections

    results = []
    for p in pairs:
        audio = p.get('audio')
        if not audio:
            continue
        ann = Path(p['annotation'])
        ref = _parse_salami_sections(ann)
        try:
            res = detect_sections(audio, chords=None, weights=weights, algorithm='scored', prob_threshold=prob_threshold, min_section_sec=4.0, nms_gap_sec=8.0, cand_prominence=0.18, cand_sub_prominence=0.3)
        except Exception as exc:
            print('detector error', p['id'], exc)
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
    return {'threshold': prob_threshold, 'summary': summary, 'per_song': results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prob-threshold', type=float, required=True)
    ap.add_argument('--max-songs', type=int, default=20)
    # weight args
    ap.add_argument('--weight-flux', type=float, required=True)
    ap.add_argument('--weight-chord', type=float, required=True)
    ap.add_argument('--weight-cadence', type=float, required=True)
    ap.add_argument('--weight-repetition', type=float, required=True)
    ap.add_argument('--weight-duration', type=float, required=True)
    ap.add_argument('--weight-chroma', type=float, required=True)
    ap.add_argument('--weight-spec-contrast', type=float, required=True)
    ap.add_argument('--weight-onset-density', type=float, required=True)
    ap.add_argument('--weight-rms', type=float, required=True)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    weights = {
        'flux_peak': args.weight_flux,
        'chord_novelty': args.weight_chord,
        'cadence_score': args.weight_cadence,
        'repetition_break': args.weight_repetition,
        'duration_prior': args.weight_duration,
        'chroma_change': args.weight_chroma,
        'spec_contrast': args.weight_spec_contrast,
        'onset_density': args.weight_onset_density,
        'rms_energy': args.weight_rms,
    }

    res = run_pilot(weights, args.prob_threshold, max_songs=args.max_songs)
    out_path = Path(args.out) if args.out else OUT / f'salami_pilot_alpha0.75_th{args.prob_threshold:.2f}.json'
    out_path.write_text(json.dumps(res, indent=2), encoding='utf-8')
    print('Wrote:', out_path)


if __name__ == '__main__':
    main()
