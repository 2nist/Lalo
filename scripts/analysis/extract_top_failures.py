import sys
import json
import argparse
from collections import defaultdict

def find_numbers(d, path=()):
    results = {}
    if isinstance(d, dict):
        for k,v in d.items():
            if isinstance(v, (int,float)):
                results[".".join(path+(k,))] = v
            else:
                results.update(find_numbers(v, path+(k,)))
    elif isinstance(d, list):
        for i,elem in enumerate(d):
            results.update(find_numbers(elem, path+(str(i),)))
    return results


def best_fp_metric(song_dict):
    nums = find_numbers(song_dict)
    fp_candidates = {k:v for k,v in nums.items() if 'fp' in k.lower()}
    # prefer fp keys that include 0.5
    fp05 = {k:v for k,v in fp_candidates.items() if '0.5' in k or '0_5' in k}
    if fp05:
        # return max fp05
        return max(fp05.values())
    if fp_candidates:
        return max(fp_candidates.values())
    return 0


def best_f1_metric(song_dict):
    nums = find_numbers(song_dict)
    f1_candidates = {k:v for k,v in nums.items() if 'f1' in k.lower()}
    f105 = {k:v for k,v in f1_candidates.items() if '0.5' in k or '0_5' in k}
    if f105:
        return max(f105.values())
    if f1_candidates:
        return max(f1_candidates.values())
    return None


def get_id(song_dict):
    for key in ('id','song_id','song','track','name','filename'):
        if key in song_dict:
            return song_dict[key]
    # try to find any top-level string field
    for k,v in song_dict.items():
        if isinstance(v,str):
            return v
    return '<unknown>'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('jsonfile')
    p.add_argument('--top',type=int,default=10)
    args = p.parse_args()
    data = json.load(open(args.jsonfile))
    per_song = data.get('per_song') or data.get('per-song') or data.get('perSong') or []
    if not per_song:
        # try to locate arrays that look like per-song by searching keys
        for k,v in data.items():
            if isinstance(v,list) and len(v)>0 and isinstance(v[0],dict):
                per_song = v
                break
    if not per_song:
        print('No per-song array found in JSON')
        return
    summary = []
    for s in per_song:
        sid = get_id(s)
        fp = best_fp_metric(s)
        f1 = best_f1_metric(s)
        summary.append((sid,fp,f1,s))
    # sort by fp desc
    summary.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
    print(f"Top {args.top} songs by FP (descending):")
    for i,(sid,fp,f1,s) in enumerate(summary[:args.top],start=1):
        print(f"{i}. {sid} — FP~{fp} — F1~{('N/A' if f1 is None else f'{f1:.4f}')}" )

if __name__ == '__main__':
    main()
