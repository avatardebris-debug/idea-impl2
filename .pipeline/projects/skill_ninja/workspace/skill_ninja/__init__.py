"""
skill_ninja — Container CLI that chains summarizer → extraction → skillify in one command.

Also acts as the public dispatcher for loading and running JSON skill files.

Usage:
    # Full pipeline: text → extraction → skill file
    python -m skill_ninja build article.txt --topic "sourdough" --output skills/sourdough.json

    # Run a skill interactively
    python -m skill_ninja run skills/sourdough.json

    # List skills in a library directory
    python -m skill_ninja list skills/

    # Inspect a skill
    python -m skill_ninja show skills/sourdough.json
"""
__version__ = "0.1.0"
