#!/usr/bin/env python3
import json
from pathlib import Path

ids=['10','12','19','23','39','40']
out_dir=Path('results')/ 'traces'
out_dir.mkdir(parents=True,exist_ok=True)
for pid in ids:
    base=out_dir/f'trace_{pid}_alpha1_th0.20.json'
    lyr=out_dir/f'trace_{pid}_alpha1_th0.20_lyrics.json'
    if not base.exists() or not lyr.exists():
        print(pid, 'missing trace files')
        continue
    b=json.loads(base.read_text(encoding='utf-8'))
    l=json.loads(lyr.read_text(encoding='utf-8'))
    def kept_map(trace):
        m={}
        for c in trace.get('candidates',[]):
            if c.get('kept'):
                key=(c.get('beat_idx'), round(c.get('time_s',0),3))
                m[key]={'time_s':c.get('time_s'),'score':c.get('score'),'features':c.get('features')}
        return m
    bm=kept_map(b)
    lm=kept_map(l)
    added=[{'beat_idx':k[0],'time_s':v['time_s'],'score':v['score']} for k,v in lm.items() if k not in bm]
    removed=[{'beat_idx':k[0],'time_s':v['time_s'],'score':v['score']} for k,v in bm.items() if k not in lm]
    common=[]
    for k in bm:
        if k in lm:
            s0=bm[k]['score']; s1=lm[k]['score']
            common.append({'beat_idx':k[0],'time_s':bm[k]['time_s'],'old_score':s0,'new_score':s1,'delta':round(s1-s0,4)})
    summary={'id':pid,'n_old_kept':len(bm),'n_new_kept':len(lm),'added':added,'removed':removed,'common':common}
    (out_dir/f'diff_kept_{pid}.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(pid, 'old_kept=',len(bm),'new_kept=',len(lm),'added=',len(added),'removed=',len(removed))
