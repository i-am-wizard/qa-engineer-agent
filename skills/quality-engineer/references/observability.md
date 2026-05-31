# Observability Verification

A feature that is not observable is not testable in production. The SKILL.md covers the *why*; this reference covers the *what to check*, signal by signal.

## Logs

- Key operations emit structured log entries (not free-form strings) with a consistent schema
- Log entries include trace/correlation IDs so a single request can be followed across services
- Errors are logged at the correct level with sufficient context to diagnose without a debugger
- No sensitive data (PII, credentials, tokens) appears in log output
- No log spam: repeated no-op calls do not flood the log at INFO or higher
- Log volume is bounded - a runaway loop should not be able to fill disk

## Metrics

- The feature increments / updates the expected counters, gauges, or histograms
- Error and success counts are tracked separately so error rate is derivable
- Latency is instrumented at meaningful boundaries, not just the outermost call
- Metrics carry the dimensions/tags needed to filter by environment, service, and version
- Cardinality of tags is bounded - user IDs as tags will blow up the metrics store

## Traces and spans

- Distributed operations produce traces that show the full call graph
- Spans have meaningful names - not just HTTP method + URL
- Span attributes capture enough context to reconstruct what happened
- Errors are marked on the span, not just logged separately
- Trace propagation headers (W3C `traceparent`) are forwarded across service boundaries

## Alerts and SLOs

- If a feature owns or affects an SLO, verify that the SLO metric is updated by the feature's path
- An alert exists (or is proposed) for the failure mode most likely to affect users
- Alert thresholds are not set so low they fire in normal operation - verify against baseline data, not vibes
- Alerts route to someone who can act, not a stale rotation

## Health and readiness

- A new dependency is reflected in the service's health/readiness probe
- Circuit breakers or retry budgets exist for unreliable dependencies
- The probe fails fast when the dependency is genuinely unreachable - does not block forever

## When no observability MCP is connected

Do not skip this verification silently. Instead:

- Add an explicit "Observability not verified - no MCP connected. Manual verification required before ship" item to the Quality Assessment
- Read the source code directly: confirm log/metric/trace calls exist at the right points, carry the right fields, and are not inside an unreachable branch
- Block ship for any new code path that has zero log, metric, or trace instrumentation in the source code itself - the absence of tooling does not excuse the absence of instrumentation

## What "verified" means

A signal is verified when, after running the test or triggering the path, the corresponding log/metric/trace is *observed in the appropriate platform* - not assumed from code. With an observability MCP connected, run the query. Without one, eyeball the code and state explicitly that runtime verification was not done.
