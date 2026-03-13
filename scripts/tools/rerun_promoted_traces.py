#!/usr/bin/env python3
"""Rerun detect_sections for selected IDs using promoted weights file.

Reads `results/sections-machine-b-promote-wave15.json` for weights and
`results/chord_ngram_vs_promoted.json` for IDs (top regressions), then
writes `results/traces/trace_{id}_promoted.json` with full candidate scores.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections
from scripts.bench.salami_benchmark import _load_salami_pairs

OUT = Path('results')
TR = OUT / 'traces'
TR.mkdir(parents=True, exist_ok=True)

def load_promoted_weights():
    p = OUT / 'sections-machine-b-promote-wave15.json'
    j = json.loads(p.read_text(encoding='utf-8'))
    return j.get('weights')

def top_ids(n=5):
    p = OUT / 'chord_ngram_vs_promoted.json'
    j = json.loads(p.read_text(encoding='utf-8'))
    return [r['id'] for r in j.get('comparison', [])[:n]]

def main(n=5):
    weights = load_promoted_weights()
    ids = top_ids(n)
    print('Loaded weights, running for ids:', ids)
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=500)
    pair_map = {str(p['id']): p for p in pairs}
    for sid in ids:
        p = pair_map.get(str(sid))
        if not p:
            print('Missing pair for', sid); continue
        audio = Path(p['audio'])
        print('Rerunning promoted trace for', sid)
        res = detect_sections(audio, chords=None, weights=weights, algorithm='heuristic', prob_threshold=0.0)
        (TR / f'trace_{sid}_promoted.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
        print('Wrote', TR / f'trace_{sid}_promoted.json')

if __name__ == '__main__':
    main(n=5)
