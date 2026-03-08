# Live Comms Runbook (Explicit Setup + Run)

This runbook is the single source of truth for live coordination setup on all machines.

## 0) One-time prerequisites on each machine

```powershell
# from any folder
git --version
python --version
```

If either command fails, install Git and Python 3.10+ first.

## 1) Sync to coordination branch

```powershell
git fetch origin
git checkout coordination/wave-1
git pull --ff-only origin coordination/wave-1
```

## 2) Start the live watcher (leave running)

Machine A:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-a -IntervalSec 20
```

Machine B:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-b -IntervalSec 20
```

Machine C:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-c -IntervalSec 20
```

Optional LAN mirror for same-Wi-Fi SMB share:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-c -IntervalSec 20 -NetworkMirrorPath "\\COORD-PC\lalo-comms\machine-c.md"
```

## 3) Create your worker branch

Machine A:

```powershell
git checkout -b runtime/btc-reference-pin
git push -u origin HEAD
```

Machine B:

```powershell
git checkout -b sections/heuristic-weight-sweep
git push -u origin HEAD
```

Machine C:

```powershell
git checkout -b diagnostics/youtube-failure-catalog
git push -u origin HEAD
```

## 4) Execute lane-specific task

### Machine A (runtime stability)

```powershell
mkdir -Force results
python tmp/validate_pipeline.py *> results/validate-machine-a.log
```

Then append status to:
- `docs/planning/machines/comms/live/machine-a.md`
- `docs/planning/machines/comms/machine-a.md` (main mirror)

### Machine B (section benchmarking)

```powershell
mkdir -Force results
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-b.json *> results/bench-machine-b.log
```

Then append status to:
- `docs/planning/machines/comms/live/machine-b.md`
- `docs/planning/machines/comms/machine-b.md` (main mirror)

### Machine C (single-song diagnostics)

```powershell
mkdir -Force results
python tmp/validate_pipeline.py *> results/validate-machine-c.log
python scripts/bench/section_benchmark.py --dev-only --algorithm heuristic --out results/sections-machine-c.json *> results/bench-machine-c.log
```

Then append status to:
- `docs/planning/machines/comms/live/machine-c.md`
- `docs/planning/machines/comms/machine-c.md` (main mirror)

## 5) Commit and push artifacts

Machine A:

```powershell
git add results/validate-machine-a.log docs/planning/machines/comms/live/machine-a.md docs/planning/machines/comms/machine-a.md
git commit -m "machine-a: runtime validation update"
git push
```

Machine B:

```powershell
git add results/sections-machine-b.json results/bench-machine-b.log docs/planning/machines/comms/live/machine-b.md docs/planning/machines/comms/machine-b.md
git commit -m "machine-b: heuristic benchmark update"
git push
```

Machine C:

```powershell
git add results/sections-machine-c.json results/bench-machine-c.log results/validate-machine-c.log docs/planning/machines/comms/live/machine-c.md docs/planning/machines/comms/machine-c.md
git commit -m "machine-c: diagnostics and benchmark update"
git push
```

## 6) Required reply format in live channel

```md
status: done
branch: <worker branch>
backend: reference|owned
algorithm: heuristic|other
artifacts:
- <artifact path 1>
- <artifact path 2>
summary: <2-5 lines>
```
