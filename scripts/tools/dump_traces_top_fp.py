#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess, sys, tempfile

ROOT = Path('.').resolve()
sys.path.insert(0, str(ROOT))

# Top FP regressions from previous compare
top_ids = [
    '0021_better','0017_badromance','0027_blackened','0014_babaoriley',
    '0036_breakingthegirl','0006_aint2proud2beg','0003_6foot7foot','0026_blackandyellow'
]

Path('results/traces').mkdir(parents=True, exist_ok=True)

for sid in top_ids:
    print('dumping', sid)
    # find pair entry
    from scripts.bench.section_benchmark import _load_harmonix_pairs, HARMONIX_DIR, AUDIO_DIR
    pairs = _load_harmonix_pairs(HARMONIX_DIR, AUDIO_DIR, max_songs=400)
    pair_map = {p.get('id'): p for p in pairs if p.get('id')}
    p = pair_map.get(sid)
    if not p:
        print('missing pair for', sid)
        continue
    audio = p.get('audio')
    if not audio:
        print('no audio for', sid)
        continue
    # call worker
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as wf:
        wf.write('{}')
        wf_path = wf.name
    outp = Path('results/traces') / (sid + '.json')
    try:
        subprocess.run([sys.executable, 'scripts/tools/_detect_worker.py', str(audio), wf_path, str(outp)], timeout=180, check=False)
        print('wrote', outp)
    except subprocess.TimeoutExpired:
        print('timeout for', sid)
    except Exception as e:
        print('error for', sid, e)

print('done')
