import sys
from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import StdioPath

import lx_tools.lib.encoding as lx_encoding

app = App(name="encoding", help="Encoding detection and conversion utilities.")


@app.command
def detect(
    input: Annotated[StdioPath, Parameter(name="--input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="--output")] = StdioPath("-"),
    *,
    all: Annotated[bool, Parameter(name=["--all", "-a"])] = False,
    verbose: Annotated[bool, Parameter(name=["--verbose", "-v"])] = False,
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
    input: Annotated[StdioPath, Parameter(name="--input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="--output")] = StdioPath("-"),
    *,
    from_: Annotated[str | None, Parameter(name=["--from", "-f"])] = None,
    to: Annotated[str, Parameter(name=["--to", "-t"])] = "utf-8",
    errors: Annotated[lx_encoding.RecodeErrors, Parameter(name=["--errors", "-e"])] = "strict",
) -> None:
    """Re-encode data from one encoding to another."""
    data = input.read_bytes()
    output.write_bytes(lx_encoding.recode(data, from_, to, errors=errors))


@app.command
def add_bom(
    input: Annotated[StdioPath, Parameter(name="--input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="--output")] = StdioPath("-"),
    *,
    encoding: Annotated[lx_encoding.BomEncoding, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Add a byte-order mark (BOM) to the data."""
    data = input.read_bytes()
    output.write_bytes(lx_encoding.add_bom(data, encoding))


@app.command
def strip_bom(
    input: Annotated[StdioPath, Parameter(name="--input")] = StdioPath("-"),
    output: Annotated[StdioPath, Parameter(name="--output")] = StdioPath("-"),
) -> None:
    """Remove any leading byte-order mark (BOM) from the data."""
    data = input.read_bytes()
    output.write_bytes(lx_encoding.strip_bom(data))
