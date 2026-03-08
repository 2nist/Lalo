# Machine B Wave 14 Note

benchmark_date: 2026-03-08T16:13:01.444233Z

## wave14a

prob_threshold: 0.5

TP: 2

FP: 34

FN: 126

Precision: 0.0556

Recall: 0.0156

Avg predictions per song: 2.25

log: results/wave14_wave14a.log


## wave14b

prob_threshold: 0.25

TP: 2

FP: 33

FN: 126

Precision: 0.0571

Recall: 0.0156

Avg predictions per song: 2.188

log: results/wave14_wave14b.log


## wave14c

prob_threshold: 0.15

TP: 2

FP: 33

FN: 126

Precision: 0.0571

Recall: 0.0156

Avg predictions per song: 2.188

log: results/wave14_wave14c.log


## Validations

- wave14a_parity_match: False

- monotonic_fp: False

- monotonic_pred: False


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