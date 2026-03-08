# Live Channel: Machine C

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-c|copilot
to: machine-c|coordinator|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <paths>
notes: <constraints>
```

## MSG-20260307-2001
from: coordinator
to: machine-c
priority: high
status: done
request: Confirm live-channel polling works, then mirror your status update into docs/planning/machines/comms/machine-c.md.
artifacts: docs/planning/machines/comms/machine-c.md, results/sections-machine-c.json (if produced)
notes: Reply in this file first, then mirror to the main comms file.

## MSG-20260307-2101
from: coordinator
to: machine-c
priority: high
status: done
request: Execute Machine C lane using the explicit runbook, then post done-status with diagnostics artifacts.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log, docs/planning/machines/comms/machine-c.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-c.

## MSG-20260307-2301
from: coordinator
to: machine-c
priority: high
status: done
request: Run Machine C bootstrap helper to bypass missing-path blockers and continue artifact generation.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log (if validation exists)
notes: Run `powershell -ExecutionPolicy Bypass -File scripts/comms/machine-c-bootstrap.ps1 -FetchHarmonixIfMissing -FetchAudioIfMissing -AudioMax 30 -Run` and post output summary.

## MSG-20260308-0002
from: machine-c
to: coordinator
priority: high
status: done
request: Lane complete. Bootstrap equivalent executed (Linux path — PowerShell not available).
artifacts:
- results/sections-machine-c.json
- results/bench-machine-c.log
notes:
- PowerShell bootstrap replaced with `tmp/fetch_harmonix_annotations.py` (Linux-compatible).
- Validation skipped: `tmp/validate_pipeline.py` not present on machine-c checkout.
- Benchmark (--dev-only heuristic, 30 songs): F1@0.5s mean=0.0443  F1@3.0s mean=0.1687
- Results pushed to origin/machine-c.

## MSG-20260307-2401
from: coordinator
to: machine-c
priority: high
status: done
request: Mirror diagnostics completion from your branch into comms and attach concise blocker-resolution summary.
artifacts: docs/planning/machines/comms/machine-c.md, results/sections-machine-c.json, results/bench-machine-c.log
notes: Branch `origin/machine-c` shows `machine-c: diagnostics lane complete`; this step is to publish final comms status and any skipped validation rationale.

## MSG-20260308-0004
from: machine-c
to: coordinator
priority: high
status: done
request: Blocker-resolution summary and diagnostics mirrored.
artifacts:
- results/sections-machine-c.json
- results/bench-machine-c.log
- results/oracle-analysis-machine-c.log
- docs/planning/machines/comms/machine-c.md
- docs/planning/machines/comms/machine-b.md (MSG-20260308-0010)
notes: |
  BLOCKER RESOLUTION SUMMARY
  --------------------------
  1. data/raw/harmonix/ missing: fetched 35 songs (70 files) from nicolaus625/cmi
     via tmp/fetch_harmonix_annotations.py (HuggingFace, targeted dir listing).
  2. tmp/validate_pipeline.py missing: SKIPPED — file not present on machine-c
     checkout. Skipped step noted in all artifacts.
  3. third_party/BTC-ISMIR19/test/example.mp3 missing: not a blocker for
     --dev-only mode (annotation-only benchmark).
  4. python not in PATH on Linux: used .venv/bin/python throughout.
  5. PowerShell bootstrap: replaced with Linux-compatible Python equivalent.

  BENCHMARK RESULT
  ----------------
  fixed_chunks F1@0.5s=0.0443  F1@3.0s=0.1687  (30 songs, heuristic, no audio)

  EXTENDED DIAGNOSTICS (annotation+beat oracle — no audio required)
  -----------------------------------------------------------------
  NMS ceiling loss: 30% of real boundaries suppressed by NMS_DISTANCE_SEC=16.0
  MIN filter loss:  13% of real sections removed by MIN_SECTION_SEC=8.0
  Oracle ceiling (current params):  F1@0.5s=0.8222
  Oracle ceiling (proposed params): F1@0.5s=0.9590  (+0.1368 from param fixes)
  label_accuracy=0.0 confirmed as naming mismatch, not signal failure.
  Full hypothesis posted to machine-b (MSG-20260308-0010).

## MSG-20260308-0101
from: coordinator
to: machine-c
priority: normal
status: done
request: Run Wave 2 diagnostics-only lane (non-audio-dependent). Summarize top 5 failure patterns from `results/bench-machine-c.log` and map each to a testable benchmark hypothesis for Machine B.
artifacts: results/machine-c-failure-taxonomy.md, docs/planning/machines/comms/machine-c.md
notes: No model/backend/default changes in this lane. This is analysis + hypothesis packaging only.

## MSG-20260308-0102
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 2 failure taxonomy complete. 5 patterns + hypotheses packaged for Machine B.
artifacts:
- results/machine-c-failure-taxonomy.md
- docs/planning/machines/comms/machine-c.md
notes: |
  WAVE 2 SUMMARY — top 5 failure patterns + Machine B hypotheses
  ---------------------------------------------------------------
  H1 Chunk-size mismatch: 32s vs 19.9s median section; 23/30 songs
     score F1=0; under-segmented by 2.23 boundaries/song. Fix: CHUNK_SIZE=20s.
  H2 NMS over-suppression: 16s NMS kills 30% real boundaries.
     NMS=8s → oracle ceiling 0.8222→0.9590 (+0.1368).
  H3 MIN filter too tight: 8s floor structurally excludes 13% true sections.
     MIN=4s → oracle +0.035.
  H4 Ref parser BROKEN (critical): ref_boundaries=0 for all 30 machine-b
     songs. 327 expected boundaries never loaded. Learned weights invalid.
     Fix this first — all other metrics are meaningless until resolved.
  H5 Label naming mismatch: detector emits "Section N", GT uses
     verse/chorus/intro. Structural 0.0 — weight tuning cannot fix.
     Post-hoc position classifier expected to reach label_acc 0.25+.
  PRIORITY ORDER: H4 → H2+H3 → H1 → H5

## MSG-20260308-0201
from: coordinator
to: machine-c
priority: high
status: done
request: Finalize Wave 2 diagnostics handoff by syncing your completion commit into coordination-visible comms and highlighting the top 2 hypotheses Machine B should test first.
artifacts: docs/planning/machines/comms/machine-c.md, docs/planning/machines/comms/live/machine-c.md, results/machine-c-failure-taxonomy.md
notes: Your branch shows completion (`origin/machine-c` latest commit). This step is a sync + prioritization handoff.

## MSG-20260308-0202
from: machine-c
to: coordinator
priority: high
status: done
request: Wave 2 handoff finalized. Completion synced. Top 2 hypotheses for Machine B highlighted below.
artifacts:
- results/machine-c-failure-taxonomy.md
- docs/planning/machines/comms/machine-c.md
- docs/planning/machines/comms/machine-b.md (MSG-20260308-0015)
notes: |
  WAVE 2 HANDOFF — Sync + Prioritization
  ---------------------------------------
  Branch origin/machine-c @ 895c6fa contains:
    results/machine-c-failure-taxonomy.md   — 5 failure patterns, full evidence
    results/analysis5-machine-c.log         — ref parser bug proof
    results/oracle-analysis-machine-c.log   — parameter ceiling analysis
    results/bench-machine-c.log             — 30-song heuristic baseline

  TOP 2 HYPOTHESES FOR MACHINE B (test in this order)
  ----------------------------------------------------

  #1 — H4: Fix the reference boundary parser (CRITICAL, blocks everything)
       Evidence: ref_boundaries=0 for all 30 songs in false_pos_neg_per_song.csv;
       327 expected boundaries missing. XGBoost CV F1=0.0 across all 5 folds
       confirms training is also poisoned by this bug. All learned weights
       (linear and XGBoost) are trained against empty reference — invalid.
       New signal: XGBoost identifies chroma_change (50.4% importance) and
       onset_density (16.9%) as strongest features. These importances are
       computed from the feature matrix, not the labels — they are likely
       valid and suggest chroma is the primary signal. But the weights cannot
       be evaluated until ref_boundaries > 0.
       Test: add debug print of section file path + first 3 lines for
       song 0003_6foot7foot. File exists in our corpus with 11 boundaries.

  #2 — H2: Reduce NMS_DISTANCE_SEC 16 → 8 (highest F1 gain, annotation-only)
       Evidence: 30% of adjacent true boundaries in Harmonix < 16s apart.
       Oracle ceiling with NMS=16s: F1@0.5s=0.8222 (−0.1368 vs proposed).
       Oracle ceiling with NMS=8s:  F1@0.5s=0.9590.
       This test requires zero audio dependency — run on annotation-only corpus.
       Measurable the moment H4 is fixed.

  SECONDARY: H3 (MIN=8→4s, +0.035 oracle) can be tested simultaneously with H2.
  DEFERRED:  H1 (chunk size) and H5 (label classifier) are lower priority.

## MSG-20260308-0301
from: coordinator
to: machine-c
priority: normal
status: done
request: Stay in support mode. Validate Machine B parser-fix branch once available and confirm whether H2/H3 gains persist after H4 is fixed.
artifacts: docs/planning/machines/comms/machine-c.md
notes: No new modeling work yet; this is verification support for B's parser-first lane.

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
status: done
summary: Support-mode verification completed on `origin/machine-c` commit `27c7276a`. Machine C validated non-zero reference boundaries and confirmed H2/H3 confidence persistence after Machine B label-tolerance update.

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
  ===================================================================
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

=======
status: done
summary: Verification posted by Machine C (`MSG-20260308-0402` on branch). Key outcomes: ref=0 count is 0/30 (PASS), XGBoost CV mean F1=0.380 (non-zero), H2 confidence increased, H3 remains medium and supported.

## MSG-20260308-0501
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 4 verification pass. Validate Machine B H2/H3 tuning output once posted and confirm whether recall improves without breaking boundary sanity.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL with concise rationale and top risk note.

status: done
summary: Superseded by Wave 4b candidate-generator recall verification lane.

## MSG-20260308-0601
from: coordinator
to: machine-c
priority: normal
status: open
request: Wave 4b verification pass. Validate Machine B candidate-generator recall output and confirm recall gain vs baseline without destabilizing precision.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL plus one highest-priority risk.
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
