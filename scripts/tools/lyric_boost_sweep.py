#!/usr/bin/env python3
"""Sweep lyric-gap boost multiplier and evaluate SALAMI F1@3.0 on 20-song pilot.

This script loads base candidate scores (no lyrics), applies an adjustable
boost to candidates near lyric gaps and a penalty to those inside lyric
lines, re-runs NMS, builds sections, and computes boundary F1@3.0.
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

from scripts.analysis import section_detector as detmod
from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

LYRICS_DIR = Path('data/lyrics')


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


def run_sweep(boost_values=(0.0, 0.25, 0.5, 0.75, 1.0), penalty_mult=1.0, max_songs=20):
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=max_songs)
    results = []
    for boost in boost_values:
        t0 = time.time()
        per_song = []
        for p in pairs:
            audio = Path(p['audio'])
            ann = Path(p['annotation'])
            ref = _parse_salami_sections(ann)
            lyrics = _load_lyrics_for_id(p['id'])

            # Base run: get candidates and base scores with no lyrics
            base = detmod.detect_sections(audio, chords=None, weights=None, algorithm='heuristic', prob_threshold=0.0, lyrics=None)
            candidates = base.get('candidates', [])
            if not candidates:
                per_song.append({'id': p['id'], 'f1_3.0': 0.0})
                continue

            times = [c['time_s'] for c in candidates]
            scores = [float(c.get('score', 0.0)) for c in candidates]

            # Build lyric intervals and gaps
            lyric_intervals = []
            gaps = []
            if lyrics:
                for l in lyrics:
                    s = float(l.get('start', l.get('time', 0)))
                    e = float(l.get('end', l.get('time', 0)))
                    lyric_intervals.append((s, e))
                lyric_intervals.sort()
                for a, b in zip(lyric_intervals, lyric_intervals[1:]):
                    gs = a[1]; ge = b[0]
                    if ge - gs > 0.05:
                        gaps.append((gs, ge))

            # Apply adjustable penalties/boosts
            base_penalty = 0.1
            base_boost = 0.15
            adj_scores = []
            for i, t in enumerate(times):
                s = scores[i]
                if lyrics and any(s0 <= t <= e0 for s0, e0 in lyric_intervals):
                    s = max(0.0, s - penalty_mult * base_penalty)
                else:
                    if lyrics:
                        for gs, ge in gaps:
                            center = (gs + ge) / 2.0
                            if abs(t - center) <= 2.0:
                                s = min(1.0, s + boost * base_boost)
                                break
                adj_scores.append(s)

            # Re-run NMS using detector's helper
            import numpy as np
            kept_mask = detmod._nms_by_score(np.array(times), np.array(adj_scores), min_gap_sec=detmod.NMS_DISTANCE_SEC)
            kept_sorted = sorted(float(t) for i, t in enumerate(times) if kept_mask[i])
            # enforce min_section_sec
            final = []
            for t in kept_sorted:
                prev = final[-1] if final else 0.0
                if t - prev >= detmod.MIN_SECTION_SEC:
                    final.append(t)

            boundary_times = [0.0] + sorted(final) + [base.get('meta', {}).get('duration_s', 0.0)]
            sections = [{'start_s': boundary_times[i], 'end_s': boundary_times[i+1]} for i in range(len(boundary_times)-1) if boundary_times[i+1]-boundary_times[i]>=1.0]
            det = [{'start_s': s['start_s'], 'end_s': s['end_s']} for s in sections]
            f30 = _boundary_f1(ref, det, 3.0)
            per_song.append({'id': p['id'], 'f1_3.0': f30['f1']})

        mean_f = round(mean([x['f1_3.0'] for x in per_song]) if per_song else 0.0, 4)
        results.append({'boost': boost, 'penalty_mult': penalty_mult, 'mean_f1_3.0': mean_f, 'n': len(per_song)})
        print(f'boost={boost} -> mean F1@3.0={mean_f} (n={len(per_song)}) in {round(time.time()-t0,1)}s')

    (OUT / 'salami_lyric_boost_sweep.json').write_text(json.dumps({'results': results}, indent=2), encoding='utf-8')
    print('Wrote results/salami_lyric_boost_sweep.json')


if __name__ == '__main__':
    run_sweep()
