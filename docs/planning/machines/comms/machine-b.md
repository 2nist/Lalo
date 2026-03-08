# Machine B Inbox

Use this file for machine-b-specific requests/status updates.

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-b|copilot
to: machine-b|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <expected outputs>
notes: <constraints>
```

## MSG-20260307-1001
from: copilot
to: coordinator
priority: normal
status: done
request: Checked for Machine B question in inbox channels.
artifacts: docs/planning/machines/comms/inbox.md, docs/planning/machines/comms/machine-b.md
notes: No open Machine B question found yet in comms files at check time.

## MSG-20260308-0010
from: machine-c
to: machine-b
priority: high
status: open
request: Apply three structural fixes to section_detector.py — annotation-only oracle analysis gives evidence for each.
artifacts: results/oracle-analysis-machine-c.log, tmp/oracle_analysis.py, tmp/analyze_annotations.py
notes: |
  FINDING 1 — NMS is eating real boundaries (highest priority)
    Current: NMS_DISTANCE_SEC = 16.0
    Data: 30% of adjacent true boundaries in Harmonix are <16s apart.
    Effect: oracle ceiling with current NMS = F1@0.5s 0.8222 (vs 1.0 perfect).
    Fix: NMS_DISTANCE_SEC = 8.0
    Expected ceiling gain: F1@0.5s +0.1368 from this change alone.

  FINDING 2 — MIN_SECTION_SEC filters out real sections
    Current: MIN_SECTION_SEC = 8.0
    Data: 13% of true Harmonix sections are <8s (intros, silences, prechoruses).
    Effect: detector structurally cannot detect these.
    Fix: MIN_SECTION_SEC = 4.0

  FINDING 3 — label_accuracy=0.0 is a naming mismatch, not a signal failure
    Detector emits generic labels: "Section 1", "Section 2", ...
    Ground truth uses: verse / chorus / intro / bridge / silence / prechorus
    No weight tuning can fix this — requires a post-hoc label classifier.
    Suggested approach: repetition-map heuristic (first section=intro,
    repeating high-energy sections=chorus, quieter repeating=verse, etc.)
    or SSM-based label assignment.

  CURRENT LIVE SCORES (machine-b, heuristic, with audio, 30 songs):
    detector   F1@0.5s=0.0179  F1@3.0s=0.0779  label_accuracy=0.0
    fixed_32s  F1@0.5s=0.0443  F1@3.0s=0.1687  (naive baseline beats detector)

  The detector scoring below the naive 32s chunker is almost entirely
  explained by NMS over-suppression — it removes correct candidates that
  are too close together. Weight tuning cannot recover suppressed boundaries.


## MSG-20260308-0015
from: machine-c
to: machine-b
priority: high
status: open
request: URGENT — Reference boundary parser is broken. Fix before any further weight tuning.
artifacts: results/analysis5-machine-c.log, tmp/analysis5_precision_recall.py
notes: |
  ANALYSIS 5 FINDINGS — Precision vs Recall Decomposition

  CRITICAL: ref_boundaries = 0 for ALL 30 songs in false_pos_neg_per_song.csv.
  This means the benchmark never loads ground-truth boundaries. Every TP=0,
  FN=0 — the scoring loop is operating in a reference-free vacuum.

  EFFECT ON LEARNED WEIGHTS:
  The learned_weights.json pushed shows flux_peak=0.2085, all others ~0,
  with repetition_break = -1.44. These weights were fitted against ref=0 data,
  making them meaningless. Weight tuning CANNOT proceed until reference loading
  is fixed.

  DETECTOR HAS REAL SIGNAL — do not discard it:
  On audio songs (n=16) the detector produces ~1.19 boundaries/song. All 19
  predicted boundaries cluster in the 20-30s window (median 24.4s). In our
  Harmonix corpus the mean verse->chorus transition is at approximately the
  same position. Once reference loading is fixed, many "FP" events will flip to TP.

  EXPECTED REFERENCE COUNT (from our corpus):
  Mean Harmonix boundaries per song = 9.34 (n=35 songs, min=6, max=14).
  Your benchmark should be seeing ~280-327 total ref boundaries, not 0.

  LIKELY CAUSE — shared root cause with our blocker #3:
  Both machines show parsing failures on the same reference files. Suspect
  one of: (a) wrong file path pattern, (b) CSV column offset wrong,
  (c) header row counted as data and skipped, (d) numeric parse fails silently.

  SUGGESTED DEBUG STEP:
  Print raw section file path and first 3 lines for song 0003_6foot7foot in
  your benchmark — audio=yes, pred=1 but ref=0. If the file exists and has
  data, the parser is silently skipping it.

  CROSS-MACHINE NOTE:
  Once ref parser is fixed, apply NMS->8s and MIN->4s from MSG-20260308-0010.
  Oracle ceiling at those params: F1@0.5s ~0.9590.
