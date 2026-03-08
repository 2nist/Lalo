# Machine A Inbox

Use this file for machine-a-specific requests and status updates.

## MSG-20260308-0101
from: machine-a
to: coordinator
priority: high
status: done
request: Wave 2 integration gate checklist and regression risk review for integrated B/C outputs.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes:
- Integration branch reviewed: `origin/integration/machine-a-wave1`
- Integrated commits:
  - `585bb04c` (machine-b benchmark attribution + artifact)
  - `33741c1b` (machine-c diagnostics lane complete)
  - `5b1f0e67` (machine-a integration + verification)

## Merge-Readiness Checklist

- [x] Commit integration chain is present on integration branch
- [x] `scripts/bench/section_benchmark.py` compiles cleanly
- [x] `results/sections-machine-b.json` present and parseable
- [x] `results/sections-machine-c.json` present and parseable
- [x] Machine B artifact keeps `algorithm=heuristic`
- [ ] Machine C artifact includes detector summary metrics (`summary.detector`)

## Gate Summary

Status: conditional-pass

- Machine B benchmark artifact quality is acceptable for review.
- Machine C artifact appears diagnostics-oriented and currently exposes only `summary.fixed_chunks` (no `summary.detector`).
- Recommendation: keep B changes eligible for merge, but require one C follow-up artifact with detector metrics present (or explicit rationale for diagnostics-only output) before full gate close.

## MSG-20260308-0301
from: machine-a
to: coordinator
priority: high
status: in-progress
request: Wave 3 integration gate tracking update after checking Machine B parser-fix lane completion state.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes:
- Checked latest Machine B worker history and artifacts on `origin/machine-b/worker-wave1`.
- Latest commit is still Wave 2 (`d75a6e6d`) and contains only:
  - `results/machine-b-wave2-note.md`
  - `results/machine-b-xgb-summary.md`
  - `results/sections-machine-b-wave2.json`
- Expected Wave 3 parser-fix artifacts are not present yet:
  - `results/sections-machine-b-wave3.json`
  - `results/machine-b-wave3-note.md`
- Integration gate remains blocked on parser-fix evidence (non-zero reference boundaries).

## Wave 3 Interim Recommendation

Decision: hold-for-more-data

- Do not close the integration gate yet.
- Unblock condition: Machine B publishes parser-fix patch + before/after benchmark table proving non-zero reference boundaries.
- Next Machine A action after unblock: run final merge recommendation (`merge-now` or `merge-with-guardrail`) based on rerun metrics and risk delta.
