---
agent: ask
description: "Use when starting a scoped work item in LALO and you need the agent to declare lane, validation, boundaries, and artifacts before changing code."
---

You are starting work in the LALO repo.

Before making changes:

1. Classify the task into exactly one lane:
   - runtime-stability
   - section-benchmarking
   - single-song-diagnostics
   - docs-and-tooling
2. State the files you expect to modify.
3. State the validation command you will use.
4. State which files or subsystems must not change.
5. State which artifact paths should be produced or updated.

Then proceed with the work.

Constraints:

- Do not mix chord runtime migration and section detector tuning.
- Do not use a single YouTube analysis as proof of improvement.
- If the task is ambiguous across lanes, stop and split it into separate work items.

Output format:

```text
Lane:
Files to change:
Validation:
Do not change:
Artifacts:
```
