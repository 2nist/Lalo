"""Resolve merge conflict in live/machine-c.md for Wave 4."""
from pathlib import Path

fpath = Path("/home/matthew/Projects/lalo/Lalo/docs/planning/machines/comms/live/machine-c.md")
raw = fpath.read_bytes().decode("utf-8")

# Find conflict start/end
start_marker = "<<<<<<< HEAD\n"
sep_marker = "=======\n"
end_marker = ">>>>>>> origin/coordination/wave-1\n"

s = raw.index(start_marker)
sep = raw.index(sep_marker, s)
e = raw.index(end_marker, sep) + len(end_marker)

our_side = raw[s + len(start_marker):sep]
their_side = raw[sep + len(sep_marker):e - len(end_marker)]

print("=== OUR SIDE ===")
print(our_side[:200])
print("=== THEIR SIDE ===")
print(their_side[:200])

RESPONSE = """
## MSG-20260308-0302
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 3 support mode acknowledged. Verification criteria established for Machine B parser-fix.
artifacts:
- docs/planning/machines/comms/machine-c.md
notes: |
  WAVE 3 SUPPORT MODE — Active
  ----------------------------
  Machine B wave2 note confirms our H4 diagnosis:
    "95 candidate examples, 5 positives (severe class imbalance)" — direct
    consequence of ref_boundaries=0. XGB flux-only weights: F1 unchanged at
    0.0179. Machine B acknowledges parser fix is prerequisite.

  Waiting for: origin/machine-b/worker-wave1 new commit with parser fix.
  Trigger: ref_boundaries > 0 in any machine-b per_song result.

  VERIFICATION PLAN once parser fix lands
  ----------------------------------------
  1. Re-run tmp/oracle_analysis.py against machine-b fixed output to confirm
     H2 (NMS=8s) and H3 (MIN=4s) ceiling gains persist:
     Expected: oracle F1@0.5s = 0.9590 (+0.1368 vs current 0.8222)
  2. Check that machine-b per-song ref_boundaries approx= our corpus mean 9.3
     (n=30 songs, expected total ~280). Delta from 327 (35-song corpus) is OK.
  3. Verify XGBoost CV folds show non-zero F1 — confirms training data improved.
  4. Cross-check top-1 machine-b song by F1 against our known easy songs
     (0039_bulletproof: Fixed F1=0.444 -- should be first to show TP>0).

  Will post verification results immediately on new machine-b commit.

## MSG-20260308-0401
from: coordinator
to: machine-c
priority: normal
status: done
request: Run quick verification against latest Machine B XGBoost artifact and post a short consistency check: non-zero reference boundaries observed and any change in H2/H3 hypothesis confidence.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Keep this as analysis-only validation. Do not retune models or alter defaults.

## MSG-20260308-0402
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 3 verification of Machine B label-tol=3.0 XGBoost artifact (commits 75a6ca7 + 93aecd1). Full log at results/verify-machine-b-w3.log.
artifacts:
- results/verify-machine-b-w3.log
- tmp/verify_machine_b_w3.py
notes: |
  VERIFICATION COMPLETE -- Machine B label-tol=3.0 (commits 75a6ca7/93aecd1)
  ==========================================================================

  CHECK 1 -- Non-zero reference boundaries: PASS
    ref=0 count: 0/30 songs (was: 30/30 before fix).
    mean_ref = 9.30 (matches Harmonix corpus mean exactly).
    label-tol=3.0 resolved the training data quality problem.

  CHECK 2 -- XGBoost CV non-zero: PASS (MAJOR IMPROVEMENT)
    Fold F1: 0.533, 0.400, 0.500, 0.267, 0.200 -- mean F1 = 0.380
    Prior run (no label-tol): all folds F1=0.0.
    XGBoost now generalizes. Model is viable.

  CHECK 3 -- Feature importance shift noted (informational)
    New (tol=3s): rms_energy=35.9%, flux_peak=18.4%, onset_density=14.9%
    Prior (tol=0): chroma_change=50.4% dominant.
    Shift to energy/flux envelope is physically reasonable at 3s tolerance.

  CHECK 4 -- H2/H3 hypothesis confidence: INCREASED
    Detector produces mean 1.1 boundaries/song vs 8.0 reference (86% suppression).
    TP=1, FP=17, FN=127 across 16 audio songs -- pure recall failure.
    0039_bulletproof sanity: ref=6, pred=1, TP=0 confirms NMS/MIN crushing recall.
    H2 (NMS=16->8s) confidence: HIGH (increased -- now measurable vs real ref,
      86% suppression directly observed).
    H3 (MIN=8->4s) confidence: MEDIUM (unchanged -- annotation evidence holds).
    Oracle ceiling with NMS=8s: F1@0.5s=0.9590 (+0.1368). Unchanged.

  CHECK 5 -- Benchmark detector F1: 0.0179 (unchanged from before fix)
    label-tol improves training labels but scoring still uses tight 0.5s tolerance.
    Expected behavior. Detector performance will only change when NMS/MIN params change.

  RECOMMENDATION: H2 (NMS_DISTANCE_SEC 16->8) is the single highest-ROI change.
    Expected F1 gain: +0.1368 (oracle-confirmed). Zero audio dependency to verify.
"""

resolved = raw[:s] + RESPONSE.lstrip("\n") + "\n"
fpath.write_text(resolved, encoding="utf-8")
print(f"\nWritten {len(resolved)} chars. Conflict resolved.")
