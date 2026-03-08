# Machine Comms Protocol

This folder is a lightweight message bus for humans and agents using Markdown files in git.

## How to use

1. You (human coordinator) write tasks in `inbox.md`.
2. You tell me: "check inbox".
3. I read `inbox.md`, execute actionable items, and write updates to `outbox.md`.
4. Machines can also post status in their own files (`machine-a.md`, `machine-b.md`, `machine-c.md`).

## Message format (recommended)

Use one block per request:

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator
to: machine-a|machine-b|machine-c|copilot
priority: high|normal|low
status: open
request: <what to do>
artifacts: <paths expected>
notes: <constraints>
```

When completed, I will update status and add a response entry in `outbox.md`.

## Conventions

- Keep one source of truth for instructions per machine.
- Include exact command lines and artifact paths when possible.
- Do not store secrets in these files.

## Live Polling Option (same Wi-Fi)

Use live channels in `docs/planning/machines/comms/live/` for faster updates and run the watcher script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-c -IntervalSec 20
```

Optional LAN mirror path (SMB share):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/comms/watch-machine.ps1 -MachineId machine-c -NetworkMirrorPath "\\COORD-PC\lalo-comms\machine-c.md"
```
