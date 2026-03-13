#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess, sys, tempfile

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))
from scripts.bench.section_benchmark import _load_harmonix_pairs, HARMONIX_DIR, AUDIO_DIR, _boundary_f1, _parse_harmonix_sections

# targeted IDs (top-FP regressions)
target_ids = [
    '0021_better','0017_badromance','0027_blackened','0014_babaoriley',
    '0036_breakingthegirl','0006_aint2proud2beg','0003_6foot7foot','0026_blackandyellow'
]

pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=400)
pair_map = {p.get('id'): p for p in pairs if p.get('id')}
with_audio = [pair_map[i] for i in target_ids if i in pair_map]

duration_offsets = [0.06, 0.08, 0.10, 0.12]
prob_thresholds = [0.0, 0.3, 0.5]

results = []
Path('results').mkdir(parents=True, exist_ok=True)

for off in duration_offsets:
    for prob in prob_thresholds:
        tot_tp = tot_fp = tot_fn = 0
        tot_preds = 0
        count = 0
        print(f"Running off={off} prob={prob}")
        for p in with_audio:
            audio_path = p.get('audio')
            if not audio_path:
                continue
            # prepare weights file with duration offset
            # read baseline weights
            from pathlib import Path as P
            baseline = json.loads(P('results/sections-machine-b-wave9.json').read_text())
            w = baseline.get('weights', {})
            w = dict(w)
            w['duration_prior'] = round(w.get('duration_prior', 0.0) + off, 4)
            # write weights to temp file
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as wf:
                json.dump(w, wf)
                wf_path = wf.name
            outp = Path('results') / f"trace_{p.get('id')}_off{off}_prob{prob}.json"
            try:
                subprocess.run([sys.executable, 'scripts/tools/_detect_worker.py', str(audio_path), wf_path, str(outp)], timeout=90, check=False)
                r = json.loads(outp.read_text())
            except subprocess.TimeoutExpired:
                print('timeout', p.get('id'))
                continue
            except Exception as e:
                print('error read', p.get('id'), e)
                continue
            if 'error' in r:
                print('worker error', p.get('id'), r.get('error'))
                continue
            # compute boundary f1
            det_raw = r.get('sections', [])
            det = []
            for ss in det_raw:
                if 'start_ms' in ss and 'duration_ms' in ss:
                    start_s = float(ss['start_ms'])/1000.0
                    end_s = start_s + float(ss['duration_ms'])/1000.0
                    det.append({'start_s': start_s,'end_s': end_s})
            ref = _parse_harmonix_sections(Path(p['sections_file']))
            b = _boundary_f1(ref, det, 0.5)
            tot_tp += b['tp']; tot_fp += b['fp']; tot_fn += b['fn']; tot_preds += b.get('pred_boundaries',0); count += 1
        precision=round(tot_tp/(tot_tp+tot_fp),4) if (tot_tp+tot_fp)>0 else 0.0
        recall=round(tot_tp/(tot_tp+tot_fn),4) if (tot_tp+tot_fn)>0 else 0.0
        avg_pred=round(tot_preds/count,3) if count>0 else 0.0
        results.append({'duration_offset':off,'prob_threshold':prob,'tp':tot_tp,'fp':tot_fp,'fn':tot_fn,'precision':precision,'recall':recall,'avg_pred_per_song':avg_pred})
        # write incremental
        Path('results/grid_targeted_duration_prob.json').write_text(json.dumps(results,indent=2))
        print('wrote partial results')

print('done')
