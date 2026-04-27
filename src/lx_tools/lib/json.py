import orjson


def sort_json(data: bytes) -> bytes:
    """Sort all JSON keys recursively."""
    return orjson.dumps(orjson.loads(data), option=orjson.OPT_SORT_KEYS)


def pretty_json(data: bytes, *, sort_keys: bool = False) -> bytes:
    """Pretty-print JSON with 2-space indentation."""
    option = orjson.OPT_INDENT_2 | (orjson.OPT_SORT_KEYS if sort_keys else 0)
    return orjson.dumps(orjson.loads(data), option=option)


def minify_json(data: bytes, *, sort_keys: bool = False) -> bytes:
    """Minify JSON by removing unnecessary whitespace."""
    option = orjson.OPT_SORT_KEYS if sort_keys else 0
    return orjson.dumps(orjson.loads(data), option=option)


def validate_json(data: bytes) -> None:
    """Validate JSON syntax. Raises on invalid input."""
    orjson.loads(data)
