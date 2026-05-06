from collections import deque
from collections.abc import Iterable
import random
from typing import Sequence, cast

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


def get_last_n_lines(data: Iterable[bytes], n: int) -> Sequence[bytes]:
    """Get the last N non-empty lines from data."""
    out: deque[bytes] = deque(maxlen=n)
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
        return cast(object, orjson.loads(line))  # orjson.loads() returns Any so need to cast to make mypy happy
    except UnicodeDecodeError as e:
        raise JSONLError(f"JSONL line is not valid UTF-8: {e}") from e
    except orjson.JSONDecodeError as e:
        raise JSONLError(f"Invalid JSONL line: {e}") from e


def sample_jsonl(
    stream: Iterable[bytes],
    k: int,
    *,
    seed: int | float | str | bytes | bytearray | None = None,
) -> list[bytes]:
    """Sample k lines from a JSONL stream using reservoir sampling.

    Memory usage is O(k) regardless of stream length.
    Raises if fewer than k lines are available.
    """
    rng = random.Random(seed)
    reservoir: list[bytes] = []
    total = 0

    for line in stream:
        if total < k:
            reservoir.append(line)
        else:
            j = rng.randint(0, total)
            if j < k:
                reservoir[j] = line
        total += 1

    if total < k:
        raise JSONLError(f"Cannot sample {k} lines from {total} available.")

    return reservoir


def shuffle_jsonl(
    stream: Iterable[bytes],
    *,
    seed: int | float | str | bytes | bytearray | None = None,
) -> list[bytes]:
    """Shuffle JSON Lines using incremental forward Fisher-Yates.

    Builds the result line-by-line, swapping each new line with a random
    earlier position. Memory usage is O(n) where n is the number of lines.
    """
    rng = random.Random(seed)
    result: list[bytes] = []
    for k, line in enumerate(stream):
        result.append(line)
        j = rng.randint(0, k)
        if j < k:
            result[k], result[j] = result[j], result[k]
    return result


def dedup_jsonl(lines: Iterable[bytes]) -> list[bytes]:
    """Remove duplicate lines from JSON Lines.

    Keeps the first occurrence of each unique value.
    Empty lines are dropped.
    """
    seen: set[bytes] = set()
    result: list[bytes] = []
    for line in lines:
        if not line.strip():
            continue
        data = parse_line(line)
        if data is None:
            continue
        key = orjson.dumps(data)
        if key not in seen:
            seen.add(key)
            result.append(line.rstrip(b"\r\n"))
    return result


def rename_jsonl(lines: Iterable[bytes], old: str, new: str) -> list[bytes]:
    """Rename a top-level key in every non-empty JSONL object line.

    Empty lines are dropped.
    Raises JSONLError if any line is not an object,
    if the old key does not exist in any line, or if the new key already exists
    (unless new == old, in which case that line is passed through unchanged).
    """
    result: list[bytes] = []
    for line in lines:
        if not line.strip():
            continue
        data = parse_line(line)
        if data is None:
            continue
        if not isinstance(data, dict):
            raise JSONLError(f"JSONL line is not an object: {line!r}")
        if old not in data:
            raise JSONLError(f"Key {old!r} not found in JSONL line: {line!r}")
        if new in data and new != old:
            raise JSONLError(f"Key {new!r} already exists in JSONL line: {line!r}")
        if old == new:
            result.append(line.rstrip(b"\r\n"))
        else:
            renamed = {new if k == old else k: v for k, v in data.items()}
            result.append(orjson.dumps(renamed))
    return result


def select_jsonl(lines: Iterable[bytes], keys: list[str], strict: bool = False) -> list[bytes]:
    """Select specific keys from every non-empty JSONL object line.

    Empty lines are dropped.
    Each line must be a JSON object.
    Missing keys are silently omitted unless strict=True.
    """
    result: list[bytes] = []
    for line in lines:
        if not line.strip():
            continue
        data = parse_line(line)
        if data is None:
            continue
        if not isinstance(data, dict):
            raise JSONLError(f"JSONL line is not an object: {line!r}")
        if strict:
            missing = [k for k in keys if k not in data]
            if missing:
                raise JSONLError(f"Missing key(s) {', '.join(missing)} in JSONL line: {line!r}")
        selected = {k: data[k] for k in keys if k in data}
        result.append(orjson.dumps(selected))
    return result


def move_jsonl(lines: Iterable[bytes], keys: list[str], back: bool = False, strict: bool = False) -> list[bytes]:
    """Reorder keys in every non-empty JSONL object line.

    Empty lines are dropped.
    Each line must be a JSON object.
    """
    result: list[bytes] = []
    for line in lines:
        if not line.strip():
            continue
        data = parse_line(line)
        if data is None:
            continue
        if not isinstance(data, dict):
            raise JSONLError(f"JSONL line is not an object: {line!r}")
        if strict:
            missing = [k for k in keys if k not in data]
            if missing:
                raise JSONLError(f"Missing key(s) {', '.join(missing)} in JSONL line: {line!r}")
        existing = [k for k in keys if k in data]
        remaining = [k for k in data if k not in existing]
        order = remaining + existing if back else existing + remaining
        result.append(orjson.dumps({k: data[k] for k in order}))
    return result


def sort_jsonl(lines: list[bytes], sort_key: str, *, reverse: bool = False, strict: bool = False) -> list[bytes]:
    """Sort JSON Lines by a top-level key.

    Lines without the key or with a null value sort first.
    With strict=True, raises if any line is missing the key.
    Raises if the key exists with mixed types across lines.
    """
    entries = []
    for line in lines:
        data = parse_line(line)
        if data is None:
            continue
        if not isinstance(data, dict):
            raise JSONLError(f"JSONL line is not an object: {line!r}")
        if sort_key not in data:
            if strict:
                raise JSONLError(f"Missing key {sort_key!r} in JSONL line: {line!r}")
        entries.append(data)
    try:
        entries.sort(key=lambda x: (x.get(sort_key) is not None, x.get(sort_key)), reverse=reverse)
    except TypeError as e:
        ctx = (entry for entry in entries if sort_key in entry)
        first_seen_type = type(next(ctx))
        for entry in ctx:
            if type(entry[sort_key]) is not first_seen_type:
                raise JSONLError(
                    f"Cannot sort JSONL lines by key {sort_key!r} because they are of different types."
                    f" Expected {first_seen_type!r}, got {type(entry[sort_key])!r} in line: {orjson.dumps(entry)!r}"
                ) from e
    return [orjson.dumps(entry) for entry in entries]
