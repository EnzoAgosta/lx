import orjson


def sort_json(data: bytes) -> bytes:
    """Sort all JSON keys recursively."""
    return orjson.dumps(orjson.loads(data), option=orjson.OPT_SORT_KEYS)


def pretty_json(data: bytes) -> bytes:
    """Pretty-print JSON with 2-space indentation."""
    return orjson.dumps(orjson.loads(data), option=orjson.OPT_INDENT_2)


def minify_json(data: bytes) -> bytes:
    """Minify JSON by removing unnecessary whitespace."""
    return orjson.dumps(orjson.loads(data))


def validate_json(data: bytes) -> None:
    """Validate JSON syntax. Raises on invalid input."""
    orjson.loads(data)
