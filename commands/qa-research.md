---
description: "Run only the research phase. Reads the Jira ticket and codebase, returns a Test Surface Map without writing tests. Useful for reviewing coverage gaps before committing to test writing. Usage: /qa-research <TICKET-KEY or feature description>"
---

# /qa-research - Research-Only Phase

Apply the `quality-engineer` skill, then invoke the **qa-researcher** sub-agent.

Arguments: $ARGUMENTS (ticket key or feature description)

Return the Test Surface Map and stop. Do not invoke qa-writer or qa-validator.

The map is written to `.claude/qa/<TICKET-KEY>-surface-map.md` so a subsequent `/qa` call can pick up from qa-writer.
