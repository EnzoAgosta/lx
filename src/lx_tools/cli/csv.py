import sys
from typing import Annotated

import cyclopts
from cyclopts import App, Group, Parameter, validators
from cyclopts.types import StdioPath

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.csv as lx_csv

app = App(name="csv", help="CSV manipulation utilities.")

only_one = Group(validator=cyclopts.validators.MutuallyExclusive())


@app.command
def sort(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    name: Annotated[str | None, Parameter(name=["--name", "-n"], group=only_one)] = None,
    index: Annotated[
        int | None, Parameter(name=["--index", "-i"], group=only_one, validator=validators.Number(gte=0))
    ] = None,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort CSV rows by a column in ascending order.

    Specify the column with --name or --index (mutually exclusive).
    Input is decoded with --encoding; output is always UTF-8.
    """
    check_empty_stdin(input, app, ["sort"])
    if not name and not index:
        sys.exit("Must specify --name or --index.")
    try:
        text = input.read_text(encoding=encoding)
        if name is not None:
            result = lx_csv.sort_csv_by_name(text, name, desc=False, strict=strict)
        else:
            result = lx_csv.sort_csv_by_index(text, index, desc=False, strict=strict, header=header)
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def reverse(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    name: Annotated[str | None, Parameter(name=["--name", "-n"], group=only_one)] = None,
    index: Annotated[
        int | None, Parameter(name=["--index", "-i"], group=only_one, validator=validators.Number(gte=0))
    ] = None,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort CSV rows by a column in descending order.

    Specify the column with --name or --index (mutually exclusive).
    Input is decoded with --encoding; output is always UTF-8.
    """
    check_empty_stdin(input, app, ["reverse"])
    if not name and not index:
        sys.exit("Must specify --name or --index.")
    try:
        text = input.read_text(encoding=encoding)
        if name is not None:
            result = lx_csv.sort_csv_by_name(text, name, desc=True, strict=strict)
        else:
            result = lx_csv.sort_csv_by_index(text, index, desc=True, strict=strict, header=header)
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def select(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    names: Annotated[str | None, Parameter(name=["--names", "-n"], group=only_one)] = None,
    indices: Annotated[str | None, Parameter(name=["--indices", "-i"], group=only_one)] = None,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Output only the specified columns.

    Specify columns with --names (comma-separated) or --indices (comma-separated).
    Mutually exclusive.
    """
    check_empty_stdin(input, app, ["select"])
    if not names and not indices:
        sys.exit("Must specify --names or --indices.")
    try:
        text = input.read_text(encoding=encoding)
        if names is not None:
            result = lx_csv.select_column_by_name(
                text, names=[name.strip() for name in names.split(",")], strict=strict
            )
        else:
            result = lx_csv.select_column_by_index(
                text, indices=[int(i.strip()) for i in indices.split(",")], strict=strict, header=header
            )
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def remove(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    names: Annotated[str | None, Parameter(name=["--names", "-n"], group=only_one)] = None,
    indices: Annotated[str | None, Parameter(name=["--indices", "-i"], group=only_one)] = None,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Remove the specified columns, keeping the rest in original order.

    Specify columns with --names (comma-separated) or --indices (comma-separated).
    Mutually exclusive.
    """
    check_empty_stdin(input, app, ["remove"])
    if not names and not indices:
        sys.exit("Must specify --names or --indices.")
    try:
        text = input.read_text(encoding=encoding)
        if names is not None:
            result = lx_csv.remove_column_by_name(
                text, names=[name.strip() for name in names.split(",")], strict=strict
            )
        else:
            result = lx_csv.remove_column_by_index(
                text, indices=[int(i.strip()) for i in indices.split(",")], strict=strict, header=header
            )
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))
