import orjson


class JSONError(Exception):
    """Base class for JSON errors."""


def _loads(data: bytes) -> object:
    """Parse JSON bytes, wrapping orjson errors."""
    try:
        return orjson.loads(data)
    except orjson.JSONDecodeError as e:
        raise JSONError(f"Invalid JSON: {e}") from e


def _sort_array_by_key(array: list, key: str, *, reverse: bool = False, strict: bool = False) -> bytes:
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


def pretty_json(data: bytes, *, sort_keys: bool = False) -> bytes:
    """Pretty-print JSON with 2-space indentation."""
    option = orjson.OPT_INDENT_2 | (orjson.OPT_SORT_KEYS if sort_keys else 0)
    return orjson.dumps(_loads(data), option=option)


def minify_json(data: bytes, *, sort_keys: bool = False) -> bytes:
    """Minify JSON by removing unnecessary whitespace."""
    option = orjson.OPT_SORT_KEYS if sort_keys else 0
    return orjson.dumps(_loads(data), option=option)


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
