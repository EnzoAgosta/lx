import sys
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
    *,
    sort_keys: bool = False,
) -> None:
    """Pretty-print JSON with 2-space indentation."""
    output.write_bytes(lx_json.pretty_json(input.read_bytes(), sort_keys=sort_keys))


@app.command
def minify(
    input: Annotated[StdioPath, Parameter(name="input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="output")] = StdioPath("-"),
    *,
    sort_keys: bool = False,
) -> None:
    """Minify JSON by removing unnecessary whitespace."""
    output.write_bytes(lx_json.minify_json(input.read_bytes(), sort_keys=sort_keys))


@app.command
def validate(
    input: Annotated[StdioPath, Parameter(name="input")] = StdioPath("-"),
) -> None:
    """Validate JSON syntax."""
    try:
        lx_json.validate_json(input.read_bytes())
    except Exception as e:
        sys.exit(f"Invalid JSON: {e}")


@app.command
def reverse(
    input: Annotated[StdioPath, Parameter(name="input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="output")] = StdioPath("-"),
) -> None:
    """Reverse the order of top-level JSON keys.

    Sorts keys ascending, then reverses. Only affects the top level;
    nested objects are left untouched. Deterministic but not efficient.
    """
    output.write_bytes(lx_json.reverse_json(input.read_bytes()))
