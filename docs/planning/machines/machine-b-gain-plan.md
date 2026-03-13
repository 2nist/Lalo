# Machine B: Incremental Gain Plan
# Section Detection Improvements — Strict Execution

## Purpose

This document is a strict, ordered execution plan for a background agent.
The agent MUST follow these steps in sequence without deviation.

## Primary Dataset: McGill SALAMI (Billboard subset)

**This plan targets the McGill SALAMI dataset as the primary evaluation target.**

- 212 usable annotation + audio pairs (confirmed)
- Audio: `data/salami_audio/<salami_id>.m4a` (trimmed, SALAMI-aligned)
- Annotations: `datasets/mcgill/mcgill_jcrd_salami_Billboard/<id_4digit>_*.json`
- Format: `sections[].start_ms` / `sections[].duration_ms`

The Harmonix dev-only benchmark is kept as a **regression sanity check only**.
All primary gain decisions are made on SALAMI numbers.

### Critical Rules (Non-Negotiable)

1. **DO NOT** redesign, rewrite, or replace any existing system.
2. **DO NOT** touch `audioanalysis/`, `audioanalysis/btc_runtime/`, or `audioanalysis/chord_pipeline.py`.
3. **DO NOT** change the benchmark's evaluation logic (scoring, tolerance windows, output format).
4. **DO NOT** change the chord detection pipeline or BTC runtime.
5. After each step, run `python -m py_compile scripts/analysis/section_detector.py scripts/bench/section_benchmark.py` and stop if it fails.
6. After each step that changes detection logic, run the SALAMI benchmark (Steps 1–2 first) and record F1 delta before proceeding.
7. If SALAMI F1 regresses at any step, revert that step and record the regression in `results/gain-plan-log.json`. Do not attempt to fix it — skip to the next step.
8. After any SALAMI eval, also run `--dev-only` Harmonix as a sanity check. It is OK for Harmonix numbers to be different; they must not catastrophically collapse (F1@3.0s must stay >= 0.20).

### Baselines

Harmonix dev-only (Wave-15, legacy reference — do not optimise for this):
- F1 @ 0.5s: **0.0498**
- F1 @ 3.0s: **0.3073**

McGill SALAMI (to be established in Step 2 — this becomes the primary gain target):
- F1 @ 0.5s: **TBD in Step 2**
- F1 @ 3.0s: **TBD in Step 2**

---

## Step 0: Confirm Environment

**Goal**: Verify all required files, libraries, and matched pairs are in place before writing any code.

**Command:**
```
python -u -c "
from pathlib import Path; import json, msaf, sklearn, mir_eval, joblib
ann_dir = Path('datasets/mcgill/mcgill_jcrd_salami_Billboard')
audio_dir = Path('data/salami_audio')
ann_map = {}
for f in ann_dir.glob('*.json'):
    num = f.stem.split('_')[0].lstrip('0') or '0'
    ann_map[num] = f
m4as = {f.stem for f in audio_dir.glob('[0-9]*.m4a')}
both = sorted(ann_map.keys() & m4as, key=int)
print('Usable SALAMI pairs:', len(both))
print('msaf:', msaf.__version__, '  sklearn:', sklearn.__version__, '  mir_eval:', mir_eval.__version__)
assert len(both) >= 150, 'Too few pairs — check data/salami_audio and datasets/mcgill'
print('PASS')
"
```

**Pass condition**: Prints `PASS` with >= 150 pairs.

**Record**: Create `results/gain-plan-log.json`:
```json
{
  "primary_dataset": "mcgill_salami_billboard",
  "primary_audio_dir": "data/salami_audio",
  "primary_ann_dir": "datasets/mcgill/mcgill_jcrd_salami_Billboard",
  "usable_pairs": <n>,
  "harmonix_legacy_baseline": { "f1_05": 0.0498, "f1_3": 0.3073 },
  "salami_baseline": null,
  "steps": []
}
```

---

## Step 1: Build SALAMI Benchmark Adapter

**Goal**: Create `scripts/bench/salami_benchmark.py` — the primary evaluation
script going forward. This mirrors `section_benchmark.py` but reads McGill SALAMI
annotations and audio.

**SALAMI annotation format** (confirmed):
```json
{
  "title": "...", "artist": "...",
  "sections": [
    { "id": "A1", "sectionType": "Intro", "start_ms": 73, "duration_ms": 22273 }
  ]
}
```

**Pairing logic**:
- For each `data/salami_audio/<salami_id>.m4a`:
  - Find annotation: `datasets/mcgill/mcgill_jcrd_salami_Billboard/<salami_id zero-padded to 4 digits>_*.json`
    (e.g. salami_id `3` → glob `0003_*.json`)
  - Extract reference boundaries: `[s["start_ms"] / 1000.0 for s in d["sections"]]`
  - Also compute reference intervals: `[[start_s, start_s + duration_ms/1000] for each section]`
- Run `detect_sections(audio_path, chords=None, algorithm=args.algorithm)`
- Evaluate with same `_boundary_f1` function at tolerances [0.5, 3.0]

**The new script must**:
- Accept `--algorithm heuristic|auto|msaf_scluster|msaf_sf|scored`
- Accept `--max-songs N` and `--out <path>`
- Accept `--salami-audio-dir` (default `data/salami_audio`) and `--ann-dir`
- Copy the `_boundary_f1` function verbatim from `section_benchmark.py` — do NOT import it, copy it, to keep the scripts independent
- Output the **identical top-level JSON summary format** as `section_benchmark.py`:
  `{"summary": {...}, "per_song": [...]}`
- Store `candidates` list in each `per_song` entry (needed for Step 7 training data extraction)
- NOT modify `section_benchmark.py` in any way

**Compile check**: `python -m py_compile scripts/bench/salami_benchmark.py`

**Pilot test** (20 songs to confirm it runs):
```
python -u scripts/bench/salami_benchmark.py --max-songs 20 --algorithm heuristic --out results/salami-pilot-20.json
```

**Pass condition**: Runs without error on 20 songs, produces valid JSON with
`summary.detector.F1@0.5s` and `summary.detector.F1@3.0s` keys.

**Log entry**: `{ "step": 1, "name": "salami_benchmark_adapter", "pilot_songs": 20, "status": "completed" }`

---

## Step 2: Establish SALAMI Baseline (All 212 Pairs)

**Goal**: Run the full SALAMI benchmark with the current heuristic detector.
This establishes the primary baseline numbers that all subsequent steps must beat or match.

**Command:**
```
python -u scripts/bench/salami_benchmark.py --algorithm heuristic --out results/salami-baseline-heuristic.json
```

Also run Harmonix sanity check (fast, ~30 songs):
```
python -u scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/harmonix-sanity-baseline.json
```

**Record** both F1 numbers in `results/gain-plan-log.json`:
```json
"salami_baseline": { "f1_05": <value>, "f1_3": <value>, "songs": <n>, "source": "salami-baseline-heuristic.json" },
"harmonix_sanity": { "f1_05": <value>, "f1_3": <value>, "source": "harmonix-sanity-baseline.json" }
```

**Pass condition**: Runs on >= 150 SALAMI songs without error.
These baseline numbers become the regression guard for all remaining steps.

**Log entry**: `{ "step": 2, "name": "salami_baseline", "salami_f1_05": <value>, "salami_f1_3": <value>, "status": "completed" }`

---

## Step 3: Add Pairwise + Deviation Metrics to SALAMI Benchmark Output

**Goal**: Add `mir_eval.segment.pairwise` and `mir_eval.segment.deviation` to
the per-song results in `salami_benchmark.py`. Diagnostic metrics only —
no change to detection logic.

**File to edit**: `scripts/bench/salami_benchmark.py` (only — NOT section_benchmark.py)

**What to add**:
- Import `mir_eval.segment` at the top.
- At per-song result assembly, add:
  - `pairwise_f1`: `mir_eval.segment.pairwise(ref_intervals, ref_labels, est_intervals, est_labels)[2]`
    Use `sectionType` value as label for ref intervals (available from SALAMI annotations).
    Use `"S"` as uniform label for all detected sections.
  - `mean_deviation_s`: `mir_eval.segment.deviation(ref_intervals, est_intervals)[0]`
- These go in `per_song[*]` only — do not change top-level summary aggregation.

**Compile check**: `python -m py_compile scripts/bench/salami_benchmark.py`

**Verification**: Re-run pilot (20 songs), confirm F1 numbers unchanged, confirm new keys appear.

**Log entry**: `{ "step": 3, "name": "pairwise_metrics_salami", "delta_f1": 0.0, "status": "completed" }`

---

## Step 4: Upgrade SSM — Replace Simple Checkerboard with Full Recurrence Matrix

**Goal**: Replace the hand-rolled cosine SSM in `_build_ssm` with
`librosa.segment.recurrence_matrix` + `librosa.segment.path_enhance`.
This improves the `repetition_break` signal without changing any other logic.

**File to edit**: `scripts/analysis/section_detector.py`

**Exact change — inside `_build_ssm`, replace the SSM construction block only**:

Current (the line computing `G_norm @ G_norm.T`):
```python
G = np.stack(groups)
G_norm = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-8)
return G_norm @ G_norm.T, np.array(group_times)
```

Replace with:
```python
G = np.stack(groups)
try:
    import librosa.segment as lseg
    R = lseg.recurrence_matrix(G.T, metric='cosine', mode='affinity',
                                sparse=False, sym=True)
    R = lseg.path_enhance(R, n=9)
except Exception:
    G_norm = G / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-8)
    R = G_norm @ G_norm.T
return R, np.array(group_times)
```

The `try/except` keeps the old behaviour as fallback on any failure.
Do NOT change `_checkerboard_novelty`, `_repetition_break_at_candidates`,
`SSM_BAR_BEATS`, or `SSM_WINDOW_BARS`.

**Compile check**: `python -m py_compile scripts/analysis/section_detector.py`

**SALAMI benchmark check** (20-song pilot first, then full if pilot passes):
```
python -u scripts/bench/salami_benchmark.py --max-songs 20 --algorithm heuristic --out results/salami-step4-pilot.json
python -u scripts/bench/salami_benchmark.py --algorithm heuristic --out results/salami-step4-full.json
```

Also run Harmonix sanity:
```
python -u scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/harmonix-step4.json
```

**Pass condition (SALAMI)**: F1@0.5s >= salami_baseline.f1_05 - 0.005 (neutral or gain).
**Pass condition (Harmonix)**: F1@3.0s >= 0.20.
Revert the `_build_ssm` change if SALAMI regresses.

**Log entry**: `{ "step": 4, "name": "recurrence_matrix_ssm", "salami_delta_f1_05": <delta>, "salami_delta_f1_3": <delta>, "status": "completed|reverted" }`

---

## Step 5: Add MSAF Boundary Votes as a 10th Feature Signal

**Goal**: Run `msaf` with `scluster` on each song and inject its boundary
timestamps as a binary proximity feature (`msaf_vote`) into the candidate
feature vector. This adds one feature; it does NOT replace the heuristic.

**Files to edit**: `scripts/analysis/section_detector.py`

### 5a: Add `msaf_vote` to DEFAULT_WEIGHTS
```python
"msaf_vote": 0.15,
```

### 5b: Add `_msaf_boundary_votes` helper after `_build_ssm`
```python
def _msaf_boundary_votes(
    audio_path: Path,
    candidate_times: np.ndarray,
    tolerance_sec: float = 4.0,
    msaf_algo: str = "scluster",
) -> np.ndarray:
    """Return 1.0 for each candidate within tolerance_sec of an MSAF boundary, else 0.0.
    Returns zeros on any failure (MSAF unavailable, timeout, etc)."""
    votes = np.zeros(len(candidate_times))
    try:
        import warnings, msaf
        warnings.filterwarnings("ignore")
        results = msaf.process(str(audio_path), boundaries_id=msaf_algo,
                               feature="pcp", labels_id=None, annot_beats=False)
        msaf_times = np.array([float(t) for t in results[0]])
        for i, ct in enumerate(candidate_times):
            if len(msaf_times) and np.min(np.abs(msaf_times - ct)) <= tolerance_sec:
                votes[i] = 1.0
    except Exception:
        pass
    return votes
```

### 5c: Call inside `detect_sections` (heuristic path only)
After `rep_break = _repetition_break_at_candidates(...)`:
```python
msaf_vote = _msaf_boundary_votes(audio_path, times)
```

### 5d: Add to `scores` expression
```python
+ weights.get("msaf_vote", 0.0) * msaf_vote
```

### 5e: Add to `feats` dict in candidate log
```python
"msaf_vote": round(float(msaf_vote[i]), 4),
```

**Compile check**: `python -m py_compile scripts/analysis/section_detector.py`

**SALAMI pilot** (5 songs to check timing — MSAF adds per-song overhead):
```
python -u scripts/bench/salami_benchmark.py --max-songs 5 --algorithm heuristic --out results/salami-step5-pilot5.json
```
If any song takes > 120s, set a 60s subprocess timeout around the `msaf.process` call.

**SALAMI full**:
```
python -u scripts/bench/salami_benchmark.py --algorithm heuristic --out results/salami-step5-full.json
```

**Harmonix sanity**:
```
python -u scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/harmonix-step5.json
```

**Pass condition (SALAMI)**: F1@0.5s >= salami_baseline.f1_05 - 0.005.
**Pass condition (Harmonix)**: F1@3.0s >= 0.20.
Revert Steps 5a–5e if SALAMI regresses.

**Log entry**: `{ "step": 5, "name": "msaf_vote_feature", "salami_delta_f1_05": <delta>, "salami_delta_f1_3": <delta>, "status": "completed|reverted" }`

---

## Step 6: Grid Search on `msaf_vote` + `repetition_break` Weights Against SALAMI

**Goal**: Find the best weights for the two new structural features using SALAMI
as the eval target (not Harmonix).

**File to edit**: `scripts/tools/grid_small_params.py`

Add a `--grid structural` mode that sweeps:
- `msaf_vote_weights = [0.05, 0.10, 0.15, 0.20, 0.30]`
- `rep_break_weights = [0.05, 0.10, 0.15, 0.20]`
- All other weights fixed at `DEFAULT_WEIGHTS` values
- Evaluate each combo on a 30-song SALAMI sample (not the 8-song Harmonix regression set)
  — use salami IDs from the first 30 matched pairs sorted by ID
- Output to `results/grid_structural.json`

**Command**:
```
python scripts/tools/grid_small_params.py --grid structural --out results/grid_structural.json
```

**Pass condition**: Completes, records best combo, logs SALAMI F1 per combo.

**Log entry**: `{ "step": 6, "name": "structural_weight_grid_salami", "best_combo": { "msaf_vote": <v>, "rep_break": <v>, "salami_f1_05": <v> }, "status": "completed" }`

---

## Step 7: Apply Best Weights and Run Full SALAMI + Harmonix Eval

**Goal**: Apply the winning weights from Step 6 to `DEFAULT_WEIGHTS` and do
a full eval on both datasets.

**Decision rule**:
- Only update `DEFAULT_WEIGHTS` if the grid best combo shows SALAMI F1@3.0s improvement >= 0.005 over Step 2 baseline.
- Otherwise: leave `DEFAULT_WEIGHTS` unchanged and log as `weights_unchanged`.

**Commands**:
```
python -u scripts/bench/salami_benchmark.py --algorithm heuristic --out results/salami-step7-final.json
python -u scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/harmonix-step7-final.json
```

**Pass condition (SALAMI)**: F1@0.5s >= salami_baseline.f1_05 - 0.005.
**Pass condition (Harmonix)**: F1@3.0s >= 0.20.
Revert weight change if SALAMI regresses.

**Log entry**: `{ "step": 7, "name": "apply_best_weights", "weights_updated": true|false, "salami_f1_05": <v>, "salami_f1_3": <v>, "harmonix_f1_3": <v>, "status": "completed|reverted" }`

---

## Step 8: Extract Training Data for Learned Scorer from SALAMI

**Goal**: From the best SALAMI benchmark run so far, extract TP/FP labeled
feature vectors for training a gradient-boosted classifier.

**Create**: `scripts/train/extract_training_data.py`

**Logic**:
- Read the best SALAMI benchmark result JSON (whichever of step2/step5/step7 gave highest F1@3.0s)
- For each song's `per_song[*].detector.candidates` list:
  - For each candidate, compare `time_s` to SALAMI reference boundaries
  - Label `1` (TP) if within 0.5s of any reference boundary, else `0` (FP)
  - Emit row with all feature columns: `flux_peak, chord_novelty, cadence_score, repetition_break, duration_prior, chroma_change, spec_contrast, onset_density, rms_energy, msaf_vote, label`
  - If `msaf_vote` key is absent (pre-Step-5 result), fill with `0.0`
- Write to `data/training/salami_candidates.csv`
- Print class balance

**Create directory first**: `mkdir -p data/training`

**Command**:
```
python scripts/train/extract_training_data.py --benchmark results/salami-baseline-heuristic.json --out data/training/salami_candidates.csv
```

**Pass condition**: CSV written with >= 500 rows and >= 50 positive (TP) rows.

**Log entry**: `{ "step": 8, "name": "extract_training_data", "total_rows": <n>, "positive_rows": <n>, "class_balance_pct_positive": <pct>, "status": "completed" }`

---

## Step 9: Train Gradient-Boosted Scorer

**Goal**: Train a `GradientBoostingClassifier` on SALAMI candidate data.

**Create**: `scripts/train/train_scorer.py`

**Constraints** (do not deviate):
- `sklearn.ensemble.GradientBoostingClassifier` only — no torch, no tensorflow.
- 80/20 stratified train/val split on the `label` column.
- Inverse-frequency `sample_weight` to handle class imbalance.
- Hyperparameters: `n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8`
  — do not auto-tune these, leave for manual iteration.
- Feature columns: all 10 feature columns in the order listed in Step 8.
- Save to `data/training/scorer_gbt.pkl` via `joblib.dump`.
- Print: train F1, val F1, top-3 feature importances by name.

**Command**:
```
python scripts/train/train_scorer.py --data data/training/salami_candidates.csv --out data/training/scorer_gbt.pkl
```

**Pass condition**: Val F1 > 0.25 (low bar — confirms model is learning).

**Log entry**: `{ "step": 9, "name": "train_scorer", "val_f1": <value>, "top_features": [...], "model_path": "data/training/scorer_gbt.pkl", "status": "completed" }`

---

## Step 10: Wire Scorer as `algorithm="scored"` Mode in Detector

**Goal**: Add a `scored` algorithm mode to `detect_sections` that replaces the
linear weighted sum with the trained GBT scorer for candidate ranking.
This is an additional mode — it does NOT replace `heuristic` or change defaults.

**File to edit**: `scripts/analysis/section_detector.py`

**What to add**:
- When `algorithm="scored"`:
  - Load `data/training/scorer_gbt.pkl` lazily, cache in a module-level dict.
  - If pkl does not exist → fall back to `"heuristic"` silently, log in result meta.
  - Compute all 10 feature vectors identically to heuristic mode.
  - Replace `scores = (weights[...] * feature ...)` with `scores = model.predict_proba(X)[:, 1]`
    where `X` is `np.column_stack([flux_scores, chord_novelty, ..., msaf_vote])`.
  - Pass `scores` into the existing `_nms_by_score` unchanged.
  - All NMS, beat-snapping, min_section_sec logic is **identical** to heuristic.
  - Set `"algorithm": "scored"` in result meta.

**Compile check**: `python -m py_compile scripts/analysis/section_detector.py`

**Benchmark check — SALAMI primary**:
```
python -u scripts/bench/salami_benchmark.py --algorithm scored --out results/salami-step10-scored.json
```

**Benchmark check — Harmonix sanity**:
```
python -u scripts/bench/section_benchmark.py --dev-only --algorithm scored --out results/harmonix-step10-scored.json
```

**Pass condition (SALAMI)**: F1@0.5s >= salami_baseline.f1_05 (neutral is fine —
this is a new mode, not a default replacement).
**Pass condition (Harmonix)**: F1@3.0s >= 0.20.

**Log entry**: `{ "step": 10, "name": "scored_algorithm_mode", "salami_f1_05": <v>, "salami_f1_3": <v>, "harmonix_f1_3": <v>, "vs_salami_baseline_delta_f1_3": <delta>, "status": "completed" }`

---

## Completion Criteria

The plan is complete when:
1. `results/gain-plan-log.json` has all 10 step entries (some may be `"status": "reverted"`).
2. `results/salami-baseline-heuristic.json` exists (Step 2).
3. `data/training/scorer_gbt.pkl` exists (Step 9).
4. SALAMI F1@3.0s from `scored` mode (Step 10) >= SALAMI baseline from Step 2.
5. Harmonix F1@3.0s >= 0.20 at end of plan.
6. `python -m py_compile scripts/analysis/section_detector.py scripts/bench/section_benchmark.py scripts/bench/salami_benchmark.py` passes.

## Files Created by This Plan

| Path | Created in Step |
|------|----------------|
| `results/gain-plan-log.json` | Step 0 |
| `scripts/bench/salami_benchmark.py` | Step 1 |
| `results/salami-pilot-20.json` | Step 1 |
| `results/salami-baseline-heuristic.json` | Step 2 |
| `results/harmonix-sanity-baseline.json` | Step 2 |
| `results/salami-step4-full.json` | Step 4 |
| `results/salami-step5-full.json` | Step 5 |
| `results/grid_structural.json` | Step 6 |
| `results/salami-step7-final.json` | Step 7 |
| `results/harmonix-step7-final.json` | Step 7 |
| `scripts/train/extract_training_data.py` | Step 8 |
| `data/training/salami_candidates.csv` | Step 8 |
| `scripts/train/train_scorer.py` | Step 9 |
| `data/training/scorer_gbt.pkl` | Step 9 |
| `results/salami-step10-scored.json` | Step 10 |
| `results/harmonix-step10-scored.json` | Step 10 |

## Files Modified by This Plan

| Path | Modified in Step |
|------|-----------------|
| `scripts/bench/salami_benchmark.py` | Step 3 (metrics only, new file) |
| `scripts/analysis/section_detector.py` | Steps 4, 5, 10 |
| `scripts/tools/grid_small_params.py` | Step 6 |
