import sys
import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text())

def find_per_song(data):
    for k in ('per_song','per-song','perSong'):
        if k in data:
            return data[k]
    # fallback: find first list of dicts
    for v in data.values():
        if isinstance(v,list) and v and isinstance(v[0],dict):
            return v
    return []

def get_id(song):
    for key in ('id','song_id','song','track','name','filename'):
        if key in song:
            return song[key]
    # fallback
    for k,v in song.items():
        if isinstance(v,str):
            return v
    return '<unknown>'

def find_number_keys(d, key_substr):
    res = {}
    if isinstance(d, dict):
        for k,v in d.items():
            if isinstance(v,(int,float)) and key_substr in k.lower():
                res[k]=v
            else:
                res.update(find_number_keys(v, key_substr))
    elif isinstance(d,list):
        for e in d:
            res.update(find_number_keys(e, key_substr))
    return res

if __name__=='__main__':
    if len(sys.argv)<3:
        print('Usage: compare_results.py baseline.json candidate.json')
        raise SystemExit(2)
    base = load(sys.argv[1])
    cand = load(sys.argv[2])
    base_per = find_per_song(base)
    cand_per = find_per_song(cand)
    base_map = { get_id(s): s for s in base_per }
    cand_map = { get_id(s): s for s in cand_per }

    # overall summaries
    def overall_stats(d):
        det = d.get('summary',{}).get('detector') or d.get('summary',{}).get('Section Detector (new)') or d.get('summary',{})
        f05 = None
        f30 = None
        if isinstance(det, dict):
            # try keys
            for k in det.keys():
                if '0.5' in k or '0_5' in k:
                    f05 = det[k]
                if '3.0' in k or '3_0' in k:
                    f30 = det[k]
        # fallback to root keys
        f05 = f05 or d.get('F1@0.5s')
        f30 = f30 or d.get('F1@3.0s')
        return f05, f30

    base_f05, base_f30 = overall_stats(base)
    cand_f05, cand_f30 = overall_stats(cand)
    print('Overall: baseline F1@0.5=', base_f05, 'F1@3.0=', base_f30)
    print('         candidate F1@0.5=', cand_f05, 'F1@3.0=', cand_f30)

    # per-song FP differences
    rows = []
    for sid, sbase in base_map.items():
        scand = cand_map.get(sid)
        base_fp = max(find_number_keys(sbase,'fp').values()) if find_number_keys(sbase,'fp') else 0
        cand_fp = max(find_number_keys(scand,'fp').values()) if scand and find_number_keys(scand,'fp') else 0
        base_f1 = max(find_number_keys(sbase,'f1').values()) if find_number_keys(sbase,'f1') else None
        cand_f1 = max(find_number_keys(scand,'f1').values()) if scand and find_number_keys(scand,'f1') else None
        rows.append((sid, base_fp, cand_fp, (cand_fp-base_fp), base_f1, cand_f1))
    # include songs in candidate not in baseline
    for sid, scand in cand_map.items():
        if sid in base_map: continue
        cand_fp = max(find_number_keys(scand,'fp').values()) if find_number_keys(scand,'fp') else 0
        cand_f1 = max(find_number_keys(scand,'f1').values()) if find_number_keys(scand,'f1') else None
        rows.append((sid, None, cand_fp, None, None, cand_f1))

    # sort by delta desc (increase in FP worst)
    rows_inc = [r for r in rows if r[3] is not None]
    rows_inc.sort(key=lambda x: x[3], reverse=True)
    print('\nTop increases in FP (candidate - baseline):')
    for r in rows_inc[:15]:
        print(f"{r[0]}: baseline_fp={r[1]} candidate_fp={r[2]} delta={r[3]} baseline_f1={r[4]} candidate_f1={r[5]}")

    rows_dec = sorted(rows_inc, key=lambda x: x[3])
    print('\nTop decreases in FP (improvements):')
    for r in rows_dec[:15]:
        print(f"{r[0]}: baseline_fp={r[1]} candidate_fp={r[2]} delta={r[3]} baseline_f1={r[4]} candidate_f1={r[5]}")

    # summary counts
    inc_count = sum(1 for r in rows if r[3] is not None and r[3]>0)
    dec_count = sum(1 for r in rows if r[3] is not None and r[3]<0)
    print(f"\nSummary: {inc_count} songs increased FP, {dec_count} songs decreased FP (out of {len(rows)} compared)")
