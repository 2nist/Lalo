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
