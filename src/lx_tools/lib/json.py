import orjson


def sort_json(data: bytes) -> bytes:
    """Sort all JSON keys recursively."""
    return orjson.dumps(orjson.loads(data), option=orjson.OPT_SORT_KEYS)


def pretty_json(data: bytes) -> bytes:
    """Pretty-print JSON with 2-space indentation."""
    return orjson.dumps(orjson.loads(data), option=orjson.OPT_INDENT_2)
