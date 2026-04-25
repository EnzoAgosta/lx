from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import StdioPath

import lx_tools.lib.json as lx_json

app = App(name="json", help="JSON utilities.")


@app.command
def sort(
    input: Annotated[StdioPath, Parameter(name="input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="output")] = StdioPath("-"),
) -> None:
    """Sort all JSON keys recursively."""
    output.write_bytes(lx_json.sort_json(input.read_bytes()))


@app.command
def pretty(
    input: Annotated[StdioPath, Parameter(name="input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="output")] = StdioPath("-"),
) -> None:
    """Pretty-print JSON with 2-space indentation."""
    output.write_bytes(lx_json.pretty_json(input.read_bytes()))
