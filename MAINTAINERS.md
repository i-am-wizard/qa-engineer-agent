# Maintainer Reference - QA Engineer Plugin

This document is for **plugin maintainers** - anyone modifying the skill, agents, references, or commands. For day-to-day **usage** of the plugin, see [README.md](README.md).

This file covers the plugin's structure, design decisions, file layout, and version history. It's an audit trail of *why the plugin is shaped the way it is*, not a guide for using it.

## What's included

| Component | File | Purpose |
|---|---|---|
| Skill | `skills/quality-engineer/SKILL.md` | The judgement layer - risk strategy, ATDD, observability, hygiene, tier matching |
| Reference | `references/intake-workflow.md` | Full Jira + GitHub intake procedure (loaded on demand) |
| Reference | `references/observability.md` | Per-signal verification checklist (loaded on demand) |
| Reference | `references/mcp-playbook.md` | Per-tool guidance for Playwright, Sentry, Datadog, Jira, GitHub |
| Reference | `references/rationalizations.md` | Recurring rationalizations and constructive responses |
| Reference | `references/output-templates.md` | Canonical formats for every pipeline artifact |
| Reference | `references/tier-exhaustive.md` | Additional checks for `--exhaustive` runs |
| Reference | `references/architecture-mapping.md` | When and how to generate Mermaid diagrams for cross-service changes |
| Evals | `evals/evals.json` | Trigger and doctrine-adherence test cases |
| Sub-agent | `agents/qa-researcher.md` | Reads ticket + codebase, produces Test Surface Map |
| Sub-agent | `agents/qa-writer.md` | Writes tests from the map; nothing else |
| Sub-agent | `agents/qa-validator.md` | Runs suite, verifies signals, returns evidence |
| Sub-agent | `agents/qa-curator.md` | Updates per-service memory across runs |
| Command | `commands/qa.md` | `/qa [--quick\|--exhaustive] <TICKET>` - pipeline |
| Command | `commands/qa-research.md` | `/qa-research <TICKET>` - research only |
| Command | `commands/qa-validate.md` | `/qa-validate` - validation only |

## Why this shape

- **Progressive disclosure.** SKILL.md is ~190 lines of judgement. Procedures, templates, and tier-specific checks live in `references/` and load only when the workflow needs them. Initial trigger cost is small; total available depth is large
- **Orchestration in commands, not agents.** The `/qa` command sequences sub-agents directly - there is no extra orchestrator persona. One fewer file in context for every run
- **Sub-agents are I/O contracts.** Each agent file is short and describes only what that role uniquely does. Doctrine lives once, in the skill
- **Artifacts survive context resets.** Every phase writes its output to `.claude/qa/<TICKET>-*.md`. The `/qa` command's resume check uses these to skip completed phases on retry
- **Tiered execution matches depth to risk.** Quick / Standard / Exhaustive let users run the right pipeline for the change, instead of paying full price for every typo fix or skipping `/qa` entirely on critical paths
- **Reasoned tone over musty MUSTs.** Doctrine is framed as consequences and underlying concerns rather than prohibitions, so the model applies judgement at the edge cases rather than refusing or performing compliance

## Tiers

| Tier | Flag | Phases | Use when |
|---|---|---|---|
| Quick | `--quick` | research → write → validate | Typo fixes, copy changes, internal-only refactors. Skips curator + Jira post |
| Standard | (default) | research → write → validate → curator → Jira post | Default for feature work and user-reaching changes |
| Exhaustive | `--exhaustive` | Standard plus mutation testing, performance baseline, security boundary checks, observability-under-load | Critical paths: payment, auth, data integrity, pre-release |

## Installation

```bash
# Verify the plugin command syntax for your Claude Code version:
claude plugins --help

# Then install from a local clone or GitHub repo using the syntax shown.
```

## Usage

```bash
# Default - standard tier
/qa PROJECT-123

# Quick tier - research + write + validate only
/qa --quick PROJECT-123

# Exhaustive tier - adds mutation, performance, security boundary, load observability
/qa --exhaustive PROJECT-123

# Force re-run even if a Quality Assessment exists
/qa PROJECT-123 --force

# Phase isolation (any tier)
/qa-research PROJECT-123      # research only
/qa-validate                  # validation only on existing suite
```

The skill itself activates automatically whenever testing, quality gates, regression risk, observability, incidents, PR review, or shipping confidence come up in a normal conversation - no slash command needed. When invoked freeform, the skill will recommend a tier based on the risk profile rather than silently assume Standard.

## MCP integrations

The pipeline uses whatever MCPs are connected. None are required - the pipeline degrades gracefully if a tool is absent, and explicitly logs the gap in the Quality Assessment rather than silently skipping verification.

| MCP | Used by | Purpose |
|---|---|---|
| Jira | qa-researcher, /qa orchestration | Read ticket + AC, post quality report |
| GitHub | qa-researcher | Read codebase, diff, existing tests |
| Playwright | qa-validator | Execute browser scenarios, capture screenshots |
| Sentry | qa-validator | Check error volume before/after |
| Datadog / Grafana / equivalent | qa-validator | Verify log, metric, trace signals |

## Pipeline sequence

```
/qa [--quick|--exhaustive] PROJECT-123
    │
    ├─ qa-researcher ──► Test Surface Map (incremental writes, status header)
    │       └─ Jira MCP: read ticket + AC
    │       └─ GitHub MCP: read code + existing tests
    │       └─ Reads .claude/qa/memory/<service>.md if it exists
    │
    ├─ [optional human gate: review map, confirm AC]
    │
    ├─ qa-writer ──► test files
    │       └─ Input: Test Surface Map (Status: COMPLETE)
    │
    ├─ qa-validator ──► Validation Report (raw output attached)
    │       └─ Run test suite
    │       └─ Playwright MCP: browser scenarios + screenshots
    │       └─ Observability MCP: log / metric / trace signals
    │       └─ Sentry MCP: error volume check
    │       └─ [if --exhaustive] mutation, perf, security, load observability
    │
    ├─ /qa compiles Quality Assessment
    │
    ├─ [Standard/Exhaustive only] qa-curator ──► Service Memory updated
    │
    └─ [Standard/Exhaustive only] Jira MCP ──► comment posted on ticket
```

## Sequential by data dependency

The pipeline is sequential because the data dependencies require it: qa-writer needs the map qa-researcher produces; qa-validator needs the tests qa-writer produces; qa-curator needs all three artifacts. This isn't accidental - it's the addyosmani composition rule applied here: the command orchestrates, sub-agents don't invoke each other. Parallel fan-out is reserved for cases where multiple agents can run on the same input (e.g. multi-reviewer audits), which is a different pattern than this pipeline.

## Doctrine the pipeline enforces

Framed as reasoning rather than rules (see `references/rationalizations.md` for why):

- **AC traceability makes coverage intentional.** Without it, tests encode whatever the code does rather than what it should
- **A PASS verdict is only defensible with raw output attached.** A summary alone leaves nothing for review
- **Bug fixes need a regression test that failed before the fix.** Otherwise the fix is a patch, not a guarantee
- **Two correction cycles is the budget.** Beyond that, the failure pattern is usually structural
- **An incident closes when the signal returns to baseline.** Code merge alone is a hypothesis

## Evals

`evals/evals.json` contains trigger cases and doctrine-adherence cases. Run them through Claude in a fresh session after changing the skill description or doctrine to catch regressions. Cases failing trigger checks drive description tuning; cases failing behaviour checks drive doctrine clarification in SKILL.md or the relevant agent.

## What changed from v2.1.2

- **PEP 723 inline metadata in `run_evals.py`.** The script now declares its `anthropic` dependency in a metadata block, making it runnable via `uv run run_evals.py` with no install step. The traditional `pip install anthropic && python3 run_evals.py` path still works
- READMEs (user-facing and scripts/) updated to lead with the uv invocation pattern

## What changed from v2.1.1

- **Architecture mapping for cross-service changes.** qa-researcher now generates a Mermaid diagram (sequence, flowchart, or state - whichever fits) when a change spans more than two services, crosses an async boundary, introduces a new external dependency, or modifies a state machine. Single-module changes skip the diagram entirely rather than include an empty stub. When the change spans services the code doesn't fully reveal, the agent asks for an architecture sketch rather than guessing
- **New reference: `architecture-mapping.md`.** Decision criteria for when to draw a diagram, which type fits the change, and how each diagram element traces back to a test scenario
- **`Architecture Impact` section** added to the Test Surface Map template in `output-templates.md`
- **Three new eval cases** for cross-service, single-module-skip, and ask-rather-than-guess behaviours (total: 20 cases)
- **README split.** The user-facing usage guide is now `README.md`. This document (renamed `MAINTAINERS.md`) is the maintainer reference

## What changed from v2.1.0

- **Eval runner.** `skills/quality-engineer/scripts/run_evals.py` exercises `evals/evals.json` against the Claude API and writes a markdown review report. Optional `--judge` flag uses a second Claude call to evaluate each response

## What changed from v2.0

- **Tiered execution.** `/qa --quick` skips curator + Jira post; `/qa --exhaustive` adds mutation, performance, security boundary, and load observability checks. Standard remains the default
- **Evals.** `evals/evals.json` ships with 17 cases covering positive triggers, close-miss negatives, doctrine adherence, MCP degradation, and tier behaviour
- **Reasoned tone throughout.** Agent "Hard rules" sections rewritten as "Doctrine the X reflects" sections - same constraints, but framed as consequences and underlying concerns so the model applies judgement at edge cases
- **Tier-matching guidance in SKILL.md.** When invoked freeform (no `/qa` command), the skill explicitly recommends a tier based on risk profile

## What changed from v1.x

(Retained from v2.0 for reference)

- One source of doctrine - SKILL.md is the only home for the QA mindset, principles, verification checklist
- References instead of inline procedures - intake, observability, MCP playbook, rationalizations, templates all in `references/`, loaded only when needed
- No orchestrator agent - `/qa` command does orchestration directly
- Triggering rewritten - positive framing, third-person voice, covers PR review / refactor / incidents
- SKILL.md is ~190 lines (was 540 in v1)
