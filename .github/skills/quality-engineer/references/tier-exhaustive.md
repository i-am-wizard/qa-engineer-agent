# Exhaustive Tier: Additional Checks

When `/qa --exhaustive` is invoked, qa-validator runs everything in the Standard tier plus the checks below. The exhaustive tier exists because critical paths - payment, auth, data integrity, anything where a regression has user-visible cost beyond annoyance - deserve scrutiny that's not worth the runtime cost on every change.

If the user requests exhaustive on a low-risk change, that's fine - the cost is theirs to spend. But the inverse is the failure mode worth catching: a payment processor change being run as `--quick` because the developer is in a hurry. The skill should surface this pattern in the Quality Assessment when it sees it.

## Added checks

### Mutation testing

Run a mutation testing tool against the changed modules (e.g. `mutmut`, `stryker`, `pitest` - pick by language). Report the mutation score.

A mutation score below 70% means tests pass against code that is provably wrong. Surface specific surviving mutants in the report - they identify exactly which conditional, return value, or boundary check is not actually being tested.

Mutation testing is expensive. That's why it's exhaustive-tier only - but it's the most direct way to catch tests that look like they cover something but don't actually exercise the logic.

### Performance baseline

For any code path with a defined SLO or latency budget:

- Capture baseline latency before the change (from staging or local benchmark)
- Capture latency after the change
- Report the delta and whether it stays within SLO

If no SLO exists for the path, surface that as a gap - exhaustive tier is a reasonable point to ask whether one should exist, not to invent a number.

### Security boundary checks

For any code path that crosses an auth or trust boundary:

- Negative tests for unauthenticated access (should fail closed)
- Negative tests for authenticated-but-unauthorised access (different user, expired token, revoked permission)
- Input validation for fields that originate from untrusted sources - length limits, type checks, injection-resistant encoding
- Output encoding where data flows back to a browser or another service

These aren't a full security audit - that's a separate skill. They're the boundary checks that an exhaustive-tier QA run should not miss.

### Data integrity invariants

If the change touches persistence:

- Run the test suite against a database that starts with realistic existing data, not just an empty schema. (Some bugs only manifest when records already exist)
- Verify referential integrity is preserved after a successful operation - no orphaned records
- Verify atomicity on failure - a half-failed operation leaves the database in a valid state, not a partial one
- For multi-step flows, verify the compensating action works (the rollback path is tested as deliberately as the happy path)

### Observability under load

If the change has performance implications:

- Verify logs and metrics still emit correctly under realistic load, not just single-request tests. Some structured logging implementations drop messages under throughput pressure - that's a production blind spot worth catching pre-ship
- Verify trace propagation still works across concurrent requests

## What exhaustive does *not* do

The exhaustive tier is not a substitute for:

- A full security audit (separate skill / specialist)
- A formal performance test under realistic production load (separate tooling)
- A penetration test
- An accessibility audit

Exhaustive is the tier where standard QA pushes harder, not where QA expands its remit beyond testing.

## Reporting

The Validation Report (see `output-templates.md`) gets an additional section when exhaustive was run:

```markdown
### Exhaustive-Tier Findings

#### Mutation Score
- Score: <%>
- Surviving mutants: <count>
- Top 3 surviving mutants:
  - <file:line> - <mutation type> - <reason this matters>

#### Performance
- Baseline p99: <ms>
- After change p99: <ms>
- SLO bound: <ms or 'no SLO defined'>
- Verdict: within / exceeds

#### Security Boundary Checks
- Unauthenticated access tests: pass/fail
- Authorisation tests: pass/fail
- Input validation: pass/fail
- Output encoding: pass/fail

#### Data Integrity
- Realistic-data run: pass/fail
- Referential integrity: pass/fail
- Atomicity on failure: pass/fail
- Compensating action: pass/fail / n/a

#### Observability Under Load
- Log emission under concurrency: pass/fail / n/a
- Trace propagation under concurrency: pass/fail / n/a
```
