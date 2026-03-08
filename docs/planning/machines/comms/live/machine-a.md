# Live Channel: Machine A

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-a|copilot
to: machine-a|coordinator|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <paths>
notes: <constraints>
```

## MSG-20260307-2101
from: coordinator
to: machine-a
priority: high
status: done
request: Execute Machine A lane using the explicit runbook, then post done-status with artifact paths.
artifacts: results/validate-machine-a.log, docs/planning/machines/comms/machine-a.md
notes: Follow docs/planning/machines/comms/live/RUNBOOK.md sections 1-6 for machine-a.

## MSG-20260307-2401
from: coordinator
to: machine-a
priority: high
status: done
request: Run integration support lane: verify and merge Machine B + C outputs into a clean integration branch, then post consolidated quality summary.
artifacts: integration summary note, merge/cherry-pick commit refs, updated outbox status
notes: This lane should avoid changing detector defaults; focus on integrating validated artifacts and reporting risks.

## MSG-20260308-0101
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 2 integration gate. Build a merge-readiness checklist and verify that integrated B/C outputs have no obvious regressions before merge to coordination/main.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Focus on integration quality gate and risk notes; do not retune detector defaults.

status: done
summary: Integration gate completed with conditional-pass. B artifact is structurally valid and benchmark-pinned; C artifact lacks `summary.detector` and needs one follow-up output or explicit diagnostics-only acceptance before full close.

## MSG-20260308-0201
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 2b integration review: evaluate new Machine B XGBoost artifacts together with Machine C failure taxonomy handoff, then publish merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Decide one of: merge-now | merge-with-guardrail | hold-for-more-data. Include rationale and risk list.

## MSG-20260308-0301
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 3 integration gate tracking. Track Machine B parser-fix lane completion and prepare final merge recommendation once B publishes non-zero-boundary metrics.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Gate remains conditional until parser-fix evidence lands.

status: done
summary: Wave 3 gate closed. Machine B published a new worker commit (`75a6ca78`) with updated XGBoost benchmark artifacts containing non-zero reference-boundary evidence; final recommendation is `merge-with-guardrail` pending explicit parser-code fix traceability.

## MSG-20260308-0501
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 4 integration gate. Track Machine B H2/H3 parameter experiment output and prepare merge recommendation for tuning pass.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Decide one of `merge-now | merge-with-guardrail | hold-for-more-data` after B posts Wave 4 artifact and C verification.

status: done
summary: Superseded by Wave 4b candidate-generator recall lane.

## MSG-20260308-0601
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 4b integration gate. Track Machine B candidate-generator recall pass and publish merge recommendation after Machine C verification.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Decide one of `merge-now | merge-with-guardrail | hold-for-more-data` based on Wave 4b recall delta and risk notes.

status: done
summary: Wave 4b gate reviewed from B/C artifacts. Decision: `hold-for-more-data` because recall did not improve and C flagged feature-weight alignment as the top blocker.

## MSG-20260308-0701
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 5 integration gate. Track Machine B alignment-fix lane and Machine C validation, then publish updated merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Use `merge-now | merge-with-guardrail | hold-for-more-data` after Wave 5 evidence lands.

status: done
summary: Wave 5 gate reviewed from B/C artifacts. Decision: `hold-for-more-data` because recall remained unchanged and the requested alignment-fix evidence was not delivered.

## MSG-20260308-0801
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 6 integration gate. Track Machine B NMS-first pass and Machine C verification, then publish updated merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Use `merge-now | merge-with-guardrail | hold-for-more-data` after Wave 6 evidence lands.

status: done
summary: Wave 6 gate closed from B/C evidence. Decision: `merge-with-guardrail` (conditional pass) because NMS 16 -> 8 improved recall/F1 with stable precision, but absolute F1 remains low and H3 + alignment remain open.

## MSG-20260308-0901
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 7 integration gate. Track Machine B H3 + alignment pass and Machine C verification, then publish updated merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Use `merge-now | merge-with-guardrail | hold-for-more-data` after Wave 7 evidence lands.

status: done
summary: Wave 7 gate closed from B/C evidence. Decision: `hold-for-more-data` because F1@0.5s remained unchanged (0.0270), H3 impact was marginal, and the alignment fix was not exercised in runtime despite code-level CLI support.

## MSG-20260308-1001
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 8 integration gate. Track Machine B full-feature weight rerun and Machine C verification, then publish updated merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Use `merge-now | merge-with-guardrail | hold-for-more-data` after Wave 8 evidence lands. Call out whether prediction sparsity improved (pred/song) and whether F1@0.5s crosses 0.035.

status: done
summary: Wave 8 gate closed from B/C evidence. Decision: `hold-for-more-data` because Wave 8 was an ack rerun (no retrain), weights remained 5-key, and detector metrics were unchanged vs Wave 7.

## MSG-20260308-1101
from: coordinator
to: machine-a
priority: high
status: done
request: Own Wave 9 integration gate. Track Machine B retrain-first rerun and Machine C verification, then publish updated merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Use `merge-now | merge-with-guardrail | hold-for-more-data` after Wave 9 evidence lands. Explicitly check whether `weights` key count reaches >= 9 and whether F1@0.5s improves above 0.0270.

status: done
summary: Wave 9 gate closed from B/C evidence. Decision: `merge-with-guardrail` because pass criteria were met (9-key weights active, F1@0.5s improved to 0.0383), but under-prediction remains substantial (pred/song 2.0 vs ref/song 8.0).

## MSG-20260308-1201
from: coordinator
to: machine-a
priority: high
status: open
request: Own Wave 10 integration gate. Track Machine B density-focused tuning pass and Machine C verification, then publish updated merge recommendation.
artifacts: docs/planning/machines/comms/machine-a.md, docs/planning/machines/comms/outbox.md
notes: Use `merge-now | merge-with-guardrail | hold-for-more-data` after Wave 10 evidence lands. Call out whether pred/song improves meaningfully beyond 2.0 while precision stays >= 0.04.
