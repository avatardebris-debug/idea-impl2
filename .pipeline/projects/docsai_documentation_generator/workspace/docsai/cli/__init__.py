"""DocsAI CLI entry point."""

import typer

from docsai.cli.spec import spec
from docsai.cli.readme import readme as readme_cmd
from docsai.cli.changelog import changelog as changelog_cmd

app = typer.Typer(
    name="docsai",
    help="AI-powered technical documentation assistant",
)

# Register as top-level commands to match the test expectations (e.g. `docsai spec`, `docsai readme`)
app.command(name="spec")(spec)
app.command(name="readme", help="Generate README documentation")(readme_cmd)
app.command(name="changelog", help="Generate changelog from git history")(changelog_cmd)

def main():
    app()

if __name__ == "__main__":
    main()
