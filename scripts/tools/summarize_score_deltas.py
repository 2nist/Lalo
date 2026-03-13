#!/usr/bin/env python3
"""Summarize score deltas and kept-flag changes for selected ids.
Writes results/traces/score_deltas_summary.json and prints a concise table.
"""
from __future__ import annotations

import json
from pathlib import Path

TR = Path('results') / 'traces'

def load(sid):
    p = TR / f'score_deltas_{sid}.json'
    return json.loads(p.read_text(encoding='utf-8'))

def summarize(sid):
    j = load(sid)
    rows = j.get('rows', [])
    pos = sum(1 for r in rows if r['delta'] is not None and r['delta'] > 0)
    neg = sum(1 for r in rows if r['delta'] is not None and r['delta'] < 0)
    zero = sum(1 for r in rows if r['delta'] == 0)
    kept_changes = 0
    for r in rows:
        pc = r.get('prom_candidate') or {}
        cc = r.get('chord_candidate') or {}
        if pc.get('kept') != cc.get('kept'):
            kept_changes += 1
    return {'id': sid, 'n_rows': len(rows), 'pos': pos, 'neg': neg, 'zero': zero, 'kept_changes': kept_changes}

def main():
    ids = ['114','111','21','79','26']
    out = {'summary': [], 'per_id': []}
    for sid in ids:
        s = summarize(sid)
        out['per_id'].append(s)
        out['summary'].append({'id': sid, 'pos': s['pos'], 'neg': s['neg'], 'kept_changes': s['kept_changes']})
    (TR / 'score_deltas_summary.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    for s in out['per_id']:
        print(f"ID {s['id']}: rows={s['n_rows']} +{s['pos']} -{s['neg']} 0:{s['zero']} kept_changes={s['kept_changes']}")

if __name__ == '__main__':
    main()
