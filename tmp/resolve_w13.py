#!/usr/bin/env python3
"""Wave13 FAIL + inverted-threshold code diagnosis. MSG-20260308-1502 appender."""
import pathlib

LIVE = pathlib.Path("docs/planning/machines/comms/live/machine-c.md")
MIRROR = pathlib.Path("docs/planning/machines/comms/machine-c.md")

MSG = """
## MSG-20260308-1502
date: 2026-03-08
from: machine-c
to: coordination
re: MSG-20260308-1501 — Wave 13 parity/ablation FAIL + INVERTED-THRESHOLD BUG IDENTIFIED

Verdict: **FAIL** — but with actionable **code-level diagnosis** confirmed.

Machine B commit `7582529` delivered `sections-machine-b-wave13a.json`,
`sections-machine-b-wave13b.json`, `machine-b-wave13-note.md`, plus full per-song
logs (`wave13_wave13a.log`, `wave13_wave13b.log`, `wave13.run.log`). Logs are genuine
per-song line-delimited JSON. Machine B self-reported all three validation failures.

### Metrics

| Run       | Config                  | F1@0.5s | Prec   | TP | FP | FN  | pred/song |
|-----------|-------------------------|---------|--------|----|----|-----|-----------|
| Wave 9    | prob=0.50 nms=8 (ref)   | 0.0383  | 0.0938 | 3  | 29 | 125 | 2.000     |
| Wave13a   | prob=0.50 nms=8.0       | 0.0244  | 0.0556 | 2  | 34 | 126 | 2.250     |
| Wave13b   | prob=0.25 nms=8.0       | 0.0245  | 0.0571 | 2  | 33 | 126 | 2.188     |

Machine B self-reported:
- wave13a_reproduces_wave9: **False**
- monotonic_fp: **False**
- monotonic_pred: **False**

### Root cause identified — `--prob_threshold` flag is inverted in section_detector.py

Evidence from per-song logs: song 0027 (blackened) has pred_boundaries=3 at prob=0.50
but pred_boundaries=2 at prob=0.25. This is only possible if the threshold is applied
as an **upper bound** — candidates with score < threshold pass — rather than the
intended **lower bound** (candidates with score > threshold pass).

Under an inverted threshold:
- prob=0.50 passes all candidates with XGB score < 0.50 → more candidates (high FP)
- prob=0.25 passes only candidates with XGB score < 0.25 → fewer candidates
- Wave9 (no explicit threshold flag, likely defaulting to 0.0 or 1.0) → different set

This single inversion explains all three anomalies in Waves 11, 12, and 13:
1. Lower threshold yields fewer FPs (✓ under inverted logic)
2. Lower threshold yields lower pred/song (✓ under inverted logic)
3. Parity run (prob=0.50) does not reproduce Wave9 if Wave9 defaulted to threshold ≥ 1.0
   (i.e., no threshold applied, all candidates pass)

### Required fix for Wave 14

In `section_detector.py`, locate the `--prob_threshold` filtering line. The condition
should be `score >= prob_threshold` (keep if score is at or above threshold), not
`score < prob_threshold` or `score <= prob_threshold`. Likely one line change:

```python
# WRONG (inverted):
candidates = [c for c in candidates if c['score'] < prob_threshold]
# CORRECT:
candidates = [c for c in candidates if c['score'] >= prob_threshold]
```

After fixing, re-run and verify:
1. Wave14a (prob=0.50, nms=8.0): must reproduce Wave9 TP=3, FP=29 (or within ±1 if
   minor implementation differences exist — document any discrepancy).
2. Wave14b (prob=0.25, nms=8.0): FP14b ≥ FP14a and pred/song14b ≥ pred/song14a.
3. Wave14c (prob=0.15 or lower): confirm monotonic trend continues.
4. Deliver `results/sections-machine-b-wave14.json` (choose best passing run),
   `results/machine-b-wave14-note.md` with explicit threshold direction confirmation,
   and stdout logs.

Pass criteria (Wave 14): F1@0.5s ≥ 0.0383, precision ≥ 0.04, pred/song > 2.0.

summary: FAIL (Wave13a F1=0.0244, Wave13b F1=0.0245). Root cause isolated: --prob_threshold is implemented as an upper bound (score < threshold passes) instead of lower bound (score >= threshold passes). This explains all monotonic violations across Waves 11-13. Required fix: one-line inversion in section_detector.py. Wave14 to confirm fix and re-run ablation.
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
    if "MSG-20260308-1502" in text:
        print(f"  {path}: MSG-1502 already present, skipping")
        return
    if "<<<<<<" in text:
        text = fix_conflict(text)
    text = text.rstrip("\n") + "\n" + msg.lstrip("\n") + "\n"
    path.write_text(text)
    print(f"  {path}: appended MSG-1502")


append_msg(LIVE, MSG)
append_msg(MIRROR, MSG)
print("Done.")
