#!/usr/bin/env python3
"""Compare `results/chord_ngram_*.json` against promoted baseline JSON.

Writes:
 - results/chord_ngram_vs_promoted.json
 - results/chord_ngram_vs_promoted.csv
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

def load_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))

def load_promoted(path_candidates):
    # prefer promoted_wave15_salami_with_lyrics.json if present
    candidates = [p for p in path_candidates if 'promoted_wave15' in p.name and 'salami' in p.name]
    if candidates:
        return load_json(candidates[0])
    # fallback: try sections-machine-b-promote-wave15.json
    for p in path_candidates:
        if p.name == 'sections-machine-b-promote-wave15.json':
            return load_json(p)
    raise FileNotFoundError('Promoted baseline JSON not found')


def main():
    chord_h = Path('results/chord_ngram_harmonix.json')
    chord_s = Path('results/chord_ngram_salami.json')
    files = list(Path('results').glob('*.json'))
    promoted = None
    try:
        promoted = load_promoted(files)
    except FileNotFoundError:
        # attempt known path
        p = Path('results/promoted_wave15_salami_with_lyrics.json')
        if p.exists():
            promoted = load_json(p)
        else:
            raise

    chord_s_data = load_json(chord_s) if chord_s.exists() else {}

    # promoted per-song mapping: try to find 'per_song' with ids
    promoted_map = {}
    if 'per_song' in promoted:
        for e in promoted['per_song']:
            promoted_map[str(e.get('id'))] = e

    out = {'date': promoted.get('date'), 'comparison': []}
    for e in chord_s_data.get('per_song', []):
        sid = str(e.get('id'))
        chord_f = e.get('f1_3.0')
        base = promoted_map.get(sid)
        base_f = base.get('f1_3.0') if base else None
        delta = None if base_f is None else round((chord_f - base_f),4)
        out['comparison'].append({'id': sid, 'chord_f1_3.0': chord_f, 'promoted_f1_3.0': base_f, 'delta': delta})

    # sort by delta ascending (worst regressions first)
    out['comparison'] = sorted(out['comparison'], key=lambda x: (x['delta'] is None, x['delta']))

    (OUT / 'chord_ngram_vs_promoted.json').write_text(json.dumps(out, indent=2), encoding='utf-8')

    # write CSV
    import csv
    with open(OUT / 'chord_ngram_vs_promoted.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['id','chord_f1_3.0','promoted_f1_3.0','delta'])
        for r in out['comparison']:
            w.writerow([r['id'], r['chord_f1_3.0'], r['promoted_f1_3.0'], r['delta']])

    print('Wrote results/chord_ngram_vs_promoted.json and .csv')


if __name__ == '__main__':
    main()
