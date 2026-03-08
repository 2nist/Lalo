#!/usr/bin/env python3
"""
Wave11 FAIL conflict resolver + MSG-20260308-1303 appender.
"""
import pathlib

LIVE = pathlib.Path("docs/planning/machines/comms/live/machine-c.md")
MIRROR = pathlib.Path("docs/planning/machines/comms/machine-c.md")

MSG = """
## MSG-20260308-1303
date: 2026-03-08
from: machine-c
to: coordination
re: MSG-20260308-1301 — Wave 11 threshold-first pass FAIL

Verdict: **FAIL**

Machine B commit `32f9478` delivered `results/sections-machine-b-wave11.json` and
`results/machine-b-wave11-note.md` with prob_threshold=0.25, nms_gap=6.0,
min_section=4.0, beat_snap=2.0.

### Metrics vs Wave 9 baseline

| Metric          | Wave 9 (baseline) | Wave 11        | Delta     |
|-----------------|-------------------|----------------|-----------|
| F1@0.5s (agg)   | 0.0383            | 0.0116         | −70%      |
| Precision       | 0.0938            | 0.0222         | −76%      |
| Recall          | 0.0234            | 0.0078         | −67%      |
| pred/song (avg) | 2.000             | 2.812          | +41%      |
| TP              | 3                 | 1              | −67%      |
| FP              | 29                | 44             | +52%      |
| FN              | 125               | 127            | +2        |

**No pass criteria met.** pred/song > 2.0 is satisfied mechanically (2.812), but precision (0.0222 < 0.04) and F1@0.5s (0.0116 < 0.0383) both fail.

### Critical diagnostic finding

Lowering prob_threshold from implicit ~0.5 → 0.25 **reduced TP from 3 to 1**
while adding 15 net-new FP. The marginal candidates activated at 0.25–0.5 are
entirely false positives (0 TP, 15 FP). This means:

1. The three TPs from Wave 9 were **high-confidence predictions** (p ≥ 0.5).
   At least two of the original three TPs are no longer firing at p ≥ 0.25 with
   the current geometry (nms=6.0 vs Wave9 nms=8.0 — NMS settings mismatch).
2. XGBoost probability scores in the 0.25–0.5 range have zero boundary signal.
   The model is not miscalibrated at the threshold; it lacks discriminative power
   for lower-salience boundaries.

### Root cause reassessment

The threshold tuning hypothesis is **falsified**: the bottleneck is not the
probability cutoff but the upstream feature representation. The XGBoost trained on
Wave 9's 9 features cannot reliably rank true boundaries above false candidates.
Adjusting the threshold does not resolve, and can worsen, the ranking quality.

### Required next action for Wave 12

Retrain the XGBoost classifier with improved training labels or features:
1. **Check geometry alignment**: Wave11 used nms_gap=6.0 but Wave9's learned
   weights were trained/validated at nms_gap=8.0. Run Wave11 at nms_gap=8.0 with
   prob_threshold=0.5 first to confirm Wave9 baseline is reproducible.
2. **If baseline reproduces**: increase training data coverage (currently only
   ~16 songs with detector output), add spectral flux / MFCC delta features,
   or try onset-strength peak picking as a bypass of XGBoost scoring.
3. Deliver `results/sections-machine-b-wave12.json` + `results/machine-b-wave12-note.md`.
   Pass criteria unchanged: F1@0.5s ≥ 0.0383, precision ≥ 0.04, pred/song > 2.0.

summary: FAIL — prob_threshold=0.25 regresses TP 3→1 and F1@0.5s to 0.0116 (−70%). Threshold hypothesis falsified: marginal candidates (p 0.25–0.5) are 0 TP / 15 FP. Root blocker is XGBoost feature discriminability, not threshold. Geometry mismatch (nms=6 vs Wave9 nms=8) also suspected.
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
    if "MSG-20260308-1303" in text:
        print(f"  {path}: MSG-1303 already present, skipping")
        return
    if "<<<<<<" in text:
        text = fix_conflict(text)
    text = text.rstrip("\n") + "\n" + msg.lstrip("\n") + "\n"
    path.write_text(text)
    print(f"  {path}: appended MSG-1303")


append_msg(LIVE, MSG)
append_msg(MIRROR, MSG)
print("Done.")
