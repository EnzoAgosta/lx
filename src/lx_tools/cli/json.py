import sys
from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import StdioPath

from lx_tools.cli import InputType, OutputType
import lx_tools.lib.json as lx_json

app = App(name="json", help="JSON utilities. Assumes valid UTF-8 per RFC 8259.")


@app.command
def sort(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Sort all JSON keys recursively."""
    try:
        output.write_bytes(lx_json.sort_json(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def pretty(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    sort_keys: Annotated[bool, Parameter(name=["--sort-keys", "-s"])] = False,
) -> None:
    """Pretty-print JSON with 2-space indentation."""
    try:
        output.write_bytes(lx_json.pretty_json(input.read_bytes(), sort_keys=sort_keys))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def minify(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    sort_keys: Annotated[bool, Parameter(name=["--sort-keys", "-s"])] = False,
) -> None:
    """Minify JSON by removing unnecessary whitespace."""
    try:
        output.write_bytes(lx_json.minify_json(input.read_bytes(), sort_keys=sort_keys))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def validate(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Validate JSON syntax. Outputs the input data as-is for chaining."""
    try:
        output.write_bytes(lx_json.validate_json(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def reverse(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Reverse the order of top-level JSON keys.

    Sorts keys ascending, then reverses. Only affects the top level;
    nested objects are left untouched. Deterministic but not efficient.
    """
    try:
        output.write_bytes(lx_json.reverse_json(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def to_jsonl(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Convert a JSON array to JSON Lines."""
    try:
        output.write_bytes(lx_json.to_jsonl(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))
