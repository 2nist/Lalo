import sys
import traceback
from pathlib import Path
from scripts.bench import salami_benchmark as bench
sys.argv = ['scripts/bench/salami_benchmark.py', '--algorithm', 'scored', '--max-songs', '1', '--out', 'results/salami-step10-scored-debug.json']
try:
    bench.main()
except SystemExit as exc:
    print('SystemExit', exc.code)
    traceback.print_exc()
except Exception:
    traceback.print_exc()
