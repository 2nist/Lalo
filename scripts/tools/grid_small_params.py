#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import os

from statistics import mean

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))
from scripts.bench.section_benchmark import (
    _load_harmonix_pairs,
    _boundary_f1,
    HARMONIX_DIR,
    AUDIO_DIR,
)
from scripts.bench.salami_benchmark import _parse_salami_sections
from scripts.analysis.section_detector import (
    DEFAULT_WEIGHTS,
    detect_sections,
)

# targets (top regressions)
target_ids = [
    '0021_better',
    '0017_badromance',
    '0027_blackened',
    '0014_babaoriley',
    '0036_breakingthegirl',
    '0006_aint2proud2beg',
    '0003_6foot7foot',
    '0026_blackandyellow',
]

ann_dir = ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard'
audio_dir = ROOT / 'data' / 'salami_audio'

results_dir = Path('results')
traces_dir = results_dir / 'traces'
results_dir.mkdir(parents=True, exist_ok=True)
traces_dir.mkdir(parents=True, exist_ok=True)

wave9_path = results_dir / 'sections-machine-b-wave9.json'
if not wave9_path.exists():
    raise SystemExit('Missing baseline results/sections-machine-b-wave9.json')
wave9 = json.loads(wave9_path.read_text())
base_weights = wave9.get('weights') or {}
base_duration = float(base_weights.get('duration_prior', 0.0))

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=400)
pair_map = {p.get('id'): p for p in pairs if p.get('id')}
with_audio = [pair_map[i] for i in target_ids if i in pair_map]
print('will run on', len(with_audio), 'songs')

salami_pairs = []
for audio_file in sorted(audio_dir.glob('[0-9]*.m4a'), key=lambda p: int(p.stem)):
    ann_candidates = sorted(ann_dir.glob(f'{int(audio_file.stem):04d}_*.json'))
    if not ann_candidates:
        continue
    salami_pairs.append({
        'id': audio_file.stem,
        'audio': str(audio_file),
        'annotation': str(ann_candidates[0]),
    })
salami_sample = salami_pairs[:30]


def run_harmonix_grid(out_path: Path) -> None:
    nms_gap_values = [8, 12, 16, 20]
    cand_prominence_values = [0.18, 0.30, 0.45]
    out_path = out_path or results_dir / 'grid_small_params.json'
    results = []
    for nms in nms_gap_values:
        for prom in cand_prominence_values:
            w = dict(base_weights)
            w['nms_gap_sec'] = nms
            w['cand_prominence'] = round(prom, 4)
            tot_tp = tot_fp = tot_fn = tot_preds = count = 0
            for p in with_audio:
                audio = p.get('audio')
                if not audio:
                    continue
                wf_path = None
                try:
                    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as wf:
                        json.dump(w, wf)
                        wf_path = wf.name
                    outp = traces_dir / (p.get('id') + f'.grid.nms{nms}.prom{prom}.json')
                    try:
                        subprocess.run(
                            [sys.executable, 'scripts/tools/_detect_worker.py', str(audio), wf_path, str(outp)],
                            timeout=120,
                            check=False,
                        )
                    except subprocess.TimeoutExpired:
                        print('timeout', p.get('id'))
                        continue
                    if not outp.exists():
                        print('no output from worker for', p.get('id'))
                        continue
                    try:
                        r = json.loads(outp.read_text())
                    except Exception as e:
                        print('error reading json for', p.get('id'), e)
                        continue
                finally:
                    if wf_path and os.path.exists(wf_path):
                        try:
                            os.remove(wf_path)
                        except Exception:
                            pass
                if 'error' in r:
                    print('worker error', p.get('id'), r.get('error'))
                    continue
                det_raw = r.get('sections', [])
                det = []
                for ss in det_raw:
                    if 'start_ms' in ss and 'duration_ms' in ss:
                        start_s = float(ss['start_ms']) / 1000.0
                        end_s = start_s + float(ss['duration_ms']) / 1000.0
                        det.append({'start_s': start_s, 'end_s': end_s})
                ref = _parse_harmonix_sections(Path(p['sections_file']))
                b = _boundary_f1(ref, det, 0.5)
                tot_tp += b['tp']
                tot_fp += b['fp']
                tot_fn += b['fn']
                tot_preds += b.get('pred_boundaries', 0)
                count += 1
            precision = round(tot_tp / (tot_tp + tot_fp), 4) if (tot_tp + tot_fp) > 0 else 0.0
            recall = round(tot_tp / (tot_tp + tot_fn), 4) if (tot_tp + tot_fn) > 0 else 0.0
            row = {
                'nms_gap_sec': nms,
                'cand_prominence': prom,
                'tp': tot_tp,
                'fp': tot_fp,
                'fn': tot_fn,
                'precision': precision,
                'recall': recall,
                'avg_pred_per_song': round(tot_preds / count, 3) if count else 0.0,
            }
            results.append(row)
            try:
                out_path.write_text(json.dumps(results, indent=2))
            except Exception as e:
                print('failed to write incremental results', e)
            print('nms', nms, 'prom', prom, 'tp', tot_tp, 'fp', tot_fp)
    try:
        out_path.write_text(json.dumps(results, indent=2))
        print('Wrote', str(out_path))
    except Exception as e:
        print('failed to write final results', e)


def run_structural_grid(out_path: Path, prune_overrides: dict = None) -> None:
    msaf_vote_weights = [0.05, 0.10, 0.15, 0.20, 0.30]
    rep_break_weights = [0.05, 0.10, 0.15, 0.20]
    out_path = out_path or results_dir / 'grid_structural.json'
    results = []
    for msaf_weight in msaf_vote_weights:
        for rep_weight in rep_break_weights:
            combo_weights = dict(DEFAULT_WEIGHTS)
            combo_weights['msaf_vote'] = msaf_weight
            combo_weights['repetition_break'] = rep_weight
            f1_values = []
            pred_counts = []
            for pair in salami_sample:
                audio = Path(pair['audio'])
                ann_path = Path(pair['annotation'])
                ref_sections = _parse_salami_sections(ann_path)
                if not ref_sections:
                    continue
                det_res = detect_sections(
                    audio,
                    chords=None,
                    weights=combo_weights,
                    beat_snap_sec=0,
                    algorithm='heuristic',
                    downbeat_confidence_thresh=0.0,
                    min_section_sec=(prune_overrides.get('min_section_sec') if prune_overrides else None),
                    nms_gap_sec=(prune_overrides.get('nms_gap_sec') if prune_overrides else None),
                    cand_prominence=(prune_overrides.get('prominence') if prune_overrides else None),
                    cand_sub_prominence=(prune_overrides.get('sub_prominence') if prune_overrides else None),
                )
                det_sections = [
                    {
                        'start_s': float(s['start_ms']) / 1000.0,
                        'end_s': float(s['start_ms'] + s['duration_ms']) / 1000.0,
                    }
                    for s in det_res.get('sections', [])
                ]
                b = _boundary_f1(ref_sections, det_sections, 0.5)
                f1_values.append(b['f1'])
                pred_counts.append(len(det_sections))
            mean_f1 = round(mean(f1_values), 4) if f1_values else 0.0
            avg_preds = round(mean(pred_counts), 3) if pred_counts else 0.0
            row = {
                'msaf_vote': msaf_weight,
                'repetition_break': rep_weight,
                'salami_f1_05': mean_f1,
                'avg_pred_per_song': avg_preds,
            }
            results.append(row)
            try:
                out_path.write_text(json.dumps(results, indent=2))
            except Exception as e:
                print('failed to write incremental results', e)
            print('msaf_vote', msaf_weight, 'rep_break', rep_weight, 'F1@0.5', mean_f1)
    try:
        out_path.write_text(json.dumps(results, indent=2))
        print('Wrote', str(out_path))
        best = max(results, key=lambda x: x['salami_f1_05'], default=None)
        if best:
            print('best combo', best)
    except Exception as e:
        print('failed to write final results', e)


def main() -> None:
    parser = argparse.ArgumentParser(description='Run small grid parameter experiments')
    parser.add_argument(
        '--grid',
        choices=[None, 'structural'],
        default=None,
        help='Choose which grid to run',
    )
    parser.add_argument(
        '--out',
        type=Path,
        default=results_dir / 'grid_small_params.json',
        help='Output JSON path',
    )
    parser.add_argument(
        '--nms_gap_sec',
        type=float,
        default=None,
        help='Override NMS gap seconds for candidate pruning',
    )
    parser.add_argument(
        '--min_section_sec',
        type=float,
        default=None,
        help='Override minimum section seconds for candidate pruning',
    )
    parser.add_argument(
        '--prominence',
        type=float,
        default=None,
        help='Override candidate prominence threshold',
    )
    parser.add_argument(
        '--sub_prominence',
        type=float,
        default=None,
        help='Override candidate sub-prominence threshold',
    )
    args = parser.parse_args()
    if args.grid == 'structural':
        prune_overrides = {
            'nms_gap_sec': args.nms_gap_sec,
            'min_section_sec': args.min_section_sec,
            'prominence': args.prominence,
            'sub_prominence': args.sub_prominence,
        }
        run_structural_grid(args.out, prune_overrides)
    else:
        run_harmonix_grid(args.out)


if __name__ == '__main__':
    main()
