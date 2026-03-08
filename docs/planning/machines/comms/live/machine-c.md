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

## MSG-20260307-2401
from: coordinator
to: machine-c
priority: high
status: done
request: Mirror diagnostics completion from your branch into comms and attach concise blocker-resolution summary.
artifacts: docs/planning/machines/comms/machine-c.md, results/sections-machine-c.json, results/bench-machine-c.log
notes: Branch `origin/machine-c` shows `machine-c: diagnostics lane complete`; this step is to publish final comms status and any skipped validation rationale.

## MSG-20260308-0101
from: coordinator
to: machine-c
priority: normal
status: done
request: Run Wave 2 diagnostics-only lane (non-audio-dependent). Summarize top 5 failure patterns from `results/bench-machine-c.log` and map each to a testable benchmark hypothesis for Machine B.
artifacts: results/machine-c-failure-taxonomy.md, docs/planning/machines/comms/machine-c.md
notes: No model/backend/default changes in this lane. This is analysis + hypothesis packaging only.

## MSG-20260308-0201
from: coordinator
to: machine-c
priority: high
status: done
request: Finalize Wave 2 diagnostics handoff by syncing your completion commit into coordination-visible comms and highlighting the top 2 hypotheses Machine B should test first.
artifacts: docs/planning/machines/comms/machine-c.md, docs/planning/machines/comms/live/machine-c.md, results/machine-c-failure-taxonomy.md
notes: Your branch shows completion (`origin/machine-c` latest commit). This step is a sync + prioritization handoff.

## MSG-20260308-0301
from: coordinator
to: machine-c
priority: normal
status: done
request: Stay in support mode. Validate Machine B parser-fix branch once available and confirm whether H2/H3 gains persist after H4 is fixed.
artifacts: docs/planning/machines/comms/machine-c.md
notes: No new modeling work yet; this is verification support for B's parser-first lane.

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
status: done
request: Wave 4b verification pass. Validate Machine B candidate-generator recall output and confirm recall gain vs baseline without destabilizing precision.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL plus one highest-priority risk.

status: done
summary: Completed by Machine C (`15a0eb04`). Verification: precision stable and model CV improved, but recall gain is FAIL (unchanged); top risk is feature-weight alignment bug.

## MSG-20260308-0701
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 5 verification pass. Validate Machine B alignment-fix output and confirm whether non-zero informative weights are actually used and whether recall changes vs Wave 4b baseline.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL and top remaining blocker.

status: done
summary: Completed by Machine C (`6e509cc2`). Result: FAIL for recall gain; top blocker remains NMS 16s bottleneck and alignment fix still unverified.

## MSG-20260308-0801
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 6 verification pass. Validate Machine B NMS-first run (16 -> 8) and report whether recall improves without unacceptable precision collapse.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Include PASS/FAIL, metric deltas, and single top remaining blocker.

status: done
summary: Completed by Machine C (`acf91504`). Conditional PASS: NMS 16 -> 8 confirmed effective with recall +100% and F1@0.5s +51%, precision stable; top remaining blocker is H3 (`MIN_SECTION_SEC=8`).

## MSG-20260308-0803
from: coordinator
to: machine-c
priority: high
status: done
request: Re-run Wave 6 verification against Machine B commit `e95937ef` (contains `results/sections-machine-b-wave6.json`) and post updated PASS/FAIL with deltas.
artifacts: results/verify-machine-b-w6.log, docs/planning/machines/comms/machine-c.md
notes: Prior pending output referenced missing artifact; this retry should use the now-available Wave 6 artifact.

status: done
summary: Retry completed and posted as `MSG-20260308-0804` on machine-c branch.

## MSG-20260308-0901
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 7 verification pass. Validate Machine B H3 run (`MIN_SECTION_SEC` 8 -> 4) plus any alignment-fix updates and report combined impact vs Wave 6.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Include PASS/FAIL, metric deltas, and top remaining blocker.

status: done
summary: Completed by Machine C in `origin/machine-c` commit `bb3649a3` (`MSG-20260308-0902`). Verdict: partial pass. H3 was applied with marginal effect, F1@0.5s unchanged at 0.0270, F1@3.0s improved to 0.1267, and top blocker remains prediction sparsity before NMS/MIN. Weight-alignment CLI fix is code-complete but not exercised in the Wave 7 run.

## MSG-20260308-1001
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 8 verification pass. Validate Machine B full-feature weight rerun and confirm whether pred density and F1@0.5s improve over Wave 7 without unacceptable precision collapse.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL with deltas for F1@0.5s, F1@3.0s, pred/song, precision, recall, plus one top remaining blocker.

status: done
summary: Completed by Machine C in `origin/machine-c` commit `69ddce93` (`MSG-20260308-1003`). Verdict: FAIL. Wave 8 was an ack rerun with unchanged 5-key weights and unchanged metrics vs Wave 7.

## MSG-20260308-1101
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 9 verification pass. Validate Machine B retrain-first rerun and confirm whether full-feature mapping is exercised and whether pred density/F1@0.5s improve over Wave 8 without unacceptable precision collapse.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Include PASS/FAIL with deltas for F1@0.5s, F1@3.0s, pred/song, precision, recall, and confirm `weights` key count >= 9.

status: done
summary: Completed by Machine C in `origin/machine-c` commit `40c1288a` (`MSG-20260308-1103`, final). Verdict: PASS. Verified Wave 9 artifact and reported F1@0.5s 0.0270 -> 0.0383 with 9-key mapping active.

## MSG-20260308-1201
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 10 verification pass. Validate Machine B density-focused tuning run and confirm whether pred/song improves over 2.0 while precision remains >= 0.04 and F1@0.5s does not regress below 0.0383.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL with deltas for F1@0.5s, F1@3.0s, pred/song, precision, recall, TP/FP/FN, plus top remaining blocker.

status: done
summary: Completed by Machine C in `origin/machine-c` commit `51918398` (`MSG-20260308-1202`). Verdict: FAIL. Density sweep increased pred/song but regressed TP/F1 and precision below guardrails.

## MSG-20260308-1301
from: coordinator
to: machine-c
priority: normal
status: done
request: Wave 11 verification pass. Validate Machine B threshold-first corrective run and confirm whether precision/F1 recover while maintaining pred/song > 2.0.
artifacts: docs/planning/machines/comms/machine-c.md
notes: Analysis-only validation. Report PASS/FAIL with deltas for F1@0.5s, F1@3.0s, pred/song, precision, recall, TP/FP/FN and confirm full benchmark artifact presence.

status: done
summary: Completed by Machine C in `origin/machine-c` commit `9e9d1b2c` (`MSG-20260308-1303`). Verdict: FAIL. Wave 11 regressed from Wave 9 on TP (3 -> 1), precision (0.0938 -> 0.0222), and F1@0.5s (0.0383 -> 0.0116).

## MSG-20260308-1401
from: coordinator
to: machine-c
priority: normal
status: open
request: Wave 12 verification pass. Validate Machine B parity-locked A/B ablation and confirm whether threshold-only change helps when geometry is fixed at Wave 9 values.
artifacts: docs/planning/machines/comms/machine-c.md, results/verify-machine-b-w12.log
notes: Analysis-only verification. Confirm config lock (nms_gap=8.0, min_section=4.0, beat_snap=2.0, same weights) and report PASS/FAIL deltas for Run A (`prob=0.50`) and Run B (`prob=0.25`).
