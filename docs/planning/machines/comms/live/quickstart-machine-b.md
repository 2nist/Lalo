# Quickstart: Machine B

Run these commands from repo root:

```powershell
git fetch origin
git checkout coordination/wave-1
git pull --ff-only origin coordination/wave-1
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-b -IntervalSec 20
```
