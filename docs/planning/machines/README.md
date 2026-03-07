# Machine Kits

This directory holds machine-specific coordination material for parallel work.

Use these files when three machines are active against one integration branch.

## Branch Policy

Do not put all three machines directly on the same branch head.

Use:

1. one integration branch
2. one worker branch per machine

Recommended layout:

- integration branch: `coordination/<wave-name>`
- machine A branch: `runtime/<topic>`
- machine B branch: `sections/<topic>`
- machine C branch: `diagnostics/<topic>`

Each machine should update only its own lane unless explicitly reassigned.

## Machine Roles

- `machine-a-runtime.md`: BTC runtime consistency and parity
- `machine-b-sections.md`: section benchmark and tuning work
- `machine-c-diagnostics.md`: single-song and YouTube diagnostics

## Shared Rule

Any proposed change becomes promotable only after:

1. machine owner validates its lane criteria
2. results are handed off with exact commands and artifacts
3. integration branch review confirms no cross-lane regression
