#!/usr/bin/env python3
import json
from pathlib import Path
import csv

old_path = Path('results/harmonix-sanity-baseline.json')
new_path = Path('results/harmonix_validation.json')
out_json = Path('results/harmonix_diff.json')
out_csv = Path('results/harmonix_diff.csv')

old = json.loads(old_path.read_text())
new = json.loads(new_path.read_text())
old_map = {p['id']: p for p in old.get('per_song', [])}
new_map = {p['id']: p for p in new.get('per_song', [])}
ids = sorted(set(old_map) | set(new_map))
rows = []
for id in ids:
    pa = old_map.get(id)
    pb = new_map.get(id)
    row = {'id': id}
    if pa and 'detector' in pa and '3.0' in pa['detector']:
        od = pa['detector']['3.0']
        row['old_tp'] = od.get('tp')
        row['old_fp'] = od.get('fp')
        row['old_fn'] = od.get('fn')
        row['old_f1'] = od.get('f1')
    else:
        row['old_tp'] = row['old_fp'] = row['old_fn'] = row['old_f1'] = None
    if pb and 'detector' in pb and '3.0' in pb['detector']:
        nd = pb['detector']['3.0']
        row['new_tp'] = nd.get('tp')
        row['new_fp'] = nd.get('fp')
        row['new_fn'] = nd.get('fn')
        row['new_f1'] = nd.get('f1')
    else:
        row['new_tp'] = row['new_fp'] = row['new_fn'] = row['new_f1'] = None
    try:
        row['delta_f1'] = (row['new_f1'] or 0) - (row['old_f1'] or 0)
    except Exception:
        row['delta_f1'] = None
    try:
        row['delta_tp'] = (row['new_tp'] or 0) - (row['old_tp'] or 0)
    except Exception:
        row['delta_tp'] = None
    try:
        row['delta_fp'] = (row['new_fp'] or 0) - (row['old_fp'] or 0)
    except Exception:
        row['delta_fp'] = None
    rows.append(row)

out_json.write_text(json.dumps(rows, indent=2))
with out_csv.open('w', newline='', encoding='utf-8') as fh:
    if rows:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
print('Wrote', out_json, 'and', out_csv)
