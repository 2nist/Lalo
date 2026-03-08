Machine B delta note (wave-1)

Command run:
`PYENV_VERSION=chord-extractor-env python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-b.json`

Before:
- Benchmark output recorded requested algorithm only.
- Effective backend/fallback behavior was not explicitly attributable per song.

After:
- Output now records `requested_algorithm`, `effective_algorithm`, and `fallback_used` for each detector-scored song.
- Top-level output now includes `effective_algorithms` counts across evaluated songs.

Current run summary:
- songs evaluated: 30
- songs with local audio and detector scores: 16
- effective algorithm counts: `{\"heuristic\": 16}`
- fallback used rows: 0
