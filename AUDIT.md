# lx-tools Code Audit

Date: 2026-04-29
Status: Issues identified, fixes pending discussion

---

## 🔴 Bugs / Broken things

### 1. `lx json validate` is broken
- `lib/json.py`: `validate_json()` returns `None`.
- `cli/json.py`: `output.write_bytes(lx_json.validate_json(...))` tries to write `None`. That'll raise `TypeError`.
- **Fix:** Return `data` from `validate_json`, or have the CLI not try to write the return value.

### 2. `jsonl sort` / `reverse` sorts by serialized bytes, not by value
- `lib/jsonl.py` line 70: `entries.append((orjson.dumps(value), line))`, then sorts by that.
- This means numbers sort lexicographically as JSON strings: `10` comes before `2` because `b"10" < b"2"`.
- Sorting ages `[10, 2, 1]` gives `[1, 10, 2]` instead of `[1, 2, 10]`.
- **Fix:** Use a tuple-based sort key that preserves type ordering, or extract Python values.

### 3. Global `random.seed()` mutation
- `csv shuffle/sample` and `jsonl shuffle/sample` call `random.seed(seed)` globally.
- This poisons the global `random` state for anything else in the process.
- **Fix:** Use `rng = random.Random(seed); rng.shuffle(...)` / `rng.sample(...)` instead.

---

## 🟡 Architecture / Abstraction questions

### 4. The `lib/` layer is very thin for JSON/JSONL
- `lib/json.py` is 62 lines of orjson wrappers.
- `lib/jsonl.py` is 73 lines.
- `cli/json.py` is 160 lines, `cli/jsonl.py` is 349 lines. Most of the real code is in the CLI.
- **Question:** Is `lib/` meant to be a public Python API? If not, some of these wrappers are abstraction for abstraction's sake. If yes, the CLI modules should probably not `import orjson` directly (but `jsonl.py` CLI does, see #10).

### 5. `lib/csv.py` API inconsistency: `str` vs `TextIO`
- `sort_csv_by_name(text: str)` takes a string.
- `select_column_by_name(stream: TextIO)` takes a stream.
- No obvious reason for the split. `sort` could stream just as easily, or `select` could take `text`. Pick one.

### 6. `InputType` / `OutputType` type aliases are CLI-only but live in `cli/__init__.py`
- They're `Annotated[StdioPath, Parameter(...)]` — tightly coupled to cyclopts.
- That's fine if lib functions stay pure (`bytes`/`str`). Just noting that the "reusable library" pitch is slightly undermined by the type aliases being CLI-specific.

### 7. `check_empty_stdin` passes command name manually
- Every command: `check_empty_stdin(input, app, ["sort"])`.
- Could cyclopts introspection give you the current command name? Or is explicit better here?

---

## 🟠 Complexity / Overengineering

### 8. `_get_indices_from_names` uses `float("inf")` for missing columns
- When a name isn't found and `strict=False`, it appends `float("inf")` as a placeholder index.
- `_get_cells` then sees `idx >= len(source)` and emits `""`.
- This is clever but magical. A separate "not found" sentinel or just checking membership inline would be more obvious.

### 9. `remove_column_by_index` duplicates header/no-header logic
- Lines 156-175 have two separate branches with overlapping CSV writer setup. Could be unified.

### 10. `jsonl` CLI imports `orjson` directly
- Line 7: `import orjson` in `cli/jsonl.py`, used in `pluck` and `to_json`.
- If `lib/` is the abstraction layer, the CLI shouldn't touch orjson. `lib/jsonl.py` should provide `serialize(obj) -> bytes`.

### 11. `detect_encoding` returns a union type based on a boolean flag
- `def detect_encoding(..., all: bool) -> EncodingMatch | list[EncodingMatch] | None`
- This forces callers to do `isinstance(result, list)`. Two functions (`detect_encoding` / `detect_all_encodings`) would be cleaner and more type-safe.

### 12. `BomEncoding` Literal accepts both `"utf-8"` and `"utf-8-sig"`
- `add_bom` normalizes `"utf-8"` → `"utf-8-sig"` anyway. Having both in the type is redundant.

### 13. `reverse_json` serializes, deserializes, rebuilds, serializes
- `orjson.dumps(obj, OPT_SORT_KEYS)` → `loads()` → dict comprehension → `dumps()`.
- For top-level keys only, you could just do `{k: obj[k] for k in reversed(sorted(obj))}` in pure Python and save a round-trip.

### 14. CSV `select`/`remove` use comma-separated strings instead of repeated flags
- `--names Name,Email` instead of `--name Name --name Email`.
- Cyclopts natively supports `list[str]` with repeated flags. The comma-split approach is less idiomatic and requires manual `.split(",")` + `.strip()`.

### 15. `pyproject.toml` requires Python `>=3.14`
- Python 3.14 isn't even released yet. Your code uses `str | None` (3.10+) and type aliases (3.12+). Unless you're using 3.14-specific features, this prevents anyone on 3.12/3.13 from installing it.

---

## 🟢 Nitpicks / Minor

### 16. `jsonl validate` normalizes line endings
- It strips `\r\n` and rejoins with `\n`. Other commands do this too. Intentional? Just noting it mutates the file.

### 17. `jsonl pluck` silently skips with no `--strict` option
- `sort` and `reverse` have `--strict` for missing keys. `pluck` doesn't. Maybe intentional, maybe an oversight.

### 18. `check_encoding` leaks `LookupError`
- `codecs.lookup(expected)` can raise if the user passes garbage. No catch → ugly traceback.

### 19. `_parse_csv` materializes everything via `list(csv.reader(...))`
- `head`, `tail`, `count` in the lib all call `_parse_csv` or `csv.reader`. For `head` and `count`, streaming would work. But given `sort`/`shuffle`/`sample` need everything anyway, maybe not worth changing.

### 20. `only_one` group in CSV CLI
- It's a module-level `Group` object used for multiple commands. Fine, but the name `only_one` doesn't explain *what* is mutually exclusive.

---

## Meta Question

### What is `lib/` for?
- If it's a public Python API for other projects: keep it, but make the CLI not bypass it (orjson imports in `cli/jsonl.py`).
- If it's only there to keep CLI files shorter: some modules (`lib/json.py`, `lib/jsonl.py`) are so thin they might not justify the indirection. The error handling and I/O logic dominates the CLI files anyway.
- The split is worth keeping for CSV and encoding, but for JSON/JSONL the CLI files are doing almost all the work while the lib files just add a layer of `try/except` wrapping around orjson.
