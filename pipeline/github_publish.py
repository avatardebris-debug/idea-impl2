"""
Per-project git + optional GitHub publish for pipeline project folders.

Default: local git commit of whole projects/<slug>/ (workspace + state + phases).
Push to GitHub only when PIPELINE_GITHUB_PUBLISH=1.

Non-essential: failures never raise to callers of maybe_publish_project.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool
from pipeline.paths import project_dir as default_project_dir

# Default triggers (complete + field_proven)
_DEFAULT_ON = frozenset({"complete", "field_proven"})

_GITIGNORE = """\
# Pipeline project publish — keep secrets and junk out of remotes
.env
.env.*
!.env.example
**/.venv/
**/venv/
**/__pycache__/
**/*.py[cod]
**/.pytest_cache/
**/.mypy_cache/
**/.ruff_cache/
**/*.egg-info/
**/dist/
**/build/
**/.DS_Store
**/Thumbs.db
**/*.pem
**/*.key
**/node_modules/
"""


@dataclass
class PublishResult:
    ok: bool = True
    skipped: bool = False
    local_only: bool = True
    slug: str = ""
    trigger: str = ""
    sha: str = ""
    url: str = ""
    repo_name: str = ""
    error: str = ""
    message: str = ""
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def publish_enabled() -> bool:
    return env_bool("PIPELINE_GITHUB_PUBLISH", default=False)


def publish_triggers() -> frozenset[str]:
    raw = os.environ.get("PIPELINE_GITHUB_ON", "complete,field_proven").strip()
    if not raw:
        return _DEFAULT_ON
    return frozenset(p.strip().lower() for p in raw.split(",") if p.strip())


def github_org() -> str:
    return os.environ.get("PIPELINE_GITHUB_ORG", "").strip()


def repo_prefix() -> str:
    return os.environ.get("PIPELINE_GITHUB_REPO_PREFIX", "pipe-").strip()


def repo_visibility() -> str:
    v = os.environ.get("PIPELINE_GITHUB_VISIBILITY", "private").strip().lower()
    return v if v in ("private", "public") else "private"


def repo_name_for_slug(slug: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-._") or "project"
    return f"{repo_prefix()}{safe}"


def _git(
    *args: str, cwd: Path, check: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def _commit_env() -> dict[str, str]:
    """Identity for commits without requiring global git config."""
    env = os.environ.copy()
    author = os.environ.get("GIT_COMMIT_AUTHOR", "").strip()
    name = os.environ.get("GIT_COMMIT_NAME", os.environ.get("GIT_AUTHOR_NAME", "")).strip()
    email = os.environ.get(
        "GIT_COMMIT_EMAIL", os.environ.get("GIT_AUTHOR_EMAIL", "")
    ).strip()
    if author and "<" in author and ">" in author:
        # "Name <email>"
        try:
            name_part, rest = author.rsplit("<", 1)
            name = name_part.strip() or name
            email = rest.rstrip(">").strip() or email
        except ValueError:
            pass
    if not name:
        name = "Pipeline Publisher"
    if not email:
        email = "pipeline@localhost"
    env.setdefault("GIT_AUTHOR_NAME", name)
    env.setdefault("GIT_AUTHOR_EMAIL", email)
    env.setdefault("GIT_COMMITTER_NAME", name)
    env.setdefault("GIT_COMMITTER_EMAIL", email)
    return env


def _git_env(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_commit_env(),
        check=False,
    )


def status_path(project: Path) -> Path:
    return project / "state" / "github_status.json"


def write_status(project: Path, result: PublishResult, extra: dict | None = None) -> None:
    path = status_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict()
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    if extra:
        payload.update(extra)
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def ensure_gitignore(project: Path) -> None:
    gi = project / ".gitignore"
    if gi.is_file():
        return
    try:
        gi.write_text(_GITIGNORE, encoding="utf-8")
    except OSError:
        pass


def ensure_readme_hint(project: Path, slug: str) -> None:
    """Add a short root README if missing so clone visitors know layout."""
    readme = project / "README.md"
    if readme.is_file():
        return
    title = slug
    desc = ""
    idea = project / "state" / "current_idea.json"
    if idea.is_file():
        try:
            data = json.loads(idea.read_text(encoding="utf-8"))
            title = data.get("title") or title
            desc = (data.get("description") or "")[:500]
        except Exception:
            pass
    body = (
        f"# {title}\n\n"
        f"{desc}\n\n"
        f"## Layout\n\n"
        f"- `workspace/` — runnable product code\n"
        f"- `state/` — pipeline idea state and plans\n"
        f"- `phases/` — phase tasks, reviews, ship field tests\n\n"
        f"_Published from the idea-impl pipeline (slug: `{slug}`)._\n"
    )
    try:
        readme.write_text(body, encoding="utf-8")
    except OSError:
        pass


def ensure_local_git(project: Path, *, slug: str, message: str) -> PublishResult:
    """Init (if needed), commit whole project tree. Returns result with sha."""
    result = PublishResult(ok=True, local_only=True, slug=slug, message=message)
    if not project.is_dir():
        result.ok = False
        result.error = f"project dir missing: {project}"
        return result

    ensure_gitignore(project)
    ensure_readme_hint(project, slug)

    git_dir = project / ".git"
    if not git_dir.exists():
        init = _git("init", "-b", "main", cwd=project)
        if init.returncode != 0:
            # older git: init then checkout -b main
            init = _git("init", cwd=project)
            if init.returncode != 0:
                result.ok = False
                result.error = (init.stderr or init.stdout or "git init failed").strip()
                return result
            _git("checkout", "-b", "main", cwd=project)
        result.details.append("git init")

    add = _git("add", "-A", cwd=project)
    if add.returncode != 0:
        result.ok = False
        result.error = (add.stderr or add.stdout or "git add failed").strip()
        return result

    status = _git("status", "--porcelain", cwd=project)
    if not (status.stdout or "").strip():
        rev = _git("rev-parse", "HEAD", cwd=project)
        if rev.returncode == 0:
            result.sha = rev.stdout.strip()
            result.details.append("nothing to commit")
            result.message = "clean working tree"
            return result
        # empty repo with no commits yet — allow empty? create .gitkeep
        keep = project / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
            _git("add", "-A", cwd=project)

    commit = _git_env("commit", "-m", message, cwd=project)
    out = (commit.stdout or "") + (commit.stderr or "")
    if commit.returncode != 0 and "nothing to commit" not in out.lower():
        result.ok = False
        result.error = out.strip() or "git commit failed"
        return result

    rev = _git("rev-parse", "HEAD", cwd=project)
    if rev.returncode == 0:
        result.sha = rev.stdout.strip()
    result.details.append("committed")
    return result


def _remote_url(project: Path) -> str:
    r = _git("remote", "get-url", "origin", cwd=project)
    if r.returncode == 0:
        return (r.stdout or "").strip()
    return ""


def _gh_available() -> bool:
    try:
        p = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return p.returncode == 0
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return False


def push_to_github(project: Path, *, slug: str, result: PublishResult) -> PublishResult:
    """Ensure remote + push. Mutates and returns result."""
    result.local_only = False
    org = github_org()
    name = repo_name_for_slug(slug)
    result.repo_name = name
    vis = repo_visibility()

    if not org:
        result.ok = False
        result.error = "PIPELINE_GITHUB_ORG is not set"
        return result

    full = f"{org}/{name}"
    existing = _remote_url(project)

    if not existing:
        if _gh_available():
            create = subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    full,
                    f"--{vis}",
                    "--source",
                    str(project),
                    "--remote",
                    "origin",
                    "--push",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(project),
                check=False,
                env=_commit_env(),
            )
            if create.returncode == 0:
                result.url = f"https://github.com/{full}"
                result.details.append("gh repo create --push")
                result.message = f"published {full}"
                result.ok = True
                return result
            # repo may already exist
            err = (create.stderr or create.stdout or "").strip()
            result.details.append(f"gh create: {err[:200]}")
            # fall through to set remote + push
            url = f"https://github.com/{full}.git"
            _git("remote", "add", "origin", url, cwd=project)
        else:
            token = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", "")).strip()
            if token:
                url = f"https://x-access-token:{token}@github.com/{full}.git"
            else:
                url = f"https://github.com/{full}.git"
            add_r = _git("remote", "add", "origin", url, cwd=project)
            if add_r.returncode != 0 and "already exists" not in (
                add_r.stderr or ""
            ).lower():
                # try set-url
                _git("remote", "set-url", "origin", url, cwd=project)
            if not token and not _gh_available():
                result.ok = False
                result.error = (
                    "no gh CLI and no GITHUB_TOKEN; cannot create/push remote. "
                    "Install GitHub CLI or set GITHUB_TOKEN + create repo manually."
                )
                return result

    # Push (repo assumed to exist or was created)
    branch = "main"
    br = _git("rev-parse", "--abbrev-ref", "HEAD", cwd=project)
    if br.returncode == 0 and br.stdout.strip():
        branch = br.stdout.strip()

    push = _git_env("push", "-u", "origin", branch, cwd=project)
    if push.returncode != 0:
        # try create via API if push failed for missing repo
        err = (push.stderr or push.stdout or "").strip()
        if _gh_available() and (
            "repository not found" in err.lower() or "not found" in err.lower()
        ):
            create2 = subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    full,
                    f"--{vis}",
                    "--source",
                    str(project),
                    "--remote",
                    "origin",
                    "--push",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(project),
                check=False,
                env=_commit_env(),
            )
            if create2.returncode == 0:
                result.url = f"https://github.com/{full}"
                result.ok = True
                result.message = f"published {full}"
                return result
            result.ok = False
            result.error = (create2.stderr or create2.stdout or err).strip()[:500]
            return result
        result.ok = False
        result.error = err[:500] or "git push failed"
        return result

    result.url = f"https://github.com/{full}"
    result.ok = True
    result.message = f"pushed {full}"
    result.details.append("git push")
    return result


def publish_project(
    slug: str,
    *,
    trigger: str,
    project_path: Path | None = None,
    force_push: bool | None = None,
) -> PublishResult:
    """
    Commit whole project dir; push if publish enabled (or force_push=True).

    force_push=None → use PIPELINE_GITHUB_PUBLISH
    force_push=True/False → override env for CLI
    """
    trigger = (trigger or "").strip().lower()
    project = project_path or default_project_dir(slug)
    msg = f"pipeline: {slug} ({trigger}) {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"

    result = ensure_local_git(project, slug=slug, message=msg)
    result.trigger = trigger
    if not result.ok:
        write_status(project, result)
        return result

    do_push = publish_enabled() if force_push is None else force_push
    if not do_push:
        result.local_only = True
        result.message = result.message or "local git only (PIPELINE_GITHUB_PUBLISH off)"
        write_status(project, result)
        return result

    result = push_to_github(project, slug=slug, result=result)
    write_status(project, result)
    return result


def maybe_publish_project(slug: str, *, trigger: str) -> PublishResult | None:
    """
    Hook for complete / field_proven. Always local-commits when trigger matches;
    pushes only if PIPELINE_GITHUB_PUBLISH=1.

    Returns None if trigger not configured; never raises.
    """
    try:
        trig = (trigger or "").strip().lower()
        if trig not in publish_triggers():
            return None
        result = publish_project(slug, trigger=trig)
        if result.ok:
            if result.url:
                print(f"  [github] {slug} → {result.url} ({result.sha[:8] if result.sha else '?'})")
            else:
                print(
                    f"  [github] {slug} local commit {result.sha[:8] if result.sha else '?'} "
                    f"({result.message or 'ok'})"
                )
        else:
            print(f"  [github] {slug} publish issue: {result.error or result.message}")
        return result
    except Exception as exc:
        print(f"  [github] {slug} skipped (non-critical): {exc}")
        return PublishResult(ok=False, slug=slug, trigger=trigger, error=str(exc))


def list_eligible_slugs(
    *,
    statuses: frozenset[str] | None = None,
    projects_root: Path | None = None,
) -> list[str]:
    from pipeline.paths import projects_dir

    root = projects_root or projects_dir()
    want = statuses or publish_triggers()
    found: list[str] = []
    if not root.is_dir():
        return found
    for p in sorted(root.iterdir()):
        if not p.is_dir() or p.name.startswith("."):
            continue
        sf = p / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8")).get("status", "")
        except Exception:
            continue
        if st in want:
            found.append(p.name)
    return found
