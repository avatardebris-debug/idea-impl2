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
    "required": [...]
  },
  "steps": [
    {"step": 1, "action": str, "detail": str, "tools": [...], "warnings": [...]}
  ],
  "components": [...],   // ingredients/materials if applicable
  "tips": [...],
  "source": {
    "format": "recipe|steps|sop",
    "extracted_at": "ISO8601",
    "model": "model_name"
  }
}
"""
__version__ = "0.1.0"
