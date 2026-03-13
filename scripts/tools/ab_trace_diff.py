#!/usr/bin/env python3
"""A/B trace diff: for worst regressions, dump detect_sections traces for promoted vs chord-ngram.

Outputs per-id:
 - results/traces/trace_{id}_promoted.json
 - results/traces/trace_{id}_chordngram.json
 - results/traces/trace_diff_{id}.json
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
import time

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections
from scripts.bench.salami_benchmark import _load_salami_pairs

OUT = Path('results')
TRACES = OUT / 'traces'
TRACES.mkdir(parents=True, exist_ok=True)

CHORD_WEIGHTS = {'chord_ngram_rep': 0.2}


def load_promoted_weights():
    p = Path('sections-machine-b-promote-wave15.json')
    if p.exists():
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
            return j.get('weights') or j.get('model_weights') or None
        except Exception:
            return None
    return None


def dump_trace(obj, path: Path):
    path.write_text(json.dumps(obj, indent=2), encoding='utf-8')


def simple_diff(promoted, chord):
    # promoted/chord are detect_sections result dicts containing 'sections' and 'meta'
    prom_times = sorted([s['start_ms'] for s in promoted.get('sections', [])])
    chord_times = sorted([s['start_ms'] for s in chord.get('sections', [])])
    added = [t for t in chord_times if t not in prom_times]
    removed = [t for t in prom_times if t not in chord_times]
    return {'added_starts_ms': added, 'removed_starts_ms': removed, 'prom_count': len(prom_times), 'chord_count': len(chord_times)}


def main(n_worst: int = 5):
    comp = json.loads((Path('results') / 'chord_ngram_vs_promoted.json').read_text(encoding='utf-8'))
    rows = comp.get('comparison', [])
    # worst regressions: smallest delta
    worst = [r for r in rows if r['delta'] is not None]
    worst = sorted(worst, key=lambda x: x['delta'])[:n_worst]
    promoted_weights = load_promoted_weights()
    print('Promoted weights present:', bool(promoted_weights))

    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=500)
    pair_map = {str(p['id']): p for p in pairs}

    for r in worst:
        sid = str(r['id'])
        p = pair_map.get(sid)
        if not p:
            print('Missing pair for', sid)
            continue
        audio = Path(p['audio'])
        print('Processing id', sid, 'audio', audio)
        t0 = time.time()
        prom = detect_sections(audio, chords=None, weights=promoted_weights, algorithm='heuristic', prob_threshold=0.0)
        dump_trace(prom, TRACES / f'trace_{sid}_promoted.json')
        chord = detect_sections(audio, chords=None, weights=CHORD_WEIGHTS, algorithm='heuristic', prob_threshold=0.0)
        dump_trace(chord, TRACES / f'trace_{sid}_chordngram.json')
        diff = simple_diff(prom, chord)
        dump_trace(diff, TRACES / f'trace_diff_{sid}.json')
        print('Wrote traces for', sid, 'in', round(time.time()-t0,2), 's')


if __name__ == '__main__':
    main(n_worst=5)
