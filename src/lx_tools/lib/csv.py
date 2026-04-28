import csv
import io
import random


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


def select_column_by_name(text: str, names: list[str], *, strict: bool = False) -> str:
    """Select specific columns from CSV by name, preserving the order given."""
    parsed_header, rows = _parse_csv(text, header=True)
    if parsed_header is None:
        raise CSVError("Cannot select columns by name without header. Use --header.")
    indices = _get_indices_from_names(names, parsed_header, strict)
    result_rows = [
        _get_cells(row, indices, strict=strict, row_idx=row_idx) for row_idx, row in enumerate(rows, start=1)
    ]
    return _write_csv([names, *result_rows])


def select_column_by_index(text: str, indices: list[int], *, strict: bool = False, header: bool = False) -> str:
    """Select specific columns from CSV by index, preserving the order given."""
    parsed_header, rows = _parse_csv(text, header=header)
    result_rows = [
        _get_cells(row, indices, strict=strict, row_idx=row_idx) for row_idx, row in enumerate(rows, start=1)
    ]
    if parsed_header is not None:
        return _write_csv([_get_cells(parsed_header, indices, strict=strict, row_idx=0), *result_rows])
    return _write_csv(result_rows)


def remove_column_by_name(text: str, names: list[str], *, strict: bool = False) -> str:
    """Remove specific columns from CSV by name, keeping the rest in original order."""
    header, rows = _parse_csv(text, header=True)
    if header is None:
        raise CSVError("Cannot remove columns by name without header. Use --header.")
    drop = {i for i in _get_indices_from_names(names, header, strict) if i < len(header)}
    keep = [i for i in range(len(header)) if i not in drop]
    result_header = _get_cells(header, keep)
    result_rows = [_get_cells(row, keep, strict=strict, row_idx=row_idx) for row_idx, row in enumerate(rows, start=1)]
    return _write_csv([result_header, *result_rows])


def remove_column_by_index(text: str, indices: list[int], *, strict: bool = False, header: bool = False) -> str:
    """Remove specific columns from CSV by index, keeping the rest in original order."""
    parsed_header, rows = _parse_csv(text, header=header)
    drop = set(indices)
    if parsed_header is not None:
        keep = [i for i in range(len(parsed_header)) if i not in drop]
        result_header = _get_cells(parsed_header, keep)
        result_rows = [
            _get_cells(row, keep, strict=strict, row_idx=row_idx) for row_idx, row in enumerate(rows, start=1)
        ]
        return _write_csv([result_header, *result_rows])
    result_rows = [[row[i] for i in range(len(row)) if i not in drop] for row in rows]
    return _write_csv(result_rows)


def count_csv(text: str, *, header: bool = False) -> int:
    """Count rows in CSV text.
    Returns data rows only if header=True, else all rows."""
    _, rows = _parse_csv(text, header=header)
    return len(rows)


def head_csv(text: str, n: int, *, header: bool = False) -> str:
    """Return the first N data rows, preserving header if present."""
    parsed_header, rows = _parse_csv(text, header=header)
    result = rows[:n]
    if parsed_header is not None:
        return _write_csv([parsed_header, *result])
    return _write_csv(result)


def tail_csv(text: str, n: int, *, header: bool = False) -> str:
    """Return the last N data rows, preserving header if present."""
    parsed_header, rows = _parse_csv(text, header=header)
    result = rows[-n:]
    if parsed_header is not None:
        return _write_csv([parsed_header, *result])
    return _write_csv(result)


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
