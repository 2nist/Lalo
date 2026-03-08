# Machine C — Wave 2 Failure Taxonomy
**Generated**: 2026-03-07  
**Lane**: single-song-diagnostics (analysis-only, no audio dependency)  
**Source data**: `results/bench-machine-c.log`, `results/sections-machine-c.json`, `results/analysis5-machine-c.log`, `results/oracle-analysis-machine-c.log`, `results/bench-machine-b.log`  
**Benchmark corpus**: 30 Harmonix songs, annotation-only (0 audio), heuristic algorithm

---

## Summary Scores (Cross-Machine)

| Method | Machine | F1@0.5s | F1@3.0s | Notes |
|---|---|---|---|---|
| fixed_chunks (32s) | machine-c | 0.0443 | 0.1687 | annotation-only |
| detector (audio) | machine-b | 0.0179 | 0.0779 | ref_boundaries=0, invalid |
| oracle (current params) | machine-c | 0.8222 | 0.8222 | annotation ceiling |
| oracle (proposed params) | machine-c | 0.9590 | 0.9590 | NMS→8s, MIN→4s |

---

## Failure Pattern 1 — Fixed-Chunk Size Mismatches Musical Section Length

**Severity**: HIGH — accounts for 23/30 songs scoring F1@0.5s=0.000  
**Type**: Structural / Parameter mismatch

**Evidence**:
- Median Harmonix section duration = **19.9s**; current chunk size = **32s** (161% of median)
- Fixed-32s under-segments 24/30 songs (80%); over-segments only 4/30 (13%)
- Mean boundary count deficit: **−2.23 per song** (predicts 2.23 fewer boundaries than ground truth)
- 21/30 songs under-segmented by 2+ boundaries
- Aggregate: TP=8, FP=174, FN=241 → precision=0.044, recall=0.032

**Root cause**: Chunk stride of 32s exceeds actual section length for most pop/rock songs in Harmonix. When chunk boundaries land between two real boundaries they score FP + FN simultaneously.

**Testable Hypothesis for Machine B (H1)**:
> Reducing chunk size from 32s to 20s (≈ median section duration) will increase fixed_chunks F1@0.5s from 0.0443 to ≥0.10.  
> Test: Set `CHUNK_SIZE_SEC = 20` in `section_benchmark.py` and re-run `--dev-only`. Expect TP↑ and the 23-song zero-F1 cluster to partially break up.  
> Leading indicator: mean pred_boundaries per song should increase from ~4.6 to ~7.0, approaching the ground-truth mean of 9.3.

---

## Failure Pattern 2 — NMS Over-Suppression Kills Real Boundaries

**Severity**: HIGH — reduces oracle ceiling by −0.1368 F1  
**Type**: Algorithmic parameter too aggressive

**Evidence**:
- `NMS_DISTANCE_SEC = 16.0` suppresses any predicted boundary within 16s of a higher-scoring one
- 30% of adjacent true Harmonix boundaries are **<16s apart** (measured across 35 songs)
- Oracle with current NMS: F1@0.5s = 0.8667 (vs 1.0 perfect, −0.1333 from NMS alone)
- Combined NMS + MIN oracle: F1@0.5s = 0.8222

**Root cause**: NMS was tuned for a coarser segment granularity. Pop/rock songs regularly have intro→verse (8–12s) and verse→chorus (12–16s) transitions that are closer than 16s.

**Testable Hypothesis for Machine B (H2)**:
> Setting `NMS_DISTANCE_SEC = 8.0` will raise the oracle ceiling from F1@0.5s=0.8222 to ≥0.9590 (+0.1368).  
> Test (annotation-only, no audio required): Run `tmp/oracle_analysis.py` with NMS parameter patched to 8.0. Expect the suppressed-boundary count to drop from 30% to <10%.  
> Validation: Per-song NMS suppression rate should be measurable as a new benchmark column.

---

## Failure Pattern 3 — MIN_SECTION Filter Excludes Short Structural Events

**Severity**: MEDIUM — eliminates 13% of true sections structurally  
**Type**: Structural / Hard floor too high

**Evidence**:
- `MIN_SECTION_SEC = 8.0` silently drops any detected section shorter than 8 seconds
- 13% of true Harmonix sections are **<8s** (intros, silences, pre-choruses, short tags)
- Oracle without MIN filter: F1@0.5s = 0.8667; oracle with MIN=8s: F1@0.5s = 0.9016
- Net cost of current MIN setting: −0.0349 F1

**Root cause**: The filter was designed to remove noise fragments but the lower bound was set too conservatively, cutting legitimate short structural sections.

**Testable Hypothesis for Machine B (H3)**:
> Setting `MIN_SECTION_SEC = 4.0` will recover 13% of structurally excluded sections.  
> Test: Re-run benchmark with MIN=4.0. Expect FN to decrease by ~10–15 per song on average. F1 gain from this change alone (annotation-only): +0.0349.  
> Note: Combined with H2 (NMS=8s), expected ceiling: F1@0.5s=0.9590.

---

## Failure Pattern 4 — Reference Boundary Parser Broken (Machine B — 100% Silent Failure)

**Severity**: CRITICAL — invalidates all Machine B scoring  
**Type**: Engineering / Parser bug

**Evidence** (from `results/analysis5-machine-c.log`):
- `ref_boundaries = 0` for **all 30 songs** in `results/false_pos_neg_per_song.csv`
- Expected: ~9.3 ref boundaries/song → ~280 total across 30 songs; actual: **0**
- Consequence: TP=0, FN=0 for all songs; every detector prediction counted as FP
- Machine-b published `learned_weights.json` trained against this invalid ground truth:
  - `flux_peak=0.2085`, `repetition_break=−1.44`, all others ≈ 0
  - These weights are fitted to predict against empty reference; they are meaningless

**Root cause**: Reference section files exist and contain data (confirmed in our corpus), but machine-b's parser fails silently returning count=0. Shared root cause with our blocker #3 (label_accuracy=0.0).

**Testable Hypothesis for Machine B (H4)**:
> Fixing the reference boundary parser will cause all metrics (precision, recall, F1, label_accuracy) to become non-zero and meaningful for the first time.  
> Test: For song `0003_6foot7foot` (audio=yes, pred=1, ref=0), add a debug print of the section file path and first 3 lines. If the file exists and has data, the parser is silently failing.  
> Expected after fix: ref_boundaries ≈ 9 per song, FN will dominate (detector currently produces only 1–2 boundaries vs 9 ground truth), which will correctly characterise the detector as a **recall failure** not a precision failure.

---

## Failure Pattern 5 — Label Naming Mismatch (Structurally Guarantees label_accuracy=0)

**Severity**: MEDIUM — blocks any label quality measurement  
**Type**: Design gap — label vocabulary mismatch

**Evidence**:
- Machine-b detector emits: `"Section 1"`, `"Section 2"`, `"Section 3"`, …
- Harmonix ground truth uses: `verse`, `chorus`, `intro`, `bridge`, `silence`, `prechorus`, `outro`
- String equality check → label_accuracy=0.0000 for all songs (confirmed, n=16 audio songs)
- No weight tuning can convert `"Section 1"` to `"verse"` — these are categorically different vocabularies

**Root cause**: No post-hoc label classification step exists between boundary detection and label assignment. The detector inherits generic section numbers rather than musically meaningful labels.

**Testable Hypothesis for Machine B (H5)**:
> Adding a 3-class position-based label heuristic (first section → `intro`, last section → `outro`, alternating remaining by energy → `chorus`/`verse`) will raise label_accuracy from 0.0 to ≥0.25.  
> Test (zero audio dependency): Implement as a post-processing function; apply to existing `sections-machine-b.json` output without re-running the detector. Run benchmark scorer's label eval only.  
> Stretch: use repetition-map (SSM diagonal) to distinguish verse from chorus — expected label_accuracy ≥0.50.

---

## Bonus Observation — Prototype Scorer Module Missing (`scripts.experiments`)

**Severity**: LOW (blocks Proto@0.5s column only)  
**Type**: Missing dependency

**Evidence** (`results/bench-machine-b.log`):
- 18/30 songs log: `prototype error: No module named 'scripts.experiments'`
- `Proto@0.5s` column shows `-` for all songs; only `Det@0.5s` and `Fixed@0.5s` are populated

**Hypothesis for Machine B**: The prototype scorer path requires `scripts/experiments/__init__.py` to exist. Creating an empty stub or installing the module will unblock this column with zero logic changes.

---

## Priority Order for Machine B

| # | Pattern | Hypotheses | Expected F1 Gain | Effort |
|---|---|---|---|---|
| 1 | Ref parser broken | H4 | Unlocks all scoring | Low (debug + fix) |
| 2 | NMS over-suppression | H2 | +0.1368 ceiling | Low (param change) |
| 3 | MIN filter too high | H3 | +0.035 ceiling | Low (param change) |
| 4 | Chunk size mismatch | H1 | +0.06 baseline est. | Low (param change) |
| 5 | Label mismatch | H5 | label_acc 0→0.25+ | Medium (post-proc) |

**Recommended execution order**: H4 → H2+H3 (simultaneously) → H1 → H5  
H4 must come first — without valid ref_boundaries, none of H1–H3 gains are measurable.
