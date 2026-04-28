import sys
from typing import Annotated

from cyclopts import App, Parameter, validators
from cyclopts.types import StdioPath

type InputType = Annotated[StdioPath, Parameter(name="--input", validator=validators.Path(exists=True, dir_okay=False))]
type OutputType = Annotated[StdioPath, Parameter(name="--output", validator=validators.Path(dir_okay=False))]


def check_empty_stdin(input: StdioPath, app: App, commands: list[str]) -> None:
    """If input is stdin and the terminal has no piped data, print help and exit."""
    if input.is_stdio and sys.stdin.isatty():
        app.help_print(commands)
        sys.exit(0)


app = App(
    help="""A Swiss-army knife for data manipulation on the command line.

Supports JSON, JSON Lines, CSV and encoding operations.
Every command accepts files as positional arguments or via --input/--output,
and defaults to stdin/stdout for easy piping.

Use --help on any subcommand for detailed usage.

If calling a subcommand with no arguments without piping data,
prints the command's help and exits with status 0.
""",
)

# Import sub-apps after type aliases to avoid circular imports.
from lx_tools.cli.csv import app as csv_app
from lx_tools.cli.encoding import app as encoding_app
from lx_tools.cli.json import app as json_app
from lx_tools.cli.jsonl import app as jsonl_app

app.command(json_app)
app.command(jsonl_app)
app.command(encoding_app)
app.command(csv_app)

if __name__ == "__main__":
    app()
