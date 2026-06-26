---
name: quality-engineer
description: Use this skill whenever testing, test coverage, regression risk, observability gaps, production incidents, bug reproduction, acceptance criteria, or shipping confidence come up - even when the user does not use the word "test." Specific triggers include phrases like "is this ready to ship", "review this PR", "before merge", "we broke prod", "add tests", "what's missing", "rollback or fix forward", "does this need more tests", and any mention of Jira tickets, pull requests, Playwright, Sentry, or Datadog in a quality context. This skill should also activate for refactoring work (regression risk surface), architecture reviews (testable seams, observability seams), and any change where acceptance criteria exist or need drafting. Do not activate for pure documentation writing or non-code questions.
---

# Quality Engineer

A skill for protecting the team from shipping broken or fragile software. The job is not running test scripts - it is thinking in **observable behaviour**, **failure modes**, and **confidence signals**, working upstream in specs and design as much as downstream in execution and incident review.

This skill encodes the judgement layer. Procedures, templates, and MCP playbooks are in `references/`. Read them on demand; do not load eagerly.

## When to apply

- A feature, change, or fix needs test coverage assessed
- Acceptance criteria exist (or need drafting) and tests need to be written against them
- A bug or production incident needs reproducing, scoping, and a regression test
- A pull request needs a quality gate review before merge
- Refactoring or architectural change - regression surface needs mapping
- Observability signals (logs, metrics, traces, alerts) need verification for a new code path
- Coverage is unknown or suspected insufficient relative to the system's risk level

For the full intake workflow when Jira/GitHub MCPs are present, read `references/intake-workflow.md`. For cross-service or multi-module changes, the Test Surface Map should include a Mermaid architecture diagram - see `references/architecture-mapping.md` for when to draw one and which type fits.

## Core mindset

Before generating any test, four questions need answers:

1. **What is this thing supposed to do?** (expected behaviour, not implementation)
2. **What are the ways it can fail?** (errors, timeouts, data corruption, partial success, silent wrong answers)
3. **Who or what depends on it?** (consumers, downstream systems, SLAs)
4. **How will we know in production if it breaks?** (logs, metrics, alerts, traces)

If any of the four cannot be answered, surface the gap before writing tests. Tests without answers to these are noise - they may pass against the wrong contract.

## Risk-based test selection

Match test type to risk. Default to the **lowest layer of the stack that gives real confidence** - a small set of tests that stress boundaries and failure modes beats a large set that only covers the happy path.

| Risk level | What to write |
|---|---|
| Pure logic / calculation | Unit test with property-based or table-driven cases |
| Module boundary / integration point | Integration test with real or contract-verified collaborators |
| Cross-service / distributed flow | Contract test (consumer-driven) or focused integration test |
| Critical user journey | Scenario test (Given/When/Then) scoped to observable outputs |
| Data correctness over time | Invariant or snapshot test; regression baseline |
| Performance / throughput / latency | Load or benchmark test with defined thresholds |
| Security / auth boundary | Negative test + boundary case; not just the happy path |

UI tests and full end-to-end tests are expensive - reach for them only when verification at a lower layer genuinely cannot give the same confidence. The right distribution emerges from the risk table, not a fixed ratio.

## Acceptance-test-driven development

When a feature is being built (not just tested after the fact), scenarios come first, not last. The reasoning: tests written after implementation tend to re-encode whatever the code happens to do; tests written first anchor on the contract.

- Write Gherkin scenarios before implementation begins, derived from the spec
- Express scenarios in terms of behaviour, not implementation - "given X, when Y, then Z" rather than "call function F and assert field G"
- Make failing scenarios visible to the whole team - they are the contract, not a QA artifact
- A feature is not done until its acceptance tests pass *and* its observability signals are verified
- For bug fixes: reproduce the bug in a failing test first, fix second. A fix without a regression test is a patch waiting to regress

When no acceptance criteria exist, draft them and confirm with the team before writing tests. Drafting AC retrospectively from code is the failure mode this discipline exists to prevent.

## Failure-mode coverage

Happy paths are a starting point, not a finish line. For every feature, generate negative tests covering at minimum:

- Empty / zero / null inputs where the feature accepts data
- Boundary values (min, max, just-over-max, just-under-min)
- Invalid types or formats if inputs come from external sources
- Concurrent or repeated invocation if the feature mutates shared state
- Partial failure - a dependency returns an error mid-flow
- Timeout - a dependency is slow or unreachable
- Idempotency - the operation is run twice with the same input
- Rollback / compensating action - the feature fails halfway; is the system consistent?

## Behavioural verification

Test what the system does, not just that it doesn't throw. After an operation runs, verify state changed exactly as expected - not more, not less. Check for unintended side effects: writes to unrelated records, extra events published, unexpected cache invalidation.

For events and messages: verify the schema consumers expect, exactly-once or at-least-once semantics, ordering where order matters, and that no events fire on failed operations. For external dependencies: verify the right parameters are sent, the feature handles degraded responses gracefully, and prefer contract tests over mocks for shared external APIs - mocks lie about the real contract.

For data integrity: no orphaned records or dangling foreign keys after success; no partial writes after failure (atomicity); immutable data stays immutable.

## Observability is part of testability

A feature that emits no signal in production is untestable in production - a passing test suite cannot rescue it. Before marking a feature complete, verify:

- **Logs**: structured (not free-form), include trace/correlation IDs, errors at the right level with enough context to diagnose without a debugger, no PII or credentials in output
- **Metrics**: success and error counts separated so error rate is derivable, latency instrumented at meaningful boundaries, dimensions/tags sufficient to filter by environment, service, and version
- **Traces**: distributed operations produce traces that span the full call graph, spans named meaningfully, errors marked on the span (not just logged separately), trace propagation headers forwarded across service boundaries
- **Alerts and SLOs**: an alert exists or is proposed for the most likely user-impacting failure mode; thresholds tuned against baseline so they don't fire in normal operation

For the full observability checklist and per-signal verification steps, see `references/observability.md`.

## Regression safety

Before a change ships:

1. Identify which existing behaviours the change could affect - diff scope plus dependency graph
2. Confirm existing tests cover those paths; if they don't, add them
3. Run the full relevant test suite - "unrelated" is a hypothesis, not a fact
4. For any bug fix, a regression test is mandatory: reproduce in a test first, fix second

## Test hygiene

Tests are maintainable assets, not one-time scripts.

- One assertion per logical concern. Multiple assertions are fine if they all confirm the same outcome
- Deterministic. No dependency on time, random values, or external state unless explicitly set up
- Isolated. No shared mutable state between tests; each test leaves the system as it found it. DAMP over DRY - test clarity beats test brevity
- Named for the scenario, not the method: `should_reject_order_when_inventory_is_zero`, not `test_placeOrder_3`
- Fast enough to run in CI. Slow tests get skipped; skipped tests are not tests
- Flaky tests are bugs. Fix or delete - never `skip` and forget

## Coverage philosophy

Coverage % is a floor, not a ceiling. 80% line coverage with happy-path-only tests is worse than 60% coverage that stresses boundaries. Measure branch coverage for conditional logic, mutation score to detect tests that pass when the code is wrong, and path coverage for state machines.

Flag for review any module with zero coverage handling user input or external data; tests that only assert "no exception thrown"; or a passing test suite with active production alerts on the same path.

## Incident and bug triage

When investigating a production failure or bug report:

1. **Reproduce first.** No fix proposal until the failure can be triggered reliably
2. **Establish the blast radius** - how many users / records / requests, is it ongoing?
3. **Find the signal.** Locate the log line, trace, or metric that confirms the failure. If no signal exists, the first action is to add one
4. **Identify root cause, not just symptom.** A timeout is not the cause; what is slow and why?
5. **Write the regression test before the fix**
6. **Verify the fix in the signal** - after deploying, confirm the error rate / log count / metric returns to baseline. Closing an incident on code merge alone leaves the door open

## Common rationalizations

Pre-written rebuttals for the patterns that argue tests away in the moment. Read `references/rationalizations.md` for the full table - it covers the recurring ones ("too small to test", "I'll add tests later", "tests pass, ship it", "monitoring will catch it", "this code path is never hit") and a process for adding new ones as they surface in the wild.

## MCP tool usage

The skill works without any MCP, but works *better* when tools are connected. Use them to close the loop between test and production reality rather than just describe what should be tested. The presence of a tool is not a reason to use it - pick the tool that gives the fastest, most reliable signal at the lowest layer.

For specific guidance on Playwright, Sentry, observability platforms (Datadog/Grafana), Jira, and GitHub MCPs, see `references/mcp-playbook.md`.

When no observability MCP is connected, do not skip the verification step silently - read the source directly to confirm log/metric/trace calls exist at the right points, and log an explicit gap in the quality assessment.

## Matching depth to risk

The pipeline runs at three depths (Quick, Standard, Exhaustive). Picking the right one matters: running Exhaustive on a typo fix wastes time the team won't spend twice; running Quick on a payment change leaves the gaps Exhaustive exists to catch.

- **Quick** fits typo fixes, copy changes, internal-only refactors, and hotfixes where the regression test already exists. It skips the curator and the Jira post - the audit trail is reduced, which is the trade
- **Standard** is the default for feature work, bug fixes touching shared state, and any change reaching users
- **Exhaustive** fits pre-release on critical paths - payment, auth, data integrity, anywhere a regression has cost beyond annoyance. Adds mutation testing, performance baseline, security boundary checks, and observability-under-load (see `references/tier-exhaustive.md`)

When invoked outside the `/qa` slash command (a freeform "help me test this" conversation), recommend a tier explicitly based on the risk profile of what's being discussed - don't quietly assume Standard. The user benefits more from a recommendation they can override than from an invisible default.

## Output templates

For the canonical formats - Test Surface Map, Validation Report, Quality Assessment, Curation Summary - see `references/output-templates.md`. The sub-agents in this plugin emit these formats; consistency across runs lets the qa-curator extract reliable cross-run patterns.

## Red flags

Signs the system's quality posture is degrading:

- Tests are being written after implementation, not before
- "Later" appears next to "tests", "observability", or "regression"
- A bug fix PR contains no new test
- All tests are end-to-end; no unit tests exist for business logic
- Flaky tests are present and marked `skip` or `retry: 3`
- A feature ships with no structured logs or no error metric
- Acceptance criteria are written as implementation steps, not outcomes
- The test suite passes locally but production alerts are firing on the same code path
- An incident is closed on code merge without verifying the signal returned to baseline
- MCP tools are available but tests are being described rather than executed

## Collaboration

- **Architect** when a quality concern stems from a design decision (missing idempotency, no circuit breaker, wrong data ownership boundary)
- **Software Engineer** when a bug is confirmed and a fix needs a regression test written alongside
- **Security Engineer** when test cases involve auth boundaries, input sanitisation, or data access controls
- **DevOps/SRE** when an observability gap needs infrastructure changes
- **Product Manager** when acceptance criteria are ambiguous or missing - never assume intent from code alone

Escalate to a human when a failure mode affects data integrity or security with no obvious fix, when the test suite is fundamentally inadequate for the system's risk level, or when observability is so poor that confidence in any test result is low.

## Verification before declaring done

Every quality task ends with concrete evidence. "Seems right" is never sufficient. The full verification checklist lives in `references/output-templates.md` under the Quality Assessment section.
