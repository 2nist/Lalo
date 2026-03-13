import traceback
import sys
from pathlib import Path
from scripts.analysis.section_detector import detect_sections
base = Path('data/salami_audio')
audio = sorted(base.glob('[0-9]*.m4a'))[0]
song_id = audio.stem
ann_dir = Path('datasets/mcgill/mcgill_jcrd_salami_Billboard')
ann = next(ann_dir.glob(f'{int(song_id):04d}_*.json'))
print('testing', audio, 'annotation', ann)
try:
    result = detect_sections(audio, algorithm='scored')
    print('meta', result.get('meta'))
except SystemExit as exc:
    print('SystemExit', exc)
    sys.stdout.flush()
except Exception:
    traceback.print_exc()
