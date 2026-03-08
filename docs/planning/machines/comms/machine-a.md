# Machine A Inbox

Use this file for machine-a-specific requests/status updates.

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-a|copilot
to: machine-a|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <expected outputs>
notes: <constraints>
```

## MSG-20260307-2201
from: machine-a
to: coordinator
priority: high
status: done
request: Execute Machine A lane using explicit runbook and report validation status.
artifacts: results/validate-machine-a.log
notes: Validation completed successfully. Direct segment match 40/40 (100.0%). mir_eval metrics all 1.0000.
