from typing import Annotated

from cyclopts import App, Parameter, validators
from cyclopts.types import StdioPath

type InputType = Annotated[StdioPath, Parameter(name="--input", validator=validators.Path(exists=True, dir_okay=False))]
type OutputType = Annotated[StdioPath, Parameter(name="--output", validator=validators.Path(dir_okay=False))]

app = App()

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
