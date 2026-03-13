#!/usr/bin/env python3
import json
import csv
from pathlib import Path

ids=['10','12','19','23','39','40']
in_dir=Path('results')/'traces'
for pid in ids:
    jpath=in_dir/f'diff_kept_{pid}.json'
    if not jpath.exists():
        print('missing', jpath)
        continue
    data=json.loads(jpath.read_text(encoding='utf-8'))
    rows=data.get('common',[])
    out=in_dir/f'diff_kept_{pid}.csv'
    with out.open('w',newline='',encoding='utf-8') as fh:
        w=csv.writer(fh)
        w.writerow(['beat_idx','time_s','old_score','new_score','delta'])
        for r in rows:
            w.writerow([r.get('beat_idx'), r.get('time_s'), r.get('old_score'), r.get('new_score'), r.get('delta')])
    print('Wrote', out)
