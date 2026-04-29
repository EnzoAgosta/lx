import orjson


class JSONError(Exception):
    """Base class for JSON errors."""


def _loads(data: bytes) -> object:
    """Parse JSON bytes, wrapping orjson errors."""
    try:
        return orjson.loads(data)
    except orjson.JSONDecodeError as e:
        raise JSONError(f"Invalid JSON: {e}") from e


def sort_json(data: bytes) -> bytes:
    """Sort all JSON keys recursively."""
    return orjson.dumps(_loads(data), option=orjson.OPT_SORT_KEYS)


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


def reverse_json(data: bytes) -> bytes:
    """Sort top-level JSON keys ascending, then reverse their order.

    Note: Only top-level keys are affected. This is a convenience command;
    it parses, sorts, reverses, and re-serializes, which is deterministic
    but not efficient.
    """
    obj = _loads(data)
    sorted_bytes = orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
    sorted_obj = _loads(sorted_bytes)
    # Can't really properly type this, so we have to ignore the next line
    reversed_obj = {k: sorted_obj[k] for k in reversed(sorted_obj)}  # type: ignore
    return orjson.dumps(reversed_obj)


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
