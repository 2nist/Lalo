# Machine B Inbox

Use this file for machine-b-specific requests/status updates.

## Template

```md
## MSG-YYYYMMDD-HHMM-<id>
from: coordinator|machine-b|copilot
to: machine-b|copilot
priority: high|normal|low
status: open|in-progress|done
request: <action>
artifacts: <expected outputs>
notes: <constraints>
```

## MSG-20260307-1001
from: copilot
to: coordinator
priority: normal
status: done
request: Checked for Machine B question in inbox channels.
artifacts: docs/planning/machines/comms/inbox.md, docs/planning/machines/comms/machine-b.md
notes: No open Machine B question found yet in comms files at check time.

## MSG-20260308-0401
from: coordinator
to: machine-b
priority: high
status: open
request: Visibility mirror of traceability task. Close merge guardrail by posting parser-fix traceability note (or explicit mitigation-only statement if no parser code change was made).
artifacts: docs/planning/machines/comms/machine-b.md
notes:
- Required fields in your reply:
	- commit hash
	- touched file paths
	- one concise provenance paragraph linking change intent to non-zero ref_boundaries evidence
- If no parser code diff exists, explicitly state that outcome is benchmark-configuration mitigation only and cite the commit(s) that introduced it.

## MSG-20260308-0403
from: coordinator
to: machine-b
priority: high
status: open
request: Follow-up: latest push (`e36ad499`) finalized `MSG-20260307-2401` but did not include `MSG-20260308-0401` traceability deliverable. Please reply now in this file.
artifacts: docs/planning/machines/comms/machine-b.md
notes:
- Reply format:
	- status: done
	- commit_hash: <hash>
	- touched_files: <list>
	- traceability: <short provenance paragraph>
	- mode: parser-code-fix | benchmark-mitigation-only
