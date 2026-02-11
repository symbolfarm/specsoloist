---
name: quine_diff
type: bundle
status: draft
---

# Overview

A tool to compare generated source code in `build/quine/src/` against original source in `src/` to identify semantic differences and verify fidelity. It performs a recursive comparison of directories, ignoring non-functional changes like whitespace and comments, and produces both a human-readable colored diff and a machine-readable JSON report.

# Types

```yaml:types
FileDiff:
  description: Represents the comparison result for a single file.
  properties:
    path:
      type: string
      description: Relative path from the root of the comparison.
    status:
      type: string
      enum: [match, mismatch, missing_original, missing_generated]
      description: The result of the comparison.
    diff:
      type: optional
      of: {type: string}
      description: The unified diff text if status is mismatch.

DiffReport:
  description: A comprehensive summary of the directory comparison.
  properties:
    summary:
      type: object
      properties:
        total_files: {type: integer}
        passed: {type: integer}
        failed: {type: integer}
        missing_original: {type: integer}
        missing_generated: {type: integer}
    details:
      type: array
      items: {type: ref, ref: quine_diff/FileDiff}
```

# Functions

```yaml:functions
run_comparison:
  inputs:
    original_dir: {type: string}
    generated_dir: {type: string}
    report_path: {type: string}
  outputs:
    report: {type: ref, ref: quine_diff/DiffReport}
  behavior: Walks both directories recursively, compares files, prints a summary and any discrepancies (with color) to stdout, and saves the JSON report to report_path.

compare_files:
  inputs:
    original_path: {type: optional, of: {type: string}}
    generated_path: {type: optional, of: {type: string}}
  outputs:
    diff: {type: ref, ref: quine_diff/FileDiff}
  behavior: Compares two individual files. Handles cases where one or both files are missing. If both exist, it uses is_semantically_equivalent to determine the status.

is_semantically_equivalent:
  inputs:
    content_a: {type: string}
    content_b: {type: string}
  outputs:
    result: {type: boolean}
  behavior: Determines if two source code strings are functionally identical by stripping comments, docstrings, and normalizing whitespace.

generate_unified_diff:
  inputs:
    content_a: {type: string}
    content_b: {type: string}
    color: {type: boolean, default: true}
  outputs:
    diff_text: {type: string}
  behavior: Produces a standard unified diff between two strings. If color is true, applies ANSI color codes.
```

# Behavior

## Recursive Walk
The tool must find all files in both `original_dir` and `generated_dir`. It should ignore common metadata directories like `.git` or `__pycache__`. Files are matched by their relative path from the directory root.

## Semantic Matching
The comparison must strip non-functional elements before comparison. This includes:
- Comments (e.g., `#` in Python, `//` or `/* */` in C-style).
- Docstrings (e.g., triple-quoted strings in Python).
- Whitespace and indentation normalization (stripping trailing whitespace, collapsing multiple spaces/newlines).

## Report Generation
The `DiffReport` must be serialized to JSON and written to the specified `report_path`. Parent directories of the report path should be created if they don't exist. The tool should also output a summary to the console with color-coded results.

# Examples

| Original Content | Generated Content | Equivalent? |
|------------------|-------------------|-------------|
| `x = 1 # set x`  | `x=1`             | Yes         |
| `"""docs"""\ndef f(): pass` | `def f(): pass` | Yes |
| `a = 1`          | `a = 2`           | No          |
| `  print( "hi" )`| `print("hi")`     | Yes |
