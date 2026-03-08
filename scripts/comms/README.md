# Comms Watcher

Use the watcher to poll machine-specific live channel files and show open messages.

## Quick Start

```powershell
# One-time check for machine C
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-c -Once

# Continuous poll every 20s for machine B
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-b -IntervalSec 20
```

## Optional Network Mirror

If you host a shared SMB file for fast LAN updates, point the watcher at it:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-c -NetworkMirrorPath "\\COORD-PC\lalo-comms\machine-c.md"
```

When `-NetworkMirrorPath` is set, the watcher copies that file into the repo live channel before each poll.

## Machine C bootstrap helper

Use this helper to diagnose missing paths and run fallback commands for Machine C.

```powershell
# checks only (prints exact commands)
powershell -ExecutionPolicy Bypass -File scripts/comms/machine-c-bootstrap.ps1

# checks + fetch harmonix if missing + run commands
powershell -ExecutionPolicy Bypass -File scripts/comms/machine-c-bootstrap.ps1 -FetchHarmonixIfMissing -Run

# checks + fetch harmonix + fetch audio (up to 30 songs) + run commands
powershell -ExecutionPolicy Bypass -File scripts/comms/machine-c-bootstrap.ps1 -FetchHarmonixIfMissing -FetchAudioIfMissing -AudioMax 30 -Run
```
