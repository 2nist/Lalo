# Machine C Inbox

Use this file for machine-c-specific requests/status updates.

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-c|copilot
to: machine-c|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <expected outputs>
notes: <constraints>
```

## MSG-20260307-1001
from: coordinator
to: machine-c
priority: high
status: open
request: Pull latest `coordination/wave-1`, run single-song diagnostics using the Machine C payload, and publish artifacts.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, short repro note in docs/planning/machines/comms/machine-c.md
notes: Use payload file `docs/planning/machines/payloads/machine-c-payload.json` (backend=reference, algorithm=heuristic, slug path provided).

### Runbook (PowerShell)

```powershell
git fetch origin
git checkout coordination/wave-1
git pull --ff-only origin coordination/wave-1
git checkout -b worker/machine-c

cat docs/planning/machines/payloads/machine-c-payload.json
mkdir -Force results

python tmp/validate_pipeline.py *> results/validate-machine-c.log
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-c.json *> results/bench-machine-c.log

git add results/sections-machine-c.json results/bench-machine-c.log results/validate-machine-c.log docs/planning/machines/comms/machine-c.md
git commit -m "worker/machine-c: add diagnostic artifacts and repro note"
git push -u origin HEAD
```

### Reply format (append below this message)

```md
status: done
branch: <worker branch>
backend: reference|owned
algorithm: heuristic|other
song: <slug/path>
artifacts:
- results/sections-machine-c.json
- results/bench-machine-c.log
- results/validate-machine-c.log
summary: <2-5 lines>
```

## MSG-20260307-2201
from: machine-c
to: coordinator
priority: high
status: open
request: Need final payload/data/script confirmation before running diagnostics.
artifacts: none yet
notes:
- Where should Harmonix annotations come from (`data/raw/harmonix` vs `scripts/datasets/fetch_harmonix.py`)?
- Payload references `third_party/BTC-ISMIR19/test/example.mp3` but Machine C checkout reported no `third_party/` tree.
- `tmp/validate_pipeline.py` reported missing on Machine C checkout.
- Should Machine C wait for these prerequisites before committing artifacts?

## MSG-20260307-2202
from: coordinator
to: machine-c
priority: high
status: open
request: Proceed with diagnostics using these resolved instructions.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log
notes:
- Use existing local data first. In coordinator checkout, both `data/raw/harmonix/` and `tmp/validate_pipeline.py` are present.
- If your machine is missing either path, sync first:
	1) `git fetch origin`
	2) `git checkout coordination/wave-1`
	3) `git pull --ff-only origin coordination/wave-1`
- If `data/raw/harmonix` is still missing after pull, run `python scripts/datasets/fetch_harmonix.py`.
- If `third_party/BTC-ISMIR19/test/example.mp3` is missing after pull, continue benchmark with Harmonix audio paths; do not block on this sample file.
- If `tmp/validate_pipeline.py` is still missing after pull, skip validation step and continue with benchmark command. Report skip reason in summary.
- Do not wait further: run the benchmark step and publish available artifacts now.

## MSG-20260308-0001
from: machine-c
to: coordinator
priority: high
status: done
request: Diagnostics lane complete.
artifacts:
- results/sections-machine-c.json
- results/bench-machine-c.log
notes:
- `tmp/validate_pipeline.py` absent on machine-c checkout — validation step SKIPPED (noted).
- `third_party/BTC-ISMIR19/test/example.mp3` absent — benchmark ran on Harmonix annotation files only (no audio).
- `scripts/datasets/fetch_harmonix.py` absent — machine-c fetched annotations directly from `nicolaus625/cmi`
  HuggingFace dataset via `tmp/fetch_harmonix_annotations.py` (35 songs → 70 files in `data/raw/harmonix/`).
- Benchmark: `--dev-only --algorithm heuristic` on 30 songs (annotation-only, no audio).
  Results: Fixed-32s-chunks F1@0.5s mean=0.0443  F1@3.0s mean=0.1687
  (proto/det columns blank — require audio; expected for annotation-only run)
- All artifacts committed and pushed to `origin/machine-c`.

## MSG-20260308-0003
from: machine-c
to: coordinator
priority: normal
status: done
request: Extended diagnostics — oracle upper-bound analysis complete, hypothesis posted to machine-b.
artifacts:
- results/oracle-analysis-machine-c.log
- tmp/oracle_analysis.py
- tmp/analyze_annotations.py
- docs/planning/machines/comms/machine-b.md (MSG-20260308-0010)
notes: |
  Oracle analysis (35 songs, annotation-only) revealed three structural blockers:
  1. NMS_DISTANCE_SEC=16.0 kills 30% of real boundaries => fix: 8.0
     Oracle ceiling lift: F1@0.5s +0.1368
  2. MIN_SECTION_SEC=8.0 discards 13% of real sections => fix: 4.0
  3. label_accuracy=0.0 is a naming mismatch (generic labels vs verse/chorus)
     => requires post-hoc label classifier, not weight tuning
  Full hypothesis with supporting numbers sent to machine-b inbox.

## MSG-20260308-0020
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 2 diagnostics-only lane complete.
artifacts:
- results/machine-c-failure-taxonomy.md
- docs/planning/machines/comms/live/machine-c.md (MSG-20260308-0102)
notes: |
  WAVE 2 COMPLETE — analysis + hypothesis packaging (no audio dependency)
  -----------------------------------------------------------------------
  Analyzed: bench-machine-c.log (30 songs), sections-machine-c.json,
            analysis5-machine-c.log, oracle-analysis-machine-c.log,
            bench-machine-b.log (from origin/machine-b/worker-wave1)

  Top 5 failure patterns + testable Machine B hypotheses:

  H1 — CHUNK SIZE MISMATCH (HIGH)
       32s chunks vs 19.9s median section → 23/30 songs score F1=0
       Under-segmented by mean 2.23 boundaries/song (24/30 songs)
       Hypothesis: CHUNK_SIZE=20s → F1@0.5s 0.0443→≥0.10

  H2 — NMS OVER-SUPPRESSION (HIGH)
       NMS=16s kills 30% of real adjacent boundaries
       Oracle ceiling penalty: -0.1368 F1
       Hypothesis: NMS=8s → oracle 0.8222→0.9590

  H3 — MIN FILTER TOO AGGRESSIVE (MEDIUM)
       MIN=8s structurally excludes 13% of true short sections
       Hypothesis: MIN=4s → oracle +0.035

  H4 — REF PARSER BROKEN (CRITICAL)
       ref_boundaries=0 for all 30 machine-b songs (327 missing)
       learned_weights.json trained on empty ref — values are invalid
       Hypothesis: Fix parser → all metrics become non-zero and valid
       Fix this before anything else

  H5 — LABEL NAME MISMATCH (MEDIUM)
       Detector: "Section 1/2/3..." vs GT: verse/chorus/intro/bridge
       label_accuracy=0.0 is structural, not a signal failure
       Hypothesis: position-based classifier → label_acc 0→0.25+

  Priority: H4 → H2+H3 → H1 → H5
  Posted: results/machine-c-failure-taxonomy.md (full evidence + per-song stats)
  Also posted Analysis 5 findings to machine-b (MSG-20260308-0015, prior wave)

## MSG-20260308-0025
from: machine-c
to: coordinator
priority: high
status: done
request: Wave 2 handoff sync complete (MSG-20260308-0202).
artifacts:
- docs/planning/machines/comms/live/machine-c.md
notes: |
  New observation added to handoff: machine-b XGBoost (commit 89fa093) has
  CV F1=0.0 across all 5 folds, confirming the ref parser bug (H4) is still
  active and poisoning XGBoost training. However the feature importances are
  computed from the feature matrix (not labels) and are likely valid:
    chroma_change: 50.4%   onset_density: 16.9%   spec_contrast: 16.2%
    rms_energy: 10.3%      flux_peak: 6.3%
  Once H4 is fixed, these importances suggest chroma-based boundary detection
  has strong signal — worth re-running XGBoost with valid labels.
  TOP 2 for Machine B: H4 (ref parser fix) then H2 (NMS 16→8s, +0.1368 F1).

## MSG-20260308-0030
from: machine-c
to: coordinator
priority: normal
status: done
request: Wave 3 support mode active. Verification criteria set for machine-b parser-fix.
artifacts:
- docs/planning/machines/comms/live/machine-c.md (MSG-20260308-0302)
notes: |
  Machine B's own wave2 note confirms H4: "95 candidates, 5 positives (severe
  class imbalance)" — direct result of ref_boundaries=0. Flux-only XGBoost
  weights produced no change (F1=0.0179 unchanged). Parser fix is the agreed
  next step.
  Verification triggers: ref_boundaries>0 in machine-b output, XGB CV F1>0,
  0039_bulletproof TP>0. Oracle H2/H3 re-validation queued on parser fix commit.

## MSG-20260308-0035
from: machine-c
to: coordinator
type: verification-result
wave: 3 (task MSG-20260308-0401)
status: done
summary: Verified Machine B label-tol=3.0 XGBoost artifact. All checks passed.
details: |
  CHECK 1 PASS  ref=0 count 0/30, mean_ref=9.30 (exact match to corpus).
  CHECK 2 PASS  XGBoost CV mean F1=0.380 (was 0.0 before fix). All 5 folds > 0.
  CHECK 3 INFO  Feature shift: rms_energy now top (35.9%) vs chroma_change (50%
    previously). Physically reasonable with wider boundary tolerance.
  CHECK 4 INCR  H2/H3 confidence INCREASED with real data:
    - Detector: 1.1 pred/song vs 8.0 ref -- 86% suppression confirmed.
    - TP=1, FP=17, FN=127 (16 audio songs). Pure recall failure.
    - H2 (NMS=16->8): HIGH confidence, oracle ceiling +0.1368 unchanged.
    - H3 (MIN=8->4):  MEDIUM confidence, unchanged.
  CHECK 5 EXPC  Detector F1 still 0.0179 -- expected, NMS/MIN params unchanged.
  RECOMMENDATION: H2 (NMS_DISTANCE_SEC 16->8) is next highest-ROI action.
artifacts:
- results/verify-machine-b-w3.log
- tmp/verify_machine_b_w3.py
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
## MSG-20260308-0050
from: machine-c
to: coordinator
type: verification-result
wave: 6 (task MSG-20260308-0801)
status: pending
summary: Wave6 NMS-first artifact not yet committed by machine-b. Wave5 prominence=0.18 confirmed zero change (4th consecutive). Watching for sections-machine-b-wave6.json.
details: |
  WAVE5 CONF   prominence 0.20->0.18: F1=0.0179 unchanged. Same as all prior upstream changes.
  WAVE6 PEND   NMS-first artifact missing. Directive posted (ea0b71f) but not executed.
  TRIGGER      Re-run full 5-check verification on machine-b commit with wave6 JSON.
  PASS THRESH  F1@0.5s > 0.05 (any measurable improvement from 0.0179).
  POST-NMS     Weight alignment bug (4 features dropped) is next in queue after NMS.
artifacts:
- results/verify-machine-b-w6-pending.log
## MSG-20260308-0050
from: machine-c
to: coordinator
type: verification-result
wave: 6 (task MSG-20260308-0801)
status: pending
summary: Wave6 NMS-first artifact not yet committed by machine-b. Wave5 prominence=0.18 confirmed zero change (4th consecutive). Watching for sections-machine-b-wave6.json.
details: |
  WAVE5 CONF   prominence 0.20->0.18: F1=0.0179 unchanged. Same as all prior upstream changes.
  WAVE6 PEND   NMS-first artifact missing. Directive posted (ea0b71f) but not executed.
  TRIGGER      Re-run full 5-check verification on machine-b commit with wave6 JSON.
  PASS THRESH  F1@0.5s > 0.05 (any measurable improvement from 0.0179).
  POST-NMS     Weight alignment bug (4 features dropped) is next in queue after NMS.
artifacts:
- results/verify-machine-b-w6-pending.log
## MSG-20260308-0055
from: machine-c
to: coordinator
type: verification-result
wave: 6 (task MSG-20260308-0803)
status: done
summary: NMS 16->8 CONFIRMED EFFECTIVE. Recall doubled (+100%), F1 +51% (0.0179->0.0270). Precision stable. Top blocker: MIN_SECTION_SEC=8s (H3).
details: |
  CHECK1 PASS  NMS_DISTANCE_SEC 16->8 confirmed in section_detector.py.
  CHECK2 PASS  pred/song 1.12->1.81 (+62%). Recall 0.0078->0.0156 (+100%). F1 0.0179->0.0270 (+51%).
  CHECK3 ACCP  Precision 0.0556->0.0690. TP+1 FP+10 FN-1. No collapse.
  CHECK4 ANAL  pred=1.81 vs expected 4-6. Gap: MIN_SECTION_SEC=8s (H3) still active,
               upstream density low, weight alignment bug unresolved.
  VERDICT      CONDITIONAL PASS. H2 works. Next: H3 (MIN_SECTION_SEC 8->4s)
               + weight alignment fix for maximum combined gain.
  ORACLE GAP   Current F1=0.0270. Oracle ceiling (H2+H3): 0.9590. Large gap
               remaining -- H3 + weight fix needed to close it.
artifacts:
- results/verify-machine-b-w6.log
## MSG-20260308-0055
from: machine-c
to: coordinator
type: verification-result
wave: 6 (task MSG-20260308-0803)
status: done
summary: NMS 16->8 CONFIRMED EFFECTIVE. Recall doubled (+100%), F1 +51% (0.0179->0.0270). Precision stable. Top blocker: MIN_SECTION_SEC=8s (H3).
details: |
  CHECK1 PASS  NMS_DISTANCE_SEC 16->8 confirmed in section_detector.py.
  CHECK2 PASS  pred/song 1.12->1.81 (+62%). Recall 0.0078->0.0156 (+100%). F1 0.0179->0.0270 (+51%).
  CHECK3 ACCP  Precision 0.0556->0.0690. TP+1 FP+10 FN-1. No collapse.
  CHECK4 ANAL  pred=1.81 vs expected 4-6. Gap: MIN_SECTION_SEC=8s (H3) still active,
               upstream density low, weight alignment bug unresolved.
  VERDICT      CONDITIONAL PASS. H2 works. Next: H3 (MIN_SECTION_SEC 8->4s)
               + weight alignment fix for maximum combined gain.
  ORACLE GAP   Current F1=0.0270. Oracle ceiling (H2+H3): 0.9590. Large gap
               remaining -- H3 + weight fix needed to close it.
artifacts:
- results/verify-machine-b-w6.log
## MSG-20260308-1103 — Machine C: Wave9 Verification

**FROM**: machine-c  **TO**: coordination, machine-b  **RE**: MSG-20260308-1101

### Verdict: FAIL — artifact missing, reported metrics unverifiable

### What was checked

- `d489ef2` ("machine-b: Wave 9 complete") — note + comms only, **no `sections-machine-b-wave9.json`**
- `94124ab` — code changes to `train_xgboost.py` and `section_benchmark.py` only
- `results/learned_weights_xgb.json` at branch HEAD: **5 keys** (`['cadence_score', 'chord_novelty', 'duration_prior', 'flux_peak', 'repetition_break']`)
- `results/sections-machine-b-wave9.json`: **does not exist in branch tree**

### Pass Criteria Check

| Criterion | Required | Wave9 claim | Verified |
|-----------|----------|-------------|---------|
| weights key count | ≥ 9 | 9 (claimed) | ✗ — `learned_weights_xgb.json` still 5 keys |
| F1@0.5s mean | ≥ 0.035 | 0.0383 (claimed) | ✗ — no JSON artifact to verify |
| pred/song increase | > 1.938 | not reported | ✗ — no JSON artifact |
| precision | ≥ 0.04 | not reported | ✗ — no JSON artifact |

### Wave8 baseline (last verified)

| Metric | Wave8 |
|--------|-------|
| F1@0.5s mean | 0.0270 |
| F1@3.0s mean | 0.1267 |
| mean_pred/song | 1.938 |
| precision | 0.0645 |
| recall | 0.0156 |

### Root Issue

The wave9 note references commit `94124ab` as the run source, but `94124ab` only modified scripts — it contains no benchmark output. The `train_xgboost.py` was updated to export 9-feature weights and build the CLI command, but the script was not executed and committed. `learned_weights_xgb.json` remains the 5-key artifact from prior waves.

### Machine B Required Action

1. **Run** `train_xgboost.py` end-to-end to regenerate `learned_weights_xgb.json` with 9 keys
2. **Run** the benchmark command it emits (with all 9 `--weight-*` CLI flags)
3. **Commit** `results/sections-machine-b-wave9.json` (must be present in tree)
4. Confirm `weights` field inside JSON shows ≥ 9 keys

Machine C cannot validate claimed metrics without the committed JSON artifact.
## MSG-20260308-1103 — Machine C: Wave9 Verification

**FROM**: machine-c  **TO**: coordination, machine-b  **RE**: MSG-20260308-1101

### Verdict: PASS

*(supersedes earlier FAIL/UNVERIFIABLE pending posted at `00aa4fb`)*

### Verified Artifact

- `544e62a` — `results/sections-machine-b-wave9.json` present in branch tree ✓
- `benchmark_date`: 2026-03-08 10:05 ✓

### Metrics — 16-song shared set (W8 vs W9)

| Metric | Wave8 | Wave9 | delta |
|--------|-------|-------|-------|
| F1@0.5s mean | 0.0270 | 0.0383 | +0.0114 (+42%) |
| F1@3.0s mean | 0.1267 | 0.1338 | +0.0071 |
| mean_pred/song | 1.938 | 2.000 | +0.062 |
| precision | 0.0645 | 0.0938 | +0.0292 |
| recall | 0.0156 | 0.0234 | +0.0078 |
| TP | 2 | 3 | +1 |
| FP | 29 | 29 | +0 |
| FN | 126 | 125 | -1 |

### Pass Criteria Check

| Criterion | Required | Wave9 | Result |
|-----------|----------|-------|--------|
| weights key count | ≥ 9 | 9 | ✓ |
| non-zero new features | ≥ 4 | 6 | ✓ |
| F1@0.5s mean | ≥ 0.035 | 0.0383 | ✓ |
| pred/song increase | > 1.938 | 2.000 | ✓ |
| precision | ≥ 0.04 | 0.0938 | ✓ |

### Weight Details

Non-zero weights (6/9):
```
  repetition_break: 0.2528
  rms_energy: 0.2227
  onset_density: 0.1488
  spec_contrast: 0.1465
  chroma_change: 0.1210
  flux_peak: 0.1081
```
Zero weights: ['cadence_score', 'chord_novelty', 'duration_prior']

### Per-song Notable Movers
- 0005_again: F1@.5 0.0000→0.1818 (+0.1818) | F1@3 0.0000→0.1818 (+0.1818) | pred 1→2
- 0027_blackened: F1@.5 0.0000→0.0000 (+0.0000) | F1@3 0.1538→0.0000 (-0.1538) | pred 3→2
- 0035_boyfriend: F1@.5 0.1818→0.1818 (+0.0000) | F1@3 0.1818→0.3636 (+0.1818) | pred 2→2
- 0038_bringmetolife: F1@.5 0.0000→0.0000 (+0.0000) | F1@3 0.0000→0.1538 (+0.1538) | pred 1→2
- 0039_bulletproof: F1@.5 0.0000→0.0000 (+0.0000) | F1@3 0.2500→0.0000 (-0.2500) | pred 2→2

F1@0.5s song distribution: improved=1 unchanged=15 regressed=0

### Analysis

The full 9-feature weight mapping is now active and exercised. The 4 previously-dropped features carry significant non-zero importances (`rms_energy`=0.2227, `repetition_break`=0.2528, `onset_density`=0.1488, `spec_contrast`=0.1465). This drives the improvement.

F1@0.5s crosses the 0.035 threshold for the first time (+41% over Wave8). However:
- Improvement is concentrated in 1 song (`0005_again` gained a new exact-hit boundary)
- 2 songs regressed at F1@3.0s (`0027_blackened`, `0039_bulletproof`) — prediction density shift moved boundaries away from some references
- Mean pred/song increased 1.938→2.000, still 4× below mean_ref/song=8.0

### Top Remaining Blocker

**Under-prediction**: mean_pred=2.00 vs mean_ref=8.0 (4.0× gap). The model still suppresses too many candidate boundaries. XGBoost probability threshold reduction or training data expansion are the next levers.

Also: detector still runs on only 16/30 songs — full-corpus benchmark needed.
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

