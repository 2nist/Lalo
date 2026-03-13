#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import argparse

ROOT = Path('.').resolve()
import sys
sys.path.insert(0, str(ROOT))

from scripts.analysis.section_detector import detect_sections

BASELINE_PATH = Path('results') / 'salami_baseline_mild_prune.full.json'

p = argparse.ArgumentParser()
p.add_argument('--max-songs', type=int, default=30)
p.add_argument('--nms_gap_sec', type=float, default=12.0)
p.add_argument('--min_section_sec', type=float, default=6.0)
p.add_argument('--prominence', type=float, default=0.25)
p.add_argument('--sub_prominence', type=float, default=0.3)
p.add_argument('--out', default='results/candidate_counts_promoted_prune.json')
args = p.parse_args()

if not BASELINE_PATH.exists():
    print('Baseline results not found:', BASELINE_PATH)
    sys.exit(1)

baseline = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))
weights = baseline.get('weights', {})

# build salami pairs
ann_dir = Path('datasets') / 'mcgill' / 'mcgill_jcrd_salami_Billboard'
audio_dir = Path('data') / 'salami_audio'

pairs = []
for audio_file in sorted(audio_dir.glob('[0-9]*.m4a'), key=lambda p: int(p.stem)):
    ann_candidates = sorted(ann_dir.glob(f'{int(audio_file.stem):04d}_*.json'))
    if not ann_candidates:
        continue
    pairs.append({'id': audio_file.stem, 'audio': str(audio_file), 'annotation': str(ann_candidates[0])})

pairs = pairs[: args.max_songs]
print('Running candidate counts on', len(pairs), 'songs')

results = []
for p in pairs:
    audio = Path(p['audio'])
    try:
        r = detect_sections(
            audio,
            chords=None,
            weights=weights,
            beat_snap_sec=0,
            algorithm='heuristic',
            downbeat_confidence_thresh=0.0,
            min_section_sec=args.min_section_sec,
            nms_gap_sec=args.nms_gap_sec,
            cand_prominence=args.prominence,
            cand_sub_prominence=args.sub_prominence,
        )
    except Exception as e:
        print('error detect', p['id'], e)
        continue
    cand_count = len(r.get('candidates', []) or [])
    sec_count = len(r.get('sections', []) or [])
    results.append({'id': p['id'], 'candidates': cand_count, 'sections': sec_count, 'meta': r.get('meta', {})})
    print('id', p['id'], 'candidates', cand_count, 'sections', sec_count)

outp = Path(args.out)
outp.write_text(json.dumps(results, indent=2), encoding='utf-8')
print('Wrote', outp)
