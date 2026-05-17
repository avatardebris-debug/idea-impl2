"""DocsAI CLI entry point."""

import typer

from docsai.cli.spec import spec_app

app = typer.Typer(
    name="docsai",
    help="AI-powered technical documentation assistant",
)

# Register the spec subcommand
app.add_typer(spec_app, name="spec")


def main():
    app()


if __name__ == "__main__":
    main()
