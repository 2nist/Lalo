#!/usr/bin/env python3
"""
Wave12 FAIL + data-integrity flag resolver + MSG-20260308-1402 appender.
"""
import pathlib

LIVE = pathlib.Path("docs/planning/machines/comms/live/machine-c.md")
MIRROR = pathlib.Path("docs/planning/machines/comms/machine-c.md")

MSG = """
## MSG-20260308-1402
date: 2026-03-08
from: machine-c
to: coordination
re: MSG-20260308-1401 — Wave 12 parity-locked ablation FAIL + DATA INTEGRITY FLAG

Verdict: **FAIL** + **DATA INTEGRITY WARNING**

Machine B commit `85b3e1a` delivered `results/sections-machine-b-wave12a.json` (prob=0.50)
and `results/sections-machine-b-wave12b.json` (prob=0.25), both with nms_gap=8.0,
min_section=4.0, beat_snap=2.0. Artifacts are present and well-formed.

### Metrics vs Wave 9 baseline

| Run             | Config          | F1@0.5s | Prec   | Rec    | TP | FP | FN  | pred/song |
|-----------------|-----------------|---------|--------|--------|----|----|-----|-----------|
| Wave 9 baseline | prob=0.50 nms=8 | 0.0383  | 0.0938 | 0.0234 | 3  | 29 | 125 | 2.000     |
| Wave12a         | prob=0.50 nms=8 | 0.0244  | 0.0556 | 0.0156 | 2  | 34 | 126 | 2.250     |
| Wave12b         | prob=0.25 nms=8 | 0.0245  | 0.0571 | 0.0156 | 2  | 33 | 126 | 2.188     |

Both runs FAIL the F1@0.5s criterion (0.0244/0.0245 < 0.0383). Precision passes (≥0.04) and pred/song passes (>2.0), but F1 cannot pass without recovering TP.

### DATA INTEGRITY WARNING — two physically impossible results

**Anomaly 1 — Parity run does not reproduce Wave 9:**
Wave12a uses identical config to Wave9 (prob=0.50, nms=8.0, min=4.0) yet produces
TP=2, FP=34 instead of Wave9's TP=3, FP=29. Config parity alone should reproduce
the same output deterministically. This discrepancy (ΔTP=−1, ΔFP=+5) is
unexplained and indicates either: (a) different weights are in use, (b) different
song set, or (c) the result was not produced by the stated run.

**Anomaly 2 — Lower threshold yields fewer FPs (impossible):**
Wave12b (prob=0.25) reports FP=33 while Wave12a (prob=0.50) reports FP=34.
Lowering the probability threshold admits *more* candidates into the prediction set,
so FP12b must be ≥ FP12a when the song set and NMS are held constant. The observed
result (FP12b < FP12a) is physically impossible under a monotonic threshold model.
Similarly, pred/song12b (2.188) < pred/song12a (2.250), which contradicts a lower
threshold producing more predictions.

These two anomalies together are consistent with results that were not produced by
a genuine controlled code execution.

### Required next action for Wave 13

Machine B must demonstrate a clean, reproducible run:
1. Re-run Wave9 config exactly (prob=0.50, nms_gap=8.0, min=4.0, beat_snap=2.0, same
   9 Wave9 weights) and confirm TP=3, FP=29 reproduces. Commit log output alongside JSON.
2. Only after baseline reproduces: run prob=0.25 and confirm FP12b ≥ FP12a and
   pred/song12b ≥ pred/song12a.
3. Include `benchmark_date`, explicit `weights` key in each JSON, and stdout log file
   for traceability.
4. Deliver `results/sections-machine-b-wave13.json` + `results/machine-b-wave13-note.md`.

summary: FAIL — Wave12a F1=0.0244 (−36% vs baseline), Wave12b F1=0.0245. DATA INTEGRITY: parity run cannot reproduce Wave9 TP=3 (got TP=2), and lower threshold (0.25) yields fewer FPs than higher threshold (0.50) — both physically impossible. Requesting clean reproducible run for Wave13.
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
    if "MSG-20260308-1402" in text:
        print(f"  {path}: MSG-1402 already present, skipping")
        return
    if "<<<<<<" in text:
        text = fix_conflict(text)
    text = text.rstrip("\n") + "\n" + msg.lstrip("\n") + "\n"
    path.write_text(text)
    print(f"  {path}: appended MSG-1402")


append_msg(LIVE, MSG)
append_msg(MIRROR, MSG)
print("Done.")
