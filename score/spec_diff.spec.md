---
name: spec_diff
type: bundle
---

# Overview

Spec-vs-code drift detection for SpecSoloist. Compares a spec's declared public symbols against
a compiled implementation and its test file, reporting three categories of issue:

- **MISSING** — symbol declared in the spec but absent from the compiled code
- **UNDOCUMENTED** — public symbol present in the compiled code but not declared in the spec
- **TEST_GAP** — test scenario described in the spec with no matching test function

Results are returned as structured data objects and can be formatted as human-readable text or JSON.

# Types

## SpecDiffIssue

A single drift issue found by spec_diff.

**Fields:**
- `kind` (string): One of `"MISSING"`, `"UNDOCUMENTED"`, `"TEST_GAP"`.
- `symbol` (string): The symbol name (or quoted scenario description for TEST_GAP).
- `detail` (string): Human-readable explanation of the issue.

## SpecDiffResult

Result of comparing a spec against its compiled code.

**Fields:**
- `spec_name` (string): The spec name that was diffed.
- `code_path` (optional string): Absolute path to the implementation file that was inspected, or `None` if not found.
- `test_path` (optional string): Absolute path to the test file that was inspected, or `None` if not found.
- `issues` (list of SpecDiffIssue, default empty): All issues detected.

**Properties:**
- `issue_count` (int): Total number of issues in `issues`.

**Methods:**
- `to_dict()` -> dict: Serialise to a JSON-compatible dict with keys `spec_name`, `code_path`, `test_path`, `issue_count`, and `issues` (list of dicts with `kind`, `symbol`, `detail`).

# Functions

## extract_spec_symbols(parsed_spec) -> list of string

Extract the declared public symbol names from a parsed spec object.

- For `bundle` specs: returns keys from `bundle_functions` and `bundle_types`. If both are empty, falls back to scanning `## Heading` patterns in the spec body.
- For `function` or `class` specs: returns `[metadata.name]`.
- For `reference` specs: returns an empty list (external libraries — nothing to diff).
- For all other types (`module`, `type`, `workflow`, etc.): scans `##` and `###` headings in the body for identifiers that look like function or class names (snake_case, UpperCamelCase, or headings that include a `(` signature). Skips common prose section titles (Overview, Behavior, Examples, etc.).

Deduplicates the result before returning.

## extract_code_symbols(code_path) -> list of string

Return top-level function and class names from a Python source file, plus public method names from each class.

- Uses the AST module — the file is never imported or executed.
- Top-level `def`, `async def`, and `class` nodes are included.
- For each class, includes method names that do not start with `__`, plus `__init__`.
- Returns an empty list if the file does not exist or cannot be parsed.

## extract_test_names(test_path) -> list of string

Return all function names starting with `test_` from a Python test file.

- Uses the AST module — the file is never imported or executed.
- Walks the full AST (not just top-level) to find test functions inside classes too.
- Returns an empty list if `test_path` is falsy, the file does not exist, or cannot be parsed.

## extract_test_scenarios(body) -> list of string

Extract scenario descriptions from a `## Test Scenarios` section in a spec body string.

- Returns an empty list if no `## Test Scenarios` (or `# Test Scenarios`) heading is found.
- Captures text between the heading and the next top-level heading.
- Returns one entry per list item (`- description`, `* description`, `+ description`) or `###` sub-heading found in the section.

## diff_spec(spec_name, root_dir, arrangement=None, code_path=None, test_path=None) -> SpecDiffResult

Compare a spec against its compiled implementation.

**Arguments:**
- `spec_name` (string): The spec name (e.g. `"parser"`, `"manifest"`).
- `root_dir` (string): Project root directory used for path resolution.
- `arrangement` (optional): Arrangement object; if provided, used to resolve implementation and test paths before falling back to conventions.
- `code_path` (optional string): Explicit path to the implementation file; overrides auto-detection.
- `test_path` (optional string): Explicit path to the test file; overrides auto-detection.

**Path resolution (when not overridden):**

Implementation file search order:
1. `arrangement.output_paths.resolve_implementation(spec_name)` if arrangement is provided
2. `{root_dir}/src/specsoloist/{spec_name}.py`
3. `{root_dir}/src/spechestra/{spec_name}.py`
4. `{root_dir}/build/{spec_name}.py`
5. `{root_dir}/src/{spec_name}.py`

Test file search order:
1. `arrangement.output_paths.resolve_tests(spec_name)` if arrangement is provided
2. `{root_dir}/tests/test_{spec_name}.py`
3. `{root_dir}/build/tests/test_{spec_name}.py`

**Spec file resolution:**
Looks for `{root_dir}/score/{spec_name}.spec.md`, falling back to `{root_dir}/src/{spec_name}.spec.md`. Returns a `SpecDiffResult` with a single MISSING issue if the spec file is not found.

**Issue detection (skipped for `reference` specs):**
1. MISSING: symbols in the spec but not found in the code file.
2. UNDOCUMENTED: public symbols (no leading `_`) in the code but not declared in the spec.
3. TEST_GAP: scenarios in the spec's `## Test Scenarios` section with no matching test function. Matching is fuzzy — a scenario matches if any significant word (≥ 4 chars, not a stop word) appears in any test function name.

## format_result_text(result) -> string

Format a `SpecDiffResult` as human-readable terminal output.

- If `issue_count == 0`: returns `"{spec_name} — no issues"`.
- Otherwise: returns a multi-line string with one line per issue, each prefixed with a marker symbol and the issue kind (`MISSING`, `UNDOCUMENTED`, `TEST GAP`).

## format_result_json(result) -> string

Format a `SpecDiffResult` as a JSON string using `result.to_dict()`.

# Test Scenarios

- extract_code_symbols returns top-level functions
- extract_code_symbols returns class names
- extract_code_symbols does not return nested functions
- extract_code_symbols returns empty list for missing file
- extract_code_symbols returns empty list on syntax error
- extract_spec_symbols returns function names from bundle yaml:functions block
- extract_spec_symbols returns spec name for function type spec
- extract_spec_symbols returns heading symbols from module spec
- extract_spec_symbols returns empty list for reference spec
- diff_spec reports no issues when spec and code are in sync
- diff_spec reports MISSING for symbol in spec but not in code
- diff_spec reports UNDOCUMENTED for public symbol in code but not in spec
- diff_spec does not flag private symbols as UNDOCUMENTED
- format_result_json produces valid parseable JSON
- format_result_text shows no issues message when clean
- format_result_text shows MISSING marker
- format_result_text shows UNDOCUMENTED marker
- format_result_text shows TEST GAP marker
