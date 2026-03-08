"""Resolve all merge conflicts for Wave 4b coordination merge."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

MSG_0602 = """
## MSG-20260308-0602
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 4b verification of Machine B candidate-generator recall (commit c45bfce). Full log at results/verify-machine-b-w4b.log.
artifacts:
- results/verify-machine-b-w4b.log
- tmp/verify_machine_b_w4b.py
notes: |
  VERIFICATION: Wave 4b candidate-generator recall (Machine B commit c45bfce)
  ==========================================================================

  CHECK 1 -- Recall gain vs baseline: FAIL (no improvement yet)
    Baseline (75a6ca7): pred/song=1.12  ref/song=8.00  Recall=0.0078  F1=0.0137
    Current (c45bfce):  pred/song=1.12  ref/song=8.00  Recall=0.0078  F1=0.0137
    Delta: recall=+0.0000  F1=+0.0000
    NMS_DISTANCE_SEC and MIN_SECTION_SEC unchanged. Candidate count unchanged.

  CHECK 2 -- Precision stability: STABLE
    Precision held at 0.0556 (TP=1 FP=17 FN=127). No regression.

  CHECK 3 -- XGBoost model quality: IMPROVED
    Best params: {n_estimators:50, max_depth:3, lr:0.1}
    CV F1: 0.4505 (was 0.3800, +0.0705). Model quality up, not yet deployed.

  CHECK 4 -- TOP RISK: Weight alignment bug (FAIL)
    Importances array: 9 values, 5 non-zero (indices 0,5,6,7,8).
    Weight dict: 5 keys, only flux_peak=1.0 non-zero.
    4 informative features discarded in extraction step.
    When NMS/MIN are reduced (H2+H3), the scorer must use all 5 non-zero
    features or recall gain will be partial. Fix before deploying NMS changes.

  CHECK 5 -- Suppression: UNCHANGED
    86% suppression (pred=1.12 vs ref=8.00). Oracle ceiling NMS=8s: +0.1368.
    Candidate-generator recall gain DEPENDS ON H2 (NMS reduction), not XGBoost.

  VERDICT: PASS on model quality. FAIL on recall gain (work not yet deployed).
  TOP RISK: Weight extraction drops 4/5 informative features -- fix alignment
  before applying NMS/MIN changes or XGBoost contribution will be wasted.
"""

def resolve_file(fpath: Path, extra_tail: str = "") -> int:
    text = fpath.read_bytes().decode("utf-8")
    count = 0
    # Repeatedly resolve conflict blocks: keep both HEAD and theirs sides
    while True:
        m = re.search(r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> origin/coordination/wave-1\n',
                      text, re.DOTALL)
        if not m:
            break
        our_side   = m.group(1)
        their_side = m.group(2)
        text = text[:m.start()] + our_side + their_side + text[m.end():]
        count += 1
    if extra_tail:
        text = text.rstrip("\n") + "\n" + extra_tail.lstrip("\n")
    fpath.write_text(text, encoding="utf-8")
    return count


# 1. Resolve live/machine-c.md — keep both sides + append MSG-0602
mc_live = ROOT / "docs/planning/machines/comms/live/machine-c.md"
n = resolve_file(mc_live, MSG_0602)
print(f"live/machine-c.md: {n} conflict(s) resolved, MSG-0602 appended")


# 2. Resolve machine-b.md — keep both sides (no new message needed)
mb = ROOT / "docs/planning/machines/comms/machine-b.md"
n2 = resolve_file(mb)
print(f"machine-b.md: {n2} conflict(s) resolved")


# 3. Append to machine-c.md main mirror
mc_main = ROOT / "docs/planning/machines/comms/machine-c.md"
tail = """
## MSG-20260308-0040
from: machine-c
to: coordinator
type: verification-result
wave: 4b (task MSG-20260308-0601)
status: done
summary: Verified Machine B candidate-generator recall. Recall UNCHANGED, model quality UP, TOP RISK weight alignment bug.
details: |
  CHECK1 FAIL  Recall unchanged: pred/song=1.12 vs ref=8.00 (86% suppression, NMS not changed).
  CHECK2 STBL  Precision stable at 0.0556. No regression.
  CHECK3 PASS  XGBoost CV F1=0.4505 (was 0.380). Model quality improved.
  CHECK4 FAIL  Weight alignment bug: 9 importances but 5 weight keys;
               4 informative features (indices 0,5,6,7) silently dropped.
               flux_peak=1.0 collapse. Must fix before deploying NMS/MIN.
  CHECK5 UNCH  NMS=16s still suppresses 86%. Oracle ceiling +0.1368 persists.
  TOP RISK: Weight extraction alignment bug will waste XGBoost contribution
            when H2+H3 (NMS/MIN) changes finally land.
artifacts:
- results/verify-machine-b-w4b.log
- tmp/verify_machine_b_w4b.py
"""
mc_main_text = mc_main.read_bytes().decode("utf-8")
mc_main.write_text(mc_main_text.rstrip("\n") + "\n" + tail.lstrip("\n"), encoding="utf-8")
print("machine-c.md: MSG-20260308-0040 appended")

# Verify no conflicts remain
for fpath in [mc_live, mb, mc_main]:
    remaining = fpath.read_text().count("<<<<<<< HEAD")
    status = "CLEAN" if remaining == 0 else f"{remaining} conflict(s) remain"
    print(f"  {fpath.name}: {status}")
