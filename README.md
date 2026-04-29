# lx

A pipe-friendly Swiss-army knife CLI for data manipulation.

> **Design principle:** `lx` manipulates data structure. It does not query.
>
> Named-key extraction (`pluck`, `get`, `select`) is only provided as a convenience when the target is unambiguously a Python `dict`. If you need traversal, indexing, conditionals, or expressions — use `jq`, `yq`, `xsv`, or another specialist tool. `lx` is meant to be used _alongside_ them, not as a replacement.

Every command defaults to reading from `stdin` and writing to `stdout`, so `lx` composes naturally with other Unix tools.

> **Status:** Early development (`v0.1.0`). APIs and command names may change.

---

## Features

- **JSON** – pretty-print, minify, validate, sort keys (recursively or by array key), reverse key or array order, convert to JSON Lines
- **JSON Lines** – count, head, tail, validate, sort and reverse-sort by key, pluck fields, shuffle, sample, convert to a JSON array
- **CSV** – sort and reverse-sort by column name or index, select or remove columns, count rows, head, tail, shuffle, sample
- **Encoding** – detect (with confidence scores), check against an expected encoding, recode, add or strip BOM

Built on [**orjson**](https://github.com/ijl/orjson) for fast JSON handling and [**charset-normalizer**](https://github.com/Ousret/charset_normalizer) for encoding detection.

---

## Installation

`lx` is designed to be installed and run via [**uv**](https://docs.astral.sh/uv/).

### Run without installing

```bash
uvx lx --help
uvx lx json pretty data.json
```

### Install as a tool

```bash
uv tool install lx-tools
lx --help
```

`uv` handles the virtual environment, Python version, and `PATH` automatically.

### From source (development)

```bash
git clone https://github.com/enzo-agosta/lx-tools.git
cd lx-tools
uv sync
```

---

## Usage

`lx` is organized into sub-commands by data format. Every command accepts file arguments or reads from `stdin` and writes to `stdout` by default.

### JSON

```bash
# Pretty-print (2-space indent)
lx json pretty data.json

# Minify
lx json minify data.json > data.min.json

# Validate and pass through unchanged
lx json validate data.json | lx json pretty

# Sort top-level keys (or array elements)
lx json sort messy.json

# Sort keys recursively in every nested object
lx json sort --recurse messy.json

# Sort an array of objects by a top-level key
lx json sort --key age users.json

# Reverse top-level keys or array order
lx json reverse '{"a":1,"b":2,"c":3}'

# Reverse-sort an array of objects by key
lx json reverse --key age users.json

# Convert a JSON array to JSON Lines
cat array.json | lx json to-jsonl
```

### JSON Lines

```bash
# Count valid, non-empty lines
lx jsonl count data.jsonl

# First/last N lines (defaults to 10)
lx jsonl head -n 5 data.jsonl
lx jsonl tail -n 20 data.jsonl

# Validate every non-empty line
lx jsonl validate data.jsonl | lx jsonl sort --key name

# Sort lines by a top-level key
lx jsonl sort --key timestamp data.jsonl

# Reverse-sort by key (missing keys sort last)
lx jsonl reverse --key timestamp data.jsonl

# Extract a field from each object
lx jsonl pluck --key user_id data.jsonl

# Convert JSON Lines to a JSON array
lx jsonl to-json data.jsonl

# Shuffle randomly (use --seed for reproducibility)
lx jsonl shuffle --seed 42 data.jsonl

# Sample N lines without replacement
lx jsonl sample -n 100 --seed 42 data.jsonl
```

### CSV

```bash
# Sort by column name (requires --header)
lx csv sort --header --name Age data.csv

# Sort by zero-based column index
lx csv sort --index 2 data.csv

# Reverse-sort by column name
lx csv reverse --header --name Age data.csv

# Keep only specific columns (first row treated as header)
lx csv select --names Name,Email data.csv

# Keep columns by index
lx csv select --indices 0,2,4 data.csv

# Drop columns by name
lx csv remove --names Password,InternalID data.csv

# Count rows (--header excludes the first row)
lx csv count --header data.csv

# First/last N data rows (preserves header)
lx csv head -n 5 --header data.csv
lx csv tail -n 5 --header data.csv

# Shuffle or sample rows (preserves header)
lx csv shuffle --seed 42 --header data.csv
lx csv sample -n 100 --seed 42 --header data.csv
```

### Encoding

```bash
# Detect encoding
lx encoding detect file.txt

# See all candidates with confidence scores
lx encoding detect --all --long file.txt

# Check against an expected encoding (passes through on match)
lx encoding check --expected utf-8 file.txt

# Recode from one encoding to another
lx encoding recode --from latin1 --to utf-8 file.txt

# Add a BOM (strips any existing BOM first)
lx encoding add-bom --encoding utf-16-le file.txt

# Strip BOM
lx encoding strip-bom file.txt
```

### Flags you will reach for often

- `--strict` – on `sort`, `reverse`, and `pluck` commands: raise an error instead of silently skipping rows or objects that lack the requested key.
- `--seed` – on `shuffle` and `sample` commands: make random output reproducible.
- `--raw-lines` – on `jsonl head`, `tail`, `shuffle`, and `sample`: skip JSON validation and treat the input as plain text lines.
- `--recurse` – on `json sort`: sort keys recursively inside nested objects.
- `--header` – on CSV commands: treat the first row as a header and preserve it through the operation.

### Piping examples

```bash
# Stable diff between two JSON files
lx json sort --recurse a.json > a.sorted.json
lx json sort --recurse b.json > b.sorted.json
diff a.sorted.json b.sorted.json

# Chain multiple operations
curl -s https://api.example.com/data.json \
  | lx jsonl to-json \
  | lx json sort --key id \
  | lx json pretty \
  | lx encoding add-bom --encoding utf-8 \
  > sorted.json

# Sample CSV, then select columns
lx csv sample huge.csv --header -n 1000 - | lx csv select --names colA,colB --output subset.csv

# Query YAML with yq, then format with lx
cat config.yml | yq '.services.web' | lx json pretty --output config.web.json

# Detect and recode in one shot
lx encoding detect --all --long legacy.txt
lx encoding recode --from windows-1252 --to utf-8 legacy.txt legacy.utf8.txt
```

---

## Architecture

The project separates **CLI concerns** from **reusable library logic**:

```text
src/lx_tools/
├── cli/        # cyclopts-based command-line interface
│   ├── csv.py
│   ├── encoding.py
│   ├── json.py
│   └── jsonl.py
└── lib/        # Pure functions and core business logic
    ├── csv.py
    ├── encoding.py
    ├── json.py
    └── jsonl.py
```

- CLI modules handle argument parsing, I/O wiring, and error formatting.
- Library modules are importable and can be used independently in other Python projects.

---

## Development

```bash
# Sync dependencies
uv sync

# Run the CLI in the project environment
uv run lx --help

# Build and publish (CI handles releases via Trusted Publishing)
uv build
```

---

## Contributing

Contributions are welcome! Because the project is still in its early stages, opening an issue to discuss larger changes before submitting a PR is appreciated.

---

## License

MIT
