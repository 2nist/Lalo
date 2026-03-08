#!/usr/bin/env python3
"""Wave14 FAIL — threshold inversion persists. MSG-20260308-1602 appender."""
import pathlib

LIVE = pathlib.Path("docs/planning/machines/comms/live/machine-c.md")
MIRROR = pathlib.Path("docs/planning/machines/comms/machine-c.md")

MSG = """
## MSG-20260308-1602
date: 2026-03-08
from: machine-c
to: coordination
re: MSG-20260308-1601 — Wave 14 threshold-direction fix FAIL — inversion NOT fixed

Verdict: **FAIL** — `--prob_threshold` inversion persists in Wave 14 unchanged.

Machine B commit `ae79ba8` delivered three runs (prob=0.50/0.25/0.15) with full
per-song logs. Artifacts are present and genuine. Machine B self-reported all
three validation checks as False.

### Metrics

| Run     | prob  | F1@0.5s | Prec   | TP | FP | FN  | pred/song |
|---------|-------|---------|--------|----|----|-----|-----------|
| Wave 9  | 0.50  | 0.0383  | 0.0938 | 3  | 29 | 125 | 2.000     |
| Wave14a | 0.50  | 0.0244  | 0.0556 | 2  | 34 | 126 | 2.250     |
| Wave14b | 0.25  | 0.0245  | 0.0571 | 2  | 33 | 126 | 2.188     |
| Wave14c | 0.15  | 0.0245  | 0.0571 | 2  | 33 | 126 | 2.188     |

Observations (identical to Waves 12 and 13):
- 14a (prob=0.50) gives MORE predictions than 14b/14c — still inverted direction.
- 14b (prob=0.25) == 14c (prob=0.15) exactly — no candidates have XGB scores in [0.15, 0.25).

### The fix was not applied

The per-song log for song 0027 confirms: prob=0.50 gives pred=3, prob=0.25 gives
pred=2, prob=0.15 gives pred=2. This is precisely the upper-bound behavior identified
in Wave 13. Wave14a numbers are bit-for-bit identical to Wave13a, and Wave14b/Wave14c
are identical to Wave13b. The code was not changed between waves.

### New diagnostic information from 14b == 14c

The equality of runs at prob=0.25 and prob=0.15 reveals the XGB score distribution:
no candidates score in [0.15, 0.25). Combined with the inverted direction, this means
most XGB scores cluster either near 0 (low signal) or above 0.25 (the known TP/FP boundary).

### Required fix for Wave 15 — explicit verification required

Machine B must:
1. Open `scripts/analysis/section_detector.py` and locate the threshold filter line.
   Report the exact line number and current code (include surrounding 3 lines).
2. Change `score < prob_threshold` (or equivalent) to `score >= prob_threshold`.
3. Re-run Wave9 parity config (prob=0.50, nms=8.0, min=4.0): must yield MORE
   predictions than prob=0.70, and FEWER predictions than prob=0.30 to confirm direction.
4. Include the diff of the changed line in `machine-b-wave15-note.md`.
5. Deliver `results/sections-machine-b-wave15.json` + note + logs.

Pass criteria (Wave 15): F1@0.5s ≥ 0.0383, precision ≥ 0.04, pred/song > 2.0,
AND monotonic_fp=True, monotonic_pred=True.

summary: FAIL — Wave14 results bit-for-bit identical to Wave13. Threshold inversion not fixed. New finding: no XGB candidates score in [0.15, 0.25) range. Fix requires explicit code change to section_detector.py with diff provided in note.
"""


def fix_conflict(text: str) -> str:
    out, in_ours, in_theirs = [], False, False
    for line in text.splitlines(keepends=True):
        if line.startswith("<<<<<<<"):
            in_ours, in_theirs = True, False
        elif line.startswith("=======") and in_ours:
            in_ours, in_theirs = False, True
        elif line.startswith(">>>>>>>") and in_theirs:
            in_theirs = False
        elif in_ours:
            out.append(line)
        elif not in_theirs:
            out.append(line)
    return "".join(out)


def append_msg(path: pathlib.Path, msg: str):
    text = path.read_text()
    if "MSG-20260308-1602" in text:
        print(f"  {path}: MSG-1602 already present, skipping")
        return
    if "<<<<<<" in text:
        text = fix_conflict(text)
    text = text.rstrip("\n") + "\n" + msg.lstrip("\n") + "\n"
    path.write_text(text)
    print(f"  {path}: appended MSG-1602")


append_msg(LIVE, MSG)
append_msg(MIRROR, MSG)
print("Done.")
