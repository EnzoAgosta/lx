import random
import sys
from typing import Annotated

from cyclopts import App, Parameter, validators
from cyclopts.types import StdioPath
import orjson

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.jsonl as lx_jsonl

app = App(name="jsonl", help="JSON Lines utilities. Assumes valid UTF-8 per RFC 8259.")


@app.command
def count(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Count non-empty and valid lines."""
    check_empty_stdin(input, app, ["count"])
    try:
        with input.open("rb") as f:
            n = sum(1 for line in f if lx_jsonl.parse_line(line) is not None)
        output.write_text(f"{n}\n")
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))


@app.command
def head(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Output the first N non-empty lines."""
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
    """Output the last N non-empty lines."""
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
    If valid, returns the input data as-is for chaining."""
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
    """Sort JSON Lines by a top-level key in ascending order."""
    check_empty_stdin(input, app, ["sort"])
    with input.open("rb") as f:
        lines = f.readlines()
    try:
        result = lx_jsonl.sort_jsonl(lines, key, strict=strict)
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))
    output.write_bytes(b"".join(result))


@app.command
def reverse(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str, Parameter(name=["--key", "-k"])],
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort JSON Lines by a top-level key in descending order."""
    check_empty_stdin(input, app, ["reverse"])
    with input.open("rb") as f:
        lines = f.readlines()
    try:
        result = lx_jsonl.sort_jsonl(lines, key, reverse=True, strict=strict)
    except lx_jsonl.JSONLError as e:
        sys.exit(str(e))
    output.write_bytes(b"".join(result))


@app.command
def pluck(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str, Parameter(name=["--key", "-k"])],
) -> None:
    """Extract a top-level field from each non-empty JSONL object line."""
    check_empty_stdin(input, app, ["pluck"])
    with input.open("rb") as f:
        try:
            result = [lx_jsonl.pluck_field(line, key) for line in f]
        except lx_jsonl.JSONLError as e:
            sys.exit(str(e))
    output.write_bytes(b"\n".join(orjson.dumps(line) for line in result if line is not None))


@app.command
def to_json(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Convert JSON Lines to a JSON array."""
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
    seed: Annotated[int | float | str, Parameter(name=["--seed", "-s"])] = None,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Shuffle JSON Lines as-is."""
    check_empty_stdin(input, app, ["shuffle"])
    with input.open("rb") as f:
        lines = f.readlines()
    if not raw:
        for line in lines:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
    if seed is not None:
        random.seed(seed)
    random.shuffle(lines)
    output.write_bytes(b"".join(lines))


@app.command
def sample(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    n: Annotated[int, Parameter(name=["--n", "-n"], validator=validators.Number(gt=0))] = 10,
    seed: Annotated[int | float | str, Parameter(name=["--seed", "-s"])] = None,
    raw: Annotated[bool, Parameter(name=["--raw-lines", "-r"])] = False,
) -> None:
    """Sample N lines from JSON Lines without replacement."""
    check_empty_stdin(input, app, ["sample"])
    with input.open("rb") as f:
        lines = f.readlines()
    if not raw:
        for line in lines:
            try:
                lx_jsonl.parse_line(line)
            except lx_jsonl.JSONLError as e:
                sys.exit(str(e))
    if seed is not None:
        random.seed(seed)
    try:
        result = random.sample(lines, k=n)
    except ValueError:
        sys.exit(f"Cannot sample {n} lines from {len(lines)} available.")
    output.write_bytes(b"".join(result))
