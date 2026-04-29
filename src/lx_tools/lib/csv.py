from collections.abc import Iterator
import csv
import io
import random
from collections import deque
from itertools import chain
from typing import Literal, TextIO, overload


class CSVError(Exception):
    """Base class for CSV errors."""


def _format_csv(*rows: list[str]) -> str:
    """Format CSV into a string ready to be written."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerows(rows)
    return out.getvalue()


def safe_get_next_row(stream: Iterator[list[str]]) -> list[str]:
    """Get the header from a CSV stream"""
    try:
        return next(stream)
    except StopIteration:
        raise CSVError("Csv file is empty")


def _get_indices_from_names(names: list[str], header: list[str], strict: bool) -> list[int]:
    """Get indices of columns by name."""
    indices: list[int] = []
    for name in names:
        if name not in header:
            if strict:
                raise CSVError(f"Column name not found in header: {name!r}. Available columns: {header!r}")
            indices.append(-1)
            continue
        index = header.index(name)
        indices.append(index)
    return indices


@overload
def _get_column_at(source: list[str], index: int, strict: bool, row_idx: int, return_None: Literal[False]) -> str: ...
@overload
def _get_column_at(
    source: list[str], index: int, strict: bool, row_idx: int, return_None: bool = False
) -> str | None: ...
def _get_column_at(source: list[str], index: int, strict: bool, row_idx: int, return_None: bool = False) -> str | None:
    """Extract a single column at a given index from a row or return "" if missing."""
    if index >= len(source):
        if strict:
            raise CSVError(f"Row {row_idx!r} only has {len(source)!r} columns but expected at least {index!r}.")
        return None if return_None else ""
    return source[index]


def _get_columns_at(source: list[str], indices: list[int], strict: bool, row_idx: int, return_None: bool) -> list[str]:
    """Returns all columns at given indices from a row."""
    return [
        column
        for index in indices
        if (column := _get_column_at(source, index, strict=strict, row_idx=row_idx, return_None=return_None))
        is not None
    ]


def sort_csv_by_name(stream: TextIO, key: str, desc: bool = False, *, strict: bool = False) -> str:
    """Sort CSV rows by a column name."""
    reader = csv.reader(stream)
    parsed_header = safe_get_next_row(reader)
    if key not in parsed_header:
        raise CSVError(f"Column name not found in header: {key!r}. Available columns: {parsed_header!r}")
    index = parsed_header.index(key)

    rows = (
        row
        for _, row in sorted(
            enumerate(reader, start=1),
            key=lambda x: _get_column_at(x[1], index, strict=strict, row_idx=x[0], return_None=False),
            reverse=desc,
        )
    )
    return _format_csv(parsed_header, *rows)


def sort_csv_by_index(
    stream: TextIO, index: int, desc: bool = False, *, strict: bool = False, header: bool = False
) -> str:
    """Sort CSV rows by a column index."""
    reader = csv.reader(stream)
    parsed_header = None
    if header:
        parsed_header = safe_get_next_row(reader)

    rows = (
        row
        for _, row in sorted(
            enumerate(reader, start=1 if header else 0),
            key=lambda x: _get_column_at(x[1], index, strict=strict, row_idx=x[0], return_None=False),
            reverse=desc,
        )
    )
    return _format_csv(parsed_header, *rows) if parsed_header is not None else _format_csv(*rows)


def select_column_by_name(stream: TextIO, names: list[str], *, strict: bool = False) -> str:
    """Select specific columns from CSV by name, preserving the order given."""
    reader = csv.reader(stream)
    parsed_header = safe_get_next_row(reader)
    indices = _get_indices_from_names(names, parsed_header, strict)

    return _format_csv(
        *(
            _get_columns_at(row, indices, strict=strict, row_idx=row_idx, return_None=False)
            for row_idx, row in enumerate(chain([parsed_header], reader))
        )
    )


def select_column_by_index(stream: TextIO, indices: list[int], *, strict: bool = False) -> str:
    """Select specific columns from CSV by index, preserving the order given."""
    reader = csv.reader(stream)
    for i in indices:
        if i < 0:
            raise CSVError(f"Negative indexes are not allowed. Got {i!r}.")

    return _format_csv(
        *(
            _get_columns_at(row, indices, strict=strict, row_idx=row_idx, return_None=False)
            for row_idx, row in enumerate(reader, start=1)
        )
    )


def remove_column_by_name(stream: TextIO, names: list[str], *, strict: bool = False) -> str:
    """Remove specific columns from CSV by name, keeping the original order."""
    reader = csv.reader(stream)
    parsed_header = safe_get_next_row(reader)
    indices = _get_indices_from_names(names, parsed_header, strict)

    keep = sorted(set(range(len(parsed_header))) - set(indices))

    return _format_csv(
        *(
            _get_columns_at(row, keep, strict=strict, row_idx=row_idx, return_None=False)
            for row_idx, row in enumerate(chain([parsed_header], reader))
        )
    )


def remove_column_by_index(stream: TextIO, indices: list[int], *, strict: bool = False) -> str:
    """Remove specific columns from CSV by index, keeping the rest in original order."""
    reader = csv.reader(stream)
    indices_ = set(indices)

    for i in indices_:
        if i < 0:
            raise CSVError(f"Negative indexes are not allowed. Got {i!r}.")

    return _format_csv(
        *(
            _get_columns_at(
                row, sorted(set(range(len(row))) - indices_), strict=strict, row_idx=row_idx, return_None=True
            )
            for row_idx, row in enumerate(reader, start=1)
        )
    )


def count_csv(stream: TextIO, *, header: bool = False) -> int:
    """Count rows in CSV text.
    Returns data rows only if header=True, else all rows."""
    reader = csv.reader(stream)
    if header:
        safe_get_next_row(reader)
    return sum(1 for _ in reader)


def head_csv(stream: TextIO, n: int, *, header: bool = False) -> str:
    """Return the first N data rows, preserving header if present.
    Parses only as many rows as needed from the text stream."""
    reader = csv.reader(stream)
    result = []
    if header:
        result.append(safe_get_next_row(reader))
    try:
        for _ in range(n):
            result.append(next(reader))
    except StopIteration:
        pass
    return _format_csv(*result)


def tail_csv(stream: TextIO, n: int, *, header: bool = False) -> str:
    """Return the last N data rows, preserving header if present.
    Uses a deque to avoid keeping all rows in memory."""
    reader = csv.reader(stream)
    out: deque[list[str]] = deque(maxlen=n)
    parsed_header = safe_get_next_row(reader) if header else None
    out.extend(reader)
    return _format_csv(parsed_header, *out) if parsed_header is not None else _format_csv(*out)


def shuffle_csv(
    stream: TextIO, *, header: bool = False, seed: int | float | str | bytes | bytearray | None = None
) -> str:
    """Shuffle CSV rows randomly. Preserves header if present."""
    reader = csv.reader(stream)
    rng = random.Random(seed)
    parsed_header = safe_get_next_row(reader) if header else None
    rows = list(reader)
    rng.shuffle(rows)
    return _format_csv(parsed_header, *rows) if parsed_header is not None else _format_csv(*rows)


def sample_csv(
    stream: TextIO, n: int, *, header: bool = False, seed: int | float | str | bytes | bytearray | None = None
) -> str:
    """Sample N rows without replacement. Preserves header if present."""
    reader = csv.reader(stream)
    rng = random.Random(seed)
    parsed_header = safe_get_next_row(reader) if header else None
    rows = list(reader)
    try:
        result = rng.sample(rows, k=n)
    except ValueError:
        raise CSVError(f"Cannot sample {n} rows from {len(rows)} available.")
    return _format_csv(parsed_header, *result) if parsed_header is not None else _format_csv(*result)
