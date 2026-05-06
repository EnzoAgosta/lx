import sys
from typing import Annotated

from cyclopts import App, Parameter, validators
from cyclopts.types import StdioPath
import orjson

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.jsonl as lx_jsonl

app = App(
    name="jsonl",
    help="""JSON Lines utilities. Assumes valid UTF-8 per RFC 8259.

    All output normalizes line endings to \\n regardless of input.
    """,
)


@app.command
def count(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Count non-empty and valid JSON Lines.

    Empty lines are ignored.
    Invalid JSON causes an error.

    Example: lx jsonl count file.jsonl
    """
    check_empty_stdin(input, app, ["count"])
    try:
        with input.open("rb") as f:
            n = sum(1 for line in f if lx_jsonl.parse_line(line) is not None)
        output.write_text(f"{n}\n")
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))


@app.command
def dedup(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Remove duplicate lines from JSON Lines.

    Keeps the first occurrence of each unique JSON value.
    Empty lines are dropped.

    Example: lx jsonl dedup file.jsonl
    """
    check_empty_stdin(input, app, ["dedup"])
    with input.open("rb") as f:
        try:
            result = lx_jsonl.dedup_jsonl(f)
        except lx_jsonl.JSONLError as e:
            sys.exit(str(e))
    output.write_bytes(b"\n".join(result) + b"\n")


@app.command
def head(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Output the first N non-empty lines.

    By default each line is validated as JSON.
    You can use --raw-lines to skip validation
    and treat the input as plain text lines
    if you're planning on piping the output
    to another command and validating it there.

    Example: lx jsonl head -n 5 file.jsonl

    Options
    -------
    --lines, -n
        Number of lines to output (default: 10).
    --raw-lines, -r
        Skip JSON validation. (default: False)
    """
    check_empty_stdin(input, app, ["head"])
    with input.open("rb") as f:
        head_lines = lx_jsonl.get_first_n_lines(f, lines)
    if not raw:
        for line in head_lines:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
    output.write_bytes(b"\n".join(head_lines) + b"\n")


@app.command
def tail(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Output the last N non-empty lines.

    Uses a deque and reads the file line-by-line
    to stay memory-efficient on large files.

    By default each line is validated as JSON.
    You can use --raw-lines to skip validation
    and treat the input as plain text lines
    if you're planning on piping the output
    to another command and validating it there.

    Example: lx jsonl tail -n 5 file.jsonl

    Options
    -------
    --lines, -n
        Number of lines to output (default: 10).
    --raw-lines, -r
        Skip JSON validation.
    """
    check_empty_stdin(input, app, ["tail"])
    with input.open("rb") as f:
        tail_lines = lx_jsonl.get_last_n_lines(f, lines)
    if not raw:
        for line in tail_lines:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
    output.write_bytes(b"\n".join(tail_lines) + b"\n")


@app.command
def validate(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Validate that every non-empty line is valid JSON.

    If valid, the input is returned with line endings normalized to \n
    so you can use this as a guard in a pipeline (though most other
    commands still validate internally anyway).

    Example: lx jsonl validate file.jsonl | lx jsonl sort --key name
    """
    check_empty_stdin(input, app, ["validate"])
    lines = []
    with input.open("rb") as f:
        for line in f:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
            lines.append(line.rstrip(b"\r\n"))
    output.write_bytes(b"\n".join(lines) + b"\n")


@app.command
def sort(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str, Parameter(name=["--key", "-k"])],
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort JSON Lines by a top-level key in ascending order.

    Every non-empty line must be a JSON object.
    Missing keys sort as null (they appear first).

    Use --strict to raise an error instead.

    Example: lx jsonl sort --key age users.jsonl

    Options
    -------
    --key, -k
        The top-level object key to sort by (required).
    --strict, -s
        Error if any line is missing the key.
    """
    check_empty_stdin(input, app, ["sort"])
    with input.open("rb") as f:
        lines = f.readlines()
    try:
        result = lx_jsonl.sort_jsonl(lines, key, strict=strict)
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))
    output.write_bytes(b"\n".join(result) + b"\n")


@app.command
def reverse(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str, Parameter(name=["--key", "-k"])],
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort JSON Lines by a top-level key in descending order.

    Every non-empty line must be a JSON object.
    Missing keys sort as null (they appear last).

    Use --strict to raise an error instead.

    Example: lx jsonl reverse --key age users.jsonl

    Options
    -------
    --key, -k
        The top-level object key to sort by (required).
    --strict, -s
        Error if any line is missing the key.
    """
    check_empty_stdin(input, app, ["reverse"])
    with input.open("rb") as f:
        lines = f.readlines()
    try:
        result = lx_jsonl.sort_jsonl(lines, key, reverse=True, strict=strict)
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))
    output.write_bytes(b"\n".join(result) + b"\n")


@app.command
def select(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    keys: Annotated[str, Parameter(name=["--keys", "-k"])],
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Select specific keys from every non-empty JSON object line.

    Empty lines are dropped.
    Each line must be a JSON object.
    Missing keys are silently omitted by default.
    Use --strict to error if a key is missing in any line.

    Example: lx jsonl select --keys name,age users.jsonl

    Options
    -------
    --keys, -k
        Comma-separated keys to keep (required).
    --strict, -s
        Error if any line is missing a key.
    """
    check_empty_stdin(input, app, ["select"])
    parsed_keys = [k.strip() for k in keys.split(",")]
    with input.open("rb") as f:
        try:
            result = lx_jsonl.select_jsonl(f, keys=parsed_keys, strict=strict)
        except lx_jsonl.JSONLError as e:
            sys.exit(str(e))
    output.write_bytes(b"\n".join(result) + b"\n")


@app.command
def rename(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    old: Annotated[str, Parameter(name=["--old"])],
    new: Annotated[str, Parameter(name=["--new"])],
) -> None:
    """Rename a top-level key in every non-empty JSONL object line.

    Empty lines are dropped.
    Errors if any line is not an object, if the old key is missing,
    or if the new key already exists in that object (unless new == old).

    Example: lx jsonl rename --old name --new full_name data.jsonl
    """
    check_empty_stdin(input, app, ["rename"])
    with input.open("rb") as f:
        try:
            result = lx_jsonl.rename_jsonl(f, old=old, new=new)
        except lx_jsonl.JSONLError as e:
            sys.exit(str(e))
    output.write_bytes(b"\n".join(result) + b"\n")


@app.command
def to_json(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Convert JSON Lines to a single JSON array.

    Empty lines are ignored.
    The output is a compact JSON array that
    can be safely piped to other commands that
    expect JSON data.

    Example: lx jsonl to_json file.jsonl | lx json pretty --output pretty.json
    """
    check_empty_stdin(input, app, ["to_json"])
    with input.open("rb") as f:
        try:
            result = [lx_jsonl.parse_line(line) for line in f]
        except lx_jsonl.JSONLError as e:
            sys.exit(str(e))
    output.write_bytes(orjson.dumps([line for line in result if line is not None]))


@app.command
def shuffle(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    seed: Annotated[int | float | str | None, Parameter(name=["--seed", "-s"])] = None,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Shuffle JSON Lines randomly.

    By default each line is validated as JSON.
    You can use --raw-lines to skip validation
    and treat the input as plain text lines
    if you're planning on piping the output
    to another command and validating it there.

    Use --seed for a reproducible shuffle order.

    Example: lx jsonl shuffle --seed 42 file.jsonl

    Options
    -------
    --seed, -s
        Random seed for deterministic output.
    --raw-lines, -r
        Skip JSON validation.
    """
    check_empty_stdin(input, app, ["shuffle"])
    try:
        with input.open("rb") as f:
            lines = lx_jsonl.shuffle_jsonl(f, seed=seed)
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))
    if not raw:
        for line in lines:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
    output.write_bytes(b"".join(lines))


@app.command
def sample(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    n: Annotated[int, Parameter(name=["--n", "-n"], validator=validators.Number(gt=0))] = 10,
    seed: Annotated[int | float | str | None, Parameter(name=["--seed", "-s"])] = None,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Sample N lines from JSON Lines without replacement.

    Uses reservoir sampling so memory usage stays O(n)
    regardless of file size.

    By default each line is validated as JSON.
    You can use --raw-lines to skip validation
    and treat the input as plain text lines
    if you're planning on piping the output
    to another command and validating it there.

    Use --seed for a reproducible sample.

    Errors if N is larger than the number of available lines.

    Example: lx jsonl sample -n 5 --seed 42 file.jsonl

    Options
    -------
    --n, -n
        Number of lines to sample (default: 10).
    --seed, -s
        Random seed for deterministic output.
    --raw-lines, -r
        Skip JSON validation.
    """
    check_empty_stdin(input, app, ["sample"])
    try:
        with input.open("rb") as f:
            result = lx_jsonl.sample_jsonl(f, k=n, seed=seed)
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))
    if not raw:
        for line in result:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
    output.write_bytes(b"".join(result))
