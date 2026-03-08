# Machine B Wave 14 Note

benchmark_date: 2026-03-08T22:03:19.346174Z

## wave14a

prob_threshold: 0.5

TP: 3

FP: 28

FN: 125

Precision: 0.0968

Recall: 0.0234

Avg predictions per song: 1.938

log: results/wave14_wave14a.log


## wave14b

prob_threshold: 0.25

TP: 3

FP: 29

FN: 125

Precision: 0.0938

Recall: 0.0234

Avg predictions per song: 2.0

log: results/wave14_wave14b.log


## wave14c

prob_threshold: 0.15

TP: 3

FP: 29

FN: 125

Precision: 0.0938

Recall: 0.0234

Avg predictions per song: 2.0

log: results/wave14_wave14c.log


## Validations

- wave14a_parity_match: False

- monotonic_fp: True

- monotonic_pred: True


## Active weights

{
  "flux_peak": 0.1081,
  "chord_novelty": 0.0,
  "cadence_score": 0.0,
  "repetition_break": 0.2528,
  "duration_prior": 0.0,
  "chroma_change": 0.121,
  "spec_contrast": 0.1465,
  "onset_density": 0.1488,
  "rms_energy": 0.2227
}