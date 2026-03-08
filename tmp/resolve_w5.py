"""Resolve merge conflicts for Wave 5 coordination merge."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

MSG_0702 = """
## MSG-20260308-0702
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 5 verification of Machine B alignment-fix output (commit bc1b29f). Full log at results/verify-machine-b-w5.log.
artifacts:
- results/verify-machine-b-w5.log
notes: |
  VERIFICATION: Wave 5 alignment-fix (Machine B commit bc1b29f, sub_prominence 0.4->0.3)
  ====================================================================================

  CHECK 1 -- Recall gain vs Wave 4b baseline: FAIL
    Before: pred/song=1.12  ref/song=8.00  Recall=0.0078  F1@0.5s=0.0179
    After:  pred/song=1.12  ref/song=8.00  Recall=0.0078  F1@0.5s=0.0179
    Delta: recall=+0.0000  F1=+0.0000
    sub_prominence 0.4->0.3 produced zero change in candidate count or recall.

  CHECK 2 -- Non-zero informative weights deployed: UNVERIFIED
    Weight extraction alignment bug from Wave 4b (4 features dropped, flux_peak=1.0)
    has NOT been addressed in this commit. No weight file updated.
    Task scope was sub_prominence tuning only; alignment fix not yet implemented.

  CHECK 3 -- Precision stability: STABLE
    TP=1 FP=17 FN=127 unchanged. No regression.

  TOP REMAINING BLOCKER: NMS_DISTANCE_SEC=16s
    sub_prominence controls which peaks become candidates. NMS_DISTANCE_SEC
    then collapses any two candidates within 16s down to one. Even if
    sub_prominence 0.3 increases pre-NMS candidate count, NMS suppresses
    ~86% of them. This is a series bottleneck:
      candidates -> NMS (16s) -> survivors -> scorer (flux_peak=1.0)
    The sub_prominence change acts upstream of the bottleneck and cannot
    improve recall until NMS is addressed first.
    Oracle ceiling with NMS=8s: F1@0.5s=0.9590 (+0.1368). Unchanged.

  VERDICT: FAIL on both recall gain and weight alignment deployment.
  NEXT ACTION FOR MACHINE B: Reduce NMS_DISTANCE_SEC (H2: 16->8s) before
  any further upstream candidate-generator tuning. That single change
  unlocks recall gain that all prior work has been blocked on.
"""

def resolve_conflicts(fpath: Path) -> int:
    text = fpath.read_bytes().decode("utf-8")
    count = 0
    while True:
        m = re.search(
            r'<<<<<<< HEAD\n(.*?)=======\n(.*?)>>>>>>> origin/coordination/wave-1\n',
            text, re.DOTALL)
        if not m:
            break
        text = text[:m.start()] + m.group(1) + m.group(2) + text[m.end():]
        count += 1
    fpath.write_text(text, encoding="utf-8")
    return count

# 1. live/machine-c.md — merge both sides + append MSG-0702
mc_live = ROOT / "docs/planning/machines/comms/live/machine-c.md"
n = resolve_conflicts(mc_live)
mc_live.write_text(mc_live.read_text().rstrip("\n") + "\n" + MSG_0702.lstrip("\n"), encoding="utf-8")
print(f"live/machine-c.md: {n} conflict(s), MSG-0702 appended")

# 2. machine-b.md — keep both sides, no new message needed
mb = ROOT / "docs/planning/machines/comms/machine-b.md"
n2 = resolve_conflicts(mb)
print(f"machine-b.md: {n2} conflict(s) resolved")

# 3. machine-c.md main mirror
mc_main = ROOT / "docs/planning/machines/comms/machine-c.md"
tail = """
## MSG-20260308-0045
from: machine-c
to: coordinator
type: verification-result
wave: 5 (task MSG-20260308-0701)
status: done
summary: sub_prominence 0.4->0.3 had zero effect. Recall UNCHANGED. Weight alignment bug unaddressed. NMS=16s is root blocker.
details: |
  CHECK1 FAIL  recall=0.0078 unchanged (pred=1.12 vs ref=8.00), F1@0.5s=0.0179.
  CHECK2 UNVF  Weight alignment bug not fixed in this commit. flux_peak=1.0 still.
  CHECK3 STBL  TP=1 FP=17 FN=127 unchanged. No precision regression.
  BLOCKER      NMS_DISTANCE_SEC=16s is upstream choke. sub_prominence acts before
               NMS. Oracle ceiling NMS=8s: +0.1368 F1. Must fix NMS first.
  NEXT ACTION  Reduce NMS_DISTANCE_SEC 16->8 (H2). No further upstream tuning
               will matter until NMS is unblocked.
artifacts:
- results/verify-machine-b-w5.log
"""
mc_main.write_text(mc_main.read_text().rstrip("\n") + "\n" + tail.lstrip("\n"), encoding="utf-8")
print("machine-c.md: MSG-0045 appended")

# Verify clean
for p in [mc_live, mb, mc_main]:
    c = p.read_text().count("<<<<<<< HEAD")
    print(f"  {p.name}: {'CLEAN' if c == 0 else str(c)+' conflicts remain'}")
