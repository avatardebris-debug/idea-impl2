"""
skillify — Turn extraction output into a Claude skill / JSON skill file.

Input:  extraction dict (from extraction.extractor.extract())
Output: JSON skill file usable by the skill_ninja dispatcher

Skill schema (compatible with Claude skill format + local JSON dispatcher):
{
  "skill_id":    "unique_snake_case_id",
  "name":        "Human Readable Name",
  "version":     "1.0.0",
  "description": "What this skill does",
  "tags":        ["category", "type"],
  "parameters":  {
    "type": "object",
    "properties": { ... },
    "required":  [ ... ]
  },
  "system_prompt": "You are a helpful assistant...",
  "functions": [
    {
      "name":        "execute_skill",
      "description": "Execute the skill with given parameters",
      "parameters":  { ... }
    }
  ],
  "examples": [
    {
      "input":  { "components": [...], "context": "...", "target_output": "..." },
      "output": { "result": "..." }
    }
  ]
}
"""

__version__ = "0.1.0"

from skillify.converter import convert, save_skill, load_skill

__all__ = ["convert", "save_skill", "load_skill"]
