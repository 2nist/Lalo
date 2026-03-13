#!/usr/bin/env python3
"""Dump detector candidate traces for a list of SALAMI song ids.

Writes JSON traces to `results/traces/trace_{id}_alpha1_th0.20.json` by default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.bench.salami_benchmark import _load_salami_pairs


def load_weights(path: Path):
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    return data.get('weights') or data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ids', nargs='+', required=True, help='SALAMI song ids to dump')
    ap.add_argument('--prob-threshold', type=float, default=0.2)
    ap.add_argument('--weights-file', default='results/harmonix_blend_alpha_1.00_th_0.20.json')
    ap.add_argument('--max-songs', type=int, default=200)
    args = ap.parse_args()

    weights = load_weights(Path(args.weights_file))
    if weights is None:
        raise SystemExit(f'Weights file not found or invalid: {args.weights_file}')

    pairs = _load_salami_pairs(ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard', ROOT / 'data' / 'salami_audio', max_songs=args.max_songs)
    id_set = set(args.ids)

    from scripts.analysis.section_detector import detect_sections

    out_dir = Path('results') / 'traces'
    out_dir.mkdir(parents=True, exist_ok=True)

    found = 0
    for p in pairs:
        pid = p.get('id')
        if pid is None or pid not in id_set:
            continue
        audio = p.get('audio')
        if not audio:
            print('no audio for', pid)
            continue
        trace_path = out_dir / f'trace_{pid}_alpha1_th{args.prob_threshold:.2f}.json'
        try:
            res = detect_sections(audio, chords=None, weights=weights, algorithm='scored', prob_threshold=args.prob_threshold, min_section_sec=4.0, nms_gap_sec=8.0, cand_prominence=0.18, cand_sub_prominence=0.3, trace_path=trace_path)
            print('Wrote trace for', pid, '->', trace_path)
            found += 1
        except Exception as exc:
            print('error for', pid, exc)

    if found == 0:
        print('No matching ids found in SALAMI pairs list')


if __name__ == '__main__':
    main()
