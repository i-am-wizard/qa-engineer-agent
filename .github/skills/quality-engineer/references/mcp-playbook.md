# MCP Playbook

How to use each MCP tool effectively for QA work. The principle from SKILL.md applies: presence of a tool is not a reason to use it - pick the tool that gives the fastest, most reliable signal at the lowest layer.

## Playwright MCP

Use for **observable user-facing behaviour** across flows that genuinely require a rendered browser: multi-step user journeys, client-side state transitions, visual regressions.

Do not use for things verifiable at the service or data layer. Browser tests are slow, brittle, and expensive to maintain - every browser test should be a deliberate choice, not a default.

- Prefer a running local or staging instance over mocked responses; a test against a mock browser is not a browser test
- Assert on outcome state, not implementation details: the right URL, the right element visible, the correct network request fired - not internal component names or CSS classes
- Capture a screenshot on any assertion failure so humans can review actual vs expected state
- For selector stability: prefer accessible roles and labels (`getByRole`, `getByLabel`) over CSS selectors or XPath. Selectors tied to styling break silently
- After a Playwright run, report: scenarios run, pass/fail per scenario, any flaky retries, screenshots attached to failures

## Sentry MCP (or equivalent error tracking)

- **Before writing new tests**, pull active issues related to the feature under test. Known production errors are higher-priority test cases than hypothetical edge cases
- Use stack traces and breadcrumbs from Sentry issues to inform the exact scenario to reproduce - not a generalised approximation
- After a fix ships, verify the issue volume in Sentry returns to baseline before closing the quality gate. A passing test suite with a still-firing alert is not done
- Report: issue count before / after, any new issues opened during the change window

## Observability MCP (Datadog, Grafana, New Relic, etc.)

- Query error rates, latency percentiles, and log volumes for the service **before and after** a change to establish a baseline and confirm improvement
- Use trace data to identify which span in a distributed flow is responsible for a latency regression - do not guess from code alone
- Verify that the metrics and log entries the feature is expected to emit are actually appearing after a test run, not just that the test assertion passed
- When investigating a bug, find the signal in the observability platform first, then write the reproducing test - not the other way around

## Jira MCP

- Fetch the ticket and read full description, AC, and all comments before any test is written
- Post the Quality Assessment back as a comment on the ticket - the ticket is the audit trail. If AC is not confirmed tested in the ticket, it is not confirmed tested anywhere
- If the ticket has subtasks for testing, update their status as phases complete
- If AC was missing and drafted during the run, attach the draft and flag it for team review - do not silently treat your draft as the contract

## GitHub MCP

- Read changed files directly from the branch or PR - do not guess locations
- Trace imports and dependencies up to depth 3 (see context budget in `intake-workflow.md`)
- Locate existing test files for the changed modules - read names and structure, then bodies for the directly-relevant ones
- Use blame sparingly - useful for finding the author of a fragile area, not for routine test writing

## General principle

MCP tools close the loop between test and production reality. A test that passes in isolation but whose feature has active production alerts is not a green build - it is an unresolved quality gap. MCP tools are what connect the two halves.

When a tool is *not* connected, the work doesn't stop - it gets explicitly downgraded:

- Without Playwright: describe the browser scenarios as written specifications, flag that they need execution before ship
- Without Sentry: ask the team whether any known production issues exist for this surface; record the answer
- Without an observability MCP: read source for the instrumentation, do not assume signals exist because the code path looks "normal"
- Without Jira: ask the user for AC directly, record them inline in the Test Surface Map
- Without GitHub: ask for file paths or pasted code; do not invent locations
