#!/usr/bin/env python3
"""Run promoted (wave15) weights with lyrics applied on Harmonix and SALAMI.

Writes:
- results/promoted_wave15_harmonix_with_lyrics.json
- results/promoted_wave15_salami_with_lyrics.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections
from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1
from scripts.bench.section_benchmark import _load_harmonix_pairs, _parse_harmonix_sections

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

WAVE15_FILE = OUT / 'sections-machine-b-promote-wave15.json'
LYRICS_DIR = Path('data/lyrics')


def load_wave15_weights():
    if not WAVE15_FILE.exists():
        raise SystemExit(f'missing wave15 file: {WAVE15_FILE}')
    data = json.loads(WAVE15_FILE.read_text(encoding='utf-8'))
    return data.get('weights') or {}


def _load_lyrics_for_id(sid: str) -> Optional[List[Dict]]:
    p = LYRICS_DIR / f"{sid}.lyrics.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
        if not d.get('success'):
            return None
        intervals = d.get('intervals', [])
        return [{'start': float(i.get('start', 0.0)), 'end': float(i.get('end', i.get('start', 0.0) + 2.0)), 'text': i.get('text','')} for i in intervals]
    except Exception:
        return None


def run_harmonix(weights, max_songs: int = 30):
    pairs = _load_harmonix_pairs(ROOT / 'data' / 'raw' / 'harmonix', ROOT / 'data' / 'audio', max_songs=max_songs)
    results = []
    for p in pairs:
        if not p.get('audio'):
            continue
        audio = Path(p['audio'])
        ann = Path(p['sections_file'])
        ref = _parse_harmonix_sections(ann)
        t0 = time.time()
        # try to load lyrics by id if available
        lyrics = _load_lyrics_for_id(p.get('id',''))
        res = detect_sections(audio, chords=None, weights=weights, algorithm='heuristic', prob_threshold=0.0, lyrics=lyrics)
        meta = res.get('meta', {})
        cand = meta.get('candidate_count', None)
        kept = meta.get('kept_count', None)
        det = [{'start_s': s['start_ms']/1000.0, 'end_s': (s['start_ms']+s['duration_ms'])/1000.0} for s in res.get('sections',[])]
        f = _boundary_f1(ref, det, 3.0)
        results.append({'id': p['id'], 'f1_3.0': f['f1'], 'candidate_count': cand, 'kept_count': kept, 'time_s': round(time.time()-t0,2)})
        print('harmonix id', p['id'], 'F1@3.0', f['f1'])
    summary = {'mean_f1_3.0': round(mean([r['f1_3.0'] for r in results]) if results else 0.0,4), 'n': len(results)}
    out = {'date': time.strftime('%Y-%m-%d %H:%M'), 'summary': summary, 'per_song': results}
    (OUT / 'promoted_wave15_harmonix_with_lyrics.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote results/promoted_wave15_harmonix_with_lyrics.json')
    return out


def run_salami(weights, max_songs: int = 30):
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=max_songs)
    results = []
    for p in pairs:
        audio = Path(p['audio'])
        ann = Path(p['annotation'])
        ref = _parse_salami_sections(ann)
        lyrics = _load_lyrics_for_id(p['id'])
        if lyrics:
            print(f'Using lyrics for {p["id"]} ({len(lyrics)} intervals)')
        else:
            print(f'No lyrics for {p["id"]}')
        t0 = time.time()
        res = detect_sections(audio, chords=None, weights=weights, algorithm='heuristic', prob_threshold=0.0, lyrics=lyrics)
        meta = res.get('meta', {})
        cand = meta.get('candidate_count', None)
        kept = meta.get('kept_count', None)
        det = [{'start_s': s['start_ms']/1000.0, 'end_s': (s['start_ms']+s['duration_ms'])/1000.0} for s in res.get('sections',[])]
        f05 = _boundary_f1(ref, det, 0.5)
        f30 = _boundary_f1(ref, det, 3.0)
        results.append({'id': p['id'], 'f1_0.5': f05['f1'], 'f1_3.0': f30['f1'], 'candidate_count': cand, 'kept_count': kept, 'time_s': round(time.time()-t0,2)})
        print('salami id', p['id'], 'F1@3.0', f30['f1'])
    summary = {'F1@0.5': {'mean': round(mean([r['f1_0.5'] for r in results]) if results else 0.0,4), 'n': len(results)}, 'F1@3.0': {'mean': round(mean([r['f1_3.0'] for r in results]) if results else 0.0,4), 'n': len(results)}}
    out = {'date': time.strftime('%Y-%m-%d %H:%M'), 'summary': summary, 'per_song': results}
    (OUT / 'promoted_wave15_salami_with_lyrics.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote results/promoted_wave15_salami_with_lyrics.json')
    return out


def main():
    weights = load_wave15_weights()
    print('Loaded wave15 weights:', weights)
    h = run_harmonix(weights, max_songs=30)
    s = run_salami(weights, max_songs=30)
    print('Done')


if __name__ == '__main__':
    main()
