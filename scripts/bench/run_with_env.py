import os
import sys
import runpy

os.environ['PYTHONPATH'] = os.environ.get('PYTHONPATH', '.') 
# pass through all args to the benchmark script
sys.argv = ['scripts/bench/section_benchmark.py'] + sys.argv[1:]
runpy.run_path('scripts/bench/section_benchmark.py', run_name='__main__')
