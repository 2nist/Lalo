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

## MSG-20260307-2201
from: machine-c
to: coordinator
priority: high
status: open
request: Need final payload/data/script confirmation before running diagnostics.
artifacts: none yet
notes:
- Where should Harmonix annotations come from (`data/raw/harmonix` vs `scripts/datasets/fetch_harmonix.py`)?
- Payload references `third_party/BTC-ISMIR19/test/example.mp3` but Machine C checkout reported no `third_party/` tree.
- `tmp/validate_pipeline.py` reported missing on Machine C checkout.
- Should Machine C wait for these prerequisites before committing artifacts?

## MSG-20260307-2202
from: coordinator
to: machine-c
priority: high
status: open
request: Proceed with diagnostics using these resolved instructions.
artifacts: results/sections-machine-c.json, results/bench-machine-c.log, results/validate-machine-c.log
notes:
- Use existing local data first. In coordinator checkout, both `data/raw/harmonix/` and `tmp/validate_pipeline.py` are present.
- If your machine is missing either path, sync first:
	1) `git fetch origin`
	2) `git checkout coordination/wave-1`
	3) `git pull --ff-only origin coordination/wave-1`
- If `data/raw/harmonix` is still missing after pull, run `python scripts/datasets/fetch_harmonix.py`.
- If `third_party/BTC-ISMIR19/test/example.mp3` is missing after pull, continue benchmark with Harmonix audio paths; do not block on this sample file.
- If `tmp/validate_pipeline.py` is still missing after pull, skip validation step and continue with benchmark command. Report skip reason in summary.
- Do not wait further: run the benchmark step and publish available artifacts now.
