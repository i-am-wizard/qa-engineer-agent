# Output Templates

The canonical formats used across the pipeline. The sub-agents emit these formats; consistency lets the qa-curator extract reliable patterns across runs and lets the orchestrator detect partial / failed phases.

---

## Test Surface Map

Emitted by qa-researcher. Written incrementally to `.claude/qa/<TICKET-KEY>-surface-map.md` so a session drop doesn't lose work. Status header is the resume signal.

```markdown
# Test Surface Map: <TICKET-KEY>
# Status: INCOMPLETE | COMPLETE
# Started: <timestamp>
# Updated: <timestamp>

## Source
- Ticket: <key> - <link if available>
- Branch/PR: <branch or PR ref>
- Changed files: <list>

## Acceptance Criteria (from ticket)
- AC1: <exact text>
- AC2: <exact text>
- (If none found: ⚠️ NO AC FOUND - escalate before any tests are written)

## Entry Points
| Name | Type | Accepts | Returns / Emits |
|---|---|---|---|
| <function/endpoint/handler> | <fn/endpoint/consumer/job> | <input shape> | <output/event> |

## Data Flow Branches
| Branch condition | Happy path outcome | Failure outcome |
|---|---|---|
| <condition> | <result> | <result> |

## External Dependencies
| Dependency | Call type | Contract source |
|---|---|---|
| <name> | <DB/queue/API/cache> | <test file / contract spec / unknown> |

## Architecture Impact
<Include this section only when the change qualifies per `architecture-mapping.md` - cross-service / cross-module / async boundary / new dependency / state machine change. Omit the section entirely otherwise; do not include an empty stub.>

<One-line caption stating what scope the diagram shows.>

```mermaid
<sequence / flowchart / state diagram per architecture-mapping.md - highlight changed elements>
```

Notes on the diagram (failure modes worth testing, ordering constraints, idempotency requirements):
- <note>

## Existing Test Coverage
| Test file | What it covers | Gaps identified |
|---|---|---|
| <path> | <description> | <what's missing> |

## Scenarios to Write

### Priority 1 - AC-derived (mandatory, blocks ship)
- [ ] Given <context>, when <action>, then <outcome> → AC: <line>

### Priority 2 - Edge cases and failure modes
- [ ] <scenario> - risk: <high/medium/low> - rationale: <why>

### Priority 3 - Regression and non-obvious paths
- [ ] <scenario> - rationale: <why this could break>

## Observability Gaps
- Logs: <present / missing for X operation>
- Metrics: <present / missing for X>
- Traces: <present / missing for X>

## Blockers for test writing
- <anything that must be resolved before writing tests>
```

The qa-writer reads `# Status: COMPLETE` before consuming this map. `# Status: INCOMPLETE` means the orchestrator should re-run qa-researcher.

---

## Coverage Summary

Emitted by qa-writer alongside test files.

```markdown
## Coverage Summary

| Map entry | Scenario written | Test name | Priority |
|---|---|---|---|
| AC1 | Given X when Y then Z | should_... | P1 |
| Edge: null input | ... | ... | P2 |

## Deferred (not written this cycle)
- <scenario> - reason: <time / environment dependency / needs contract first>

## Prerequisites (if any)
- <missing fixture, factory, framework>
```

---

## Validation Report

Emitted by qa-validator, written to `.claude/qa/<TICKET-KEY>-validation-report.md`. **Raw test output is mandatory and not truncated** - a summary without raw output is not a pass.

```markdown
## Validation Report: <TICKET-KEY> - <Summary>

### Test Suite Result
- Runner: <pytest / jest / go test / etc.>
- Command: <exact command run>
- Result: PASS | FAIL | BLOCKED
- Tests run: <n> | Passed: <n> | Failed: <n> | Skipped: <n>

### Raw Output
\`\`\`
<full test runner output - do not truncate>
\`\`\`

### Failed Tests (if any)
| Test name | Failure message | Stack trace (first 5 lines) |
|---|---|---|
| <name> | <message> | <trace> |

### Coverage Against Test Surface Map
| Map entry | Test name | Result |
|---|---|---|
| AC1 → scenario | should_... | ✓ pass |
| Edge: null input → scenario | should_... | ✗ fail |

### Observability Signals (if MCP connected)
| Signal | Expected | Actual | Status |
|---|---|---|---|
| Error rate | ≤ baseline | <value> | ✓ / ✗ |
| Log: <operation> | present | present / missing | ✓ / ✗ |
| Trace: <span name> | present | present / missing | ✓ / ✗ |

### Playwright Results (if MCP connected)
| Scenario | Result | Screenshot |
|---|---|---|
| <scenario> | pass / fail | <path or n/a> |

### Sentry (if MCP connected)
- Issues before change: <n>
- Issues after change: <n>
- New issues introduced: <list or none>

### Verdict
- [ ] PASS - all Priority 1 scenarios passing, no regressions, observability confirmed
- [ ] FAIL - see failed tests above; returning to qa-writer (cycle <1 or 2 of 2>)
- [ ] BLOCKED - <reason>

### Quality Debt Logged
- <any deferred scenarios>
- <any observability gaps found but not fixed this cycle>
```

---

## Quality Assessment

The final artifact, written to `.claude/qa/<TICKET-KEY>-quality-assessment.md` and posted as a Jira comment when the Jira MCP is connected.

```markdown
## Quality Assessment: <TICKET-KEY> - <Feature Name>

### Coverage Status
- Covered behaviours: <list>
- Uncovered risks: <list with severity>

### Test Cases Added / Modified
- <test name> - <what it verifies> - <pass/fail>

### Observability Signals Verified
- Logs: <present / missing / needs fix>
- Metrics: <present / missing / needs fix>
- Traces: <present / missing / needs fix>
- Alerts: <present / missing / proposed>

### Verification checklist
- [ ] Test Surface Map produced and all Priority 1 scenarios map 1:1 to AC lines
- [ ] Existing test files read; gap analysis completed before writing new tests
- [ ] All acceptance criteria have a corresponding passing test
- [ ] Negative / edge case tests exist for identified failure modes
- [ ] Test suite output attached as evidence - not just "tests pass"
- [ ] No existing tests deleted or disabled to make the suite pass
- [ ] Flaky tests introduced by the change are fixed before merge
- [ ] Structured logs emitted for key operations and verified
- [ ] Metrics and traces present with the correct dimensions/tags
- [ ] An alert exists or is proposed for the most likely production failure mode
- [ ] Performance within agreed SLO bounds - measured with data
- [ ] Data integrity verified: no orphaned state, correct rollback on failure
- [ ] For bug fixes: regression test reproduces the bug before the fix
- [ ] If observability MCP connected: baseline queried before, improvement confirmed after
- [ ] If Playwright MCP connected: scenarios executed, screenshots attached to failures
- [ ] If Sentry MCP connected: active issues checked; volume reduction confirmed after fix
- [ ] If Jira MCP connected: comment posted with scenario count, AC coverage, and gaps

### Blockers
- <anything that must be resolved before ship>

### Recommendations
- <non-blocking improvements for the next cycle>
```

---

## Curation Summary

Emitted by qa-curator after a successful pipeline run.

```markdown
## Curation Summary: <TICKET-KEY>

### Service memory file
- Path: .claude/qa/memory/<service-name>.md
- Run count: <n>

### Added
- <category>: <entry>

### Updated
- <category>: <entry> (changed: <what changed>)

### Pruned / Resolved
- <entry> → moved to Resolved because: <reason>

### Nothing extracted
- <category>: no new learnings this run (reason: <why>)
```
