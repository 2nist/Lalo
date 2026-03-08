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
