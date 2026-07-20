"""Load Grok skill markdown for pipeline injection (not TUI auto-invoke).

Skills may live in:
  - ~/.grok/skills/<name>/SKILL.md          (user)
  - ~/.grok/bundled/skills/<name>/SKILL.md
  - ~/.grok/installed-plugins/*/skills/<name>/SKILL.md
  - <factory>/.grok/skills/<name>/SKILL.md  (project)

Pipeline agents do not auto-load Superpowers; call load_skill_body() and inject.
"""

from __future__ import annotations

import os
from pathlib import Path

_GROK_HOME = Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))


def skill_search_roots() -> list[Path]:
    roots: list[Path] = []
    # Project (factory) skills
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        roots.append(PROJECT_ROOT / ".grok" / "skills")
    except Exception:
        pass
    roots.append(_GROK_HOME / "skills")
    roots.append(_GROK_HOME / "bundled" / "skills")
    plugins = _GROK_HOME / "installed-plugins"
    if plugins.is_dir():
        for plug in sorted(plugins.iterdir()):
            sk = plug / "skills"
            if sk.is_dir():
                roots.append(sk)
    return roots


def find_skill_dir(name: str) -> Path | None:
    name = (name or "").strip().lower().replace("_", "-")
    if not name:
        return None
    for root in skill_search_roots():
        if not root.is_dir():
            continue
        # direct child
        cand = root / name
        if (cand / "SKILL.md").is_file():
            return cand
        # plugin layout: root is already .../skills
        if root.name == "skills" and (root / name / "SKILL.md").is_file():
            return root / name
        # nested: installed-plugins/X/skills/name
        for p in root.rglob("SKILL.md"):
            if p.parent.name.lower() == name:
                return p.parent
    return None


def load_skill_body(name: str, *, max_chars: int = 12000) -> str:
    """Return skill markdown body (frontmatter stripped), or empty string."""
    d = find_skill_dir(name)
    if d is None:
        return ""
    path = d / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    # Strip YAML frontmatter
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            text = text[end + 4 :].lstrip("\n")
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n…(skill truncated for context)…\n"
    return text


def skill_available(name: str) -> bool:
    return find_skill_dir(name) is not None
