#!/usr/bin/env python3
"""
Wave11 conflict resolver + MSG-20260308-1302 PENDING appender.
Run AFTER git merge leaves live/machine-c.md in conflict.
"""
import pathlib

LIVE = pathlib.Path("docs/planning/machines/comms/live/machine-c.md")
MIRROR = pathlib.Path("docs/planning/machines/comms/machine-c.md")

MSG = """
## MSG-20260308-1302
date: 2026-03-08
from: machine-c
to: coordination
re: MSG-20260308-1301 — Wave 11 threshold-first verification PENDING

status: pending — no artifact submitted yet

Machine B latest commit `51faacd` ("Mirror Wave11 threshold-first instructions for machine-b") contains only comms file updates. No benchmark artifact found:
- `results/sections-machine-b-wave11.json` — **does not exist**
- `results/machine-b-wave11-note.md` — **does not exist**

Note on Wave 10 addendum: Machine B also submitted `results/sections-machine-b-wave10-top.json` (commit `517663a`), representing the top-combo density config (nms=6.0, min=3.0, snap=1.0). Metrics: TP=1, FP=43, FN=127, precision=0.0227, pred/song=2.75. This does not change the Wave 10 FAIL verdict — precision (0.0227) and F1@0.5s remain below both pass thresholds.

Awaiting `results/sections-machine-b-wave11.json` + `results/machine-b-wave11-note.md` with prob_threshold tuning applied and Wave 9 geometry baseline preserved.

summary: PENDING — Machine B has acknowledged Wave 11 instructions but submitted no artifact. Wave 10 addendum (top-combo) reviewed and does not recover prior FAIL.
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
    if "MSG-20260308-1302" in text:
        print(f"  {path}: MSG-1302 already present, skipping")
        return
    if "<<<<<<" in text:
        text = fix_conflict(text)
    text = text.rstrip("\n") + "\n" + msg.lstrip("\n") + "\n"
    path.write_text(text)
    print(f"  {path}: appended MSG-1302")


append_msg(LIVE, MSG)
append_msg(MIRROR, MSG)
print("Done.")
