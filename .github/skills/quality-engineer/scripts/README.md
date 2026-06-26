# Skill scripts

Helpers for working with the `quality-engineer` skill.

## `run_evals.py`

Runs the cases in `../evals/evals.json` against the Claude API and writes a markdown report you can review (or have judged automatically).

### Prerequisites

Two options for managing the one dependency (`anthropic` SDK):

**uv (recommended)** - no install step, isolated per run, reads the inline metadata in `run_evals.py`:

```bash
uv run run_evals.py --judge
```

**pip (traditional)** - installs into your active environment:

```bash
pip install anthropic
python3 run_evals.py --judge
```

Either way, set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Usage

```bash
# Inspect what would run without spending tokens
uv run run_evals.py --dry-run

# Run all 20 cases, write a manual-review report
uv run run_evals.py

# Run with LLM-judge - a second Claude call evaluates each response
uv run run_evals.py --judge

# Filter by category or id
uv run run_evals.py --category "triggering - negative"
uv run run_evals.py --id trigger-pr-review

# Use a different model
uv run run_evals.py --model claude-sonnet-4-6

# Faster runs by reducing the inter-call delay
uv run run_evals.py --delay 0
```

(Substitute `python3 run_evals.py` for `uv run run_evals.py` if you installed via pip.)

### What it produces

A markdown report (`eval-report-<timestamp>.md`) with one section per case containing the prompt, the response, the expected behaviour, token usage, and (if `--judge`) a pass/fail/unclear verdict with reasoning.

### When to run

- **After changing the skill description** - to catch triggering regressions
- **After changing doctrine in SKILL.md or any agent** - to catch behaviour regressions
- **After adding new cases to evals.json** - to baseline before doctrine changes
- **Before publishing a new version of the plugin**

### Limits

- The runner loads `SKILL.md` as the system prompt, plus a listing of reference files. It does *not* eagerly load references - that would distort what the model actually sees in production, where references load on demand
- The LLM-judge is fallible. Treat `unclear` verdicts as "needs human review" and re-read suspect `pass`/`fail` cases manually
- Cases involving `/qa <ticket>` invocations can't fully run from a single prompt - they need the slash command resolution. Treat those as smoke tests for the skill's tier-awareness rather than full pipeline tests
- The runner makes one API call per case (two if `--judge`). For 20 cases with judge, expect ~40 API calls - budget tokens accordingly
