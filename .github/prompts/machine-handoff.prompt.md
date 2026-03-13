---
agent: ask
description: "Use when handing LALO work from one machine or agent to another and you need a precise, low-regression handoff packet."
---

Prepare a handoff for another machine or agent working in the LALO repo.

The handoff must include:

1. active lane
2. branch name
3. changed files
4. commands already run
5. artifacts produced
6. unresolved risks
7. exact next step
8. files or subsystems the next agent must not touch

Rules:

- Do not write vague summaries.
- Use exact commands and exact paths.
- If results depend on local models, checkpoints, or optional Windows dependencies, say so.
- If benchmark evidence is missing, state that the work is not yet promotable.

Output format:

```text
Lane:
Branch:
Changed files:
Commands run:
Artifacts:
Risks:
Next step:
Do not touch:
```
