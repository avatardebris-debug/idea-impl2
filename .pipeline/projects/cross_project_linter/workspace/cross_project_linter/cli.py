"""
cli.py — cross_project_linter CLI.
"""
import argparse, pathlib, sys
from cross_project_linter.linter import lint_workspace, format_report

def main():
    parser = argparse.ArgumentParser(prog="cross_project_linter")
    parser.add_argument("command", choices=["check"])
    parser.add_argument("target_dir", help="Directory containing project workspaces")

    args = parser.parse_args()

    p = pathlib.Path(args.target_dir)
    if not p.is_dir():
        print(f"ERROR: target is not a directory: {p}", file=sys.stderr)
        sys.exit(1)

    print(f"Linting workspace: {p}", file=sys.stderr)
    
    # We will assume each sub-directory in target_dir is a workspace
    all_errors = []
    
    # If the current dir itself has pyproject.toml, it IS the workspace
    if (p / "pyproject.toml").exists() or (p / "tests").exists():
        all_errors.extend(lint_workspace(p))
    else:
        # Otherwise, search child directories
        for child in p.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                all_errors.extend(lint_workspace(child))
                
    report = format_report(all_errors)
    print(report)
    
    if all_errors:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
