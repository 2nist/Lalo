# Inbox

Post new requests here. Tell Copilot "check inbox" to process.

## MSG-20260307-0001
from: coordinator
to: copilot
priority: normal
status: done
request: Acknowledge inbox protocol and confirm readiness.
artifacts: docs/planning/machines/comms/outbox.md
notes: This is a bootstrap message.

## MSG-20260308-0602
from: coordinator
to: machine-b
priority: high
status: open
request: Visibility retry for Wave 4b. If you cannot see machine-b live messages, use this as source of truth and execute candidate-generator recall pass (`live MSG-20260308-0601`).
artifacts: docs/planning/machines/comms/machine-b.md, results/sections-machine-b-wave4b.json, results/machine-b-wave4b-note.md
notes: Acknowledge in `docs/planning/machines/comms/machine-b.md` with status `in-progress` and ETA.
