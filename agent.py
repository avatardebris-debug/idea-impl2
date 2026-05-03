"""
agent.py
The main agent loop — model-agnostic, file-tree-first.

Usage:
    python agent.py "Write a Python script that prints hello world"
    python agent.py "Write a Python script" --provider claude
    python agent.py "Write a Python script" --provider ollama --model llama3
    python agent.py "Write a Python script" --provider openai --model gpt-4o --max-steps 15
"""

from __future__ import annotations
import argparse
import json
import pathlib
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime

from llm_interface import get_llm, Message
from tools import TOOLS, TOOL_SCHEMAS, read_file, list_tree
from governance import GovernanceGate, AffirmationSystem, load_constitution
# reflection module archived — derived values section gracefully disabled

# ---------------------------------------------------------------------------
# Agent directory bootstrap
# ---------------------------------------------------------------------------

AGENT_DIR = pathlib.Path(".agent")


def bootstrap_agent_dir() -> None:
    """Create the .agent file tree skeleton if it doesn't exist."""
    (AGENT_DIR / "memory").mkdir(parents=True, exist_ok=True)
    (AGENT_DIR / "tool_outputs").mkdir(parents=True, exist_ok=True)

    facts_path = AGENT_DIR / "memory" / "facts.md"
    if not facts_path.exists():
        facts_path.write_text("# Agent Memory — Facts\n", encoding="utf-8")

    decisions_path = AGENT_DIR / "memory" / "decisions.md"
    if not decisions_path.exists():
        decisions_path.write_text("# Agent Memory — Decisions\n", encoding="utf-8")

    tasks_path = AGENT_DIR / "tasks.md"
    if not tasks_path.exists():
        tasks_path.write_text("# Tasks\n\n- [ ] (no tasks yet)\n", encoding="utf-8")

    plan_path = AGENT_DIR / "plan.md"
    if not plan_path.exists():
        plan_path.write_text("# Plan\n\n(no plan yet)\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def build_system_prompt(affirmation: AffirmationSystem | None = None,
                       pipeline_mode: bool = False) -> str:
    """Build the system prompt for the agent.

    Args:
        pipeline_mode: If True, skip the workspace file tree, shared .agent/
            memory, and plan/task files.  Pipeline agents get their own
            per-project context injected via build_context() — the repo-wide
            file tree just wastes tokens and confuses the LLM.
    """
    # Build constitution governance section (always included)
    constitution_prompt = ""
    try:
        from governance import load_constitution
        const = load_constitution()
        rules = []
        for k, v in const.get("negative_imperatives", {}).items():
            desc = v.get("description", "") if isinstance(v, dict) else str(v)
            if desc:
                rules.append(f"- NEVER: {desc.strip()}")
        for perm in const.get("permissions", {}).get("deny", []):
            rules.append(f"- BLOCKED: {perm}")
        if rules:
            constitution_prompt = "\n## Governance Rules (from constitution)\n" + "\n".join(rules)
    except Exception:
        pass

    if pipeline_mode:
        # Minimal prompt — pipeline agents get context from their own prompts
        return textwrap.dedent(f"""
            You are an autonomous AI agent that works by reading and writing files.

            ## Rules
            1. Think step by step before acting.
            2. Use `list_tree` to explore directories before reading files.
            3. When you are finished, say "DONE" and summarise what you accomplished.
            4. Do NOT fabricate file contents — always read files before editing them.
            {constitution_prompt}
        """).strip()

    # Full prompt for standalone agent usage
    tree = list_tree(".")

    try:
        memory = read_file(str(AGENT_DIR / "memory" / "facts.md"))
    except Exception:
        memory = "(none)"

    try:
        tasks = read_file(str(AGENT_DIR / "tasks.md"))
    except Exception:
        tasks = "(none)"

    try:
        plan = read_file(str(AGENT_DIR / "plan.md"))
    except Exception:
        plan = "(none)"

    return textwrap.dedent(f"""
        You are an autonomous AI agent that works by reading and writing files.

        ## Your Workspace File Tree
        {tree}

        ## Your Persistent Memory (facts.md)
        {memory}

        ## Current Plan (.agent/plan.md)
        {plan}

        ## Current Tasks (.agent/tasks.md)
        {tasks}

        ## Rules
        1. Think step by step before acting.
        2. Always update `.agent/tasks.md` with a TODO list at the start of each task.
        3. Write your high-level plan to `.agent/plan.md`.
        4. Store important facts with `append_memory`.
        5. Log significant decisions with `log_decision`.
        6. Use `list_tree` to explore the workspace before reading files.
        7. When you are finished, say "DONE" and summarise what you accomplished.
        8. Do NOT fabricate file contents — always read files before editing them.
        {constitution_prompt}
    """).strip()



# ---------------------------------------------------------------------------
# Tool executor
# ---------------------------------------------------------------------------

def execute_tool(name: str, args: dict) -> str:
    fn = TOOLS.get(name)
    if fn is None:
        return f"ERROR: Unknown tool '{name}'"
    try:
        result = fn(**args)
        return str(result)
    except TypeError as e:
        return f"ERROR calling {name}: bad arguments — {e}"
    except Exception as e:
        return f"ERROR in {name}: {e}"


# ---------------------------------------------------------------------------
# Pretty printer
# ---------------------------------------------------------------------------

def print_step(label: str, content: str, color: str = "") -> None:
    RESET  = "\033[0m"
    COLORS = {"blue": "\033[94m", "green": "\033[92m",
               "yellow": "\033[93m", "red": "\033[91m", "cyan": "\033[96m"}
    c = COLORS.get(color, "")
    border = "─" * 60
    print(f"\n{c}{border}{RESET}")
    print(f"{c}  {label}{RESET}")
    print(f"{c}{border}{RESET}")
    if content:
        print(textwrap.indent(content[:2000], "  "))
        if len(content) > 2000:
            print(f"  ... ({len(content) - 2000} more chars)")


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Structured result from an agent run."""
    answer: str = ""
    steps_used: int = 0
    messages: list[dict] = field(default_factory=list)
    governance_stats: dict = field(default_factory=dict)
    completed: bool = False
    tokens_used: int = 0

    def __str__(self) -> str:
        return self.answer


def run_agent(
    task: str,
    provider: str = "openai",
    model: str | None = None,
    max_steps: int = 20,
    temperature: float = 0.7,
    think: bool | None = None,
    num_ctx: int = 16384,
    system_prompt_addon: str = "",
    verbose: bool = True,
    pipeline_mode: bool = False,
) -> AgentResult:
    bootstrap_agent_dir()
    llm = get_llm(provider, model, temperature=temperature, think=think, num_ctx=num_ctx)

    # --- Initialize governance ---
    constitution = load_constitution()
    gate = GovernanceGate(constitution)
    affirmation = AffirmationSystem(constitution)

    if verbose:
        gov_source = "AutoHarness" if gate._pipeline else "standalone"
        print_step("🤖 AGENT START",
            f"Task: {task}\nProvider: {provider}  Model: {model or 'default'}\n"
            f"Governance: {gov_source}  Constitution: {constitution.get('identity', {}).get('name', '?')}",
            "blue")

    # Log the task (skip in pipeline mode to avoid contaminating shared log)
    if not pipeline_mode:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        with pathlib.Path(".agent/memory/decisions.md").open("a", encoding="utf-8") as f:
            f.write(f"\n\n## Task received — {ts}\n{task}")

    system_prompt = build_system_prompt(affirmation, pipeline_mode=pipeline_mode)
    if system_prompt_addon:
        system_prompt += f"\n\n## Custom Profile Instructions\n{system_prompt_addon}"

    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": task},
    ]

    final_answer = ""
    total_tokens = 0

    for step in range(1, max_steps + 1):
        affirmation.tick()

        # --- Affirmation injection ---
        injection = affirmation.get_context_injection()
        if injection:
            if verbose:
                print_step("🔄 AFFIRMATION", injection[:500], "cyan")
            messages.append({
                "role": "system",
                "content": injection,
            })

        if verbose:
            print_step(f"⟳  STEP {step}/{max_steps}", "", "cyan")

        response: Message = llm.chat(messages, tools=TOOL_SCHEMAS)

        # Accumulate token usage
        if response.usage:
            total_tokens += response.usage.total_tokens

        # ── Agent wants to call tools ──────────────────────────────────────
        if response.tool_calls:
            # Add the assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {
                        "id": tc.get("id", f"call_{i}"),
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])},
                    }
                    for i, tc in enumerate(response.tool_calls)
                ],
            })

            for tc in response.tool_calls:
                name = tc["name"]
                args = tc["args"]

                # --- GOVERNANCE GATE ---
                decision = gate.evaluate(name, args)

                if decision.action == "deny":
                    if verbose:
                        print_step(f"⛔ BLOCKED: {name}", f"Reason: {decision.reason}", "red")
                    result = f"[GOVERNANCE] Tool call BLOCKED: {decision.reason}. Do not retry this operation."
                else:
                    if verbose:
                        risk_indicator = "" if decision.risk_level == "low" else f" ⚠️[{decision.risk_level}]"
                        print_step(f"🔧 TOOL: {name}{risk_indicator}", json.dumps(args, indent=2), "yellow")

                    result = execute_tool(name, args)

                    if verbose:
                        print_step(f"✅ RESULT: {name}", result, "green")

                # Append tool result (whether allowed or blocked)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_0"),
                    "name": name,
                    "content": result,
                })

        # ── Agent has a final text response ───────────────────────────────
        else:
            final_answer = response.content
            messages.append({"role": "assistant", "content": final_answer})
            if verbose:
                stats = gate.stats
                print_step("🏁 AGENT DONE",
                    f"{final_answer}\n\n--- Governance Stats ---\n"
                    f"Allowed: {stats['allowed']}  Blocked: {stats['blocked']}  "
                    f"Total: {stats['total']}",
                    "blue")
            break

    else:
        final_answer = f"Agent reached max steps ({max_steps}) without a final answer."
        if verbose:
            print_step("⚠️  MAX STEPS REACHED", final_answer, "red")

    return AgentResult(
        answer=final_answer,
        steps_used=step,
        messages=messages,
        governance_stats=gate.stats,
        completed="DONE" in final_answer.upper() if final_answer else False,
        tokens_used=total_tokens,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Model-agnostic file-tree AI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python agent.py "Write a hello world script"
              python agent.py "Analyse the files in workspace/ and summarise them" --provider claude
              python agent.py "Fix the bug in main.py" --provider ollama --model llama3
        """),
    )
    parser.add_argument("task", help="The task for the agent to complete")
    parser.add_argument(
        "--provider", default="openai",
        choices=["openai", "claude", "gemini", "ollama", "grok"],
        help="LLM provider to use (default: openai)",
    )
    parser.add_argument("--model", default=None, help="Model override (uses provider default if omitted)")
    parser.add_argument("--max-steps", type=int, default=20, help="Maximum tool-call steps (default: 20)")
    parser.add_argument("--quiet", action="store_true", help="Suppress step-by-step output")

    args = parser.parse_args()

    result = run_agent(
        task=args.task,
        provider=args.provider,
        model=args.model,
        max_steps=args.max_steps,
        verbose=not args.quiet,
    )

    if args.quiet:
        print(result.answer)


if __name__ == "__main__":
    main()
