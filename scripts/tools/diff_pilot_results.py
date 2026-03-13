#!/usr/bin/env python3
import json
from pathlib import Path
import csv

old_path = Path('results/salami_pilot_mild_prune20.json')
new_path = Path('results/salami_pilot_score_then_nms_lyrics_ngram20.json')
out_json = Path('results/salami_pilot_diff20.json')
out_csv = Path('results/salami_pilot_diff20.csv')

old = json.loads(old_path.read_text())
new = json.loads(new_path.read_text())
old_map = {p['id']: p for p in old.get('per_song', [])}
new_map = {p['id']: p for p in new.get('per_song', [])}
ids = sorted(set(old_map) | set(new_map), key=lambda x: int(x))
rows = []
for id in ids:
    pa = old_map.get(id)
    pb = new_map.get(id)
    row = {'id': id}
    for key in ['0.5', '3.0']:
        if pa:
            od = pa['detector'].get(key, {})
            row[f'old_tp_{key}'] = od.get('tp')
            row[f'old_fp_{key}'] = od.get('fp')
            row[f'old_fn_{key}'] = od.get('fn')
            row[f'old_f1_{key}'] = od.get('f1')
        else:
            row[f'old_tp_{key}'] = None
            row[f'old_fp_{key}'] = None
            row[f'old_fn_{key}'] = None
            row[f'old_f1_{key}'] = None
        if pb:
            nd = pb['detector'].get(key, {})
            row[f'new_tp_{key}'] = nd.get('tp')
            row[f'new_fp_{key}'] = nd.get('fp')
            row[f'new_fn_{key}'] = nd.get('fn')
            row[f'new_f1_{key}'] = nd.get('f1')
        else:
            row[f'new_tp_{key}'] = None
            row[f'new_fp_{key}'] = None
            row[f'new_fn_{key}'] = None
            row[f'new_f1_{key}'] = None
        # deltas for 3.0
        if key == '3.0':
            try:
                row['delta_f1_3.0'] = (row['new_f1_3.0'] or 0) - (row['old_f1_3.0'] or 0)
            except Exception:
                row['delta_f1_3.0'] = None
            try:
                row['delta_tp_3.0'] = (row['new_tp_3.0'] or 0) - (row['old_tp_3.0'] or 0)
            except Exception:
                row['delta_tp_3.0'] = None
            try:
                row['delta_fp_3.0'] = (row['new_fp_3.0'] or 0) - (row['old_fp_3.0'] or 0)
            except Exception:
                row['delta_fp_3.0'] = None
    rows.append(row)

out_json.write_text(json.dumps(rows, indent=2))

# write CSV
with out_csv.open('w', newline='', encoding='utf-8') as fh:
    if rows:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

print('Wrote', out_json, 'and', out_csv)
