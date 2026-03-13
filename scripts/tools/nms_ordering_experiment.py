#!/usr/bin/env python3
"""NMS-ordering experiment: order candidates by chord-ngram score but keep by promoted scoring.

Writes: results/nms_chord_ordering_salami.json
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections, _nms_by_score, NMS_DISTANCE_SEC
from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

def load_promoted_weights():
    p = OUT / 'sections-machine-b-promote-wave15.json'
    j = json.loads(p.read_text(encoding='utf-8'))
    return j.get('weights')


def run_for_ids(ids: list[str]):
    weights = load_promoted_weights()
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=500)
    pair_map = {str(p['id']): p for p in pairs}
    results = []
    for sid in ids:
        p = pair_map.get(str(sid))
        if not p:
            continue
        audio = Path(p['audio'])
        ann = Path(p['annotation'])
        ref = _parse_salami_sections(ann)
        res = detect_sections(audio, chords=None, weights=None, algorithm='heuristic', prob_threshold=0.0)
        cands = res.get('candidates', [])
        times = np.array([float(c.get('time_s', 0.0)) for c in cands])
        # compute promoted and chord scores
        promoted_scores = np.array([sum(c.get('features', {}).get(k, 0.0) * weights.get(k, 0.0) for k in c.get('features', {})) for c in cands])
        chord_scores = np.array([c.get('features', {}).get('chord_ngram_rep', 0.0) * 0.2 for c in cands])
        # order by chord_scores for NMS, but selection will use promoted_scores for kept decision
        kept_mask = _nms_by_score(times, chord_scores, min_gap_sec=NMS_DISTANCE_SEC)
        kept_times = [float(cands[i].get('time_s')) for i, k in enumerate(kept_mask) if k]
        det = [{'start_s': t, 'end_s': t + 1.0} for t in kept_times]
        f = _boundary_f1(ref, det, 3.0)
        results.append({'id': sid, 'f1_3.0': f['f1'], 'n_candidates': len(cands), 'n_kept': int(sum(kept_mask))})
        print('id', sid, 'F1@3.0', f['f1'], 'kept', int(sum(kept_mask)))
    summary = {'mean_f1_3.0': round(mean([r['f1_3.0'] for r in results]) if results else 0.0,4), 'n': len(results)}
    out = {'date': __import__('time').strftime('%Y-%m-%d %H:%M'), 'summary': summary, 'per_song': results}
    (OUT / 'nms_chord_ordering_salami.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote results/nms_chord_ordering_salami.json')


if __name__ == '__main__':
    # read top 10 worst ids from chord_ngram_vs_promoted.json
    j = json.loads((OUT / 'chord_ngram_vs_promoted.json').read_text(encoding='utf-8'))
    ids = [r['id'] for r in j.get('comparison', [])[:10]]
    run_for_ids(ids)
