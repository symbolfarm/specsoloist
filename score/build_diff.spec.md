---
name: build_diff
type: bundle
dependencies:
  - ui
---

# Overview

A general-purpose tool for comparing build outputs produced from specs. Supports comparing any two directories of generated source code — whether that is a quine run vs original source, two successive build runs, or outputs across different language arrangements. Performs semantic (not syntactic) comparison, ignores non-functional differences like whitespace and comments, and produces both human-readable (colored) and machine-readable (JSON) reports.

The primary use cases are:
- **Quine fidelity**: compare `build/quine/src/` against the original `src/` to verify self-hosting.
- **Run-over-run regression**: compare two successive `sp conduct` outputs to detect drift or improvements.
- **Cross-language equivalence**: compare a Python arrangement output against a TypeScript arrangement output to confirm spec language-agnosticism.

# Types

## DiffResult

Result of a comparison for a single file path.

**Fields:**
- `path` (string): Relative path to the file from the root of the comparison.
- `status` (string): One of `PASS`, `FAIL`, `MISSING_LEFT` (exists in right but not left), `MISSING_RIGHT` (exists in left but not right).
- `diff` (optional string): A unified diff of the normalized file contents if status is `FAIL`.

## DiffSummary

Overall summary of a directory comparison.

**Fields:**
- `passed` (integer): Count of files that match semantically.
- `failed` (integer): Count of files that have semantic differences.
- `missing_left` (integer): Count of files present in right directory but not left.
- `missing_right` (integer): Count of files present in left directory but not right.
- `results` (list of DiffResult): Detailed results for every file encountered.
- `label_left` (string, default `"left"`): Human-readable label for the left directory.
- `label_right` (string, default `"right"`): Human-readable label for the right directory.

## BuildRun

Metadata describing a single recorded build run.

**Fields:**
- `run_id` (string): Unique identifier for the run (e.g. a timestamp string).
- `path` (string): Absolute path to the directory containing the build output.
- `timestamp` (string): ISO-8601 timestamp of when the run was recorded.
- `arrangement` (string, optional): The arrangement name or target language used for this run, if recorded.
- `meta` (dict, default `{}`): Any additional key-value metadata stored in the run's manifest file.

# Functions

## normalize_source(content, filename) -> string

Reduces source code to a canonical semantic form for comparison of logic rather than formatting.

- For Python files (`.py`): strips comments, docstrings, and normalises non-essential whitespace using AST round-trip (unparse after parse). If AST parsing fails (e.g. syntax error), falls back to stripping `#`-prefixed comment lines and normalising whitespace.
- For TypeScript/JavaScript files (`.ts`, `.tsx`, `.js`, `.mjs`): strips `//` line comments and `/* */` block comments, normalises whitespace.
- For all other text files: normalises line endings to `\n` and strips trailing whitespace from each line.
- Binary files: returned unchanged (byte-for-byte comparison).

## compare_files(left_path, right_path, relative_path) -> DiffResult

Compares two files at arbitrary absolute paths.

- If `left_path` does not exist: returns `DiffResult(path=relative_path, status="MISSING_LEFT")`.
- If `right_path` does not exist: returns `DiffResult(path=relative_path, status="MISSING_RIGHT")`.
- If both exist: compares their `normalize_source` output.
  - Returns `PASS` if normalised content is identical.
  - Returns `FAIL` with a unified diff of the **original** (un-normalised) file contents in the `diff` field.

## compare_directories(left_dir, right_dir, label_left="left", label_right="right") -> DiffSummary

Recursively walks both directories to find all files, compares each, and aggregates results.

- Ignores common non-source patterns: `__pycache__`, `.git`, `*.pyc`, `node_modules`, `.DS_Store`.
- Unions the file sets from both directories; each file is compared with `compare_files`.
- Returns a `DiffSummary` with counts and per-file `DiffResult` items.
- Files are sorted by path for deterministic output.

## list_build_runs(build_dir) -> list of BuildRun

Discovers and returns all recorded build runs under `build_dir`.

- Looks for subdirectories of `build_dir` that contain a `run_meta.json` file.
- Each `run_meta.json` must have at least `run_id` and `timestamp` fields.
- Returns runs sorted by timestamp, oldest first.
- Returns an empty list if `build_dir` does not exist or contains no valid run subdirectories.

## record_build_run(output_dir, arrangement=None, meta=None) -> BuildRun

Records a build run by writing a `run_meta.json` manifest inside `output_dir`.

- Generates a `run_id` from the current UTC timestamp (ISO-8601 format, colons replaced with hyphens for filesystem safety).
- Writes a JSON file at `output_dir/run_meta.json` with `run_id`, `timestamp`, `arrangement` (or null), and any extra `meta` key-value pairs.
- Returns a `BuildRun` representing the newly recorded run.
- Raises `FileNotFoundError` if `output_dir` does not exist.

## run_diff(left_dir, right_dir, report_path, label_left="left", label_right="right") -> DiffSummary

Main entry point for a single diff operation.

1. Calls `compare_directories(left_dir, right_dir, label_left, label_right)`.
2. Prints a summary table to the console using `ui` functions:
   - Header row labels use `label_left` and `label_right`.
   - File rows are coloured: green for `PASS`, red for `FAIL`, yellow for `MISSING_*`.
3. For each `FAIL` result, prints the file path and its `diff`.
4. Prints an overall verdict: `SUCCESS` (all PASS) or `FAILURE`.
5. Saves the full `DiffSummary` as JSON to `report_path` (creates parent directories as needed).
6. Returns the `DiffSummary`.

# Behavior

## Semantic comparison philosophy

The goal is functional equivalence: two files `PASS` if a developer reading both would conclude they implement the same behaviour. Comments and docstrings are cosmetic. Whitespace is cosmetic. Only logic matters.

AST-based normalisation for Python is preferred because it catches reorderings that line-level comparison would miss (e.g. swapping two independent assignments). Falls back to text-level comment stripping on syntax errors.

## Report format

The JSON report has the shape of a serialised `DiffSummary`: `passed`, `failed`, `missing_left`, `missing_right`, `label_left`, `label_right`, and `results` (array of `DiffResult` objects with `path`, `status`, `diff`).

## Ignored patterns

The following patterns are always excluded from comparison:
- `__pycache__/` (and `.pyc` files)
- `.git/`
- `node_modules/`
- `.DS_Store`
- `run_meta.json` (build run metadata, not source)
- `*.spec.md` (spec files are inputs, not outputs)

# Examples

| Path | Left Content | Right Content | Status |
|------|--------------|---------------|--------|
| `a.py` | `x = 1  # comment` | `x = 1` | `PASS` |
| `b.py` | `def f():\n  """Doc"""\n  pass` | `def f():\n  pass` | `PASS` |
| `c.py` | `x = 1` | `x = 2` | `FAIL` |
| `d.py` | (exists) | (missing) | `MISSING_RIGHT` |
| `e.py` | (missing) | (exists) | `MISSING_LEFT` |
