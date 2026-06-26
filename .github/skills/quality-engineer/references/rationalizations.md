# Common Rationalizations

Recurring patterns that argue tests away in the moment. Each one has a constructive response - not "no, you're wrong", but "here is what to check before accepting that argument."

This is a living document. When a new rationalization shows up in the wild that isn't listed here, append it.

| Rationalization | What to do |
|---|---|
| "This change is too small to need a test." | Size is independent of risk. Check whether the change touches a contract, a boundary, or shared state. A five-line change to an auth check has a larger risk surface than a 500-line refactor of internal helpers. If the AC for the parent feature still applies, the test still applies. |
| "I'll add tests later." | "Later" tends not to happen. The cheapest moment to write the test is now, while context is fresh. If genuine reasons exist to defer (environment unavailable, contract not finalised), log it as deferred quality debt in the Quality Assessment so it isn't quietly lost. |
| "Tests pass, ship it." | Passing tests are evidence of the things tested. Check: did a human review the diff? Did the runtime signal show the expected behaviour? Are observability signals present? "Tests pass" is necessary, not sufficient. |
| "We have monitoring, we'll catch it in production." | Monitoring catches failures after users see them. Useful, but not a replacement for tests that catch them before. Both layers are needed, not one or the other. |
| "It works on my machine." | The test suite is the shared definition of "working". If the behaviour isn't in a test, it isn't proven to work anywhere except the developer's machine. |
| "The existing tests would have caught this." | Treat as a hypothesis. Run the suite against the failure scenario; if it doesn't fail, that hypothesis is wrong and the gap is real. |
| "This code path is never hit in production." | If it's deployed and reachable, it can be hit. If it genuinely cannot be hit, why is it deployed? Either prove the path is unreachable or test it. |
| "No scenario exists yet, I'll write tests based on the implementation." | Tests written from implementation re-encode whatever the code happens to do. Draft the Gherkin first - even if it's rough - so the tests anchor on the intended behaviour, not the accidental behaviour. |
| "Observability can be a follow-up ticket." | A feature with no logs, metrics, or traces ships with a known blind spot. Sometimes that's an acceptable trade - but it should be a deliberate, logged trade, not a default. |
| "The flaky test is unrelated to my change." | Flaky tests are bugs. They erode trust in the suite. Fix or delete before merging, even if "unrelated" - a flaky suite is a suite no one trusts. |
| "I know enough from the ticket summary to write tests." | The summary is a label, not a spec. Read the full description, AC, and comments before touching the codebase. |
| "I'll read the code and infer what it's supposed to do." | Implementation is not the spec. A bug can be perfectly consistent with the code and completely wrong against the requirement. |
| "I don't need to map the test surface before writing." | Without a map, coverage is incidental rather than intentional. The map is the difference between "we tested some things" and "we know what we tested and what we didn't." |
| "I'll skip linking back to Jira, the PR will be enough." | The ticket is the audit trail across the lifecycle of a feature, including future debugging. If AC isn't confirmed tested in the ticket, future-you will not know it was tested. |

## Adding new entries

When a new pattern shows up:

1. Write it down as the user said it - verbatim or close to it
2. Write the constructive response: what to *check*, not what to *deny*. The goal is to push the conversation toward evidence, not toward refusal
3. Append to the table above

The table is only useful if it reflects the actual failure patterns of the team using it.
