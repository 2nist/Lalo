#!/usr/bin/env python3
"""Compute per-candidate score deltas between promoted and chord-ngram traces.

For each id, writes:
 - results/traces/score_deltas_{id}.json
 - results/traces/score_deltas_{id}.csv
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List
import csv

TR = Path('results') / 'traces'
TR.mkdir(parents=True, exist_ok=True)

def load_trace(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding='utf-8'))

def candidate_score(cand: Dict[str, Any]) -> float:
    for k in ('score', 'prob', 'probability'):
        if k in cand:
            return float(cand[k])
    # try meta
    return float(cand.get('probability_score', cand.get('model_score', 0.0)))

def find_match(start_ms: int, candidates: List[Dict[str,Any]], tol_ms: int = 200):
    # candidates may use 'start_ms' or 'time_s'
    best = None
    best_d = tol_ms + 1
    for c in candidates:
        if 'start_ms' in c:
            sm = int(c.get('start_ms', -1))
        else:
            sm = int(round(float(c.get('time_s', -1.0)) * 1000.0))
        if sm == start_ms:
            return c
        d = abs(sm - start_ms)
        if d <= tol_ms and d < best_d:
            best = c; best_d = d
    return best

def process_id(sid: str):
    prom_p = TR / f'trace_{sid}_promoted.json'
    chord_p = TR / f'trace_{sid}_chordngram.json'
    if not prom_p.exists() or not chord_p.exists():
        print('Missing traces for', sid); return
    prom = load_trace(prom_p)
    chord = load_trace(chord_p)
    prom_cands = prom.get('candidates', []) or prom.get('sections', [])
    chord_cands = chord.get('candidates', []) or chord.get('sections', [])
    rows = []
    for pc in prom_cands:
        if 'start_ms' in pc:
            start = int(pc.get('start_ms'))
        else:
            start = int(round(float(pc.get('time_s', 0.0)) * 1000.0))
        match = find_match(start, chord_cands)
        prom_score = candidate_score(pc)
        chord_score = candidate_score(match) if match else None
        delta = None if chord_score is None else round(chord_score - prom_score, 6)
        rows.append({'start_ms': start, 'prom_score': prom_score, 'chord_score': chord_score, 'delta': delta, 'prom_candidate': pc, 'chord_candidate': match})

    # sort by absolute delta descending
    rows_sorted = sorted([r for r in rows if r['delta'] is not None], key=lambda x: abs(x['delta']), reverse=True)
    out_json = {'id': sid, 'n_promoted': len(prom_cands), 'n_chord': len(chord_cands), 'rows': rows_sorted}
    (TR / f'score_deltas_{sid}.json').write_text(json.dumps(out_json, indent=2), encoding='utf-8')

    with open(TR / f'score_deltas_{sid}.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['start_ms','prom_score','chord_score','delta'])
        for r in rows_sorted:
            w.writerow([r['start_ms'], r['prom_score'], r['chord_score'], r['delta']])
    print('Wrote score deltas for', sid)


def main():
    ids = ['114','111','21','79','26']
    for sid in ids:
        process_id(sid)

if __name__ == '__main__':
    main()
