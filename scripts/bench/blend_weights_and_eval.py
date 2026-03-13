#!/usr/bin/env python3
"""Blend promoted DEFAULT_WEIGHTS with XGB-learned weights and evaluate Harmonix dev.

Writes: results/blend_weights_sweep.json and per-blend Harmonix outputs.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import DEFAULT_WEIGHTS

LEARNED = Path('results/learned_weights_xgb.json')
OUT = Path('results')
OUT.mkdir(parents=True, exist_ok=True)

ALPHAS = [0.0, 0.25, 0.5, 0.75, 1.0]

# mapping learned keys -> CLI args
KEY_MAP = {
    'flux_peak': '--weight-flux',
    'chord_novelty': '--weight-chord',
    'cadence_score': '--weight-cadence',
    'repetition_break': '--weight-repetition',
    'duration_prior': '--weight-duration',
    'chroma_change': '--weight-chroma',
    'spec_contrast': '--weight-spec-contrast',
    'onset_density': '--weight-onset-density',
    'rms_energy': '--weight-rms',
}

def load_learned():
    if not LEARNED.exists():
        raise SystemExit('Missing learned weights: results/learned_weights_xgb.json')
    data = json.loads(LEARNED.read_text(encoding='utf-8'))
    return data.get('weights', {})


def blend(w_promoted, w_learned, alpha: float):
    out = {}
    for k in KEY_MAP.keys():
        p = float(w_promoted.get(k, 0.0))
        l = float(w_learned.get(k, 0.0))
        out[k] = (1.0 - alpha) * p + alpha * l
    return out


def run_bench(weights_map, out_path):
    # Build CLI args mapping
    cmd = [sys.executable, 'scripts/bench/section_benchmark.py', '--dev-only', '--algorithm', 'heuristic', '--out', str(out_path)]
    # add mapped weights
    for k, arg in KEY_MAP.items():
        val = weights_map.get(k, 0.0)
        cmd.extend([arg, str(round(float(val), 6))])
    subprocess.run(cmd, check=True)


def main():
    learned = load_learned()
    promoted = {
        'flux_peak': DEFAULT_WEIGHTS.get('flux_peak', 0.0),
        'chord_novelty': DEFAULT_WEIGHTS.get('chord_novelty', 0.0),
        'cadence_score': DEFAULT_WEIGHTS.get('cadence_score', 0.0),
        'repetition_break': DEFAULT_WEIGHTS.get('repetition_break', 0.0),
        'duration_prior': DEFAULT_WEIGHTS.get('duration_prior', 0.0),
        'chroma_change': DEFAULT_WEIGHTS.get('chroma_change', 0.0),
        'spec_contrast': DEFAULT_WEIGHTS.get('spec_contrast', 0.0),
        'onset_density': DEFAULT_WEIGHTS.get('onset_density', 0.0),
        'rms_energy': DEFAULT_WEIGHTS.get('rms_energy', 0.0),
    }

    results = []
    for a in ALPHAS:
        print('Blending alpha=', a)
        blended = blend(promoted, learned, a)
        out_file = OUT / f'harmonix_blend_alpha_{a:.2f}.json'
        run_bench(blended, out_file)
        data = json.loads(out_file.read_text(encoding='utf-8'))
        mean_f1_3 = data.get('summary', {}).get('detector', {}).get('F1@3.0s', {}).get('mean')
        results.append({'alpha': a, 'mean_f1_3.0': mean_f1_3, 'out': str(out_file)})
        print('  mean F1@3.0 =', mean_f1_3)
    Path(OUT / 'blend_weights_sweep.json').write_text(json.dumps(results, indent=2))
    print('Wrote results/blend_weights_sweep.json')

if __name__ == '__main__':
    main()
