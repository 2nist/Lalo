#!/usr/bin/env python3
"""Compare NMS strategies on SALAMI: score-first, time-first, and hybrid time-first with score tie-break.

Writes: results/nms_strategy_compare_salami_hybrid.json
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections, _nms_by_score, NMS_DISTANCE_SEC
from scripts.bench.salami_benchmark import _load_salami_pairs, _parse_salami_sections, _boundary_f1

OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)


def load_promoted_weights():
    p = OUT / 'sections-machine-b-promote-wave15.json'
    j = json.loads(p.read_text(encoding='utf-8'))
    return j.get('weights') or {}


def nms_time_order(times: np.ndarray, min_gap_sec: float) -> np.ndarray:
    if len(times) == 0:
        return np.array([], dtype=bool)
    order = np.argsort(times)
    kept = np.zeros(len(times), dtype=bool)
    kept_times = []
    for idx in order:
        t = float(times[idx])
        if all(abs(t - k) >= min_gap_sec for k in kept_times):
            kept[idx] = True
            kept_times.append(t)
    return kept


def nms_time_score_tiebreak(times: np.ndarray, scores: np.ndarray, min_gap_sec: float) -> np.ndarray:
    """Time-ordered NMS where conflicts within the gap are resolved by keeping the higher-scoring candidate.

    Iterate left-to-right; if a candidate falls within `min_gap_sec` of an already-kept candidate,
    replace the existing kept candidate only if the new candidate has a strictly higher score.
    """
    if len(times) == 0:
        return np.array([], dtype=bool)
    order = np.argsort(times)
    kept = np.zeros(len(times), dtype=bool)
    kept_indices: list[int] = []
    for idx in order:
        t = float(times[idx])
        # find any existing kept index within min_gap_sec
        conflict_idx = None
        for k in kept_indices:
            if abs(t - float(times[k])) < min_gap_sec:
                conflict_idx = k
                break
        if conflict_idx is None:
            kept[idx] = True
            kept_indices.append(idx)
        else:
            # if newcomer has higher score, replace the conflicted kept
            try:
                if float(scores[idx]) > float(scores[conflict_idx]):
                    kept[conflict_idx] = False
                    kept[idx] = True
                    kept_indices.remove(conflict_idx)
                    kept_indices.append(idx)
            except Exception:
                # on any issue, prefer existing kept candidate
                pass
    return kept


def run_all(max_songs: int = 500):
    weights = load_promoted_weights()
    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=max_songs)
    results = []
    for p in pairs:
        sid = str(p['id'])
        audio = Path(p['audio'])
        ann = Path(p['annotation'])
        ref = _parse_salami_sections(ann)
        res = detect_sections(audio, chords=None, weights=None, algorithm='heuristic', prob_threshold=0.0)
        cands = res.get('candidates', [])
        times = np.array([float(c.get('time_s', 0.0)) for c in cands])
        features = [c.get('features', {}) for c in cands]
        promoted_scores = np.array([sum(features[i].get(k, 0.0) * weights.get(k, 0.0) for k in features[i]) for i in range(len(features))]) if features else np.array([])

        # Score-first NMS
        kept_score = _nms_by_score(times, promoted_scores, min_gap_sec=NMS_DISTANCE_SEC)
        det_score = [{'start_s': float(times[i]), 'end_s': float(times[i]) + 1.0} for i, k in enumerate(kept_score) if k]
        f_score = _boundary_f1(ref, det_score, 3.0)

        # Time-first NMS
        kept_time = nms_time_order(times, min_gap_sec=NMS_DISTANCE_SEC)
        det_time = [{'start_s': float(times[i]), 'end_s': float(times[i]) + 1.0} for i, k in enumerate(kept_time) if k]
        f_time = _boundary_f1(ref, det_time, 3.0)

        # Hybrid time-first with score tie-break
        kept_hybrid = nms_time_score_tiebreak(times, promoted_scores, min_gap_sec=NMS_DISTANCE_SEC)
        det_hybrid = [{'start_s': float(times[i]), 'end_s': float(times[i]) + 1.0} for i, k in enumerate(kept_hybrid) if k]
        f_hybrid = _boundary_f1(ref, det_hybrid, 3.0)

        results.append({'id': sid, 'f1_score_nms_3.0': f_score['f1'], 'f1_time_nms_3.0': f_time['f1'], 'f1_hybrid_nms_3.0': f_hybrid['f1'], 'n_candidates': len(cands), 'kept_score': int(sum(kept_score)), 'kept_time': int(sum(kept_time)), 'kept_hybrid': int(sum(kept_hybrid))})
        print('id', sid, 'score_nms', f_score['f1'], 'time_nms', f_time['f1'], 'hybrid', f_hybrid['f1'])

    out = {'date': __import__('time').strftime('%Y-%m-%d %H:%M'), 'per_song': results, 'summary': {'score_nms_mean': round(mean([r['f1_score_nms_3.0'] for r in results]) if results else 0.0,4), 'time_nms_mean': round(mean([r['f1_time_nms_3.0'] for r in results]) if results else 0.0,4), 'hybrid_nms_mean': round(mean([r['f1_hybrid_nms_3.0'] for r in results]) if results else 0.0,4), 'n': len(results)}}
    (OUT / 'nms_strategy_compare_salami_hybrid.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('Wrote results/nms_strategy_compare_salami_hybrid.json')


if __name__ == '__main__':
    run_all(max_songs=500)
