import os
import traceback
from pathlib import Path
from scripts.analysis.section_detector import detect_sections
os.environ['NUMBA_DISABLE_JIT'] = '1'
base = Path('data/salami_audio')
audio = sorted(base.glob('[0-9]*.m4a'))[0]
print('audio', audio)
try:
    result = detect_sections(audio, algorithm='scored')
    print('meta', result.get('meta'))
except Exception:
    traceback.print_exc()
