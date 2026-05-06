import orjson


class JSONError(Exception):
    """Base class for JSON errors."""


def _loads(data: bytes) -> object:
    """Parse JSON bytes, wrapping orjson errors."""
    try:
        return orjson.loads(data)
    except orjson.JSONDecodeError as e:
        raise JSONError(f"Invalid JSON: {e}") from e


def _sort_array_by_key(array: list[object], key: str, *, reverse: bool = False, strict: bool = False) -> bytes:
    """Sort an array of objects by a top-level key."""
    entries = []
    for item in array:
        if not isinstance(item, dict):
            raise JSONError(
                f"All array elements must be objects when using --key. Got {type(item).__name__}: {orjson.dumps(item)!r}"
            )
        if key not in item:
            if strict:
                raise JSONError(f"Missing key {key!r} in object: {orjson.dumps(item)!r}")
        entries.append(item)
    try:
        entries.sort(key=lambda x: (x.get(key) is not None, x.get(key)), reverse=reverse)
    except TypeError as e:
        ctx = (entry for entry in entries if key in entry)
        first = next(ctx, None)
        if first is not None:
            first_type = type(first[key])
            for entry in ctx:
                if type(entry[key]) is not first_type:
                    raise JSONError(
                        f"Cannot sort by key {key!r} because values are of different types. "
                        f"Expected {first_type!r}, got {type(entry[key])!r} in object: {orjson.dumps(entry)!r}"
                    ) from e
        raise JSONError(f"Cannot sort by key {key!r}: {e}") from e
    return orjson.dumps(entries)


def sort_json(data: bytes, *, recurse: bool = False, key: str | None = None, strict: bool = False) -> bytes:
    """Sort JSON keys or array elements.

    By default only top-level keys are sorted.
    Use recurse=True to sort keys recursively in every nested object.
    """
    obj = _loads(data)
    match obj:
        case str() | int() | float() | bool() | None:
            raise JSONError("Input must be a JSON object or array.")
        case dict():
            if key is not None:
                raise JSONError("Cannot use --key with a JSON object.")
            if recurse:
                return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
            return orjson.dumps({k: obj[k] for k in sorted(obj)})
        case list():
            if key is not None:
                return _sort_array_by_key(obj, key, reverse=False, strict=strict)
            if recurse:
                return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
            try:
                return orjson.dumps(sorted(obj))
            except TypeError as e:
                raise JSONError(f"Cannot sort array with mixed types: {e}") from e
        case _:
            raise RuntimeError(f"Unexpected type: {type(obj)}")


def pretty_json(data: bytes) -> bytes:
    """Pretty-print JSON with 2-space indentation."""
    return orjson.dumps(_loads(data), option=orjson.OPT_INDENT_2)


def minify_json(data: bytes) -> bytes:
    """Minify JSON by removing unnecessary whitespace."""
    return orjson.dumps(_loads(data))


def validate_json(data: bytes) -> None:
    """Validate JSON syntax. Raises on invalid input."""
    _loads(data)


def reverse_json(data: bytes, *, key: str | None = None, strict: bool = False) -> bytes:
    """Reverse the order of top-level JSON keys or array elements.

    Only affects the top-level container. Nested objects are left untouched.
    Does not sort first — use `sort | reverse` if you need sorted-then-reversed.
    """
    obj = _loads(data)
    match obj:
        case str() | int() | float() | bool() | None:
            raise JSONError("Input must be a JSON object or array.")
        case dict():
            if key is not None:
                raise JSONError("Cannot use --key with a JSON object.")
            return orjson.dumps({k: obj[k] for k in reversed(list(obj))})
        case list():
            if key is not None:
                return _sort_array_by_key(obj, key, reverse=True, strict=strict)
            return orjson.dumps(list(reversed(obj)))
        case _:
            raise RuntimeError(f"Unexpected type: {type(obj)}")


def dedup_json(data: bytes) -> bytes:
    """Remove duplicate entries from a JSON array.

    Keeps the first occurrence of each unique value.
    """
    obj = _loads(data)
    if not isinstance(obj, list):
        raise JSONError("Input must be a JSON array.")
    seen: set[bytes] = set()
    result: list[object] = []
    for item in obj:
        key = orjson.dumps(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return orjson.dumps(result)


def rename_json(data: bytes, old: str, new: str) -> bytes:
    """Rename a top-level key in a JSON object.

    Preserves key order.
    Raises JSONError if the input is not an object,
    if the old key does not exist, or if the new key already exists
    (unless new == old, in which case it's a no-op).
    """
    obj = _loads(data)
    if not isinstance(obj, dict):
        raise JSONError("Input must be a JSON object.")
    if old not in obj:
        raise JSONError(f"Key {old!r} not found in object.")
    if new in obj and new != old:
        raise JSONError(f"Key {new!r} already exists in object.")
    if old == new:
        return data
    result = {new if k == old else k: v for k, v in obj.items()}
    return orjson.dumps(result)


def pluck_json(data: bytes, key: str) -> bytes:
    """Extract a top-level key value from a JSON object.

    Returns the value, not wrapped in an object.
    Raises JSONError if input is not an object or key is missing.
    """
    obj = _loads(data)
    if not isinstance(obj, dict):
        raise JSONError("Input must be a JSON object.")
    if key not in obj:
        raise JSONError(f"Key {key!r} not found in object.")
    return orjson.dumps(obj[key])


def select_json(data: bytes, keys: list[str], strict: bool = False) -> bytes:
    """Select specific keys from a JSON object.

    Output contains only the specified keys, in the order given.
    Missing keys are silently omitted unless strict=True.
    """
    obj = _loads(data)
    if not isinstance(obj, dict):
        raise JSONError("Input must be a JSON object.")
    if strict:
        missing = [k for k in keys if k not in obj]
        if missing:
            raise JSONError(f"Missing key(s) in object: {', '.join(missing)}")
    result = {k: obj[k] for k in keys if k in obj}
    return orjson.dumps(result)


def move_json(data: bytes, keys: list[str], back: bool = False, strict: bool = False) -> bytes:
    """Reorder keys in a JSON object.

    Moves specified keys to front or back, keeping remaining keys
    in their original order.
    """
    obj = _loads(data)
    if not isinstance(obj, dict):
        raise JSONError("Input must be a JSON object.")
    if strict:
        missing = [k for k in keys if k not in obj]
        if missing:
            raise JSONError(f"Missing key(s) in object: {', '.join(missing)}")
    existing = [k for k in keys if k in obj]
    remaining = [k for k in obj if k not in existing]
    order = remaining + existing if back else existing + remaining
    return orjson.dumps({k: obj[k] for k in order})


def to_jsonl(data: bytes) -> bytes:
    """Convert a JSON array to JSON Lines.

    Each element is serialized on its own line.
    Raises if input is not a JSON array.
    """
    obj = _loads(data)
    if not isinstance(obj, list):
        raise JSONError("Input must be a JSON array.")
    lines = b"\n".join(orjson.dumps(item) for item in obj)
    return lines + b"\n" if lines else b""
