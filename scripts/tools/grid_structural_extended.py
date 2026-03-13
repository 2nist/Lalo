#!/usr/bin/env python3
import json
from pathlib import Path
from statistics import mean
import argparse
import sys

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import DEFAULT_WEIGHTS, detect_sections

ann_dir = ROOT / 'datasets' / 'mcgill' / 'mcgill_jcrd_salami_Billboard'
audio_dir = ROOT / 'data' / 'salami_audio'

results_dir = Path('results')
results_dir.mkdir(parents=True, exist_ok=True)

# sample first 30 SALAMI pairs
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

parser = argparse.ArgumentParser(description='Extended structural sweep (msaf_vote x repetition_break)')
parser.add_argument('--out', type=Path, default=results_dir / 'grid_structural_extended.json')
parser.add_argument('--nms_gap_sec', type=float, default=12.0)
parser.add_argument('--min_section_sec', type=float, default=6.0)
parser.add_argument('--prominence', type=float, default=0.25)
parser.add_argument('--sub_prominence', type=float, default=0.3)
args = parser.parse_args()

msaf_vote_weights = [0.01, 0.03, 0.05, 0.1, 0.2, 0.3]
rep_break_weights = [0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 1.0]

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
            try:
                with ann_path.open('r', encoding='utf-8') as fh:
                    ann = json.load(fh)
            except Exception:
                continue
            ref_sections = []
            for s in ann.get('sections', []):
                start_s = float(s.get('start_ms', 0.0)) / 1000.0
                dur_s = float(s.get('duration_ms', 0.0)) / 1000.0
                if dur_s <= 0:
                    continue
                ref_sections.append({'start_s': start_s, 'end_s': start_s + dur_s})
            if not ref_sections:
                continue
            det_res = detect_sections(
                audio,
                chords=None,
                weights=combo_weights,
                beat_snap_sec=0,
                algorithm='heuristic',
                downbeat_confidence_thresh=0.0,
                min_section_sec=args.min_section_sec,
                nms_gap_sec=args.nms_gap_sec,
                cand_prominence=args.prominence,
                cand_sub_prominence=args.sub_prominence,
            )
            det_sections = [
                {
                    'start_s': float(s['start_ms']) / 1000.0,
                    'end_s': (float(s['start_ms']) + float(s['duration_ms'])) / 1000.0,
                }
                for s in det_res.get('sections', [])
            ]
            # simple boundary F1@0.5 calculation
            ref_b = sorted(set(round(s['start_s'], 3) for s in ref_sections))
            if ref_b:
                ref_b = [t for t in ref_b if t > ref_b[0] + 0.1]
            pred_b = sorted(set(round(s['start_s'], 3) for s in det_sections))
            if pred_b:
                pred_b = [t for t in pred_b if t > pred_b[0] + 0.1]
            tp = 0
            used = set()
            for p in pred_b:
                best_i = None
                best_d = float('inf')
                for i, r in enumerate(ref_b):
                    if i in used:
                        continue
                    d = abs(p - r)
                    if d <= 0.5 and d < best_d:
                        best_d = d
                        best_i = i
                if best_i is not None:
                    used.add(best_i)
                    tp += 1
            fp = len(pred_b) - tp
            fn = len(ref_b) - tp
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_values.append(round(f1, 4))
            pred_counts.append(len(pred_b))
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
            args.out.write_text(json.dumps(results, indent=2), encoding='utf-8')
        except Exception:
            pass
        print('msaf_vote', msaf_weight, 'rep_break', rep_weight, 'F1@0.5', mean_f1)

try:
    args.out.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print('Wrote', str(args.out))
    best = max(results, key=lambda x: x['salami_f1_05'], default=None)
    if best:
        print('best combo', best)
except Exception as e:
    print('failed to write final results', e)
