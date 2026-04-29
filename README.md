# lx

A pipe-friendly Swiss-army knife CLI for data manipulation.

> **Design principle:** `lx` manipulates data structure. It does not query.
>
> Named-key extraction (`pluck`, `get`, `select`) is only provided as a convenience when the target is unambiguously a Python `dict`. If you need traversal, indexing, conditionals, or expressions — use `jq`, `yq`, `xsv`, or another specialist tool. `lx` is meant to be used _alongside_ them, not as a replacement.

Every command defaults to reading from `stdin` and writing to `stdout`, so `lx` composes naturally with other Unix tools.

> **Status:** Early development (`v0.0.1`). APIs and command names may change.

---

## Features

- **JSON** – sort keys, pretty-print, minify, validate, reverse key order, convert to JSON Lines
- **JSON Lines** – count, head, tail, validate, sort, pluck fields, shuffle, sample, convert to JSON array
- **CSV** – sort, reverse, select/remove columns, count rows, head, tail, shuffle, sample
- **Encoding** – detect, check, recode, add/strip BOM

Built on [**orjson**](https://github.com/ijl/orjson) for fast JSON handling and [**charset-normalizer**](https://github.com/Ousret/charset_normalizer) for encoding detection.

---

## Installation

`lx` is designed to be installed and run via [**uv**](https://docs.astral.sh/uv/).

### Run without installing

```bash
uvx lx --help
uvx lx json pretty --sort-keys data.json
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
# Pretty-print with sorted keys
lx json pretty --sort-keys data.json

# Minify
lx json minify data.json > data.min.json

# Validate
lx json validate data.json

# Convert a JSON array to JSON Lines
cat array.json | lx json to-jsonl
```

### JSON Lines

```bash
# Count valid, non-empty lines
lx jsonl count data.jsonl

# First/last N lines
lx jsonl head 10 data.jsonl
lx jsonl tail 5 data.jsonl

# Sort lines by a top-level key
lx jsonl sort --key timestamp data.jsonl

# Extract a field from each object
lx jsonl pluck user_id data.jsonl

# Convert JSON Lines to a JSON array
lx jsonl to-json data.jsonl
```

### CSV

```bash
# Sort by column name (requires --header)
lx csv sort --header --name Age data.csv

# Keep only specific columns
lx csv select --header --name Name --name Email data.csv

# Drop columns
lx csv remove --header --name InternalID data.csv

# Random sample of 100 rows
lx csv sample --header 100 data.csv
```

### Encoding

```bash
# Detect encoding
lx encoding detect file.txt

# Recode from one encoding to another
lx encoding recode --from latin1 --to utf-8 file.txt

# Strip BOM
lx encoding strip-bom file.txt
```

### Piping examples

```bash
# Chain multiple operations
curl -s https://api.example.com/data.json \
  | lx jsonl to-json \
  | lx json pretty --sort-keys \
  | lx encoding add-bom \
  > sorted.json

# Sample CSV, then select columns
cat huge.csv | lx csv sample --header 1000 - | lx csv select --header --name colA --name colB -

# Query YAML with yq, then format with lx
cat config.yml | yq '.services.web' | lx json pretty
```

---

## Architecture

The project separates **CLI concerns** from **reusable library logic**:

```
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
