# Intake Workflow: Jira + GitHub

This reference covers the full intake sequence when Jira and GitHub MCPs are both connected. Skipping steps produces tests that are technically valid but worthless in context - they test the wrong things, duplicate existing coverage, or miss the real risk surface.

If only one MCP is connected, run the side that is available and explicitly flag the other half as a gap in the Quality Assessment.

## Step 1 - Read the ticket

Using the Jira MCP, fetch the ticket by key (e.g. `PROJECT-123`) and extract:

- **Summary** - the one-line intent
- **Description** - full requirement narrative
- **Acceptance Criteria** - every AC line is a mandatory test scenario. If none exist, stop and draft them before proceeding (see ATDD section of SKILL.md)
- **Linked tickets** - parent epic, blocked-by, relates-to. These reveal scope boundaries and integration points
- **Labels / components** - identify which service, module, or domain owns this work
- **Reporter and assignee comments** - edge cases and clarifications often live here, not in the description

Flag immediately if:

- Acceptance criteria are missing → draft them and confirm with the team before continuing
- The description is implementation-focused ("add a new endpoint") with no outcome statement ("so that users can…") → surface this gap; tests derived from implementation steps are not acceptance tests

## Step 2 - Understand the codebase

Using the GitHub MCP:

1. **Locate the relevant files.** Use the ticket's component/label and any referenced branch or PR to find the code being changed. Do not guess - read the diff or branch directly
2. **Read the implementation.** Understand what the code actually does, not what the ticket says it should do. Discrepancies between the two are the highest-value test cases
3. **Identify all entry points** touched by this change: function signatures, event handlers, message consumers, scheduled jobs, CLI commands - whatever is the actual boundary of the feature
4. **Trace the data flow.** Follow inputs from entry point through to persistence, event publication, or external call. Every branch is a test scenario
5. **Find the existing tests.** Locate test files for the changed modules and read them:
   - What is already covered? Do not duplicate it
   - What is covered only by a happy-path assertion? Those need edge case siblings
   - What is not covered at all? Those are the gaps - prioritise by risk
6. **Read the dependencies.** If the feature calls another service, reads a shared library, or publishes to a queue, understand that contract. Tests that don't reflect the real dependency contract pass locally and fail in integration

## Step 3 - Build the Test Surface Map

Before writing any test, produce a structured map. This is the working document for the session - update as you learn more. The full template is in `output-templates.md`.

Key rule: every Priority 1 scenario must trace 1:1 to an AC line. If an AC line has no corresponding scenario, that is a blocker.

## Step 4 - Write tests against the map

Only after the map is complete. Each test must trace back to either a specific AC line (Priority 1) or an identified branch, failure mode, or dependency risk (Priority 2/3). A test with no entry in the map is a test that cannot be justified.

Apply the full quality strategy from SKILL.md: risk-based layer selection, behavioural verification, data integrity checks, observability signal verification.

## Step 5 - Link evidence back to the ticket

Using the Jira MCP, after tests are written and passing, post a comment on the ticket summarising:

- Total scenarios written, broken down by priority
- Any AC lines that could not be fully tested and why (dependency not mockable, environment not available)
- Observability gaps found during the process
- Any implementation discrepancies found between the ticket description and the actual code

If the ticket has subtasks for testing, update their status. If you drafted missing AC, attach the draft for team review - do not silently assume it is correct.

## Context budget for research

Research on a large codebase can exhaust the context window before test writing starts. Apply these limits strictly:

- Read a maximum of **10 source files** directly. If more are changed, prioritise: entry points first, then files touched by data flow, then test files
- Read no more than **3 levels deep** in import chains. Stop and note "dependency not traced beyond depth 3" rather than continuing indefinitely
- For existing test files, read the listing and test names first. Only read full test bodies for files directly covering changed modules
- If the codebase is too large to map within budget, scope to changed files only and mark all other sections as "not assessed - out of scope for this cycle"

## Service memory check

Before research begins, read `.claude/qa/memory/<service-name>.md` if it exists (service name from the ticket component label, or inferred from changed file paths). The memory file lets you pre-populate Priority 2 scenarios with known failure patterns, flag known fragile areas without re-tracing code, and surface recurring AC quality issues to the team. This is what makes the pipeline get smarter over runs.
