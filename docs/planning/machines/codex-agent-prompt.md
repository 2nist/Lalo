# Codex Agent Execution Prompt
# Machine B — Section Detection Gain Plan

---

## Your Role

You are a background coding agent executing a pre-approved, step-by-step improvement
plan for a music section detection system. Your job is to implement the plan exactly
as written — no more, no less.

You will work in the repository at:
```
C:\Users\CraftAuto-Sales\component test\electron-react-vite-boilerplate
```

The full plan you must execute is in:
```
docs/planning/machines/machine-b-gain-plan.md
```

**Read that file completely before writing a single line of code.**

---

## Hard Constraints — Read These First

These override everything else. Violating any of them means you have failed.

1. **DO NOT** redesign, rewrite, or replace any existing system.
   If you think a better architecture exists — ignore that thought. Execute the plan.

2. **DO NOT** touch these files or directories under any circumstances:
   - `audioanalysis/`
   - `audioanalysis/btc_runtime/`
   - `audioanalysis/chord_pipeline.py`
   - `src/` (React frontend)
   - `electron/`

3. **DO NOT** modify `scripts/bench/section_benchmark.py` except in Step 3
   where you add `pairwise_f1` and `mean_deviation_s` to `salami_benchmark.py`
   (a NEW file). The Harmonix benchmark script is read-only.

4. **DO NOT** auto-tune hyperparameters. Use the exact values specified in the plan.

5. **DO NOT** skip steps or reorder them. Steps must complete in sequence: 0, 1, 2, 3...

6. **DO NOT** use torch, tensorflow, or any neural network for the scorer in Step 9.
   Use `sklearn.ensemble.GradientBoostingClassifier` only.

7. After EVERY step that modifies a Python file, run:
   ```
   python -m py_compile scripts/analysis/section_detector.py scripts/bench/section_benchmark.py
   ```
   If this fails, fix the syntax error before continuing. Do not proceed with broken code.

8. After every step that changes detection logic, run the SALAMI benchmark
   and record the delta. If SALAMI F1@3.0s drops more than 0.005 below
   the baseline established in Step 2, revert the change and mark the step
   as `"status": "reverted"` in `results/gain-plan-log.json`.

---

## Context: What This Codebase Does

This is a music analysis application (Electron + React frontend, Python backend).

The Python pipeline:
1. Reads audio files (`.m4a`, `.mp3`, etc.)
2. Runs chord detection via `audioanalysis/chord_pipeline.py` (BTC-SL model) — **you do not touch this**
3. Runs section detection via `scripts/analysis/section_detector.py` — **this is your workspace**
4. Benchmarks results via `scripts/bench/section_benchmark.py` (Harmonix, read-only) and
   `scripts/bench/salami_benchmark.py` (SALAMI, you create this in Step 1)

The section detector (`section_detector.py`) scores candidate boundaries using a weighted
sum of 9 features per candidate, then applies NMS. The key function is:
```python
detect_sections(audio_path, chords=None, algorithm="heuristic", ...) -> dict
```

It returns:
```json
{
  "sections": [{"label": "...", "start_ms": 0, "duration_ms": 30000, "sectionType": "Detected"}],
  "candidates": [{"time_s": 12.3, "features": {...9 keys...}, "score": 0.71, "kept": true}],
  "meta": {"algorithm": "heuristic", "candidate_count": 25, "kept_count": 6}
}
```

The `candidates` list is critical — it's the training data source for the scorer in Steps 8–9.
Make sure it is always included in benchmark output.

---

## Dataset Locations

**McGill SALAMI** (primary eval dataset):
- Audio: `data/salami_audio/<salami_id>.m4a` — trimmed to SALAMI alignment window
- Metadata: `data/salami_audio/<salami_id>.meta.json`
- Annotations: `datasets/mcgill/mcgill_jcrd_salami_Billboard/<id_zero_padded_4dig>_<slug>.json`
  - Example: salami_id `3` → annotation file `0003_i_don_t_mind_james_brown.json`
  - Annotation format:
    ```json
    {
      "title": "I Don't Mind", "artist": "James Brown",
      "sections": [
        {"id": "A1", "sectionType": "Intro", "start_ms": 73, "duration_ms": 22273, "chords": [...]}
      ]
    }
    ```
  - Reference boundary times: `[s["start_ms"] / 1000.0 for s in d["sections"]]`
  - Reference intervals: `[[s["start_ms"]/1000, (s["start_ms"]+s["duration_ms"])/1000] for s in d["sections"]]`

**Harmonix** (legacy sanity-check dataset — do not optimise for it):
- Annotations: `data/raw/harmonix/<id>_sections.txt`
- Audio: `data/audio/`

---

## Key Existing Files (Read Before Editing)

Before modifying any file, read the relevant sections:

- `scripts/analysis/section_detector.py` — full detector, ~870 lines
  - `DEFAULT_WEIGHTS` dict is around line 43
  - `_build_ssm()` is around line 300 — this is what Step 4 modifies
  - `_repetition_break_at_candidates()` is right after `_build_ssm` — do NOT change it
  - `detect_sections()` starts around line 474 — Steps 5 and 10 add code here
  - The `scores = (...)` weighted sum is around line 640 — Step 5 adds one term
  - The `feats = {...}` candidate dict is around line 720 — Step 5 adds one key

- `scripts/bench/section_benchmark.py` — Harmonix benchmark, read-only after Step 1
  - The `_boundary_f1()` function (around line 155) must be COPIED verbatim into
    `salami_benchmark.py` — do not import it

- `scripts/tools/grid_small_params.py` — Step 6 adds a `--grid structural` mode

---

## How to Record Progress

Maintain `results/gain-plan-log.json` throughout. After each step, append to its
`"steps"` array. Example final shape:
```json
{
  "primary_dataset": "mcgill_salami_billboard",
  "primary_audio_dir": "data/salami_audio",
  "primary_ann_dir": "datasets/mcgill/mcgill_jcrd_salami_Billboard",
  "usable_pairs": 212,
  "harmonix_legacy_baseline": {"f1_05": 0.0498, "f1_3": 0.3073},
  "salami_baseline": {"f1_05": 0.0, "f1_3": 0.0, "songs": 0, "source": "TBD"},
  "steps": [
    {"step": 0, "name": "confirm_environment", "usable_pairs": 212, "status": "completed"},
    {"step": 1, "name": "salami_benchmark_adapter", "pilot_songs": 20, "status": "completed"},
    {"step": 2, "name": "salami_baseline", "salami_f1_05": 0.0, "salami_f1_3": 0.0, "status": "completed"},
    ...
  ]
}
```

After Step 2 completes, fill in `"salami_baseline"` at the top level. This becomes the
regression floor for all subsequent steps.

---

## Step Execution Protocol

For each step:

1. **Read** the step definition in `docs/planning/machines/machine-b-gain-plan.md`
2. **Read** the file(s) you are about to edit — understand the context around the change
3. **Make the change** exactly as specified
   - **Backup first:** before editing any file or directory, create a backup with the safe-edit tool:
     ```
     python scripts/tools/safe_edit.py --backup <file_or_dir> [...]
     ```
     The tool writes `results/edit_log.json` and places files under `backups/docs_backup/<timestamp>/`.
4. **Compile check**: `python -m py_compile <changed_files>`
5. **Run the benchmark** command(s) specified in the step
6. **Evaluate** against the pass condition
7. If pass: append `"status": "completed"` entry to log, move to next step
8. If fail: revert the change, append `"status": "reverted"` entry with reason, move to next step

**Never run a benchmark before completing the compile check.**
**Never skip the benchmark after a detection logic change.**

---

## Output Artifacts Expected

When you finish, these files must exist:

| File | From Step |
|------|-----------|
| `results/gain-plan-log.json` | Step 0 |
| `results/salami-pilot-20.json` | Step 1 |
| `results/salami-baseline-heuristic.json` | Step 2 |
| `results/harmonix-sanity-baseline.json` | Step 2 |
| `scripts/bench/salami_benchmark.py` | Step 1 |
| `scripts/train/extract_training_data.py` | Step 8 |
| `scripts/train/train_scorer.py` | Step 9 |
| `data/training/salami_candidates.csv` | Step 8 |
| `data/training/scorer_gbt.pkl` | Step 9 |
| `results/salami-step10-scored.json` | Step 10 |

---

## Environment

- OS: Windows, Python 3.10
- Working directory: `C:\Users\CraftAuto-Sales\component test\electron-react-vite-boilerplate`
- Python environment: use the system Python (not `.venv`) unless a command fails,
  then retry with `.venv\Scripts\python.exe`
- All required libraries are installed: `librosa 0.11`, `msaf 0.1.80`, `scikit-learn 1.7.1`,
  `mir_eval 0.8.2`, `madmom 0.16.1`, `numpy`, `scipy`, `joblib`
- ffmpeg is available at `tools/ffmpeg/ffmpeg.exe`

---

## Completion Check

When all 10 steps are done (or reverted), run this final verification:

```
python -m py_compile scripts/analysis/section_detector.py scripts/bench/section_benchmark.py scripts/bench/salami_benchmark.py scripts/train/extract_training_data.py scripts/train/train_scorer.py
```

Then print a summary table:

```
Step | Name                        | Status    | SALAMI F1@3.0s delta
-----|-----------------------------|-----------|-----------------------
0    | confirm_environment         | completed | —
1    | salami_benchmark_adapter    | completed | —
2    | salami_baseline             | completed | 0.000 (baseline)
3    | pairwise_metrics_salami     | completed | 0.000
4    | recurrence_matrix_ssm       | completed | +0.XXX
5    | msaf_vote_feature           | completed | +0.XXX
6    | structural_weight_grid      | completed | —
7    | apply_best_weights          | completed | +0.XXX
8    | extract_training_data       | completed | —
9    | train_scorer                | completed | val_f1=0.XX
10   | scored_algorithm_mode       | completed | +0.XXX vs baseline
```

If any step is `reverted`, note the reason in the table.

That summary table is your final output.
