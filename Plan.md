# Implementation Plan: New CLI Commands

## Overview

Add 8 new commands across `jsonl`, `encoding`, and `csv` sub-apps. All commands follow the existing patterns: `StdioPath` input/output, `check_empty_stdin` guard, lib/cli separation, and cyclopts validators.

---

## 1. `jsonl sort` / `jsonl reverse`

### Files touched

- `src/lx_tools/lib/jsonl.py` — add `sort_jsonl()`
- `src/lx_tools/cli/jsonl.py` — add `sort` and `reverse` commands

### Lib function

```python
def sort_jsonl(lines: list[bytes], key: str, *, reverse: bool = False, strict: bool = False) -> list[bytes]:
    """Sort JSON Lines by a top-level key.

    Missing keys sort as None (null). With strict=True, raises if any line
    is missing the key.
    """
```

**Behavior:**

- Parse each line with `parse_line()`
- Extract `key` from each dict; if missing → `None` (or raise if `strict`)
- Sort lines by extracted value using `orjson.dumps(value)` as sort key for cross-type determinism
- Return re-serialized lines in sorted order

### CLI signatures

```python
@app.command
def sort(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str, Parameter(name=["--key", "-k"])],
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort JSON Lines by a top-level key in ascending order."""

@app.command
def reverse(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    key: Annotated[str, Parameter(name=["--key", "-k"])],
    strict: Annotated[bool, Parameter(name=["--strict", "-s"])] = False,
) -> None:
    """Sort JSON Lines by a top-level key in descending order."""
```

**Error cases:**

- Missing `--key` → cyclopts handles (required param)
- Invalid JSONL line → `sys.exit(str(e))`
- `strict=True` and key missing → `sys.exit(...)`

---

## 2. `encoding check`

### Files touched

- `src/lx_tools/lib/encoding.py` — add `check_encoding()`
- `src/lx_tools/cli/encoding.py` — add `check` command

### Lib function

```python
import codecs

def check_encoding(data: bytes, expected: str) -> str:
    """Detect encoding and verify it matches *expected*.

    Returns the detected encoding name on match.
    Raises ValueError on mismatch or failed detection.
    """
```

**Behavior:**

- Detect encoding via `detect_encoding(data)`
- Normalize both detected and expected with `codecs.lookup(name).name`
- If match → return detected encoding
- If mismatch → raise `ValueError(f"Expected {expected_norm}, detected {detected_norm}")`
- If detection fails → propagate `ValueError("Could not detect encoding...")`

### CLI signature

```python
@app.command
def check(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    expected: Annotated[str, Parameter(name=["--expected", "-e"])],
) -> None:
    """Detect encoding and verify it matches the expected one.
    If valid, passes the input data through unchanged for chaining.
    """
```

**Chaining example:**

```bash
lx encoding check --expected utf-8 file.txt | lx encoding recode --to utf-8
```

---

## 3. `csv count`

### Files touched

- `src/lx_tools/lib/csv.py` — add `count_csv()`
- `src/lx_tools/cli/csv.py` — add `count` command

### Lib function

```python
def count_csv(text: str, *, header: bool = False) -> int:
    """Count rows in CSV text.
    Returns data rows only if header=True, else all rows."""
```

**Behavior:**

- Parse with `_parse_csv(text, header=header)`
- Return `len(rows)` (already excludes header when `header=True`)

### CLI signature

```python
@app.command
def count(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Count CSV rows."""
```

---

## 4. `csv head` / `csv tail`

### Files touched

- `src/lx_tools/lib/csv.py` — add `head_csv()` and `tail_csv()`
- `src/lx_tools/cli/csv.py` — add `head` and `tail` commands

### Lib functions

```python
def head_csv(text: str, n: int, *, header: bool = False) -> str:
    """Return the first N data rows, preserving header if present."""

def tail_csv(text: str, n: int, *, header: bool = False) -> str:
    """Return the last N data rows, preserving header if present."""
```

**Behavior:**

- Parse with `_parse_csv(text, header=header)`
- `head`: slice `rows[:n]`
- `tail`: slice `rows[-n:]`
- If header present → prepend to result
- Write with `_write_csv()`

### CLI signatures

```python
@app.command
def head(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Output the first N data rows. Preserves header if --header."""

@app.command
def tail(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    lines: Annotated[int, Parameter(name=["--lines", "-n"], validator=validators.Number(gt=0))] = 10,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Output the last N data rows. Preserves header if --header."""
```

---

## 5. `csv shuffle` / `csv sample`

### Files touched

- `src/lx_tools/lib/csv.py` — add `shuffle_csv()` and `sample_csv()`
- `src/lx_tools/cli/csv.py` — add `shuffle` and `sample` commands

### Lib functions

```python
import random

def shuffle_csv(text: str, *, header: bool = False, seed: object = None) -> str:
    """Shuffle CSV rows randomly. Preserves header if present."""

def sample_csv(text: str, n: int, *, header: bool = False, seed: object = None) -> str:
    """Sample N rows without replacement. Preserves header if present."""
```

**Behavior:**

- Parse with `_parse_csv(text, header=header)`
- `shuffle`: apply `random.shuffle(rows)`
- `sample`: apply `random.sample(rows, k=n)` (guard against `ValueError`)
- If header present → prepend to result
- Write with `_write_csv()`

### CLI signatures

```python
@app.command
def shuffle(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    seed: Annotated[int | float | str, Parameter(name=["--seed", "-s"])] = None,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Shuffle CSV rows randomly. Preserves header if --header."""

@app.command
def sample(
    input: InputType = StdioPath("-"),
    output: OutputType = StdioPath("-"),
    *,
    n: Annotated[int, Parameter(name=["--n", "-n"], validator=validators.Number(gt=0))] = 10,
    seed: Annotated[int | float | str, Parameter(name=["--seed", "-s"])] = None,
    header: Annotated[bool, Parameter(name=["--header", "-H"])] = False,
    encoding: Annotated[str, Parameter(name=["--encoding", "-e"])] = "utf-8",
) -> None:
    """Sample N rows without replacement. Preserves header if --header."""
```

**Error cases:**

- Sample N > available rows → `sys.exit(f"Cannot sample {n} rows from {len(rows)} available.")`

---

## Testing Checklist

| Command                           | Test                                             |
| --------------------------------- | ------------------------------------------------ |
| `jsonl sort --key name`           | Piped JSONL sorts ascending by key               |
| `jsonl reverse --key name`        | Piped JSONL sorts descending by key              |
| `jsonl sort --key name --strict`  | Missing key → error                              |
| `encoding check --expected utf-8` | Matching encoding → pass-through                 |
| `encoding check --expected ascii` | Mismatch → error                                 |
| `csv count`                       | Piped CSV → correct count                        |
| `csv count --header`              | Header excluded from count                       |
| `csv head -n 2 --header`          | Header + 2 data rows                             |
| `csv tail -n 2 --header`          | Header + last 2 data rows                        |
| `csv shuffle --seed 42 --header`  | Deterministic shuffle, header preserved          |
| `csv sample -n 2 --header`        | Header + 2 random data rows                      |
| `csv sample -n 999`               | Too few rows → error                             |
| All new commands                  | `check_empty_stdin` fires on bare TTY invocation |

---

## Rollout Order

1. **Lib layer first** — implement all lib functions in `jsonl.py`, `encoding.py`, `csv.py`
2. **CLI layer second** — wire up commands in `jsonl.py`, `encoding.py`, `csv.py`
3. **Test third** — run each command with stdin, file input, and edge cases
