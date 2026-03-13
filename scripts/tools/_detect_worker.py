#!/usr/bin/env python3
import json
import sys
from pathlib import Path
ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))
from scripts.analysis.section_detector import detect_sections

def main():
    if len(sys.argv) < 4:
        print('usage: _detect_worker.py <audio_path> <weights_json> <out_json>')
        sys.exit(2)
    audio_path = sys.argv[1]
    weights_path = sys.argv[2]
    out_path = sys.argv[3]
    weights = {}
    try:
        with open(weights_path, 'r') as f:
            weights = json.load(f)
    except Exception:
        weights = {}
    # extract control params from weights dict (not forwarded as weight signals)
    prob_threshold = float(weights.pop('prob_threshold', 0.0))
    nms_gap_sec = float(weights.pop('nms_gap_sec', 8.0))
    cand_prominence = float(weights.pop('cand_prominence', 0.18))
    # ensure output dir exists before any file write
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    # run detection
    try:
        res = detect_sections(Path(audio_path), chords=None, weights=weights, min_section_sec=4.0, nms_gap_sec=nms_gap_sec, beat_snap_sec=0.0, algorithm='heuristic', prob_threshold=prob_threshold, random_seed=42, downbeat_confidence_thresh=0.4, cand_prominence=cand_prominence)
        with open(out_path, 'w') as f:
            json.dump(res, f)
    except Exception as e:
        with open(out_path, 'w') as f:
            json.dump({'error': str(e)}, f)

if __name__ == '__main__':
    main()
