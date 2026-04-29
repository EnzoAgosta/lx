import sys
from typing import Annotated

from cyclopts import App, Parameter
from cyclopts.types import StdioPath

from lx_tools.cli import InputType, OutputType, check_empty_stdin
import lx_tools.lib.encoding as lx_encoding

app = App(
    name="encoding",
    help="""Encoding detection and conversion utilities.
    
    Relies on charset_normalizer for detection.
""",
)


@app.command
def detect(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    all: Annotated[bool, Parameter(name=["--all", "-a"])] = False,
    long: Annotated[bool, Parameter(name=["--long", "-l"])] = False,
) -> None:
    """Tries to detect the encoding of input data.

    This is usually unreliable on short strings/text files
    that don't contain any BOM. Use --all to see all candidates
    or try to feed more data to improve the detection.

    Outputs the name of the most likely detected encoding.

    Use --all to see every candidate sorted by confidence.

    Use --long to include confidence scores.

    Example: lx encoding detect --all --long file.txt

    Options
    -------
    --all, -a
        Show all candidate encodings instead of just the best match.
    --long, -l
        Include confidence scores (tab-separated).
    """
    check_empty_stdin(input, app, ["detect"])
    data = input.read_bytes()
    result = lx_encoding.detect_encoding(data, all=all)
    if not result:
        sys.exit("Could not detect encoding of input data.")
    matches = result if isinstance(result, list) else [result]
    if long:
        lines = "\n".join(f"{match.encoding}\t{match.confidence:.4f}" for match in matches)
    else:
        lines = "\n".join(match.encoding for match in matches)
    output.write_text(lines + "\n")


@app.command
def check(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    expected: Annotated[str, Parameter(name=["--expected", "-e"])],
) -> None:
    """Convenience command to check the encoding of input data.

    Simply calls lx encoding detect and checks that the detected encoding
    matches the expected one.

    If the detected encoding matches --expected, the input data is passed
    through unchanged so you can use this as a guard in a pipeline.

    Plain ASCII text is accepted when --expected is utf-8.

    Example: lx encoding check --expected utf-8 file.txt

    Options
    -------
    --expected, -e
        The encoding you expect the input to be in (required).
    """
    check_empty_stdin(input, app, ["check"])
    data = input.read_bytes()
    try:
        lx_encoding.check_encoding(data, expected)
    except lx_encoding.EncodingError as e:
        sys.exit(str(e))
    output.write_bytes(data)


@app.command
def recode(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    from_encoding: Annotated[str | None, Parameter(name=["--from", "-f"])] = None,
    to_encoding: Annotated[str, Parameter(name=["--to", "-t"])] = "utf-8",
    errors: Annotated[lx_encoding.RecodeErrors, Parameter(name=["--errors", "-e"])] = "strict",
) -> None:
    """Re-encode data from one encoding to another.

    If --from is omitted the source encoding is auto-detected.

    The output is always written in the --to encoding.

    Example: lx encoding recode --from latin-1 --to utf-8 latin1.txt

    Options
    -------
    --from, -f
        Source encoding (auto-detected if omitted).
    --to, -t
        Target encoding (default: utf-8).
    --errors, -e
        Error handling: strict | replace | ignore (default: strict).
    """
    check_empty_stdin(input, app, ["recode"])
    data = input.read_bytes()
    try:
        output.write_bytes(lx_encoding.recode(data, from_encoding, to_encoding, errors=errors))
    except lx_encoding.EncodingError as e:
        sys.exit(str(e))


@app.command
def add_bom(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    encoding: Annotated[lx_encoding.BomEncoding, Parameter(name=["--encoding", "-e"])],
) -> None:
    """Add a byte-order mark (BOM) to the data.

    Prepends the appropriate BOM for the given encoding.
    Any existing BOM is stripped first so the result has exactly one BOM.

    Example: lx encoding add_bom --encoding utf-16-le file.txt

    Options
    -------
    --encoding, -e
        Encoding to add a BOM for (required).
    """
    check_empty_stdin(input, app, ["add_bom"])
    data = input.read_bytes()
    output.write_bytes(lx_encoding.add_bom(data, encoding))


@app.command
def strip_bom(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
) -> None:
    """Remove any leading byte-order mark (BOM) from the data.

    Supports UTF-8, UTF-16 and UTF-32 BOM variants.
    If no BOM is present the data is passed through unchanged.

    Example: lx encoding strip_bom file.txt
    """
    check_empty_stdin(input, app, ["strip_bom"])
    data = input.read_bytes()
    output.write_bytes(lx_encoding.strip_bom(data))
