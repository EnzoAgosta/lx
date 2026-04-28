import csv
from collections import deque
import io
import random
from typing import TextIO


class CSVError(Exception):
    """Base class for CSV errors."""


def _parse_csv(text: str, *, header: bool = False) -> tuple[list[str] | None, list[list[str]]]:
    """Parse CSV text into header and rows.

    Returns (None, rows) if header=False.
    Returns (header, rows) if header=True.
    """
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return None, []
    if header:
        return rows.pop(0), rows
    return None, rows


def _write_csv(rows: list[list[str]]) -> str:
    """Write rows to CSV text."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerows(rows)
    return out.getvalue()


def _validate_min_length(row: list[str], min_len: int, row_idx: int) -> None:
    """Helper to centralize validation of row length."""
    if len(row) < min_len:
        raise CSVError(f"Row {row_idx!r} only has {len(row)!r} columns but expected at least {min_len!r}.")


def _sort_rows(rows: list[list[str]], key: int, desc: bool) -> list[list[str]]:
    """Sort rows by a column index.
    Uses an empty string as a placeholder for missing values.
    """
    return sorted(rows, key=lambda row: row[key] if key < len(row) else "", reverse=desc)


def _get_indices_from_names(names: list[str], header: list[str], strict: bool) -> list[int]:
    """Get indices of columns by name."""
    indices = []
    for name in names:
        if name not in header:
            if strict:
                raise CSVError(f"Column name not found in header: {name!r}. Available columns: {header!r}")
            indices.append(float("inf"))
            continue
        index = header.index(name)
        indices.append(index)
    return indices


def _get_cells(source: list[str], indices: list[int], *, strict: bool = False, row_idx: int | None = None) -> list[str]:
    """Extract cells at given indices from a source row or header."""
    result = []
    for idx in indices:
        if idx < 0:
            raise CSVError(f"Negative indexes are not allowed. Got {idx!r}.")
        if idx >= len(source):
            if strict and row_idx is not None:
                raise CSVError(f"Row {row_idx!r} only has {len(source)!r} columns but expected at least {idx!r}.")
            result.append("")
            continue
        result.append(source[idx])
    return result


def sort_csv_by_name(text: str, key: str, desc: bool = False, *, strict: bool = False) -> str:
    """Sort CSV rows by a column name."""
    parsed_header, rows = _parse_csv(text, header=True)
    if parsed_header is None:
        raise CSVError("Cannot sort by column name without header. Use --header.")
    if key not in parsed_header:
        if strict:
            raise CSVError(f"Column name not found in header: {key!r}. Available columns: {parsed_header!r}")
        return text
    index = parsed_header.index(key)
    if strict:
        for row_idx, row in enumerate(rows, start=1):
            _validate_min_length(row, index + 1, row_idx)
    return _write_csv([parsed_header, *_sort_rows(rows, index, desc)])


def sort_csv_by_index(text: str, key: int, desc: bool = False, *, strict: bool = False, header: bool = False) -> str:
    """Sort CSV rows by a column index."""
    parsed_header, rows = _parse_csv(text, header=header)
    if strict:
        if parsed_header is not None and key >= len(parsed_header):
            raise CSVError(f"Header only has {len(parsed_header)!r} columns but expected at least {key!r}.")
        for row_idx, row in enumerate(rows, start=1):
            _validate_min_length(row, key + 1, row_idx)
    rows = _sort_rows(rows, key, desc)
    if parsed_header is not None:
        return _write_csv([parsed_header, *rows])
    return _write_csv(rows)


def select_column_by_name(stream: TextIO, names: list[str], *, strict: bool = False) -> str:
    """Select specific columns from CSV by name, preserving the order given."""
    reader = csv.reader(stream)
    try:
        parsed_header = next(reader)
    except StopIteration:
        raise CSVError("Cannot select columns by name without header. Use --header.")
    indices = _get_indices_from_names(names, parsed_header, strict)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(_get_cells(parsed_header, indices, strict=strict, row_idx=0))
    for row_idx, row in enumerate(reader, start=1):
        writer.writerow(_get_cells(row, indices, strict=strict, row_idx=row_idx))
    return out.getvalue()


def select_column_by_index(stream: TextIO, indices: list[int], *, strict: bool = False, header: bool = False) -> str:
    """Select specific columns from CSV by index, preserving the order given."""
    reader = csv.reader(stream)
    out = io.StringIO()
    writer = csv.writer(out)
    if header:
        try:
            parsed_header = next(reader)
        except StopIteration:
            pass
        else:
            writer.writerow(_get_cells(parsed_header, indices, strict=strict, row_idx=0))
    for row_idx, row in enumerate(reader, start=1):
        writer.writerow(_get_cells(row, indices, strict=strict, row_idx=row_idx))
    return out.getvalue()


def remove_column_by_name(stream: TextIO, names: list[str], *, strict: bool = False) -> str:
    """Remove specific columns from CSV by name, keeping the rest in original order."""
    reader = csv.reader(stream)
    try:
        header = next(reader)
    except StopIteration:
        raise CSVError("Cannot remove columns by name without header. Use --header.")
    drop = {i for i in _get_indices_from_names(names, header, strict) if i < len(header)}
    keep = [i for i in range(len(header)) if i not in drop]
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(_get_cells(header, keep))
    for row_idx, row in enumerate(reader, start=1):
        writer.writerow(_get_cells(row, keep, strict=strict, row_idx=row_idx))
    return out.getvalue()


def remove_column_by_index(stream: TextIO, indices: list[int], *, strict: bool = False, header: bool = False) -> str:
    """Remove specific columns from CSV by index, keeping the rest in original order."""
    reader = csv.reader(stream)
    drop = set(indices)
    out = io.StringIO()
    writer = csv.writer(out)
    if header:
        try:
            parsed_header = next(reader)
        except StopIteration:
            pass
        else:
            keep = [i for i in range(len(parsed_header)) if i not in drop]
            writer.writerow(_get_cells(parsed_header, keep))
            for row_idx, row in enumerate(reader, start=1):
                writer.writerow(_get_cells(row, keep, strict=strict, row_idx=row_idx))
            return out.getvalue()
    for row in reader:
        writer.writerow([row[i] for i in range(len(row)) if i not in drop])
    return out.getvalue()


def count_csv(stream: TextIO, *, header: bool = False) -> int:
    """Count rows in CSV text.
    Returns data rows only if header=True, else all rows."""
    reader = csv.reader(stream)
    if header:
        try:
            next(reader)
        except StopIteration:
            pass
    return sum(1 for _ in reader)


def head_csv(stream: TextIO, n: int, *, header: bool = False) -> str:
    """Return the first N data rows, preserving header if present.
    Parses only as many rows as needed from the text stream."""
    reader = csv.reader(stream)
    parsed_header = None
    if header:
        try:
            parsed_header = next(reader)
        except StopIteration:
            pass
    result = []
    for i, row in enumerate(reader):
        if i >= n:
            break
        result.append(row)
    if parsed_header is not None:
        return _write_csv([parsed_header, *result])
    return _write_csv(result)


def tail_csv(stream: TextIO, n: int, *, header: bool = False) -> str:
    """Return the last N data rows, preserving header if present.
    Uses a deque to avoid keeping all rows in memory."""
    reader = csv.reader(stream)
    parsed_header = None
    if header:
        try:
            parsed_header = next(reader)
        except StopIteration:
            pass
    out = deque(maxlen=n)
    for row in reader:
        out.append(row)
    if parsed_header is not None:
        return _write_csv([parsed_header, *list(out)])
    return _write_csv(list(out))


def shuffle_csv(text: str, *, header: bool = False, seed: object = None) -> str:
    """Shuffle CSV rows randomly. Preserves header if present."""
    parsed_header, rows = _parse_csv(text, header=header)
    if seed is not None:
        random.seed(seed)
    random.shuffle(rows)
    if parsed_header is not None:
        return _write_csv([parsed_header, *rows])
    return _write_csv(rows)


def sample_csv(text: str, n: int, *, header: bool = False, seed: object = None) -> str:
    """Sample N rows without replacement. Preserves header if present."""
    parsed_header, rows = _parse_csv(text, header=header)
    if seed is not None:
        random.seed(seed)
    try:
        result = random.sample(rows, k=n)
    except ValueError:
        raise CSVError(f"Cannot sample {n} rows from {len(rows)} available.")
    if parsed_header is not None:
        return _write_csv([parsed_header, *result])
    return _write_csv(result)
