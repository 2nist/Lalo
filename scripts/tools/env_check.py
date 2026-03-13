from pathlib import Path
import sys

def safe_import(name):
    try:
        m = __import__(name)
        return True, getattr(m, "__version__", "<no-version>")
    except Exception as e:
        return False, str(e)

mods = ["msaf", "sklearn", "mir_eval", "librosa", "numpy"]
for m in mods:
    ok, v = safe_import(m)
    print(f"IMPORT {m}:", "OK" if ok else "ERROR", v)

ann_dir=Path('datasets/mcgill/mcgill_jcrd_salami_Billboard')
audio_dir=Path('data/salami_audio')
ann_map={}
if ann_dir.exists():
    for f in ann_dir.glob('*.json'):
        num = f.stem.split('_')[0].lstrip('0') or '0'
        ann_map[num]=str(f)
m4as = {f.stem for f in audio_dir.glob('[0-9]*.m4a')} if audio_dir.exists() else set()
common = sorted(set(ann_map.keys()) & m4as, key=lambda x:int(x) if x.isdigit() else x)
print('Usable SALAMI pairs:', len(common))
print('Example pairs (first 10 ids):', common[:10])
if len(common)>0:
    print('Example ann file:', ann_map[common[0]])
else:
    print('No matching pairs found. Check datasets/mcgill and data/salami_audio.')
