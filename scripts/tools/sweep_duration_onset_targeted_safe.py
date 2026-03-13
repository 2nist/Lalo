#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import subprocess
import tempfile
ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))
from scripts.bench.section_benchmark import _load_harmonix_pairs, _boundary_f1, HARMONIX_DIR, AUDIO_DIR, _parse_harmonix_sections

# targeted IDs (top-FP regressions from prior analysis)
target_ids = [
    '0027_blackened', '0014_babaoriley', '0021_better', '0013_athingaboutyou',
    '0006_aint2proud2beg', '0017_badromance', '0036_breakingthegirl', '0003_6foot7foot'
]

# Load Wave9 baseline
wave9_path = Path('results/sections-machine-b-wave9.json')
if not wave9_path.exists():
    raise SystemExit('Missing baseline results/sections-machine-b-wave9.json')
wave9 = json.loads(wave9_path.read_text())
weights = wave9.get('weights') or {}

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=300)
pair_map = {p.get('id'): p for p in pairs if p.get('id')}
with_audio = [pair_map[i] for i in target_ids if i in pair_map]

print('target_count', len(with_audio))

# sweep ranges
duration_offsets = [0.06, 0.08, 0.10, 0.12]

results_out = []
for off in duration_offsets:
    w = dict(weights)
    w['duration_prior'] = round(w.get('duration_prior', 0.0) + off, 4)
    tot_tp = tot_fp = tot_fn = 0
    tot_preds = 0
    count = 0
    for p in with_audio:
        audio_path = p.get('audio')
        if not audio_path:
            print('skipping no-audio id', p.get('id'))
            continue
        print('processing id', p.get('id'))
        # write weights to temp file and call worker with timeout
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as wf:
            json.dump(w, wf)
            wf_path = wf.name
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as outf:
            out_path = outf.name
        try:
            subprocess.run([sys.executable, 'scripts/tools/_detect_worker.py', str(audio_path), wf_path, out_path], timeout=90, check=False)
            # read out_path
            try:
                r = json.loads(Path(out_path).read_text())
            except Exception as e:
                print('failed to read worker output for', p.get('id'), e)
                continue
            if 'error' in r:
                print('worker error for', p.get('id'), r.get('error'))
                continue
            res = r
        except subprocess.TimeoutExpired:
            print('timeout for id', p.get('id'))
            continue
        except Exception as e:
            print('subprocess error for id', p.get('id'), e)
            continue
        det_raw = res.get('sections', [])
        det = []
        for ss in det_raw:
            if 'start_ms' in ss and 'duration_ms' in ss:
                start_s = float(ss['start_ms']) / 1000.0
                end_s = start_s + float(ss['duration_ms']) / 1000.0
                det.append({'start_s': start_s, 'end_s': end_s})
        ref = _parse_harmonix_sections(Path(p['sections_file']))
        b = _boundary_f1(ref, det, 0.5)
        tot_tp += b['tp']; tot_fp += b['fp']; tot_fn += b['fn']; tot_preds += b.get('pred_boundaries', 0); count += 1
    precision = round(tot_tp / (tot_tp + tot_fp), 4) if (tot_tp + tot_fp) > 0 else 0.0
    recall = round(tot_tp / (tot_tp + tot_fn), 4) if (tot_tp + tot_fn) > 0 else 0.0
    avg_pred = round(tot_preds / count, 3) if count > 0 else 0.0
    results_out.append({'duration_offset': off, 'tp': tot_tp, 'fp': tot_fp, 'fn': tot_fn, 'precision': precision, 'recall': recall, 'avg_pred_per_song': avg_pred})
    print(f"off={off} tp={tot_tp} fp={tot_fp} avg_pred={avg_pred}")
    # write incremental results after each offset so partial progress is saved
    outp = Path('results/sweep_duration_onset_targeted_safe.json')
    outp.write_text(json.dumps(results_out, indent=2))
    print('Updated', outp)

print('Finished sweep; final results in results/sweep_duration_onset_targeted_safe.json')
