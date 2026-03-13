#!/usr/bin/env python3
"""Evaluate isolated `chord_ngram_rep` weight on Harmonix and SALAMI.

Writes:
 - results/chord_ngram_harmonix.json
 - results/chord_ngram_salami.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections
from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1
from scripts.bench.section_benchmark import _load_harmonix_pairs, _parse_harmonix_sections

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

# Isolated chord n-gram weight
WEIGHTS = {'chord_ngram_rep': 0.2}


def run_harmonix(weights, max_songs: int = 30):
    pairs = _load_harmonix_pairs(ROOT / 'data' / 'raw' / 'harmonix', ROOT / 'data' / 'audio', max_songs=max_songs)
    results = []
    for p in pairs:
        if not p.get('audio'):
            continue
        audio = Path(p['audio'])
        ann = Path(p['sections_file'])
        ref = _parse_harmonix_sections(ann)
        t0 = time.time()
        res = detect_sections(audio, chords=None, weights=weights, algorithm='heuristic', prob_threshold=0.0)
        meta = res.get('meta', {})
        cand = meta.get('candidate_count', None)
        kept = meta.get('kept_count', None)
        det = [{'start_s': s['start_ms']/1000.0, 'end_s': (s['start_ms']+s['duration_ms'])/1000.0} for s in res.get('sections',[])]
        f = _boundary_f1(ref, det, 3.0)
        results.append({'id': p['id'], 'f1_3.0': f['f1'], 'candidate_count': cand, 'kept_count': kept, 'time_s': round(time.time()-t0,2)})
        print('harmonix id', p['id'], 'F1@3.0', f['f1'])
    summary = {'mean_f1_3.0': round(mean([r['f1_3.0'] for r in results]) if results else 0.0,4), 'n': len(results)}
    out = {'date': time.strftime('%Y-%m-%d %H:%M'), 'summary': summary, 'per_song': results}
    (OUT / 'chord_ngram_harmonix.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote results/chord_ngram_harmonix.json')
    return out


def run_salami(weights, max_songs: int = 30):
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=max_songs)
    results = []
    for p in pairs:
        audio = Path(p['audio'])
        ann = Path(p['annotation'])
        ref = _parse_salami_sections(ann)
        t0 = time.time()
        res = detect_sections(audio, chords=None, weights=weights, algorithm='heuristic', prob_threshold=0.0)
        meta = res.get('meta', {})
        cand = meta.get('candidate_count', None)
        kept = meta.get('kept_count', None)
        det = [{'start_s': s['start_ms']/1000.0, 'end_s': (s['start_ms']+s['duration_ms'])/1000.0} for s in res.get('sections',[])]
        f05 = _boundary_f1(ref, det, 0.5)
        f30 = _boundary_f1(ref, det, 3.0)
        results.append({'id': p['id'], 'f1_0.5': f05['f1'], 'f1_3.0': f30['f1'], 'candidate_count': cand, 'kept_count': kept, 'time_s': round(time.time()-t0,2)})
        print('salami id', p['id'], 'F1@3.0', f30['f1'])
    summary = {'F1@0.5': {'mean': round(mean([r['f1_0.5'] for r in results]) if results else 0.0,4), 'n': len(results)}, 'F1@3.0': {'mean': round(mean([r['f1_3.0'] for r in results]) if results else 0.0,4), 'n': len(results)}}
    out = {'date': time.strftime('%Y-%m-%d %H:%M'), 'summary': summary, 'per_song': results}
    (OUT / 'chord_ngram_salami.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote results/chord_ngram_salami.json')
    return out


def main():
    print('Running chord-ngram-only test with weights:', WEIGHTS)
    h = run_harmonix(WEIGHTS, max_songs=30)
    s = run_salami(WEIGHTS, max_songs=30)
    print('Done')


if __name__ == '__main__':
    main()
