import sys
from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import StdioPath

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.json as lx_json

app = App(
    name="json",
    help="""JSON utilities. Assumes valid UTF-8 per RFC 8259.

    Relies on orjson for all json I/O.
""",
)


@app.command
def sort(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Sort all JSON keys recursively.

    Walks the entire document and sorts keys
    in every object, including objects nested
    inside arrays.
    Arrays themselves are left in order.
    Useful for getting stable diffs between JSON files.

    Example: lx json sort messy.json
    """
    check_empty_stdin(input, app, ["sort"])
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
    """Pretty-print JSON with 2-space indentation.

    Produces human-readable output.

    Use --sort-keys to also sort all
    object keys before formatting.

    Example: lx json pretty --sort-keys compact.json

    Options
    -------
    --sort-keys, -s
        Sort keys before pretty-printing.
    """
    check_empty_stdin(input, app, ["pretty"])
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
    """Minify JSON by removing unnecessary whitespace.

    Produces the most compact representation.

    Use --sort-keys to also
    sort all object keys first.

    Example: lx json minify --sort-keys pretty.json

    Options
    -------
    --sort-keys, -s
        Sort keys before minifying.
    """
    check_empty_stdin(input, app, ["minify"])
    try:
        output.write_bytes(lx_json.minify_json(input.read_bytes(), sort_keys=sort_keys))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def validate(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Validate JSON syntax.

    Passes the input data through
    unchanged on success, so you can use
    this as a guard in a pipeline.

    Example: lx json validate data.json | lx json pretty
    """
    check_empty_stdin(input, app, ["validate"])
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

    Sorts keys ascending, then reverses them.
    Only affects the top-level object,
    nested objects are left untouched.

    Deterministic but not the
    most efficient for huge objects.

    Unless you're dealing with huge files, the
    performance difference is negligible thanks
    to the initial sorting being done in rust and not python.

    Example: lx json reverse '{"a":1,"b":2,"c":3}'
    """
    check_empty_stdin(input, app, ["reverse"])
    try:
        output.write_bytes(lx_json.reverse_json(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def to_jsonl(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Convert a JSON array to JSON Lines.

    Each element of the input array becomes one line of output.
    The input must be a JSON array at the top level.

    Example: lx json to_jsonl array.json
    """
    check_empty_stdin(input, app, ["to_jsonl"])
    try:
        output.write_bytes(lx_json.to_jsonl(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))
