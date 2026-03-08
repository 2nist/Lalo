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
