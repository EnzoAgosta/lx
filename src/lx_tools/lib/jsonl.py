from collections import deque
from collections.abc import Iterable

import orjson


class JSONLError(Exception):
    """Base class for JSONL errors."""


def get_first_n_lines(data: Iterable[bytes], n: int) -> list[bytes]:
    """Get the first N non-empty lines from data."""
    out = []
    for line in data:
        if line.strip():
            out.append(line.rstrip(b"\r\n"))
            if len(out) == n:
                break
    return out


def get_last_n_lines(data: Iterable[bytes], n: int) -> list[bytes]:
    """Get the last N non-empty lines from data."""
    out = deque(maxlen=n)
    for line in data:
        if line.strip():
            out.append(line.rstrip(b"\r\n"))
    return out


def parse_line(line: bytes) -> object | None:
    """Parse a JSONL line using orjson.
    Returns None if the line is empty.
    """
    try:
        if not line.strip():
            return None
        return orjson.loads(line)
    except UnicodeDecodeError as e:
        raise JSONLError(f"JSONL line is not valid UTF-8: {e}") from e
    except orjson.JSONDecodeError as e:
        raise JSONLError(f"Invalid JSONL line: {e}") from e


def pluck_field(line: bytes, key: str) -> object:
    """Extract a top-level field from a JSONL object line."""
    data = parse_line(line)
    if isinstance(data, dict) and key in data:
        return data[key]
    return None


def sort_jsonl(lines: list[bytes], key: str, *, reverse: bool = False, strict: bool = False) -> list[bytes]:
    """Sort JSON Lines by a top-level key.

    Missing keys sort as None (null). With strict=True, raises if any line
    is missing the key.
    """
    entries = []
    for line in lines:
        data = parse_line(line)
        if data is None:
            continue
        if not isinstance(data, dict):
            raise JSONLError(f"JSONL line is not an object: {line!r}")
        if key not in data:
            if strict:
                raise JSONLError(f"Missing key {key!r} in JSONL line: {line!r}")
        value = data.get(key)
        entries.append((orjson.dumps(value), line))

    entries.sort(key=lambda x: x[0], reverse=reverse)
    return [line for _, line in entries]
