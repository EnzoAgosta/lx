import codecs
from typing import Literal, NamedTuple, overload

from charset_normalizer import from_bytes


class EncodingMatch(NamedTuple):
    encoding: str
    confidence: float


class EncodingError(Exception):
    pass


BomEncoding = Literal[
    "utf-8-sig",
    "utf-16-be",
    "utf-16-le",
    "utf-32-be",
    "utf-32-le",
]

RecodeErrors = Literal["strict", "replace", "ignore"]


@overload
def detect_encoding(data: bytes, all: Literal[False] = False) -> EncodingMatch | None: ...
@overload
def detect_encoding(data: bytes, all: bool = False) -> list[EncodingMatch] | None: ...
def detect_encoding(data: bytes, all: bool = False) -> EncodingMatch | list[EncodingMatch] | None:
    """Detect the encoding of byte data.

    Returns the best match by default, or all matches sorted by confidence
    when *all* is True.
    """
    result = from_bytes(data)
    best = result.best()
    if best is None:
        return None
    if all:
        return [EncodingMatch(m.encoding, m.coherence) for m in result]
    return EncodingMatch(best.encoding, best.coherence)


def check_encoding(data: bytes, expected: str) -> str:
    """Detect encoding and verify it matches *expected*.

    Returns the detected encoding name on match.
    Raises ValueError on mismatch or failed detection.
    """
    detected = detect_encoding(data)
    if detected is None:
        raise EncodingError("Could not detect encoding.")
    try:
        expected_norm = codecs.lookup(expected).name
        detected_norm = codecs.lookup(detected.encoding).name
    except LookupError as e:
        raise EncodingError(f"Unknown encoding: {e}") from e
    if expected_norm == detected_norm:
        return detected.encoding
    # ASCII is a valid subset of UTF-8
    if expected_norm == "utf-8" and detected_norm == "ascii":
        return detected.encoding
    raise EncodingError(f"Expected {expected_norm}, detected {detected_norm}")


def recode(data: bytes, from_encoding: str | None, to_encoding: str, *, errors: RecodeErrors = "strict") -> bytes:
    """Re-encode data from one encoding to another."""
    if from_encoding is None:
        detected = detect_encoding(data)
        if detected is None:
            raise EncodingError("Could not auto-detect source encoding.")
        from_encoding = detected.encoding
    text = data.decode(from_encoding, errors=errors)
    return text.encode(to_encoding, errors=errors)


_BOMS = {
    "utf-8-sig": codecs.BOM_UTF8,
    "utf-16-be": codecs.BOM_UTF16_BE,
    "utf-16-le": codecs.BOM_UTF16_LE,
    "utf-32-be": codecs.BOM_UTF32_BE,
    "utf-32-le": codecs.BOM_UTF32_LE,
}


def add_bom(data: bytes, encoding: BomEncoding = "utf-8-sig") -> bytes:
    """Add a BOM for the given encoding."""
    # cyclopts handles validating `encoding` value
    stripped = strip_bom(data)
    return _BOMS[encoding] + stripped


def strip_bom(data: bytes) -> bytes:
    """Remove any leading BOM from data.

    Checks longest BOMs first to avoid partial matches
    (e.g. UTF-16-LE BOM is a prefix of UTF-32-LE BOM).
    """
    for bom in sorted(_BOMS.values(), key=len, reverse=True):
        if data.startswith(bom):
            return data.removeprefix(bom)
    return data
