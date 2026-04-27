import sys

from cyclopts import App
from cyclopts.types import StdioPath

import lx_tools.lib.encoding as lx_encoding

app = App(name="encoding", help="Encoding detection and conversion utilities.")


@app.command
def detect(
    input: StdioPath = StdioPath("-"),
    output: StdioPath = StdioPath("-"),
    *,
    all: bool = False,
    verbose: bool = False,
) -> None:
    """Detect the encoding of input data."""
    data = input.read_bytes()
    result = lx_encoding.detect_encoding(data, all=all)
    if not result:
        sys.exit("Could not detect encoding of input data.")
    matches = result if isinstance(result, list) else [result]
    if verbose:
        lines = "\n".join(f"{match.encoding}\t{match.confidence:.4f}" for match in matches)
    else:
        lines = "\n".join(match.encoding for match in matches)
    output.write_text(lines + "\n")


@app.command
def recode(
    input: StdioPath = StdioPath("-"),
    output: StdioPath = StdioPath("-"),
    *,
    from_: str | None = None,
    to: str = "utf-8",
    errors: lx_encoding.RecodeErrors = "strict",
) -> None:
    """Re-encode data from one encoding to another."""
    data = input.read_bytes()
    output.write_bytes(lx_encoding.recode(data, from_, to, errors=errors))


@app.command
def add_bom(
    input: StdioPath = StdioPath("-"),
    output: StdioPath = StdioPath("-"),
    *,
    encoding: lx_encoding.BomEncoding = "utf-8",
) -> None:
    """Add a byte-order mark (BOM) to the data."""
    data = input.read_bytes()
    output.write_bytes(lx_encoding.add_bom(data, encoding))


@app.command
def strip_bom(
    input: StdioPath = StdioPath("-"),
    output: StdioPath = StdioPath("-"),
) -> None:
    """Remove any leading byte-order mark (BOM) from the data."""
    data = input.read_bytes()
    output.write_bytes(lx_encoding.strip_bom(data))
