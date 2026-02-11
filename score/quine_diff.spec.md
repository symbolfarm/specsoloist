---
name: quine_diff
type: bundle
dependencies:
  - ui
---

# Overview

A tool to compare generated source code in `build/quine/src/` against original source in `src/` to identify semantic differences and verify fidelity. It performs recursive directory comparison, ignores non-functional changes like whitespace and comments, and generates both human-readable (colored) and machine-readable (JSON) reports.

# Types

## DiffResult

Result of a comparison for a single file path.

**Fields:**
- `path` (string): Relative path to the file from the root of the comparison.
- `status` (string): One of `PASS`, `FAIL`, `MISSING_ORIGINAL` (missing in src but exists in quine), `MISSING_GENERATED` (exists in src but missing in quine).
- `diff` (optional string): A unified diff of the file contents if status is `FAIL`.

## DiffSummary

Overall summary of the directory comparison.

**Fields:**
- `passed` (integer): Count of files that match semantically.
- `failed` (integer): Count of files that have semantic differences.
- `missing_original` (integer): Count of files present in generated but not original.
- `missing_generated` (integer): Count of files present in original but not generated.
- `results` (list of DiffResult): Detailed results for every file encountered.

# Functions

## normalize_source(content, filename) -> string

Reduces source code to a canonical semantic form to allow comparison of logic rather than formatting.
- For Python files (`.py`), it strips comments, docstrings, and normalizes non-essential whitespace (e.g., using AST parsing).
- For other files, it normalizes line endings and strips trailing whitespace.

## compare_files(original_path, generated_path, relative_path) -> DiffResult

Compares two files.
- If `original_path` does not exist: returns `MISSING_ORIGINAL`.
- If `generated_path` does not exist: returns `MISSING_GENERATED`.
- If both exist: compares their `normalize_source` output. 
- Returns `PASS` if normalized content is identical.
- Returns `FAIL` if different, including a unified diff of the original file contents in the `diff` field.

## compare_directories(original_dir, generated_dir) -> DiffSummary

Recursively walks both directories to find all files (ignoring common patterns like `__pycache__` and `.git`). Compares every file found in either directory and aggregates results into a `DiffSummary`.

## run_quine_diff(original_dir, generated_dir, report_path) -> DiffSummary

The main entry point for the tool.
1. Executes `compare_directories`.
2. Prints a summary table to the console using `ui/create_table`.
3. If there are failures, prints each failure's path and its diff.
4. Saves the summary as JSON to `report_path`.
5. Returns the `DiffSummary`.

# Behavior

## Semantic Comparison Logic
- The goal is "Fidelity": the generated code should behave identically to the original.
- In Python, we want to ensure the AST (Abstract Syntax Tree) is functionally equivalent, ignoring documentation and styling.

## Reporting
- The console output should use colors: green for `PASS`, red for `FAIL`, yellow for `MISSING`.
- The final output should clearly state if the overall result is "SUCCESS" (all PASS) or "FAILURE".

# Examples

| Path | Original Content | Generated Content | Status |
|------|------------------|-------------------|--------|
| `a.py` | `x = 1 # comment` | `x = 1` | `PASS` |
| `b.py` | `def f(): """Doc"""
  pass` | `def f():
  pass` | `PASS` |
| `c.py` | `x = 1` | `x = 2` | `FAIL` |
| `d.py` | (Exists) | (Missing) | `MISSING_GENERATED` |
