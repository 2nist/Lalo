# Live Comms Mirror

This folder is a fast-update mirror for same-network coordination.

Workflow:
1. Coordinator writes to machine-specific file (`machine-a.md`, `machine-b.md`, `machine-c.md`).
2. Worker machine runs the watcher script to poll for new `status: open` messages.
3. Worker appends completion notes and sets `status: done` when finished.
4. Final state is still mirrored back to the main comms files under docs/planning/machines/comms/.

Do not store secrets in these files.
