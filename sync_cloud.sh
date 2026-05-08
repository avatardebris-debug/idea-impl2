#!/usr/bin/env bash
# sync_cloud.sh — Cloud-side sync: rescue stray files + pull latest code
# Usage: bash sync_cloud.sh
#
# IMPORTANT: This script NEVER overwrites .pipeline/ state from git.
# Cloud state is always treated as authoritative (it is newer).

set -euo pipefail

# Paths — quote carefully, "idea impl" has a space
PROJ_ROOT="/workspace/idea impl"
PIPELINE_DIR="$PROJ_ROOT/.pipeline"
STRAY_ROOT="/workspace/workspace"

echo "=== Stopping any running pipeline ==="
pkill -f "pipeline/runner.py" 2>/dev/null || true
sleep 1

echo ""
echo "=== Snapshotting .pipeline/ state (safety backup before git) ==="
# This protects master_plan.md and all state files from being lost
# if git reset --hard is needed. Backup lives outside the git tree.
BACKUP_DIR="/workspace/pipeline_backup_$(date +%Y%m%d_%H%M%S)"
cp -r "$PIPELINE_DIR" "$BACKUP_DIR" 2>/dev/null && echo "  Backup: $BACKUP_DIR" || echo "  (backup skipped — .pipeline not found)"


echo ""
echo "=== Rescuing stray files from /workspace/workspace/ ==="
if [ ! -d "$STRAY_ROOT" ]; then
    echo "  Nothing to rescue (/workspace/workspace/ does not exist)"
else
    found_any=0
    for stray_proj in "$STRAY_ROOT"/*/; do
        [ -d "$stray_proj" ] || continue
        slug=$(basename "$stray_proj")

        # Skip meta dirs
        case "$slug" in .pytest_cache|__pycache__|.ipynb_checkpoints) continue ;; esac

        proj_dir="$PIPELINE_DIR/projects/$slug"
        if [ ! -d "$proj_dir" ]; then
            echo "  ⚠  No matching project for '$slug' — skipping"
            continue
        fi

        target_ws="$proj_dir/workspace"
        mkdir -p "$target_ws"
        echo "  Rescuing '$slug' → $target_ws"
        found_any=1

        # Copy all source files (skip caches and the stray phases/ subdir)
        while IFS= read -r src; do
            # Strip stray_proj prefix to get relative path
            rel="${src#"$stray_proj"}"
            dst="$target_ws/$rel"
            dstdir=$(dirname "$dst")
            mkdir -p "$dstdir"
            if [ ! -f "$dst" ]; then
                cp "$src" "$dst"
                echo "    + $rel"
            elif [ "$src" -nt "$dst" ]; then
                cp "$src" "$dst"
                echo "    ~ $rel  (cloud newer)"
            fi
        done < <(find "$stray_proj" -maxdepth 6 -type f \
            ! -path "*/__pycache__/*" \
            ! -path "*/.pytest_cache/*" \
            ! -path "*/.ipynb_checkpoints/*" \
            ! -path "*/phases/*")

        # Copy phase reports (validation_report.md, review.md etc)
        phases_stray="$stray_proj/phases"
        if [ -d "$phases_stray" ]; then
            while IFS= read -r src; do
                rel="${src#"$phases_stray/"}"
                dst="$proj_dir/phases/$rel"
                dstdir=$(dirname "$dst")
                mkdir -p "$dstdir"
                if [ ! -f "$dst" ]; then
                    cp "$src" "$dst"
                    echo "    + phases/$rel"
                fi
            done < <(find "$phases_stray" -type f)
        fi

        # Also rescue files placed directly inside email_tool/phases inside the workspace
        inner_phases="$stray_proj/$slug/phases"
        if [ -d "$inner_phases" ]; then
            while IFS= read -r src; do
                rel="${src#"$inner_phases/"}"
                dst="$proj_dir/phases/$rel"
                dstdir=$(dirname "$dst")
                mkdir -p "$dstdir"
                if [ ! -f "$dst" ]; then
                    cp "$src" "$dst"
                    echo "    + phases/$rel  (from inner)"
                fi
            done < <(find "$inner_phases" -type f)
        fi
    done

    if [ "$found_any" -eq 0 ]; then
        echo "  /workspace/workspace/ exists but no matching projects found"
    fi
fi

echo ""
echo "=== Rescuing stray src/ and tests/ from project root ==="
# The LLM frequently writes to /workspace/idea impl/src/ instead of
# .pipeline/projects/<slug>/workspace/src/. Find the active project
# and move files there.
cd "$PROJ_ROOT"
for stray_name in src tests test; do
    stray_dir="$PROJ_ROOT/$stray_name"
    [ -d "$stray_dir" ] || continue

    # Find the most recently modified project to assign these files to
    active_slug=""
    active_mtime=0
    for proj in "$PIPELINE_DIR"/projects/*/state/current_idea.json; do
        [ -f "$proj" ] || continue
        slug=$(basename "$(dirname "$(dirname "$proj")")")
        st=$(python3 -c "import json; print(json.load(open('$proj')).get('status',''))" 2>/dev/null)
        case "$st" in
            phase_*) ;;  # active — check mtime
            *) continue ;;
        esac
        mtime=$(stat -c %Y "$proj" 2>/dev/null || echo 0)
        if [ "$mtime" -gt "$active_mtime" ]; then
            active_mtime=$mtime
            active_slug=$slug
        fi
    done

    if [ -z "$active_slug" ]; then
        echo "  ⚠  Stray $stray_name/ found but no active project to assign it to"
        continue
    fi

    target_ws="$PIPELINE_DIR/projects/$active_slug/workspace/$stray_name"
    mkdir -p "$target_ws"
    moved=0
    while IFS= read -r f; do
        rel="${f#"$stray_dir/"}"
        dst="$target_ws/$rel"
        mkdir -p "$(dirname "$dst")"
        if [ ! -f "$dst" ]; then
            cp "$f" "$dst"
            moved=$((moved + 1))
        fi
    done < <(find "$stray_dir" -type f ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*")
    echo "  Rescued $moved file(s) from $stray_name/ → $active_slug"
    rm -rf "$stray_dir"
done
echo ""
echo "=== Clearing queue messages ==="
cd "$PROJ_ROOT"
python -c "
from pipeline.message_bus import MessageBus
from pipeline.runner import AGENT_ROLES
bus = MessageBus()
cleared = sum(bus.clear_queue(r) for r in AGENT_ROLES)
print(f'  Cleared {cleared} messages')
"

echo ""
echo "=== Pulling latest CODE only (never overwrites .pipeline state) ==="
cd "$PROJ_ROOT"
git fetch origin

# SAFE approach: only update tracked non-.pipeline files.
# NEVER use 'git reset --hard' — it would wipe .pipeline/ if those
# files aren't committed (they never are on a fresh instance).
#
# Strategy: checkout only the files that changed in origin/main
# that are NOT inside .pipeline/
git diff --name-only HEAD origin/main 2>/dev/null | \
    grep -v "^\.pipeline/" | \
    xargs -r git checkout origin/main -- 2>/dev/null || true

# If there are untracked code files conflicting, stash them first
# but always keep .pipeline untouched
git stash --include-untracked -- \
    '*.py' '*.sh' '*.md' '*.yaml' '*.json' \
    ':!.pipeline' 2>/dev/null || true
git merge --ff-only origin/main 2>/dev/null || \
    git reset --soft origin/main 2>/dev/null || true
git stash pop 2>/dev/null || true

echo "  Code updated. .pipeline/ state preserved."

echo ""
echo "=== Current project states ==="
python -c "
import json, pathlib
pipeline = pathlib.Path('.pipeline/projects')
if not pipeline.exists():
    print('  (no projects dir)')
else:
    projects = sorted(pipeline.glob('*/state/current_idea.json'))
    if not projects:
        print('  (no projects found)')
    for f in projects:
        d = json.loads(f.read_text())
        slug = f.parent.parent.name
        st   = d.get('status', '?')
        ph   = d.get('phase', '?')
        tot  = d.get('total_phases', '?')
        ws   = f.parent.parent / 'workspace'
        py   = [p for p in ws.rglob('*.py') if '__pycache__' not in str(p)] if ws.exists() else []
        tests = [p for p in py if p.name.startswith('test_')]
        print(f'  {slug[:38]:38s} {st:32s} phase={ph}/{tot}  src={len(py)-len(tests)}  tests={len(tests)}')
"

echo ""
echo "=== Ready. Run: ==="
echo "  python pipeline/runner.py --from-list --provider ollama --model qwen3.6:35b-a3b-q4_K_M --time-limit 600"

echo ""
echo "=== Auto-repairing any missing master_plan.md files ==="
cd "$PROJ_ROOT"
python fix_missing_plans.py 2>/dev/null | grep -E "(plan created|state fixed|Done:)" || true
