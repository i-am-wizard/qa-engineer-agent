# QA Engineer

A QA agent for Claude Code and GitHub Copilot CLI that reads your Jira ticket, understands your codebase, writes tests grounded in your acceptance criteria, runs them with real evidence, and remembers what it learns for next time.

If you've ever wanted a QA engineer who actually reads the ticket before writing tests, this is that.

## What it does

You point it at a Jira ticket or describe a feature. It then:

1. **Reads the ticket** - pulls AC, description, linked tickets, and comments via the Jira MCP
2. **Reads the code** - locates changed files, traces data flow, finds existing tests via the GitHub MCP
3. **Maps the test surface** - produces a structured plan tying every test back to a specific AC line, with a Mermaid architecture diagram if the change spans multiple services
4. **Writes the tests** - at the right layer of the stack, covering happy paths, edge cases, and failure modes
5. **Runs them** - executes the suite, checks observability signals (logs/metrics/traces), verifies error rates haven't spiked via Sentry, runs browser scenarios via Playwright
6. **Posts the result back to the ticket** - full audit trail with raw test output attached
7. **Remembers** - accumulates per-service memory so the next run is smarter than this one

It can be invoked as a slash command (full pipeline) or activate automatically in conversation when quality topics come up.

## Installation

```bash
# In Claude Code, add the plugin marketplace then install:
/plugin marketplace add <your-repo-url>
/plugin install qa-engineer

# Or from a local clone:
/plugin install ./path/to/qa-engineer
```

After installing, verify it loaded:

```
/plugin list
```

You should see `qa-engineer` listed.

## Using with GitHub Copilot CLI

The same pipeline runs in [GitHub Copilot CLI](https://github.com/features/copilot/cli). The Claude Code plugin (`agents/`, `commands/`, `skills/`) is the source of truth; a generated `.github/` layer exposes it to Copilot as custom agents and a skill. No separate fork, no hosted service.

```bash
npm install -g @github/copilot
```

Copilot CLI auto-discovers `.github/agents/` and `.github/skills/` when you run it **from inside this repository** (or any repo that includes the generated tree), so there's nothing to install beyond cloning. To make the agents available everywhere, copy them into your home config instead:

```bash
cp -r .github/agents/*       ~/.copilot/agents/
cp -r .github/skills/*       ~/.copilot/skills/
```

### Invocation mapping

The Claude Code slash commands map to Copilot custom agents. Each agent's name is the filename without `.agent.md`:

| Claude Code | Copilot CLI |
|---|---|
| `/qa PROJECT-123` | `copilot --agent qa --prompt "run PROJECT-123"` |
| `/qa --exhaustive PROJECT-123` | `copilot --agent qa --prompt "run PROJECT-123 --exhaustive"` |
| `/qa-research PROJECT-123` | `copilot --agent qa-research --prompt "PROJECT-123"` |
| `/qa-validate` | `copilot --agent qa-validate --prompt "validate the current suite"` |

Inside an interactive Copilot session you can also type `/agent` to pick `qa` from the list, or just describe the work (`"run the QA pipeline on PROJECT-123"`) and let Copilot infer the agent. The four phase agents — `qa-researcher`, `qa-writer`, `qa-validator`, `qa-curator` — are available individually too. The judgement-layer skill loads automatically when quality topics come up, or on demand with `/quality-engineer`.

### Connecting MCPs

Copilot CLI manages MCP servers separately from the plugin, in `~/.copilot/mcp-config.json`. Add the ones from the [MCPs table below](#mcps-youll-want-connected) with:

```bash
copilot          # start an interactive session
/mcp add         # fill in the Jira / GitHub / Playwright server, then Ctrl+S
```

The pipeline degrades gracefully when an MCP is missing, exactly as it does under Claude Code.

### Keeping the two layers in sync (maintainers)

Never edit `.github/agents/` or `.github/skills/` by hand — they're generated. Edit the canonical files under `agents/`, `commands/`, `skills/`, then regenerate:

```bash
make build-copilot     # regenerate the .github/ tree
make check-copilot      # verify it's in sync (run in CI)
```

A GitHub Actions workflow runs `check-copilot` on every PR that touches either layer, so the two can't drift.

## Quick start

### Run the full pipeline on a ticket

```
/qa PROJECT-123
```

This runs research → write → validate → curate, then posts the Quality Assessment back to the Jira ticket if a Jira MCP is connected.

### Run on a feature description (no ticket)

```
/qa "Users should be able to export their data as CSV, with a daily rate limit of 3 exports"
```

If the description doesn't include acceptance criteria, the agent will pause and draft them for your review before writing any tests.

### Match the depth to the change

Three tiers, pick the one that fits:

```bash
/qa --quick PROJECT-123        # typo fix, copy change, internal refactor
/qa PROJECT-123                # default - feature work, user-facing bug fixes
/qa --exhaustive PROJECT-123   # pre-release on critical paths (payment, auth, data integrity)
```

The exhaustive tier adds mutation testing, performance baseline, security boundary checks, and observability-under-load. It's slower - use it when a regression would actually hurt.

### Just the research, without writing tests

```
/qa-research PROJECT-123
```

Returns a Test Surface Map so you can review coverage gaps before committing to test writing. Useful before kicking off a sprint or sizing a piece of work.

### Just validate an existing suite

```
/qa-validate
```

Runs the test suite, checks observability signals, returns a Validation Report with raw output attached. Use when tests already exist and you want a signal-confirmed pass before merging.

## Common workflows

### "Is this PR ready to merge?"

Just ask in normal conversation:

> Is the change in PR #456 ready to merge?

The agent activates automatically. It'll discuss coverage gaps, regression risk, observability, and AC traceability - not just answer yes/no. You don't need a slash command for this.

### "We're getting timeouts in production"

Same - describe the problem in conversation:

> Users are reporting checkout timeouts. Can you help me figure out what's going on?

The agent applies its incident triage doctrine: reproduce first, find the signal in Sentry/Datadog, identify root cause (not just symptom), write a regression test before the fix.

### "I'm about to refactor X - what should I watch out for?"

> I'm extracting the inventory logic out of OrderService into its own module. What should I be careful about?

The agent maps the regression risk surface, looks at existing coverage for affected paths, and flags any observability gaps it finds.

### "Help me think through this new feature"

> We're adding a 'cancel subscription within 30 days' feature. Help me think it through.

The agent drafts acceptance criteria in Given/When/Then form before any code discussion. You get scenarios you can take to the team for review, rather than implementation suggestions you'll have to retro-fit AC to.

### Resuming after an interruption

If your session drops mid-pipeline, just run the same command again:

```
/qa PROJECT-123
```

It detects existing artifacts in `.claude/qa/` and resumes from where it left off - won't redo work that's already done. Force a fresh start with `--force`.

## What you'll see in your repo

The pipeline writes its working artifacts to `.claude/qa/`:

```
.claude/qa/
├── PROJECT-123-surface-map.md          # Test Surface Map from qa-researcher
├── PROJECT-123-validation-report.md    # Validation Report from qa-validator
├── PROJECT-123-quality-assessment.md   # Final Quality Assessment (also posted to Jira)
└── memory/
    └── order-service.md                # Per-service learning that grows over time
```

You can read these directly. They're the audit trail. Check them into version control if you want the team to share institutional QA memory.

The actual test files go wherever your project's test convention puts them - the agent reads existing test files to figure out the convention rather than imposing one.

## MCPs you'll want connected

The plugin works without any MCPs, but each one connected unlocks more of the pipeline:

| MCP | What it unlocks |
|---|---|
| **Jira** | Auto-reads tickets and AC; posts the Quality Assessment as a ticket comment |
| **GitHub** | Reads diffs, locates changed files, finds existing tests |
| **Playwright** | Executes browser scenarios with screenshots on failure |
| **Sentry** | Checks error volume before and after a change; flags new issues |
| **Datadog / Grafana / equivalent** | Verifies logs, metrics, and traces actually emit for new code paths |

When an MCP isn't connected, the agent degrades gracefully - it doesn't silently skip the verification, it tells you which one is missing and what gap that leaves in the audit trail.

## What it won't do

Honest about limits:

- **It won't ship tests against missing AC.** If your ticket has no acceptance criteria, the pipeline pauses and asks you to draft them (or escalate to product). This is on purpose - tests written against inferred AC tend to encode whatever the code happens to do, which is the failure mode this whole approach exists to prevent
- **It won't fabricate a PASS verdict.** If the test runner crashes, observability signals are missing, or two correction cycles haven't resolved failures, the verdict comes back BLOCKED and you get the full output. Better an honest stop than a green-looking false positive
- **It won't install your test framework.** If your repo doesn't have a test runner configured, the agent will write tests as files but flag the missing infrastructure rather than guessing at setup
- **It won't write tests for code you haven't shown it.** If GitHub MCP isn't connected and you don't paste the code, the agent asks for it rather than inventing file paths
- **It won't replace security audits, load testing, or accessibility audits.** The `--exhaustive` tier adds security *boundary checks* and *baseline* performance numbers - those aren't a substitute for the dedicated work

## Customising

You can adjust the agent's behaviour without modifying its core files:

- **Want different test priorities?** Edit the risk table in `skills/quality-engineer/SKILL.md`
- **Different observability platform than Datadog?** Update `skills/quality-engineer/references/mcp-playbook.md`
- **Team-specific rationalizations** the agent keeps hearing? Append to `skills/quality-engineer/references/rationalizations.md`
- **Service-specific memory** is built automatically - you can edit `.claude/qa/memory/<service>.md` to add patterns the agent should know about

For deeper changes (new tiers, new sub-agents, schema changes to the Test Surface Map), see [MAINTAINERS.md](MAINTAINERS.md).

## Verifying it works

Once installed, run the eval suite to confirm everything triggers correctly:

```bash
cd skills/quality-engineer/scripts
uv run run_evals.py --dry-run   # inspect what would run
uv run run_evals.py             # run all 20 cases, write a review report
uv run run_evals.py --judge     # add LLM-judge pass/fail verdicts
```

`uv` reads the inline metadata in the script and manages the one dependency automatically - no install step needed. If you don't have uv, install with `pip install anthropic` and use `python3 run_evals.py …` instead.

The eval report ends up as `eval-report-<timestamp>.md` and tells you whether each case triggered the right behaviour. Run after any change to the skill or agents to catch regressions.

## Troubleshooting

**The skill doesn't activate when I talk about testing.**
Check the description in `skills/quality-engineer/SKILL.md` matches the phrasing you use. Run `uv run scripts/run_evals.py --category triggering` to see which triggers fire and which don't.

**`/qa` says the ticket has no AC but I see AC in Jira.**
The Jira MCP may not be parsing your AC field. Verify by running `/qa-research PROJECT-X` and looking at the Test Surface Map - if the `## Acceptance Criteria` section is empty or contains the `⚠️ NO AC FOUND` warning, the AC isn't reaching the agent. Check that the MCP is connected and that AC lives in a field the integration reads (commonly the description or a custom AC field).

**The pipeline keeps re-running phases that already completed.**
Check `.claude/qa/<TICKET>-surface-map.md` exists with `# Status: COMPLETE` at the top. If the status is `INCOMPLETE`, the previous run was interrupted and resume correctly discards the partial work. If the status header is missing entirely, there may have been a write error - re-run from scratch with `/qa <TICKET> --force`.

**The agent generated a Mermaid diagram with components I don't recognise.**
That's the failure mode `architecture-mapping.md` warns about - the agent guessed at structure rather than asking. Re-run `/qa-research <TICKET>` and provide an architecture description in the prompt: `/qa-research PROJECT-X - the consumers of the OrderCreated event are PaymentService and EmailService`.

**The Validation Report says PASS but I want to verify.**
Open `.claude/qa/<TICKET>-validation-report.md`. The raw test output is attached in full - that's the evidence layer. A PASS without raw output is a bug; report it via the thumbs-down in Claude Code.

## Learn more

- **[MAINTAINERS.md](MAINTAINERS.md)** - internal structure, design decisions, version history. Read this if you want to modify how the agent works
- **`skills/quality-engineer/SKILL.md`** - the doctrine the agent applies. Worth a read to understand what the agent is trying to do
- **`skills/quality-engineer/references/`** - deep references the agent loads on demand (intake workflow, observability checklist, MCP playbook, anti-rationalizations, architecture mapping, output templates, exhaustive tier checks)
