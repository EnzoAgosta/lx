import sys
from typing import Annotated

import cyclopts
from cyclopts import App, Group, Parameter
from cyclopts.types import StdioPath

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.json as lx_json

app = App(
    name="json",
    help="""JSON utilities. Assumes valid UTF-8 per RFC 8259.

    Relies on orjson for all json I/O.
""",
)

sort_options = Group(validator=cyclopts.validators.MutuallyExclusive())


@app.command
def sort(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    recurse: Annotated[bool, Parameter(name=["--recurse", "-r"], group=sort_options)] = False,
    key: Annotated[str | None, Parameter(name=["--key", "-k"], group=sort_options)] = None,
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort JSON keys or array elements.

    By default sorts top-level object keys or array elements.
    Use --recurse to sort keys recursively in every nested object.
    Use --key to sort an array of objects by a top-level key.

    Arrays themselves are left in order when using --recurse.
    Useful for getting stable diffs between JSON files.

    Example: lx json sort messy.json
    Example: lx json sort --recurse messy.json
    Example: lx json sort '[3,1,2]'
    Example: lx json sort --key age users.json

    Options
    -------
    --recurse, -r
        Sort keys recursively in all nested objects.
    --key, -k
        Sort array of objects by this top-level key.
        Mutually exclusive with --recurse.
    --strict, -s
        Error if any object is missing the key (only with --key).
    """
    check_empty_stdin(input, app, ["sort"])
    try:
        output.write_bytes(lx_json.sort_json(input.read_bytes(), recurse=recurse, key=key, strict=strict))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def pretty(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Pretty-print JSON with 2-space indentation.

    Produces human-readable output.
    To also sort keys, pipe through `lx json sort` first.

    Example: lx json pretty compact.json
    Example: lx json sort --recurse compact.json | lx json pretty
    """
    check_empty_stdin(input, app, ["pretty"])
    try:
        output.write_bytes(lx_json.pretty_json(input.read_bytes()))
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def minify(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Minify JSON by removing unnecessary whitespace.

    Produces the most compact representation.
    To also sort keys, pipe through `lx json sort` first.

    Example: lx json minify pretty.json
    Example: lx json sort --recurse pretty.json | lx json minify
    """
    check_empty_stdin(input, app, ["minify"])
    try:
        output.write_bytes(lx_json.minify_json(input.read_bytes()))
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
        data = input.read_bytes()
        lx_json.validate_json(data)
        output.write_bytes(data)
    except lx_json.JSONError as e:
        sys.exit(str(e))


@app.command
def reverse(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str | None, Parameter(name=["--key", "-k"])] = None,
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Reverse the order of top-level JSON keys or array elements.

    Reverses the existing order without sorting first.
    Only affects the top-level container;
    nested objects are left untouched.

    Use `lx json sort ... | lx json reverse` if you need
    sorted-then-reversed output.

    Use --key to reverse-sort an array of objects by a top-level key.

    Example: lx json reverse '{"a":1,"b":2,"c":3}'
    Example: lx json reverse '[3,1,2]'
    Example: lx json reverse --key age users.json

    Options
    -------
    --key, -k
        Reverse-sort array of objects by this top-level key.
    --strict, -s
        Error if any object is missing the key (only with --key).
    """
    check_empty_stdin(input, app, ["reverse"])
    try:
        output.write_bytes(lx_json.reverse_json(input.read_bytes(), key=key, strict=strict))
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
