#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["anthropic"]
# ///
"""
Eval runner for the quality-engineer skill.

Exercises each case in evals.json against the Claude API and produces a
report markdown file with the prompt, the response, the expected behaviour,
and (optionally) an LLM-judged pass/fail.

Usage:
    # With uv (recommended - no install step needed, isolated per run):
    uv run run_evals.py
    uv run run_evals.py --judge
    uv run run_evals.py --dry-run

    # With pip (traditional):
    pip install anthropic
    python3 run_evals.py

    # Manual review mode - default. Sends prompts, collects responses, writes
    # a markdown report you review yourself.
    uv run run_evals.py

    # With LLM-judge - a separate Claude call evaluates each response against
    # expected_behaviour and returns pass/fail/unclear with a one-line reason.
    uv run run_evals.py --judge

    # Dry run - prints what would be sent without making API calls. Useful for
    # inspecting the loaded skill content before spending tokens.
    uv run run_evals.py --dry-run

    # Subset by category or id
    uv run run_evals.py --category "triggering - positive"
    uv run run_evals.py --id trigger-pr-review

Environment:
    ANTHROPIC_API_KEY    Required for non-dry-run modes
    CLAUDE_MODEL         Optional, defaults to claude-opus-4-7
                         (judge always runs on a smaller/cheaper model)

Output:
    Writes ./eval-report-<timestamp>.md alongside the script.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import sys
import time
from typing import Any

# -------- Configuration ----------------------------------------------------

SKILL_DIR = pathlib.Path(__file__).parent.parent  # skills/quality-engineer/
PLUGIN_ROOT = SKILL_DIR.parent.parent              # plugin root (qa-engineer/)
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-7")
JUDGE_MODEL = "claude-haiku-4-5-20251001"          # cheaper for judging

# Files that constitute the loaded skill context for an eval prompt.
# We mirror what Claude would actually have available when the skill triggers:
# the SKILL.md plus the relevant reference files. The runner does NOT eagerly
# load all references - that would distort the test, since real triggering
# only loads SKILL.md and lets the model pull references on demand. So we
# load SKILL.md only, and include a system-prompt note that references exist
# at the documented paths.

SKILL_FILE = SKILL_DIR / "SKILL.md"
EVALS_FILE = SKILL_DIR / "evals" / "evals.json"


# -------- API client wrapper -----------------------------------------------

def make_api_call(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    """Wraps the Anthropic Messages API. Returns the raw response dict, or
    {"error": "..."} if the call failed. Lazy import so --dry-run works
    without the SDK installed.
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            "error": "anthropic SDK not installed. Run: pip install anthropic"
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    client = Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        # Convert to dict for serialization
        return {
            "content": "".join(
                block.text for block in response.content if block.type == "text"
            ),
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


# -------- Skill loading ----------------------------------------------------

def load_skill_context() -> str:
    """Load SKILL.md as the system prompt. Adds a note about references
    available on demand, mirroring how the real Claude environment exposes
    progressive disclosure.
    """
    if not SKILL_FILE.exists():
        raise FileNotFoundError(f"Skill not found at {SKILL_FILE}")

    skill_content = SKILL_FILE.read_text()

    # List reference files so the model knows what it could read on demand.
    refs_dir = SKILL_DIR / "references"
    refs = sorted(refs_dir.glob("*.md")) if refs_dir.exists() else []
    refs_list = "\n".join(f"  - {r.relative_to(PLUGIN_ROOT)}" for r in refs)

    system_prompt = (
        f"{skill_content}\n\n"
        f"---\n\n"
        f"## Reference files available on demand\n\n"
        f"These files exist in the skill bundle and you may reference them by path "
        f"when their content is needed. The runner does not pre-load them - "
        f"behave as you would in a real session:\n\n"
        f"{refs_list}\n"
    )

    return system_prompt


# -------- LLM-judge --------------------------------------------------------

JUDGE_SYSTEM = """\
You are an evaluation judge for a Claude skill. You will receive:
- A user prompt that was sent to a model
- The model's response
- The expected behaviour for this prompt

Your job is to decide if the response matched the expected behaviour, using a
strict but charitable reading. Be specific about WHY it passed or failed.

Output JSON ONLY in this exact shape, nothing else:
{
  "verdict": "pass" | "fail" | "unclear",
  "reason": "one-sentence explanation citing specific evidence from the response"
}

- "pass": the response demonstrably exhibits the expected behaviour
- "fail": the response demonstrably contradicts the expected behaviour
- "unclear": the response is ambiguous or partial - neither clearly matches nor contradicts
"""


def judge_response(prompt: str, response: str, expected: str, model: str) -> dict[str, Any]:
    """Run a separate Claude call to judge the response against expected."""
    judge_prompt = (
        f"# Prompt sent to model\n{prompt}\n\n"
        f"# Model's response\n{response}\n\n"
        f"# Expected behaviour\n{expected}\n\n"
        f"Output your verdict as JSON only."
    )
    result = make_api_call(JUDGE_SYSTEM, judge_prompt, model)
    if "error" in result:
        return {"verdict": "unclear", "reason": f"judge error: {result['error']}"}

    raw = result["content"].strip()
    # Strip code fences if the judge wrapped them
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        parsed = json.loads(raw)
        if parsed.get("verdict") not in ("pass", "fail", "unclear"):
            return {"verdict": "unclear", "reason": f"unexpected verdict shape: {raw[:100]}"}
        return parsed
    except json.JSONDecodeError:
        return {"verdict": "unclear", "reason": f"non-JSON judge output: {raw[:100]}"}


# -------- Report writer ----------------------------------------------------

def write_report(results: list[dict[str, Any]], with_judge: bool, model: str, output_path: pathlib.Path) -> None:
    """Write a markdown report of all results."""
    total = len(results)
    passed = sum(1 for r in results if r.get("judge", {}).get("verdict") == "pass")
    failed = sum(1 for r in results if r.get("judge", {}).get("verdict") == "fail")
    unclear = sum(1 for r in results if r.get("judge", {}).get("verdict") == "unclear")
    errored = sum(1 for r in results if "error" in r)

    total_input = sum(r.get("usage", {}).get("input_tokens", 0) for r in results)
    total_output = sum(r.get("usage", {}).get("output_tokens", 0) for r in results)

    lines = [
        f"# Eval Report: quality-engineer",
        f"",
        f"- Run at: {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"- Model: `{model}`",
        f"- Judge enabled: {with_judge}",
        f"- Cases run: {total}",
    ]
    if with_judge:
        lines.append(f"- Pass / Fail / Unclear: {passed} / {failed} / {unclear}")
    if errored:
        lines.append(f"- Errored: {errored}")
    lines.extend([
        f"- Token usage: {total_input} in / {total_output} out",
        f"",
        f"---",
        f"",
    ])

    for r in results:
        case = r["case"]
        lines.append(f"## {case['id']}")
        lines.append(f"")
        lines.append(f"**Category:** {case['category']}")
        lines.append(f"")
        lines.append(f"**Prompt:**")
        lines.append(f"")
        lines.append(f"> {case['prompt']}")
        lines.append(f"")
        lines.append(f"**Expected behaviour:** {case['expected_behaviour']}")
        lines.append(f"")

        if "error" in r:
            lines.append(f"**Status:** ⚠️ ERROR - `{r['error']}`")
        else:
            if with_judge:
                v = r["judge"]["verdict"]
                emoji = {"pass": "✅", "fail": "❌", "unclear": "❓"}[v]
                lines.append(f"**Judge verdict:** {emoji} {v.upper()} - {r['judge']['reason']}")
                lines.append(f"")
            lines.append(f"**Response:**")
            lines.append(f"")
            # Indent response as blockquote
            for line in r["response"].splitlines():
                lines.append(f"> {line}")
            lines.append(f"")
            usage = r.get("usage", {})
            if usage:
                lines.append(f"*tokens: {usage.get('input_tokens', '?')} in / {usage.get('output_tokens', '?')} out*")

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    output_path.write_text("\n".join(lines))


# -------- Main -------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--judge", action="store_true", help="Use a second Claude call to judge each response")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent, do not call the API")
    parser.add_argument("--category", help="Run only cases matching this category substring")
    parser.add_argument("--id", dest="case_id", help="Run only the case with this id")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model for eval prompts (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", help="Path for the report markdown (default: ./eval-report-<timestamp>.md)")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds to wait between API calls (rate limit)")
    args = parser.parse_args()

    # Load evals
    if not EVALS_FILE.exists():
        print(f"error: evals file not found at {EVALS_FILE}", file=sys.stderr)
        return 2
    evals = json.loads(EVALS_FILE.read_text())
    cases = evals["cases"]

    # Filter
    if args.case_id:
        cases = [c for c in cases if c["id"] == args.case_id]
        if not cases:
            print(f"error: no case with id '{args.case_id}'", file=sys.stderr)
            return 2
    if args.category:
        cases = [c for c in cases if args.category.lower() in c["category"].lower()]
        if not cases:
            print(f"error: no cases matching category '{args.category}'", file=sys.stderr)
            return 2

    # Build system prompt
    try:
        system_prompt = load_skill_context()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"Loaded skill: {SKILL_FILE} ({len(system_prompt):,} chars)")
    print(f"Cases to run: {len(cases)}")
    if args.dry_run:
        print(f"\n--- DRY RUN - no API calls will be made ---\n")
        for c in cases:
            print(f"  [{c['id']}] ({c['category']})")
            print(f"    prompt: {c['prompt']}")
            print(f"    expected: {c['expected_behaviour'][:80]}{'...' if len(c['expected_behaviour']) > 80 else ''}")
            print()
        return 0

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("error: ANTHROPIC_API_KEY not set. Use --dry-run to inspect without an API call.", file=sys.stderr)
        return 2

    # Run
    results = []
    for i, case in enumerate(cases, start=1):
        print(f"[{i}/{len(cases)}] {case['id']} ... ", end="", flush=True)
        api_result = make_api_call(system_prompt, case["prompt"], args.model)

        if "error" in api_result:
            print(f"ERROR: {api_result['error']}")
            results.append({"case": case, "error": api_result["error"]})
        else:
            entry = {
                "case": case,
                "response": api_result["content"],
                "usage": api_result.get("usage", {}),
                "stop_reason": api_result.get("stop_reason"),
            }
            if args.judge:
                judge_verdict = judge_response(
                    case["prompt"], api_result["content"], case["expected_behaviour"], JUDGE_MODEL
                )
                entry["judge"] = judge_verdict
                print(f"{judge_verdict['verdict']}")
            else:
                print("done")
            results.append(entry)

        if args.delay and i < len(cases):
            time.sleep(args.delay)

    # Write report
    if args.output:
        output_path = pathlib.Path(args.output)
    else:
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = pathlib.Path(f"./eval-report-{ts}.md")

    write_report(results, args.judge, args.model, output_path)
    print(f"\nReport: {output_path}")

    # Exit code reflects pass rate when judge ran
    if args.judge:
        failed = sum(1 for r in results if r.get("judge", {}).get("verdict") == "fail")
        if failed:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
