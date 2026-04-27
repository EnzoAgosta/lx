import codecs
from typing import Literal, NamedTuple

from charset_normalizer import from_bytes


class EncodingMatch(NamedTuple):
    encoding: str
    confidence: float


BomEncoding = Literal[
    "utf-8",
    "utf-8-sig",
    "utf-16-be",
    "utf-16-le",
    "utf-32-be",
    "utf-32-le",
]

RecodeErrors = Literal["strict", "replace", "ignore"]


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


def recode(data: bytes, from_encoding: str | None, to_encoding: str, *, errors: RecodeErrors = "strict") -> bytes:
    """Re-encode data from one encoding to another."""
    if from_encoding is None:
        detected = detect_encoding(data)
        if detected is None:
            raise ValueError("Could not auto-detect source encoding.")
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


def add_bom(data: bytes, encoding: BomEncoding = "utf-8") -> bytes:
    """Add a BOM for the given encoding."""
    encoding = encoding.lower().replace("_", "-")
    key = encoding if encoding in _BOMS else f"{encoding}-sig"
    if key not in _BOMS:
        raise ValueError(f"No BOM defined for encoding: {encoding}")
    bom = _BOMS[key]
    stripped = strip_bom(data)
    return bom + stripped


def strip_bom(data: bytes) -> bytes:
    """Remove any leading BOM from data."""
    for bom in _BOMS.values():
        if data.startswith(bom):
            return data.removeprefix(bom)
    return data
