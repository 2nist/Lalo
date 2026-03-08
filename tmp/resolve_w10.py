#!/usr/bin/env python3
"""
Wave10 conflict resolver + MSG-20260308-1202 FAIL appender.
Run AFTER git merge leaves live/machine-c.md in conflict.
"""
import re, sys, pathlib

LIVE = pathlib.Path("docs/planning/machines/comms/live/machine-c.md")
MIRROR = pathlib.Path("docs/planning/machines/comms/machine-c.md")

MSG = """
## MSG-20260308-1202
date: 2026-03-08
from: machine-c
to: coordination
re: MSG-20260308-1201 — Wave 10 density sweep FAIL

Verdict: **FAIL**

Machine B commit `03df0ec` delivered `results/grid_wave10_density_all.json` (8-config
parameter sweep over nms_gap_sec × min_section_sec × beat_snap_sec).
No `results/sections-machine-b-wave10.json` full-benchmark artifact was committed.

### Grid sweep results vs Wave 9 baseline

| Metric          | Wave 9 (baseline) | Wave 10 best   | Delta     |
|-----------------|-------------------|----------------|-----------|
| F1@0.5s (agg)   | 0.0383            | 0.0116         | −70%      |
| Precision       | 0.0938            | 0.0227 (best)  | −76%      |
| Recall          | 0.0234            | 0.0078         | −67%      |
| pred/song (avg) | 2.000             | 2.75–4.375     | +38–119%  |
| TP              | 3                 | 1 (all configs)| −67%      |
| FP              | 29                | 43–69          | +48–138%  |
| FN              | 125               | 127            | +2        |

**No configuration satisfies all three Wave 10 pass criteria** (pred/song > 2.0 AND precision ≥ 0.04 AND F1@0.5s ≥ 0.0383). The sweep successfully increases pred/song by loosening NMS/MIN bounds but does so purely by generating false positives — TP *falls* from 3 to 1 across every tested configuration.

### Root cause assessment

Density-focused geometric relaxation cannot compensate for a model that fires high-confidence predictions on only ~2 boundaries per song. The XGBoost classifier probability threshold is the active bottleneck. Reducing NMS gap picks up more low-confidence candidates that are predominantly incorrect.

### Required next action for Wave 11

Lower the XGBoost probability decision threshold (currently implicit at default 0.5) and rerun the full benchmark with a single definitive configuration:
1. Re-run `section_detector.py` with `--prob_threshold 0.25` (or sweep 0.1–0.4) and **commit `results/sections-machine-b-wave11.json`** as a proper per-song benchmark artifact.
2. Deliver `results/machine-b-wave11-note.md` with weights, threshold used, and verified metrics.
3. Pass criteria (Wave 11): F1@0.5s ≥ 0.0383, precision ≥ 0.04, pred/song > 2.0 — same as Wave 10.

summary: FAIL — density sweep (03df0ec) regresses F1@0.5s to 0.0116 (−70%) and precision to max 0.0227 (−76%). TP drops from 3→1 across all 8 configs. Root blocker: XGBoost prob threshold, not geometry.
"""

def fix_conflict(text: str) -> str:
    """Strip git conflict markers, keeping HEAD (ours) content."""
    out = []
    in_ours = False
    in_theirs = False
    for line in text.splitlines(keepends=True):
        if line.startswith("<<<<<<<"):
            in_ours = True
            in_theirs = False
        elif line.startswith("=======") and in_ours:
            in_ours = False
            in_theirs = True
        elif line.startswith(">>>>>>>") and in_theirs:
            in_theirs = False
        elif in_ours:
            out.append(line)
        elif not in_theirs:
            out.append(line)
    return "".join(out)

def append_msg(path: pathlib.Path, msg: str):
    text = path.read_text()
    if "MSG-20260308-1202" in text:
        print(f"  {path}: MSG-1202 already present, skipping")
        return
    if "<<<<<<" in text:
        text = fix_conflict(text)
    text = text.rstrip("\n") + "\n" + msg.lstrip("\n") + "\n"
    path.write_text(text)
    print(f"  {path}: appended MSG-1202")

append_msg(LIVE, MSG)
append_msg(MIRROR, MSG)
print("Done.")
