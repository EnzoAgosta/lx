import sys
from typing import Annotated

import cyclopts
from cyclopts import App, Group, Parameter, validators
from cyclopts.types import StdioPath

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.csv as lx_csv

app = App(
    name="csv",
    help="""CSV manipulation utilities.

Relies on the standard library csv module for csv I/O.

Unless --encoding is specified, input is assumed to be UTF-8 and output is
always UTF-8 no matter the input encoding.
""",
)

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

    Specify the column with --name (requires --header) or --index.
    These options are mutually exclusive.

    Example: lx csv sort --header --name Age data.csv

    Options
    -------
    --name, -n
        Column name to sort by (requires --header).
    --index, -i
        Zero-based column index to sort by.
    --encoding, -e
        Input file encoding (default: utf-8).
    --header, -H
        Treat the first row as a header and preserve it.
    --strict, -s
        Error if a row is missing the sort column.
    """
    check_empty_stdin(input, app, ["sort"])
    if name is None and index is None:
        sys.exit("Must specify --name or --index.")
    try:
        with input.open("r", encoding=encoding) as f:
            if name is not None:
                result = lx_csv.sort_csv_by_name(f, name, desc=False, strict=strict)
            elif index is not None:
                result = lx_csv.sort_csv_by_index(f, index, desc=False, strict=strict, header=header)
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

    Specify the column with --name (requires --header) or --index.
    These options are mutually exclusive.

    Example: lx csv reverse --header --name Age data.csv

    Options
    -------
    --name, -n
        Column name to sort by (requires --header).
    --index, -i
        Zero-based column index to sort by.
    --encoding, -e
        Input file encoding (default: utf-8).
    --header, -H
        Treat the first row as a header and preserve it.
    --strict, -s
        Error if a row is missing the sort column.
    """
    check_empty_stdin(input, app, ["reverse"])
    if name is None and index is None:
        sys.exit("Must specify --name or --index.")
    try:
        with input.open("r", encoding=encoding) as f:
            if name is not None:
                result = lx_csv.sort_csv_by_name(f, name, desc=True, strict=strict)
            elif index is not None:
                result = lx_csv.sort_csv_by_index(f, index, desc=True, strict=strict, header=header)
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
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Output only the specified columns.

    Specify columns with --names (comma-separated) or --indices
    (comma-separated, zero-based). These options are mutually exclusive.

    When using --names, the first row is treated as a header.
    Missing cells become empty strings unless --strict is used.

    Example: lx csv select --names Name,Email data.csv

    Options
    -------
    --names, -n
        Comma-separated column names to keep.
    --indices, -i
        Comma-separated zero-based column indices to keep.
    --encoding, -e
        Input file encoding (default: utf-8).
    --strict, -s
        Error if a row is missing a requested column.
    """
    check_empty_stdin(input, app, ["select"])
    if not names and not indices:
        sys.exit("Must specify --names or --indices.")
    try:
        with input.open("r", encoding=encoding) as f:
            if names is not None:
                result = lx_csv.select_column_by_name(
                    f, names=[name.strip() for name in names.split(",")], strict=strict
                )
            elif indices is not None:
                result = lx_csv.select_column_by_index(
                    f, indices=[int(i.strip()) for i in indices.split(",")], strict=strict
                )
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def count(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Count CSV rows.

    Counts all rows by default.
    Use --header to exclude the header row
    from the count.

    Example: lx csv count --header data.csv

    Options
    -------
    --header, -H
        Exclude the first row from the count (treat it as a header).
    --encoding, -e
        Input file encoding (default: utf-8).
    """
    check_empty_stdin(input, app, ["count"])
    try:
        with input.open("r", encoding=encoding) as f:
            result = lx_csv.count_csv(f, header=header)
        output.write_text(f"{result}\n", encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def head(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Output the first N data rows.

    Memory-efficient: parses only as many rows as needed.
    Preserves the header row when --header is used.

    Example: lx csv head -n 5 --header data.csv

    Options
    -------
    --lines, -n
        Number of data rows to output (default: 10).
    --header, -H
        Treat the first row as a header and preserve it.
    --encoding, -e
        Input file encoding (default: utf-8).
    """
    check_empty_stdin(input, app, ["head"])
    try:
        with input.open("r", encoding=encoding) as f:
            result = lx_csv.head_csv(f, lines, header=header)
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def tail(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Output the last N data rows.

    Uses a deque and reads the file line-by-line
    to stay memory-efficient on large files.

    Preserves the header row when --header is used.

    Example: lx csv tail -n 5 --header data.csv

    Options
    -------
    --lines, -n
        Number of data rows to output (default: 10).
    --header, -H
        Treat the first row as a header and preserve it.
    --encoding, -e
        Input file encoding (default: utf-8).
    """
    check_empty_stdin(input, app, ["tail"])
    try:
        with input.open("r", encoding=encoding) as f:
            result = lx_csv.tail_csv(f, lines, header=header)
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def shuffle(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    seed: Annotated[int | float | str | None, Parameter(name=["--seed", "-s"])] = None,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Shuffle CSV rows randomly.

    Preserves the header row when --header is used.

    Use --seed for a reproducible shuffle order.

    Example: lx csv shuffle --seed 42 --header data.csv

    Options
    -------
    --seed, -s
        Random seed for deterministic output.
    --header, -H
        Treat the first row as a header and preserve it.
    --encoding, -e
        Input file encoding (default: utf-8).
    """
    check_empty_stdin(input, app, ["shuffle"])
    try:
        with input.open("r", encoding=encoding) as f:
            result = lx_csv.shuffle_csv(f, header=header, seed=seed)
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))


@app.command
def sample(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    n: Annotated[int, Parameter(name=["--n", "-n"], validator=validators.Number(gt=0))] = 10,
    seed: Annotated[int | float | str | None, Parameter(name=["--seed", "-s"])] = None,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Sample N rows without replacement.

    Preserves the header row when --header is used.

    Use --seed for a reproducible sample.

    Errors if N is larger than the number of data rows available.

    Example: lx csv sample -n 100 --seed 42 --header data.csv

    Options
    -------
    --n, -n
        Number of data rows to sample (default: 10).
    --seed, -s
        Random seed for deterministic output.
    --header, -H
        Treat the first row as a header and preserve it.
    --encoding, -e
        Input file encoding (default: utf-8).
    """
    check_empty_stdin(input, app, ["sample"])
    try:
        with input.open("r", encoding=encoding) as f:
            result = lx_csv.sample_csv(f, n, header=header, seed=seed)
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
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Remove specified columns, keeping the rest in original order.

    Specify columns with --names (comma-separated) or
    --indices (comma-separated, zero-based).
    These options are mutually exclusive.

    When using --names, the first row is treated as a header.

    Example: lx csv remove --names Password,InternalID data.csv

    Options
    -------
    --names, -n
        Comma-separated column names to remove.
    --indices, -i
        Comma-separated zero-based column indices to remove.
    --encoding, -e
        Input file encoding (default: utf-8).
    --strict, -s
        Error if a named column is not found in the header.
    """
    check_empty_stdin(input, app, ["remove"])
    if not names and not indices:
        sys.exit("Must specify --names or --indices.")
    try:
        with input.open("r", encoding=encoding) as f:
            if names is not None:
                result = lx_csv.remove_column_by_name(
                    f, names=[name.strip() for name in names.split(",")], strict=strict
                )
            elif indices is not None:
                result = lx_csv.remove_column_by_index(
                    f, indices=[int(i.strip()) for i in indices.split(",")], strict=strict
                )
        output.write_text(result, encoding="utf-8")
    except lx_csv.CSVError as e:
        sys.exit(str(e))
