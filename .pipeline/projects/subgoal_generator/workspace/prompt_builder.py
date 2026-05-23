"""Build an LLM-ready prompt from a high-level goal."""


def build_prompt(goal: str) -> str:
    """Return a prompt that instructs the LLM to decompose *goal* into subgoals.

    The LLM is expected to respond in a structured format:
    Each subgoal on its own block with:
      title: <string>
      description: <string>
      dependencies: [list of titles]
    """
    return (
        f"Decompose the following high-level goal into a list of ordered, actionable subgoals.\n\n"
        f"Goal: {goal}\n\n"
        "For each subgoal, provide:\n"
        "  title: <short title>\n"
        "  description: <one-sentence description>\n"
        "  dependencies: [list of subgoal titles this depends on, or empty list]\n"
        "  priority: <integer 1-5, 1 being highest priority>\n\n"
        "Rules:\n"
        "- Order subgoals logically (earlier subgoals should come first).\n"
        "- Dependencies must reference titles of earlier subgoals.\n"
        "- Include at least 3 subgoals.\n\n"
        "Output each subgoal block separated by a blank line.\n"
    )
